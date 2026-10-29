<!--
MIS standard PR template. Every section is required; delete the
HTML comments before submitting. Title must follow Conventional
Commits: <type>(<scope>): <summary> (<TICKET-ID>)

  e.g. feat(billing): add Stripe webhook retry (MIS-142)
-->

## Summary

<!-- 1–3 bullets. What changed and why. -->

-
-

## Changes

<!-- Bulleted list of notable changes. One per logical change is fine. -->

-
-

## Testing

<!-- Exact commands run + manual steps performed. Be specific so a reviewer can reproduce. -->

- [ ] Lint / format: `…`
- [ ] Type-check: `…`
- [ ] Tests: `…`
- [ ] Manual: …

## Screenshots / recordings

<!-- Required for any UI change. Delete this section if N/A and write "N/A". -->

## Checklist

- [ ] Title follows Conventional Commits
- [ ] Commits squashed; one commit per task
- [ ] Lint, format, type-check, tests pass locally
- [ ] Docs updated (README / CHANGELOG / inline as relevant)
- [ ] Migrations included + rollback plan documented (if applicable)
- [ ] No secrets, `.env`, or large binaries added
- [ ] Feature flag wired (if shipping behind a flag)

## Ticket

Closes <!-- e.g. MIS-142 -->

## Notes for reviewers

<!-- Anything you'd flag in person: tricky bits, deferred follow-ups, open questions. Delete if none. -->
