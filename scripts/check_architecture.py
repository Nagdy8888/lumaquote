"""Check authored Python documentation and enforce the app's import direction."""

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inspect_python(path: Path) -> list[str]:
    """Return missing inline contracts and forbidden layer imports for one Python module."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    errors = []
    relative = path.relative_to(ROOT).as_posix()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not ast.get_docstring(
            node
        ):
            errors.append(f"{relative}:{node.lineno}: {node.name} needs an inline docstring")
        modules = []
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            modules = [node.module or ""]
        for module in modules:
            if "/core/" in relative and (
                module.startswith("luma.features") or module.startswith("luma_agent")
            ):
                errors.append(
                    f"{relative}:{node.lineno}: shared core cannot import feature/agent implementation"
                )
            if "/backend/" in relative and module.startswith("luma_agent"):
                errors.append(f"{relative}:{node.lineno}: backend must not depend on the agent runtime")
            if "/agents/" in relative and module.endswith(".routes"):
                errors.append(
                    f"{relative}:{node.lineno}: agents call business interfaces, not HTTP route handlers"
                )
            if path.name == "rules.py" and module.split(".")[0] in {
                "fastapi",
                "httpx",
                "psycopg",
                "openai",
                "langgraph",
            }:
                errors.append(
                    f"{relative}:{node.lineno}: deterministic rules cannot depend on transport/persistence/providers"
                )
    return errors


def main() -> int:
    """Inspect actual application modules and fail when documentation or import rules are violated."""
    files = sorted((ROOT / "app/backend").rglob("*.py")) + sorted((ROOT / "app/agents").rglob("*.py"))
    errors = [error for path in files for error in inspect_python(path)]
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Architecture and inline documentation checks passed for {len(files)} Python modules.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
