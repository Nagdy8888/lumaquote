# Branching model

MIS uses **two long-lived branches** plus short-lived feature branches.

## Long-lived branches

| Branch | Environment | Who can push | Reset / rebase allowed? |
|--------|-------------|--------------|-------------------------|
| `main` | Production  | Nobody directly; PRs only | **No.** History is permanent. |
| `dev`  | Staging     | Nobody directly; PRs only | **No.** History is permanent. |

Both branches are protected. See `assets/branch-protection.md` for the exact GitHub settings.

`dev` is the **default branch** in every MIS repo so that the GitHub UI and `gh pr create` target it automatically.

## Short-lived branches

Cut from `dev`, merge back into `dev`. Naming:

```
<type>/<ticket-id>-<short-kebab-summary>
```

Type prefixes (must be one of):

| Prefix      | Meaning |
|-------------|---------|
| `feat/`     | New user-visible behaviour |
| `fix/`      | Bug fix |
| `chore/`    | Tooling, deps, config |
| `refactor/` | Internal change, no behaviour change |
| `infra/`    | Infra / deploy / CI/CD |
| `docs/`     | Docs-only |
| `test/`     | Tests-only |
| `release/`  | Promotion PRs from `dev` → `main` |
| `hotfix/`   | Emergency fix branched off `main` |

Lifetime: **hours to a few days**. If a branch is alive longer than a week, either land it or close it.

## Promotion flow: `dev` → `main`

Normal cadence — weekly (Mondays by default, or per-team agreement). On-demand for time-sensitive releases.

1. Open a PR titled `release: promote dev → main (YYYY-MM-DD)`.
2. Body: bulleted list of user-visible features / fixes since the last promotion, generated from:
   ```bash
   git log --oneline origin/main..origin/dev
   ```
3. Required before merge:
   - Latest CI on `dev` is green.
   - Staging smoke checks signed off (link the run in the PR body).
   - Migration / rollback plan documented if applicable.
4. **Merge with a merge commit** — not squash — so individual features remain visible on `main`'s history. This is the only place we use merge commits.
5. Tag the resulting commit: `git tag v$(date +%Y.%m.%d) && git push --tags`.

## Hotfix path

Production is broken; waiting for the next promotion is not acceptable.

1. Branch from `main`:
   ```bash
   git fetch origin
   git switch main && git pull --ff-only
   git switch -c hotfix/MIS-<id>-<summary>
   ```
2. Fix, commit, push, open PR targeting **`main`** (not `dev`).
3. PR follows the normal template; reviewer SLA is "now, drop other work".
4. After merge, **back-merge `main` into `dev` immediately** so `dev` does not regress on the next promotion:
   ```bash
   git switch dev && git pull --ff-only
   git merge --no-ff origin/main
   git push
   ```
   This is the only time `dev` gets a merge commit outside of promotion.

## Long-running work

If a feature genuinely cannot be split below the one-week guideline:

- Use a **feature flag** so the half-built work can land on `dev` behind the flag without affecting production.
- Re-base the working branch on `dev` daily.
- Land merge-ready slices behind the flag rather than holding everything in a single mega-PR.

Long-lived feature branches without a flag are an anti-pattern. The cost is paid in merge-conflict and review-load, not in calendar time.

## What never happens

- Direct pushes to `main` or `dev` (branch protection blocks them).
- `git push --force` to `main` or `dev` (blocked, and would be undone).
- Renaming `main` to `master` or vice versa per-repo. The standard is `main`.
- Skipping the `dev` step for a non-hotfix change.
