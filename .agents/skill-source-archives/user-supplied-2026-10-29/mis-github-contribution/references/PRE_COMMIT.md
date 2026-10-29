# Pre-commit gates per stack

Every MIS repo runs the same four classes of check, both locally (via the [pre-commit](https://pre-commit.com/) framework) and in CI. The local hook is the first line of defence; CI is the gate that blocks merge.

The four classes:

1. **Lint** — catches bugs and bad patterns.
2. **Format check** — formatter in `--check` mode (no auto-write in CI).
3. **Type-check** — wherever the language has one.
4. **Tests** — at minimum the affected package's unit tests.

The starter `.pre-commit-config.yaml` (in `assets/`) is multi-stack — drop it in any repo and remove the stacks you don't use.

## Generic hooks (every repo)

These run regardless of language:

- `trailing-whitespace`
- `end-of-file-fixer`
- `check-merge-conflict`
- `check-added-large-files` (limit: 500 KB; bump deliberately)
- `detect-secrets` (or `gitleaks`) — scans the diff for credentials

## Python

Tooling: **ruff** (lint + format) and **mypy** (types). Use **uv** for env / dep management when starting a new repo.

```yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.6.9
  hooks:
    - id: ruff           # lint
      args: [--fix]
    - id: ruff-format    # format
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.11.2
  hooks:
    - id: mypy
      args: [--strict]
      additional_dependencies: [types-requests]
```

CI mirror (GitHub Actions, single command):

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
```

## TypeScript / JavaScript

Tooling: **eslint** (lint), **prettier** (format), **tsc --noEmit** (types), **vitest** or **jest** (tests).

```yaml
- repo: local
  hooks:
    - id: eslint
      name: eslint
      entry: pnpm exec eslint
      language: system
      files: \.(ts|tsx|js|jsx)$
    - id: prettier
      name: prettier
      entry: pnpm exec prettier --check
      language: system
      files: \.(ts|tsx|js|jsx|json|md|yaml|yml)$
    - id: tsc
      name: tsc
      entry: pnpm exec tsc --noEmit
      language: system
      pass_filenames: false
```

CI mirror:

```bash
pnpm install --frozen-lockfile
pnpm lint
pnpm format:check
pnpm typecheck
pnpm test --run
```

## Go

Tooling: **golangci-lint** (lint + format + a fleet of small linters), **go vet**, **go test**.

```yaml
- repo: https://github.com/golangci/golangci-lint
  rev: v1.61.0
  hooks:
    - id: golangci-lint
```

CI mirror:

```bash
go vet ./...
golangci-lint run
go test ./...
```

## Terraform / IaC

```yaml
- repo: https://github.com/antonbabenko/pre-commit-terraform
  rev: v1.96.1
  hooks:
    - id: terraform_fmt
    - id: terraform_validate
    - id: terraform_tflint
```

## Test scope on the hook

The local hook should run **only the tests touching the changed files**, not the full suite — otherwise contributors stop running it. Patterns:

- **Python**: `pytest --picked` (via `pytest-picked`) or `pytest <changed paths>`.
- **TypeScript**: `vitest related <changed files>` / `jest --findRelatedTests`.
- **Go**: `go test ./...` is fast enough for most repos; otherwise scope by package.

CI runs the **full suite** to catch transitive breakage.

## When a hook fails

1. Read the error. It usually tells you what to fix.
2. **Do not** pass `--no-verify` to skip the hook. If you genuinely need to commit broken code (e.g., to share with a collaborator), open a draft PR and let CI flag it instead.
3. If the hook itself is broken (false positive, tool bug), fix the hook config in the same PR — don't bypass it.

## Updating hook versions

`pre-commit autoupdate` once a quarter. Land the bump as a `chore(deps):` PR with one commit per tool so reverts are surgical if a new linter version breaks things.
