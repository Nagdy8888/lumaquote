---
name: review-quotation-code
description: Review quotation-app changes against the agreed specification and business invariants. Use for branches, working-tree changes, or focused pre-release code review.
---

# Review Quotation Code

Establish the actual review scope from the request and repository state. Include staged, unstaged, and new files for working-tree reviews; for branch reviews, use the appropriate merge base and commits.
Apply [verify-engineering-coverage](../verify-engineering-coverage/SKILL.md) to substantive review scope. Inspect applicability and actual evidence rather than trusting Covered labels; include routes, direct Supabase paths, workers, and model tools that could bypass the visible flow.
Read the originating local spec, acceptance scenarios, and relevant project conventions. An issue tracker or remote publication is not required. If the spec is absent, report that limitation and review the observable business contract.
For frontend changes, use react-feature-structure for code ownership and client-crud-state for server/cache reconciliation. Use frontend-design's application-workspace reference for repeat-use UI; do not create a separate design mandate from supplied conventions. Contribution mechanics belong to contribution-workflow.
Prioritize concrete defects in customer/staff permissions, product identity, calculations, current source selection, approval invalidation, takeover, delivery deduplication, and recovery.
Trace a proposed finding through callers, state, and tests. Give the triggering scenario, user/business consequence, precise source location, and smallest effective correction.
Separate confirmed defects from questions and optional improvements. Do not claim an audit or integration validation from source inspection alone.
Review according to available tools. Use independent reviewers only when delegation is authorized and adds value; this skill does not require spawning agents.
Do not commit, publish a review, or change code as a review side effect unless the user requested that action.

