# PR review etiquette & merge rules

## Sizing rules

- **Target:** < 400 LOC of net diff (additions + deletions, excluding generated files and lockfiles).
- **Single purpose:** one concern per PR. A bug fix is one PR; the refactor that made the fix easy is another.
- If a PR grows past 400 LOC mid-flight: stop, open a stacked PR with the prep work, and rebase.
- Auto-generated files (lockfiles, snapshots, schemas) don't count toward the LOC budget but **must be in their own commit** so reviewers can fold them.

## Required checks before merge

GitHub branch protection enforces the technical checks. Reviewers enforce the human ones.

**Technical** (gates configured in branch protection):

- [ ] CI is green (lint, format, types, tests).
- [ ] PR is up to date with the target branch (`dev` or `main`).
- [ ] No unresolved review threads.
- [ ] ≥ 1 approval from a CODEOWNER for any touched path.

**Human** (reviewer checks):

- [ ] Title and commits follow Conventional Commits.
- [ ] PR body uses the template; every section is filled.
- [ ] Ticket referenced (`Closes MIS-…`).
- [ ] Screenshots / recordings present for UI changes.
- [ ] No dead code, debug logs, or commented-out blocks.
- [ ] No secrets, no `.env`, no large binaries.
- [ ] Tests cover the new code path. Bug fixes include a regression test.

## Reviewer SLA

- **First-pass review within one working day** of the request.
- **Hotfix PRs**: drop other work and review now.
- If you cannot review within the SLA, re-request a different reviewer in writing — don't silently leave the PR sitting.

## Review etiquette

- **Be specific.** "This loop is O(n²)" beats "this seems slow."
- **Prefer suggested-change blocks** for nits — they let the author accept with one click.
- **Block on:** correctness, security, public-API contracts, missing tests, performance regressions with evidence.
- **Comment-only on:** naming bikesheds, hypothetical future refactors, personal style.
- **Approve when good enough**, not when perfect. Two more rounds of nitpicks rarely improve the change and always slow it down.
- **No drive-by `+1`s.** If you approve, you read the diff.
- **Disagreements**: discuss in the PR, escalate to the tech lead if blocked > 24h.

## Author etiquette

- **Respond to every thread.** Either fix, push back with reasoning, or convert to a follow-up issue. Don't ignore.
- **Don't force-push after approval** unless you flag it in a comment. Pushes dismiss stale approvals automatically (a feature, not a bug).
- **Resolve threads as you address them** — but only the original commenter resolves substantive threads.
- **Re-request review** when you have addressed feedback. Don't make the reviewer go looking.

## Merge strategy

| Target branch | Strategy | Why |
|---------------|----------|-----|
| `dev`         | **Squash & merge** | One commit per task on `dev`. Clean linear history. |
| `main` (release PR) | **Merge commit** | Preserve the individual feature commits from `dev`. |
| `main` (hotfix) | **Squash & merge** | One commit per hotfix on `main`. |

Rebase merge is **not** used — it rewrites commit SHAs and breaks linkbacks from external systems (Jira, Sentry, Slack archives).

## CODEOWNERS

`.github/CODEOWNERS` (see `assets/CODEOWNERS`) auto-requests the right reviewer based on the touched paths. GitHub enforces that at least one CODEOWNER approval is required.

Owners should cover:

- `/infra/` — DevOps lead
- `/api/`, `/services/` — backend lead
- `/web/`, `/app/` — frontend lead
- `/migrations/` — backend lead + DBA
- `*.md`, `/docs/` — anyone (no specific owner)

When you add a major new area, update CODEOWNERS in the same PR.

## Escalation

- **Reviewer unresponsive past SLA**: post in the team channel + re-request a different reviewer.
- **Author and reviewer deadlocked > 24h**: tech lead breaks the tie.
- **Hotfix blocked on review**: the on-call lead has merge authority and can approve in place of the normal CODEOWNER.

## Stale PRs

PRs with no activity for **7 days** are marked stale by the bot. After **14 days**, they are closed automatically. Re-open with a comment explaining the path forward if work resumes.
