---
name: verify-and-review
description: Decide whether quotation-app work is correct, documented and done. Use for code review of a diff or branch, before calling a feature, phase or release complete, before ticking a plan checkbox, and for the 42-concept engineering coverage ledger.
---

# Verify and Review

One entry point for "is this right, and is it done?". It replaces three earlier skills,
which are kept unchanged as references:

- [review-quotation-code](references/review-quotation-code/GUIDE.md): code review against business invariants.
- [verify-quotation-release](references/verify-quotation-release/GUIDE.md): completion/readiness evidence.
- [engineering-coverage](references/engineering-coverage/GUIDE.md): the 42-concept ledger and its validator
  (`references/engineering-coverage/scripts/check_coverage.py`).

Their links were rewritten to the current locations on 2026-11-03; every skill they name
is listed in `AGENTS.md`'s routing table.

## Pick the job

| Job | Do this |
|---|---|
| Review a diff, branch or working tree | Follow review-quotation-code. Report confirmed defects first, with scenario, consequence, file:line and the smallest fix. |
| Claim a step, phase or release is done | Follow verify-quotation-release. Every check is Passed, Failed, Blocked or Not Run, with evidence paths. |
| Tick a plan checkbox | Rule R10: link an evidence file on the same line; its label must match the item (`live` items need `live`). |
| Security-sensitive or substantial feature | Update `docs/engineering/coverage.json`; run `check_coverage.py docs/engineering/coverage.json` (add `--release` before readiness claims). |

## Hard rules (from AGENTS.md)

- Evidence labels are only `local`, `local-substitute`, `sandbox`, `live`, `synthetic` (R9).
- Scoring rules and oracle changes are committed before the run they score; later changes are `post-hoc` (R11).
- "All checks pass" means one complete `npm run verify:full` on the final tree (R12).
- A skill, a passing presence check, or a mocked test is not proof that behavior works.
- Review does not commit, publish or change code unless the user asked for that.
