---
name: implement-human-approval
description: Implement customer clarification, durable salesperson approval, revisions, and human takeover. Use for human-in-the-loop agent state and action authorization.
---

# Implement Human Approval

Distinguish customer participation from staff authorization: a customer can clarify requirements and accept an offer; only authorized staff can approve the company's quotation and policy exceptions.

## Persist the decisions
Represent pending clarification, draft readiness, approval requests, approval/rejection, expiration, ownership, and dispatch intent as durable state.
An approval identifies company, request, quote revision or content hash, recipient, action, approver, and relevant policy version. It is not a reusable boolean.
Present the exact quotation, substitutions, commercial terms, warnings, and recipient before approval.
Verify role, company scope, current revision, expiry, and current price/availability policy when approval is recorded and again at dispatch.
Quote-affecting changes invalidate the approval and require review. Preserve the old revision and decision history.
Do not imply that quoted availability reserves inventory; reservation is a separate explicit business operation if implemented.

## Pause and resume
For LangGraph mechanics, read [langgraph-human-in-the-loop](../langgraph-human-in-the-loop/SKILL.md) and [langgraph-persistence](../langgraph-persistence/SKILL.md). A resume payload is input to validate, not proof of staff authorization.
Interrupted nodes restart on resume, and replay can rerun actions. Keep external sends behind durable action identities and an outbox or equivalent dispatch mechanism; placing a send after an interrupt alone does not make it safe to retry.
Bind the pending decision and resume request to the authorized company, conversation/thread, interrupt, and quotation revision. A framework example using a boolean approval does not replace this project's exact-revision approval record.
Persist a pending decision before suspending the agent. Resume only from an authenticated, correlated decision; duplicate callbacks must not execute the approved action twice.
Handle rejection, requested edits, no response, revoked permissions, and process restarts. Do not interpret elapsed time as approval.
A staff takeover pauses customer-facing automation. Check ownership at dispatch, including work queued before takeover. Release automation only through an explicit staff action.
Use transactions, version checks, and an outbox or equivalent durable mechanism to resolve competing edits, approvals, and sends.
Logs/checkpoints must not be the sole authority for whether an action was approved or delivered.

## Verify
Cover stale approvals, cross-company approval attempts, concurrent edits, duplicate callbacks, restart during pause, takeover with queued replies, revoked staff access, and uncertain external delivery.

