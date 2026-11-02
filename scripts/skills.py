"""Keep the project's agent skills discoverable, intact and routed (rules R1 and D32).

`.agents/skills/` is the canonical source (Codex reads it). Claude Code only discovers
skills under `.claude/skills/<name>/SKILL.md`, so `sync` mirrors every active top-level
skill there. `check` fails when the mirror drifts, when an upstream file no longer matches
the hash recorded at import, when a project-authored file changed without a manifest
refresh, when a skill lacks valid frontmatter, when a relative link in a project-authored
skill is broken, or when `AGENTS.md`'s routing table does not name every active skill.
`manifest` refreshes project-authored hashes after an intentional edit.

Usage: node scripts/python.cjs scripts/skills.py sync|check|manifest
Exit code 0 = ok, 1 = problems found (each printed on its own line).
"""

import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".agents" / "skills"
MIRROR = ROOT / ".claude" / "skills"
AGENTS = ROOT / "AGENTS.md"
UPSTREAM = SOURCE / "upstream-manifest.json"
PROJECT = SOURCE / "project-manifest.json"
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def active_skills() -> list[str]:
    """Return top-level skill folder names that contain a SKILL.md (archives and licenses excluded)."""
    return sorted(p.parent.name for p in SOURCE.glob("*/SKILL.md"))


def digest(path: Path) -> str:
    """Return the SHA-256 of a file's exact bytes, matching how manifests recorded imports."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree(base: Path) -> dict[str, str]:
    """Map every file under `base` (posix relative path) to its digest; `__pycache__` is ignored."""
    return {
        p.relative_to(base).as_posix(): digest(p)
        for p in base.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }


def located(entry: dict, name: str, relative: str) -> Path:
    """Resolve a manifest file path to where it lives now, applying the recorded rename map."""
    folder = entry.get("active_path") or entry.get("retired_path") or name
    renamed = entry.get("renamed_files", {}).get(relative, relative)
    return (SOURCE / folder / renamed).resolve()


def sync() -> list[str]:
    """Replace `.claude/skills` with an exact copy of the active skills; returns no problems.

    Side effect: deletes and rewrites `.claude/skills/`. Nothing else under `.claude/` is touched.
    """
    if MIRROR.exists():
        shutil.rmtree(MIRROR)
    for name in active_skills():
        shutil.copytree(SOURCE / name, MIRROR / name, ignore=shutil.ignore_patterns("__pycache__"))
    print(f"Synced {len(active_skills())} skills to {MIRROR.relative_to(ROOT).as_posix()}")
    return []


def check_mirror() -> list[str]:
    """Report skills missing, extra or different in the Claude Code mirror."""
    problems = []
    mirrored = sorted(p.parent.name for p in MIRROR.glob("*/SKILL.md")) if MIRROR.exists() else []
    for name in sorted(set(active_skills()) ^ set(mirrored)):
        problems.append(f"mirror: {name} differs in presence; run npm run skills:sync")
    for name in set(active_skills()) & set(mirrored):
        if tree(SOURCE / name) != tree(MIRROR / name):
            problems.append(f"mirror: {name} content differs; run npm run skills:sync")
    return problems


def check_manifests() -> list[str]:
    """Verify upstream bytes are unchanged and project-authored hashes are current."""
    problems = []
    adapted = set(json.loads(PROJECT.read_text(encoding="utf-8"))["skills"])
    for manifest_path, strict in ((UPSTREAM, True), (PROJECT, False)):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for name, entry in manifest["skills"].items():
            if entry.get("archived") or entry.get("retired_path"):
                continue
            if strict and name in adapted:
                # Locally adapted upstream skills (e.g. mermaid-diagrams) carry their
                # current hashes in the project manifest; the upstream hashes are history.
                continue
            for relative, expected in entry.get("files", {}).items():
                path = located(entry, name, relative)
                if not path.exists():
                    problems.append(
                        f"manifest: {name}/{relative} missing at {path.relative_to(ROOT).as_posix()}"
                    )
                elif digest(path) != expected:
                    kind = (
                        "upstream file modified"
                        if strict
                        else "project file changed; run npm run skills:manifest"
                    )
                    problems.append(f"manifest: {name}/{relative}: {kind}")
    return problems


def check_frontmatter() -> list[str]:
    """Require `name` equal to the folder and a non-empty `description` in every active SKILL.md."""
    problems = []
    for name in active_skills():
        text = (SOURCE / name / "SKILL.md").read_text(encoding="utf-8")
        head = text.split("---", 2)[1] if text.startswith("---") else ""
        found = re.search(r"^name:\s*(\S+)", head, re.M)
        if not found or found.group(1).strip("\"'") != name:
            problems.append(f"frontmatter: {name}/SKILL.md name must be '{name}'")
        if not re.search(r"^description:\s*\S", head, re.M):
            problems.append(f"frontmatter: {name}/SKILL.md needs a description")
    return problems


def project_files() -> list[Path]:
    """List markdown files authored in this project (upstream imports keep their own links)."""
    manifest = json.loads(PROJECT.read_text(encoding="utf-8"))
    files = []
    for name, entry in manifest["skills"].items():
        if entry.get("origin") in ("project-authored", "adapted-user-supplied") and not entry.get(
            "retired_path"
        ):
            folder = SOURCE / entry.get("active_path", name)
            files.extend(located(entry, name, rel) for rel in entry.get("files", {}) if rel.endswith(".md"))
            if not entry.get("files"):
                files.extend(folder.rglob("*.md"))
    return sorted(set(files))


def check_links() -> list[str]:
    """Report relative links in project-authored skill files whose target does not exist."""
    problems = []
    for path in project_files():
        if not path.exists():
            continue
        for target in LINK.findall(path.read_text(encoding="utf-8")):
            if re.match(r"^[a-z]+:|^#|^/", target):
                continue
            if not (path.parent / target.split("#")[0]).exists():
                problems.append(f"link: {path.relative_to(ROOT).as_posix()} -> {target} not found")
    return problems


def check_routing() -> list[str]:
    """Require AGENTS.md to name every active skill so routing never depends on memory."""
    text = AGENTS.read_text(encoding="utf-8")
    return [
        f"routing: AGENTS.md does not mention `{name}`" for name in active_skills() if f"`{name}`" not in text
    ]


def refresh_manifest() -> list[str]:
    """Rewrite project-authored file hashes (and register new skills) after an intentional edit."""
    manifest = json.loads(PROJECT.read_text(encoding="utf-8"))
    upstream = json.loads(UPSTREAM.read_text(encoding="utf-8"))["skills"]
    known = set(manifest["skills"]) | set(upstream)
    for name in active_skills():
        if name not in known:
            manifest["skills"][name] = {"origin": "project-authored", "active_path": name, "files": {}}
    # A lead skill folder can contain other skills merged into references/; those files
    # belong to their own manifest entries and must not be claimed by the lead.
    nested = {
        e.get("active_path")
        for e in list(manifest["skills"].values()) + list(upstream.values())
        if e.get("active_path") and "/" in e.get("active_path")
    }
    for name, entry in manifest["skills"].items():
        if entry.get("retired_path") or entry.get("origin") not in (
            "project-authored",
            "adapted-user-supplied",
            "retained-local",
        ):
            continue
        own = entry.get("active_path", name)
        folder = SOURCE / own
        inside = [n[len(own) + 1 :] for n in nested if n.startswith(own + "/")]
        renamed = {v: k for k, v in entry.get("renamed_files", {}).items()}
        entry["files"] = {
            renamed.get(rel, rel): sha
            for rel, sha in tree(folder).items()
            if not any(rel.startswith(prefix + "/") for prefix in inside)
        }
    PROJECT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Refreshed project-authored hashes in project-manifest.json")
    return []


def main() -> int:
    """Dispatch the sub-command and print one line per problem; returns the process exit code."""
    command = sys.argv[1] if len(sys.argv) > 1 else "check"
    if command == "sync":
        problems = sync()
    elif command == "manifest":
        problems = refresh_manifest()
    elif command == "check":
        problems = check_mirror() + check_manifests() + check_frontmatter() + check_links() + check_routing()
    else:
        print("usage: skills.py sync|check|manifest")
        return 2
    for problem in problems:
        print(problem)
    if command == "check" and not problems:
        print(f"Skills check passed for {len(active_skills())} active skills.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
