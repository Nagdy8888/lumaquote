"""Drive export protocol against real PostgreSQL and private Storage, with a Python stand-in for Apps Script.

The stand-in signs envelopes exactly as `gas/Exports.gs` does. This proves the
backend protocol, its replay/lease/digest rules and byte identity with the staff
PDF. It does NOT prove the Apps Script code runs in Google, that Drive stores the
file or that a tunnel reaches the backend; those need the live steps in
docs/MORNING_ACTIONS.md.
"""

import base64
import hashlib
import hmac
import json
import time
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from luma.core.config import settings
from luma.google_gateway import app
from psycopg.rows import dict_row
from test_manual_workflow import create_request, get_detail, make_draft, post

SHEET = "synthetic-workbook"


class Poller:
    """Minimal Apps Script substitute that signs and posts export envelopes to the real gateway."""

    def __init__(self, company, secret):
        """Remember the bound company and shared secret used for every envelope."""
        self.company, self.secret = str(company), secret

    def send(self, path, event, valid=True, **fields):
        """Sign exact JSON bytes and post them; `valid=False` sends a forged signature."""
        envelope = {
            "schema_version": 1,
            "company_id": self.company,
            "spreadsheet_id": SHEET,
            "timestamp": int(time.time()),
            "nonce": str(uuid4()),
            "event": event,
            **fields,
        }
        return self.raw(path, envelope, valid)

    def raw(self, path, envelope, valid=True):
        """Post an already-built envelope, optionally with a forged signature."""
        body = json.dumps(envelope).encode()
        signature = hmac.new(self.secret.encode(), body, hashlib.sha256).hexdigest() if valid else "0" * 64
        with TestClient(app) as client:
            return client.post(path, content=body, headers={"X-Luma-Signature": signature})

    def claim(self, **kwargs):
        """Ask for the next export."""
        return self.send("/callbacks/google/exports/claim", "drive_export_claim", **kwargs)

    def receipt(self, claimed, outcome="stored", **overrides):
        """Report an outcome for a claimed export, reading the bytes back like Drive would."""
        pdf = base64.b64decode(claimed["pdf_base64"])
        fields = {
            "export_id": claimed["export_id"],
            "claim_token": claimed["claim_token"],
            "outcome": outcome,
            **(
                {
                    "drive_file_id": "drive-file-1",
                    "sha256": hashlib.sha256(pdf).hexdigest(),
                    "size": len(pdf),
                }
                if outcome == "stored"
                else {"error_code": "drive_error"}
            ),
            **overrides,
        }
        return self.send("/callbacks/google/exports/receipt", "drive_export_receipt", **fields)


@pytest.fixture
def poller(environment, monkeypatch):
    """Configure the gateway for the isolated company and return a signing stand-in."""
    monkeypatch.setenv("GOOGLE_COMPANY_ID", str(environment["company"]))
    monkeypatch.setenv("GOOGLE_SHEET_ID", SHEET)
    monkeypatch.setenv("GOOGLE_CALLBACK_SECRET", "test-only-export-key-" + "y" * 32)
    settings.cache_clear()
    return Poller(environment["company"], settings().google_callback_secret.get_secret_value())


def approve(env, cid, revision=1):
    """Approve the current revision through the real staff API."""
    response = post(
        env, f"/conversations/{cid}/decision", {"expected_revision": revision, "decision": "approve"}
    )
    assert response.status_code == 200, response.text
    return response


def exports(env):
    """Read this tenant's export rows."""
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        return conn.execute(
            "select * from luma.drive_exports where company_id=%s order by created_at", (env["company"],)
        ).fetchall()


def approved_quote(env):
    """Create, draft and approve one quotation; return its conversation and quote ids."""
    cid = create_request(env)
    quote = make_draft(env, cid)
    approve(env, cid)
    env["files"].append(f"{env['company']}/quotes/{quote['id']}.pdf")
    return cid, quote


def test_only_an_approved_revision_is_exported_and_bytes_match_the_staff_pdf(environment, poller):
    """An unapproved draft is invisible; after approval one claim returns the exact bytes the staff PDF serves."""
    env = environment
    cid = create_request(env)
    quote = make_draft(env, cid)
    env["files"].append(f"{env['company']}/quotes/{quote['id']}.pdf")
    assert exports(env) == []
    assert poller.claim().json() == {"export": None}
    approve(env, cid)
    [row] = exports(env)
    assert (row["status"], row["attempts"], str(row["quote_id"])) == ("queued", 0, quote["id"])
    claimed = poller.claim().json()["export"]
    pdf = base64.b64decode(claimed["pdf_base64"])
    staff = env["api"].get(f"/api/quotes/{quote['id']}/pdf", headers=env["headers"]).content
    assert pdf == staff and pdf.startswith(b"%PDF")
    assert claimed["sha256"] == hashlib.sha256(staff).hexdigest() and claimed["size"] == len(staff)
    assert claimed["filename"].endswith("-r1.pdf") and "/" not in claimed["filename"]
    assert poller.claim().json() == {"export": None}  # leased, not available to a second poller
    done = poller.receipt(claimed)
    assert done.status_code == 200 and done.json() == {"status": "done"}
    [row] = exports(env)
    assert row["status"] == "done" and row["drive_file_id"] == "drive-file-1" and row["claim_token"] is None
    assert poller.claim().json() == {"export": None}
    assert get_detail(env, cid)["quote"]["status"] == "approved"  # export never alters the quotation


def test_forged_stale_cross_company_and_replayed_envelopes_are_rejected(environment, poller):
    """Signature, timestamp, company mapping and nonce rules apply to both endpoints."""
    approved_quote(environment)
    assert poller.claim(valid=False).status_code == 401
    assert poller.claim(timestamp=int(time.time()) - 600).status_code == 401
    assert poller.claim(company_id=str(uuid4())).status_code == 403
    assert poller.claim(schema_version=2).status_code == 422
    assert poller.claim(unexpected="field").status_code == 422
    envelope = {
        "schema_version": 1,
        "company_id": poller.company,
        "spreadsheet_id": SHEET,
        "timestamp": int(time.time()),
        "nonce": str(uuid4()),
        "event": "drive_export_claim",
    }
    assert poller.raw("/callbacks/google/exports/claim", envelope).status_code == 200
    assert poller.raw("/callbacks/google/exports/claim", envelope).status_code == 409
    with TestClient(app) as client:
        assert client.post("/callbacks/google/exports/claim", content=b"x" * 1025).status_code == 413
        assert client.post("/callbacks/google/exports/receipt", content=b"x" * 2049).status_code == 413


def test_receipt_needs_the_current_claim_token_and_identical_digest(environment, poller):
    """A stale token, wrong digest or wrong size cannot complete an export; a digest mismatch retries."""
    env = environment
    approved_quote(env)
    claimed = poller.claim().json()["export"]
    assert poller.receipt(claimed, claim_token=str(uuid4())).status_code == 409
    assert poller.receipt(claimed, sha256="0" * 64).status_code == 422
    [row] = exports(env)
    assert (row["status"], row["error_code"], row["claim_token"]) == ("queued", "digest_mismatch", None)
    second = poller.claim().json()["export"]
    assert second["claim_token"] != claimed["claim_token"] and second["sha256"] == claimed["sha256"]
    assert poller.receipt(claimed).status_code == 409  # the first holder's token is stale now
    assert poller.receipt(second, size=1).status_code == 422
    third = poller.claim().json()["export"]
    assert poller.receipt(third).json() == {"status": "done"}
    assert poller.receipt(third).json() == {"status": "done"}  # identical replay is idempotent
    assert poller.receipt(third, drive_file_id="other").status_code == 409
    [row] = exports(env)
    assert row["status"] == "done" and row["attempts"] == 3


def test_failures_retry_then_block_and_expired_leases_are_reclaimed(environment, poller):
    """Reported failures requeue up to five attempts; a silent client's lease expires and is reclaimed."""
    env = environment
    approved_quote(env)
    for attempt in range(1, 5):
        claimed = poller.claim().json()["export"]
        assert poller.receipt(claimed, "failed").json() == {"status": "queued"}
        assert exports(env)[0]["attempts"] == attempt
    claimed = poller.claim().json()["export"]
    assert poller.receipt(claimed, "failed").json() == {"status": "blocked"}
    assert poller.claim().json() == {"export": None}
    [row] = exports(env)
    assert (row["status"], row["attempts"], row["error_code"]) == ("blocked", 5, "drive_error")
    with psycopg.connect(env["dsn"]) as conn:
        conn.execute(
            "update luma.drive_exports set status='claimed',attempts=1,lease_until=now()-interval '1 minute',claim_token=%s where company_id=%s",
            (uuid4(), env["company"]),
        )
    reclaimed = poller.claim().json()["export"]
    assert reclaimed and exports(env)[0]["attempts"] == 2
    with psycopg.connect(env["dsn"]) as conn:
        conn.execute(
            "update luma.drive_exports set lease_until=now()-interval '1 minute',attempts=5 where company_id=%s",
            (env["company"],),
        )
    assert poller.claim().json() == {"export": None}
    assert exports(env)[0]["status"] == "blocked" and exports(env)[0]["error_code"] == "attempts_exhausted"


def test_changed_pdf_blocks_the_export_instead_of_shipping_different_bytes(environment, poller):
    """The digest pinned at first claim must match later claims; a difference is blocked, never exported."""
    env = environment
    approved_quote(env)
    first = poller.claim().json()["export"]
    assert poller.receipt(first, "failed").json() == {"status": "queued"}
    with psycopg.connect(env["dsn"]) as conn:
        conn.execute(
            "update luma.drive_exports set pdf_sha256=%s where company_id=%s", ("1" * 64, env["company"])
        )
    assert poller.claim().json() == {"export": None}
    [row] = exports(env)
    assert (row["status"], row["error_code"]) == ("blocked", "pdf_changed")


def test_rejected_or_revised_quotes_are_not_exported_and_each_revision_exports_once(environment, poller):
    """Only approval queues work, a repeated approval cannot duplicate it and a new revision is its own export."""
    env = environment
    cid = create_request(env)
    make_draft(env, cid)
    rejected = post(env, f"/conversations/{cid}/decision", {"expected_revision": 1, "decision": "reject"})
    assert rejected.status_code == 200
    assert exports(env) == []
    second = make_draft(env, cid, quantity=2)
    env["files"].append(f"{env['company']}/quotes/{second['id']}.pdf")
    approve(env, cid, revision=second["revision"])
    assert [(row["revision"], row["status"]) for row in exports(env)] == [(second["revision"], "queued")]


def test_concurrent_pollers_cannot_claim_the_same_export(environment, poller):
    """Several simultaneous claims for one queued export yield exactly one lease and one attempt."""
    from concurrent.futures import ThreadPoolExecutor

    env = environment
    approved_quote(env)
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda _: poller.claim().json(), range(6)))
    leased = [r["export"] for r in results if r["export"]]
    assert len(leased) == 1
    [row] = exports(env)
    assert (row["status"], row["attempts"], str(row["claim_token"])) == (
        "claimed",
        1,
        leased[0]["claim_token"],
    )
