"""Desktop and portrait accessibility and layout review of every top-level staff page in a real browser.

Local substitute: headless Chromium with axe-core, not assistive technology or real devices. Synthetic tenant.
"""

import os
from pathlib import Path

import pytest
from browser_servers import ROOT, run_review
from test_manual_workflow import create_request, make_draft


@pytest.mark.browser
def test_every_page_passes_axe_and_fits_both_viewports(environment):
    """Seven views at 1440 px and 430 px (six pages plus a populated conversation with a draft quotation).

    Each must have no axe violations, no horizontal overflow, one main landmark, named controls and
    no interactive control smaller than 24 x 24 CSS pixels (WCAG 2.2 target size, minimum).
    """
    cid = create_request(environment)
    make_draft(environment, cid)
    report_path = Path(
        os.environ.get("LUMA_PAGE_REVIEW_EVIDENCE", ROOT / ".local" / f"pages-{environment['company']}.json")
    )
    report = run_review(
        environment, "page-review.cjs", "pages", report_path, {"conversation_id": cid}, timeout=170
    )
    assert report["console"] == [], report["console"]
    assert len(report["pages"]) == 14
    for key, entry in report["pages"].items():
        assert entry["axe"] == [], (key, entry["axe"])
        assert entry["horizontal_overflow"] is False, key
        assert entry["main_landmarks"] == 1 and entry["h1_count"] >= 1, key
        assert entry["unnamed_controls"] == 0, key
        assert entry["small_targets"] == [], (key, entry["small_targets"])
