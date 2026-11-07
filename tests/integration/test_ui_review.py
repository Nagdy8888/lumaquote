"""Whole-app desktop and portrait review of every route in a real browser, with accessibility, layout,
capture-mode privacy, keyboard, live-update and timing checks.

Label `local-substitute`: headless Chromium against the Vite dev server (not a production build), no
assistive technology and no real device. The tenant and every message are synthetic.
"""

import json
import os
import subprocess
from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest
from browser_servers import ROOT, run_review
from test_manual_workflow import create_request, make_draft, post

FIXTURE_EMAIL = "buyer.fixture@example.test"
FIXTURE_PHONE = "+20 100 555 0199"
COMMAND = "node scripts/python.cjs -m pytest tests/integration/test_ui_review.py -q"
CONVERSATION_VIEWS = (
    "conversation-conversation-desktop",
    "conversation-conversation-portrait",
    "conversation-approval-open-desktop",
)


def current_commit() -> str:
    """Return the short commit the review ran on, or "unknown" when git is unavailable."""
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


@pytest.mark.browser
def test_every_route_passes_axe_fits_both_viewports_and_masks_capture(environment):
    """19 views (seven routes at two sizes plus the conversation states) are accessible, fit, private and fast to load.

    Each view must have no axe violations, no horizontal overflow, one main landmark and no unnamed
    control. With capture mode on, no email, phone number or key pattern may remain in the visible
    text, and the synthetic email and phone in a customer message must be masked. The keyboard pass must
    reach the skip link, the conversation list, the composer and the approval control. The live pass
    must see the "Live" label, at least one event-stream request and a second browser's note.
    """
    cid = create_request(environment)
    reply = post(
        environment,
        f"/conversations/{cid}/customer-reply",
        {"text": f"Please also send the data sheet to {FIXTURE_EMAIL} or call {FIXTURE_PHONE}."},
        uuid4(),
    )
    assert reply.status_code == 200, reply.text
    make_draft(environment, cid)
    report_path = ROOT / ".local" / f"ui-review-{environment['company']}.json"
    report = run_review(
        environment,
        "ui-review.cjs",
        "ui-review",
        report_path,
        {"conversation_id": cid, "fixture_email": FIXTURE_EMAIL},
        timeout=280,
    )
    views = report["views"]
    assert report["console"] == [], report["console"]
    assert len(views) == 19, sorted(views)
    for key, entry in views.items():
        assert entry["axe"] == [], (key, entry["axe"])
        assert entry["horizontal_overflow"] is False, key
        assert entry["main_landmarks"] == 1 and entry["h1_count"] >= 1, key
        assert entry["unnamed_controls"] == 0, key
        assert entry["capture"]["private_matches"] == [], (key, entry["capture"]["private_matches"])
    for key in CONVERSATION_VIEWS:
        assert views[key]["fixture_email_visible_in_normal_mode"] is True, key
        assert views[key]["capture"]["masked_email"] and views[key]["capture"]["masked_phone"], key
    assert set(report["keyboard"]["tab_presses_to"]) == {"skip", "list", "composer", "approval"}, report[
        "keyboard"
    ]
    assert report["live"]["live_label_seen"] is True, report["live"]
    assert report["live"]["events_requests"] >= 1, report["live"]
    assert report["live"]["cross_tab_ms"] is not None, report["live"]
    target = os.environ.get("LUMA_UI_REVIEW_EVIDENCE")
    if target:
        timings = {
            key: entry["timing"] for key, entry in views.items() if key.endswith(("-desktop", "-portrait"))
        }
        Path(target).write_text(
            json.dumps(
                {
                    "date": date.today().isoformat(),
                    "commit": current_commit(),
                    "label": "local-substitute",
                    "command": COMMAND,
                    "result": (
                        f"passed: {len(views)} views, 0 axe violations, no horizontal overflow, no private "
                        "pattern in capture mode, 0 console errors"
                    ),
                    "scope": (
                        "Whole-app review of / /inbox /quotations /catalog /integrations /requests/new "
                        "/does-not-exist at 1440x1050 and 390x844, plus the populated conversation in the "
                        "conversation view, the quotation view and with the approval panel open. Headless "
                        "Chromium (reduced motion, so the 3D scene shows its static fallback) against the "
                        "Vite dev server, synthetic tenant. Not a screen-reader, real-device or "
                        "production-build performance review."
                    ),
                    "timing_note": (
                        "dev-server numbers (unbundled modules, software rendering); not a production budget"
                    ),
                    "keyboard": report["keyboard"],
                    "live": report["live"],
                    "views": {
                        key: {
                            "axe_violations": len(entry["axe"]),
                            "horizontal_overflow": entry["horizontal_overflow"],
                            "unnamed_controls": entry["unnamed_controls"],
                            "targets_under_24px": entry["small_targets"],
                            "capture_private_matches": entry["capture"]["private_matches"],
                            "timing": timings[key],
                        }
                        for key, entry in views.items()
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
