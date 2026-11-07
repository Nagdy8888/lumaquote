"""Opt-in paid evaluation of the real agent over the development scenarios.

Each scenario drives the actual stack for one isolated synthetic tenant seeded with
the full 72-model catalog: authenticated API, private media upload, real
transcription/vision/Responses calls through the budget reservation path, the
persisted LangGraph and the durable job lifecycle. Staff approval and delivery are
never run, so nothing can be sent. The test records measurements; it does not fail
because an agent outcome differs from the answer key (that is a result). It only
fails for harness errors. The development split is the default. The holdout (`LUMA_EVAL_SPLIT=holdout`) runs only when a freeze record pins the current fixtures, agent code and model configuration, no earlier holdout run is recorded and `LUMA_EVAL_CONFIRM_HOLDOUT` is set; it is one-shot and the run is recorded in the freeze file.
"""

import json
import os
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from luma.core.config import settings
from luma.core.errors import DomainError
from luma.features.inventory.ledger import seed_opening
from luma.setup.bootstrap import FAMILIES
from luma_agent import observability as tracing
from luma_agent.runtime.audio import process_audio
from luma_agent.runtime.conversations import process_conversation
from luma_agent.runtime.jobs import finish_job
from luma_agent.runtime.media import process_media
from psycopg.rows import dict_row
from test_graph_restart import pending
from test_manual_workflow import get_detail, post
from test_photo_intake import upload_photo
from test_voice_intake import upload

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import evaluation_dataset as dataset  # noqa: E402

pytestmark = pytest.mark.skipif(
    os.environ.get("LUMA_RUN_LIVE_EVAL") != "1",
    reason="Paid agent evaluation requires explicit opt-in (LUMA_RUN_LIVE_EVAL=1).",
)

SCENARIOS, ORACLE = dataset.load()
SPLIT = os.environ.get("LUMA_EVAL_SPLIT", "development")
HOLDOUT_CONFIRMATION = "spend-the-holdout-once"
HOLDOUT_BLOCKERS = (
    dataset.freeze_problems(dataset.load_freeze(), dataset.freeze_fingerprints())
    + (
        []
        if os.environ.get("LUMA_EVAL_CONFIRM_HOLDOUT") == HOLDOUT_CONFIRMATION
        else ["confirmation not given"]
    )
    if SPLIT == "holdout"
    else []
)
SELECTED = [
    item
    for item in SCENARIOS
    if item["split"] == SPLIT
    and not HOLDOUT_BLOCKERS
    and (not os.environ.get("LUMA_EVAL_IDS") or item["id"] in os.environ["LUMA_EVAL_IDS"].split(","))
]


@pytest.fixture(scope="module", autouse=True)
def record_run_start():
    """Pin the scenario and oracle hashes when a run starts (rule R11).

    `scripts/summarize_agent_run.py` refuses to score the run against different fixtures
    unless the report is explicitly labeled post-hoc. The first start of a run name wins,
    so resuming a run cannot silently re-pin changed answer keys.
    """
    if SELECTED:
        RUN_DIR.mkdir(parents=True, exist_ok=True)
        start = RUN_DIR / "run.json"
        if not start.exists():
            start.write_text(
                json.dumps(
                    {
                        "started": datetime.now(UTC).isoformat(),
                        "split": SPLIT,
                        "fixtures_sha256": dataset.fingerprints(),
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
    yield


@pytest.fixture(scope="module", autouse=True)
def record_holdout_consumption():
    """After a holdout run (even a partial one) append it to the freeze record so it cannot be repeated."""
    yield
    if SPLIT == "holdout" and SELECTED:
        record = dataset.load_freeze()
        record["holdout_runs"].append(
            {
                "run": os.environ.get("LUMA_EVAL_RUN", "unnamed"),
                "finished": datetime.now(UTC).isoformat(),
                "scenarios": len(SELECTED),
            }
        )
        dataset.FREEZE_FILE.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def test_holdout_is_refused_unless_frozen_unspent_and_confirmed():
    """A holdout selection with any blocker runs nothing and fails loudly with the reasons."""
    assert not HOLDOUT_BLOCKERS, "Holdout refused: " + "; ".join(HOLDOUT_BLOCKERS)


RUN_DIR = Path(".local/evaluation-runs") / os.environ.get("LUMA_EVAL_RUN", "unnamed")
MAX_USD = float(os.environ.get("LUMA_EVAL_MAX_USD", "3.00"))


def seed_catalog(env):
    """Replace the fixture's three products with the 72-model synthetic catalog using the bootstrap formulas."""
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        for table in ("stock_reservations", "stock_movements", "stock_levels"):
            conn.execute(f"delete from luma.{table} where company_id=%s", (env["company"],))
        conn.execute("delete from luma.products where company_id=%s", (env["company"],))
        for family, prefix, label, watts, lumens, base_price in FAMILIES:
            for i in range(12):
                sku, cct = f"{prefix}-{i + 1:03d}", [3000, 4000, 5000][i % 3]
                pid = uuid4()
                power, light = watts + (i // 3) * 3, lumens + (i // 3) * 250
                ip = "IP65" if prefix in ("OD", "HB") else "IP44"
                conn.execute(
                    """insert into luma.products(id,company_id,sku,name,family,description,watts,lumens,cct,
                    ip_rating,price,discontinued,source_id,page,snapshot_id)
                    values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1,%s)""",
                    (
                        pid,
                        env["company"],
                        sku,
                        f"{label} {power}W / {cct}K",
                        family,
                        f"{light} lm, {ip}, {cct}K. Fictional technical data.",
                        power,
                        light,
                        cct,
                        ip,
                        base_price + (i // 3) * 8,
                        i == 11,
                        env["source"],
                        env["snapshot"],
                    ),
                )
                seed_opening(conn, env["company"], pid, 0 if i == 10 else 180 - i * 9, "test")


def drain(env, cid, errors, scenario):
    """Run this conversation's queued jobs in-process like `worker.tick`, never touching another tenant.

    Every job runs inside the worker's masked LangSmith root trace (`observability.job_trace`), so the
    evaluation is traced exactly like production; the traced copy of the job also names the evaluation
    run and scenario so each trace can be found. The copy is used for tracing only.
    """
    for _ in range(10):
        with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
            job = conn.execute(
                """update luma.jobs set status='running',fence=fence+1,attempts=attempts+1,
                lease_until=now()+interval '120 seconds'
                where id=(select id from luma.jobs where company_id=%s and conversation_id=%s
                and status='queued' order by created_at limit 1 for update skip locked) returning *""",
                (env["company"], cid),
            ).fetchone()
        if not job:
            return
        traced = {
            **job,
            "payload": {
                **(job.get("payload") or {}),
                "evaluation_run": os.environ.get("LUMA_EVAL_RUN", "unnamed"),
                "evaluation_scenario": scenario,
            },
        }
        with tracing.job_trace(traced) as run:
            outcome, failure = "done", None
            try:
                if job["kind"] == "agent":
                    process_conversation(job)
                elif job["kind"] == "transcribe":
                    process_audio(job)
                elif job["kind"] == "read_photo":
                    process_media(job, "image")
                else:
                    raise DomainError("Unexpected job kind.")
                finish_job(job, "done")
            except Exception as error:
                outcome = "blocked" if isinstance(error, DomainError) else "failed"
                failure = type(error).__name__
                errors.append(failure)
                finish_job(job, outcome, failure)
            tracing.finish(run, outcome, failure)
        tracing.flush()


def observe(env, cid):
    """Map persisted state to the answer key's vocabulary without trusting any message text."""
    detail = get_detail(env, cid)
    if detail["quote"]:
        return "draft_quote", detail["quote"]["content"]["subtotal"]
    if detail["conversation"]["status"] == "needs_staff":
        return "needs_staff", None
    if pending(env, cid) == ("clarify",):
        return "clarify", None
    return f"other:{detail['conversation']['status']}", None


def spent(directory):
    """Sum recorded estimated spend of earlier scenarios in this run so one run cannot exceed its own cap."""
    total = 0.0
    for path in directory.glob("e*.json"):
        total += json.loads(path.read_text(encoding="utf-8")).get("usage_usd", 0.0)
    return total


def run_turns(env, item, errors):
    """Play every customer turn through the real stack; return per-turn actions, replies, readings and timing."""
    observed, readings, start = [], [], time.perf_counter()
    cid = None
    for index, turn in enumerate(item["turns"]):
        if turn["kind"] == "text" and index == 0:
            created = post(
                env, "/conversations", {"customer_name": "Synthetic evaluation", "text": turn["text"]}
            )
            assert created.status_code == 200, created.text
            cid = created.json()["id"]
        elif turn["kind"] == "text":
            reply = post(env, f"/conversations/{cid}/customer-reply", {"text": turn["text"]})
            assert reply.status_code == 200, reply.text
        else:
            created = post(env, "/conversations", {"customer_name": "Synthetic evaluation", "text": "Hello."})
            assert created.status_code == 200, created.text
            cid = created.json()["id"]
            data = (dataset.FIXTURES / turn["spec"]["asset"]).read_bytes()
            sent = (upload if turn["kind"] == "audio" else upload_photo)(env, cid, data)
            assert sent.status_code == 200, sent.text
        drain(env, cid, errors, item["id"])
        observed.append(observe(env, cid)[0])
    detail = get_detail(env, cid)
    for message in detail["messages"]:
        if message.get("kind") in ("audio", "image"):
            readings.append(
                {
                    "kind": message["kind"],
                    "status": message.get("media_status"),
                    "text": message["body"][:300],
                }
            )
    replies = [d["preview"] for d in detail["delivery"] if d["kind"] == "reply"]
    return cid, observed, observe(env, cid)[1], replies, readings, (time.perf_counter() - start) * 1000


@pytest.mark.parametrize("item", SELECTED, ids=lambda item: item["id"])
def test_agent_on_development_scenario(environment, monkeypatch, item):
    """Run one scenario with paid AI enabled, score it against the answer key and persist a credential-free record."""
    env = environment
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    if spent(RUN_DIR) >= MAX_USD:
        pytest.skip(f"run spend cap USD {MAX_USD} reached")
    seed_catalog(env)
    monkeypatch.setenv("ENABLE_PAID_AI", "true")
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    settings.cache_clear()
    tracing.reset()
    assert tracing.tracing_enabled(), (
        "Every evaluation run must be traced: set LANGSMITH_API_KEY in .env or .env.local"
    )
    errors: list[str] = []
    try:
        cid, observed, subtotal, replies, readings, milliseconds = run_turns(env, item, errors)
        result = dataset.score(item, ORACLE[item["id"]], observed, subtotal, replies)
        with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
            usage = conn.execute(
                "select coalesce(sum(estimated),0) total, count(*) filter (where status='unknown') unknown from luma.usage where company_id=%s",
                (env["company"],),
            ).fetchone()
            outbox = conn.execute(
                "select kind,status,count(*) n from luma.outbox where company_id=%s group by kind,status",
                (env["company"],),
            ).fetchall()
            sends = sum(
                row["n"]
                for row in outbox
                if row["kind"] == "quotation"
                or row["status"] in ("submitting", "submitted", "delivered", "read", "local_delivered")
            )
            lines = conn.execute(
                "select content from luma.quotes where company_id=%s order by created_at desc limit 1",
                (env["company"],),
            ).fetchone()
        supported = all(
            dataset.supported(dataset.catalog_model(), line["sku"], line["quantity"]) is None
            for line in (lines["content"]["lines"] if lines else [])
        )
        result.update(
            decision_ms=round(milliseconds, 1),
            usage_usd=float(usage["total"]),
            unresolved_usage=usage["unknown"],
            unauthorized_sends=sends,
            outbox={f"{row['kind']}:{row['status']}": row["n"] for row in outbox},
            quote_lines_all_supported=supported,
            job_errors=errors,
            readings=readings,
            replies=replies,
        )
    except Exception as error:
        result = {
            "id": item["id"],
            "modality": item["modality"],
            "status": "error",
            "error": type(error).__name__,
            "usage_usd": 0.0,
            "job_errors": errors,
        }
    (RUN_DIR / f"{item['id']}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    assert result["status"] != "error", result.get("error")
    assert re.fullmatch(r"e\d{3}", item["id"])
