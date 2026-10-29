---
name: verify-quotation-release
description: Verify quotation-app readiness with reproducible evidence. Use before declaring a feature complete, releasing, or deploying the agreed workflow.
---

# Verify Quotation Release

Read the current specification, acceptance criteria, actual implementation, and environment configuration. Do not invent phases, signed-off thresholds, or infrastructure.

## Required evidence for implemented scope
Apply [verify-engineering-coverage](../verify-engineering-coverage/SKILL.md) to the whole requested release. Run its release-mode ledger check and inspect referenced evidence; missing entries, unfinished applicable controls, and unsupported Covered labels prevent a readiness claim. This catalog is not full ASVS certification.
Run applicable lint, type, build, unit, integration, and end-to-end checks with reproducible commands.
Verify request intake, clarification, product evidence, authoritative commercial data, deterministic quote output, exact-revision approval, dispatch, and staff-visible status.
Cover voice transcription ambiguity, staff takeover, customer edits, restart/resume, duplicate webhooks, unknown send outcomes, and failed synchronization where implemented.
Verify authentication, company isolation, approval authorization, secret handling, resource limits, and deletion/retention behavior for exposed features.
For implemented admission and paid-tool paths, run the applicable [abuse-control checks](../implement-abuse-controls/references/abuse-verification.md), including concurrent requests, exhausted quota, unavailable enforcement, and crash/retry outcomes. Check Supabase direct access paths as well as FastAPI. Record missing security evidence as Not Run or Blocked, never as implemented because a skill exists.
Record dependency/model/configuration versions, dataset version, environment, command results, and artifact paths.
Use product acceptance targets from the spec. Report missing targets or missing integrations explicitly rather than treating absence as a pass.

## Operational checks
Before a real deployment, verify configuration, migrations, queues, health reporting, backup/restore requirements for persistent business records, and rollback appropriate to the chosen hosting.
Exercise provider/Workspace contracts in authorized sandbox environments; mark local substitutes separately.
A working local preview is not evidence of a live WhatsApp integration. Synthetic evaluation is not client validation.

## Report
List Passed, Failed, Blocked, and Not Run with evidence and next action. Do not declare the requested release ready while mandatory checks are missing or failing.
This skill does not itself authorize deployment, live messaging, or account changes. Complete all authorized preparation and verification before requesting any genuinely required final approval.

