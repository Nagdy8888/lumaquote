---
name: contribution-workflow
description: Prepare scoped commits, branches, pull requests, and release descriptions using the repository's actual workflow. Use when the user requests Git or GitHub contribution work.
license: Proprietary - original supplied notices retained in the source archive.
---

# Contribution Workflow

Inspect git status, remotes, branch conventions, CI, hooks, templates, and user authorization before acting. An uninitialized folder does not establish a remote repository or issue tracker.

Keep changes reviewable and explain the problem, resulting behavior, validation, and material limitations. Prefer existing conventions; Conventional Commits are a reasonable new convention when needed, not a reason to rewrite history.
Use actual issue references when available. Do not invent ticket IDs, mandatory dev branches, a fixed diff-size ceiling, or one commit per task.
Select a branch strategy suited to this repository. Do not introduce main/dev promotion flows, CODEOWNERS, branch protection, or required reviewers as an installation side effect.

## Boundaries with other skills
- [review-quotation-code](../verify-and-review/references/review-quotation-code/GUIDE.md) owns substantive code review.
- [verify-engineering-coverage](../verify-and-review/references/engineering-coverage/GUIDE.md) owns engineering coverage and evidence.
- [verify-quotation-release](../verify-and-review/references/verify-quotation-release/GUIDE.md) owns release verification.
- [setup-pre-commit](../../retired-skills-2026-11-03/setup-pre-commit) owns explicitly requested hook setup; inspect existing checks and use one coherent hook chain.
- [project-documentation](../project-documentation/SKILL.md) owns decisions, guides, and release-note content.

Use [PR description prompts](assets/pr-description-prompts.md) when no repository template exists. Report local checks, external CI, and pushed/unpushed state separately. A passing local build is not proof of remote CI.

Commit, push, create/publish a PR, change repository settings, or merge only when authorized by the actual task. Preserve user edits, use repository-local configuration when requested, and never change global git settings from this skill.

