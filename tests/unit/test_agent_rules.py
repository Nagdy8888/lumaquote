"""Behavior of the rule-enforcement scripts behind AGENTS.md (R6, R8-R10, R14, R15, skills routing).

Each test builds a small temporary repository layout and points the script's module
constants at it, so the real repository is never modified. Negative cases prove each
check actually fails on the defect it names, not only that it passes on clean input.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "hooks"))
import check_docs  # noqa: E402
import guard  # noqa: E402
import skills  # noqa: E402


@pytest.fixture
def docs_root(tmp_path, monkeypatch):
    """Point check_docs at an empty temporary repository with docs/ and docs/evidence/."""
    (tmp_path / "docs" / "evidence").mkdir(parents=True)
    monkeypatch.setattr(check_docs, "ROOT", tmp_path)
    monkeypatch.setattr(check_docs, "DOCS", tmp_path / "docs")
    monkeypatch.setattr(check_docs, "EVIDENCE", tmp_path / "docs" / "evidence")
    monkeypatch.setattr(check_docs, "PLAN", tmp_path / "docs" / "IMPLEMENTATION_PLAN.md")
    monkeypatch.setattr(check_docs, "LEGACY_EVIDENCE", set())
    return tmp_path


def write(path: Path, text: str) -> Path:
    """Write UTF-8 text with LF endings, creating parent folders."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return path


def test_r8_flags_mojibake_crlf_and_broken_links_but_not_quoted_code(docs_root):
    """Mojibake in prose, CRLF and missing link targets fail; quoting the bad bytes in code is allowed."""
    bad = write(docs_root / "docs" / "bad.md", "Range 90â€“120 s\nSee [x](missing.md)\n")
    quoted = write(docs_root / "docs" / "ok.md", "Never write `â€` in prose. See [bad](bad.md)\n")
    crlf = docs_root / "docs" / "crlf.md"
    crlf.write_bytes(b"line one\r\nline two\r\n")
    assert any("mojibake" in p for p in check_docs.check_encoding(bad))
    assert any("broken link missing.md" in p for p in check_docs.check_links(bad))
    assert check_docs.check_encoding(quoted) == [] and check_docs.check_links(quoted) == []
    assert any("CRLF" in p for p in check_docs.check_encoding(crlf))


def test_r9_requires_header_and_allowed_label_for_new_evidence(docs_root):
    """New evidence without the header or with an invented label fails; a complete header passes."""
    evidence = docs_root / "docs" / "evidence"
    missing = write(evidence / "a.json", json.dumps({"date": "2026-11-03"}))
    wrong = write(evidence / "b.json", json.dumps(dict.fromkeys(check_docs.HEADER, "x")))
    good = write(evidence / "c.json", json.dumps({**dict.fromkeys(check_docs.HEADER, "x"), "label": "local"}))
    assert any("missing header field 'commit'" in p for p in check_docs.check_evidence(missing))
    assert any("label 'x'" in p for p in check_docs.check_evidence(wrong))
    assert check_docs.check_evidence(good) == []


def test_r10_ticked_items_need_evidence_and_phase_4_needs_live(docs_root):
    """A tick without evidence fails; phase 4 accepts only evidence labeled live."""
    evidence = docs_root / "docs" / "evidence"
    write(evidence / "local.json", json.dumps({"label": "local"}))
    write(evidence / "live.json", json.dumps({"label": "live"}))
    plan = (
        "## 1. Design\n- [x] No evidence here\n- [x] Linked ([e](evidence/local.json))\n"
        "## 4. Live\n- [x] Local only ([e](evidence/local.json))\n- [x] Real ([e](evidence/live.json))\n"
        "## Notes\n- [x] Outside phases ([e](evidence/local.json))\n"
    )
    write(docs_root / "docs" / "IMPLEMENTATION_PLAN.md", plan)
    problems = check_docs.check_plan()
    assert [p.split(":")[1] for p in problems] == ["2", "5"]
    assert "without an existing evidence link" in problems[0] and "'live'" in problems[1]


@pytest.mark.parametrize(
    ("command", "blocked"),
    [
        ("git push --force origin main", True),
        ("git push -f origin main", True),
        ("git push origin +main", True),
        ("git reset --hard HEAD~1", True),
        ("git commit --amend -m x", True),
        ("git commit --no-verify -m x", True),
        ("npx vercel deploy --prod", True),
        ("supabase db push", True),
        ("git push origin main", False),
        ("git commit -m 'feat: x'", False),
        ("git status && npm run verify", False),
    ],
)
def test_r15_bash_guard(command, blocked):
    """Destructive git, hook bypass and deploy commands are blocked; ordinary commands pass."""
    assert (guard.bash({"tool_input": {"command": command}}) == 2) is blocked


def test_r14_stop_requires_work_log_and_docs_for_code(monkeypatch):
    """Code changes without docs block; with a work-log entry and a reference update they pass."""
    monkeypatch.setattr(guard, "run_check", lambda arguments: "")
    monkeypatch.setattr(guard, "changed_paths", lambda: ["app/backend/luma/x.py"])
    assert guard.stop({}) == 2
    monkeypatch.setattr(guard, "changed_paths", lambda: ["app/backend/luma/x.py", "docs/WORK_LOG.md"])
    assert guard.stop({}) == 2
    monkeypatch.setattr(
        guard,
        "changed_paths",
        lambda: ["app/backend/luma/x.py", "docs/WORK_LOG.md", "docs/reference/BACKEND.md"],
    )
    assert guard.stop({}) == 0
    monkeypatch.setattr(guard, "changed_paths", lambda: ["app/backend/luma/x.py"])
    assert guard.stop({"stop_hook_active": True}) == 0


def test_r6_edit_guard_warns_on_large_deletions(tmp_path, monkeypatch):
    """A file that lost more than 30 lines against HEAD produces a warning; small edits do not."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "i"],
        cwd=tmp_path,
        check=True,
    )
    target = write(tmp_path / "f.md", "".join(f"line {i}\n" for i in range(50)))
    subprocess.run(["git", "add", "f.md"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "f"],
        cwd=tmp_path,
        check=True,
    )
    monkeypatch.setattr(guard, "ROOT", tmp_path)
    target.write_text("".join(f"line {i}\n" for i in range(45)), encoding="utf-8")
    assert guard.edit({"tool_input": {"file_path": str(target)}}) == 0
    target.write_text("line 0\n", encoding="utf-8")
    assert guard.edit({"tool_input": {"file_path": str(target)}}) == 2


def test_skills_frontmatter_and_routing(tmp_path, monkeypatch):
    """A skill whose name mismatches its folder, or that AGENTS.md never routes, is reported."""
    source = tmp_path / ".agents" / "skills"
    write(source / "good" / "SKILL.md", "---\nname: good\ndescription: Does a job.\n---\n")
    write(source / "bad" / "SKILL.md", "---\nname: other\n---\n")
    write(tmp_path / "AGENTS.md", "Use `good` for the job.\n")
    monkeypatch.setattr(skills, "SOURCE", source)
    monkeypatch.setattr(skills, "AGENTS", tmp_path / "AGENTS.md")
    problems = skills.check_frontmatter() + skills.check_routing()
    assert any("bad/SKILL.md name must be 'bad'" in p for p in problems)
    assert any("bad/SKILL.md needs a description" in p for p in problems)
    assert problems[-1] == "routing: AGENTS.md does not mention `bad`"
    assert not any("good" in p for p in problems)
