"""Review of the optional 3D lighting scene in a real browser against isolated native servers.

Drives `tests/browser/scene-review.cjs` (Playwright and axe) over the signed-in overview with motion allowed,
then reduced, and records lazy loading, keyboard use, performance, portrait layout and capture privacy.
Local substitute: headless Chromium with software WebGL, not a user's GPU. Synthetic tenant only.
"""

import os
from pathlib import Path

import pytest
from browser_servers import ROOT, run_review


@pytest.mark.browser
def test_lighting_scene_review(environment):
    """The scene loads lazily, stays optional, is keyboard-reachable where it matters and leaks no private data."""
    report_path = Path(
        os.environ.get("LUMA_SCENE_EVIDENCE", ROOT / ".local" / f"scene-{environment['company']}.json")
    )
    report = run_review(environment, "scene-review.cjs", "scene", report_path)
    assert report["console"] == [], report["console"]
    assert report["privacy"]["matches"] == [], report["privacy"]
    assert report["reduced"]["canvas_count"] == 0 and report["reduced"]["fallback_visible"] >= 1
    assert report["motion"]["scene_chunk_requested"] or report["motion"]["canvas_count"] >= 1
    assert report["keyboard"]["radio_count"] == 3 and report["keyboard"]["arrow_key_changes_selection"]
    for name in ("desktop_axe", "portrait_axe"):
        assert report["viewport"][name] == [], (name, report["viewport"][name])
    assert report["reduced"]["axe"] == []
    assert report["viewport"]["portrait_horizontal_overflow"] is False
