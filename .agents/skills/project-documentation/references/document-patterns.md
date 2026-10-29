# Document patterns

Choose one primary reader and job for each document. Follow existing paths; create the minimum new structure necessary.

## Decisions and plans
For a material architecture decision, record status, context, selected approach, consequences, alternatives, and related evidence. Do not reopen the approved React/Vite, FastAPI, LangGraph, or local Supabase choices merely to fill a template.
Once accepted, preserve the historical reasoning; make a superseding decision when the architecture changes. Correct factual mistakes transparently.
Use an RFC when an unresolved decision benefits from discussion. Routine reversible implementation choices can be resolved with judgment inside the approved design.
Keep implementation sequencing in the existing plan and update its tasks. An ADR is not a task checklist.

## Architecture
A context view names users and external services. A container view names independently runnable processes and data stores; container does not mean Docker alone.
Add a component view only where it improves understanding. Annotate important protocols, authorization/data boundaries, and durable versus transient state.
The quotation app's graph does not replace its database authorization, approval records, or outbound message outbox. Make those distinctions visible in diagrams.
Do not draw unimplemented integrations as verified. Keep Mermaid or other editable source alongside any rendered asset.

## Runbooks and incidents
Name the actual symptom, affected environment, scope, diagnostic commands, remediation options, preservation boundaries, verification, and escalation when a real owner exists.
Use commands that match the current deployment and shell. Clearly identify destructive operations and their data boundary; ordinary stop/start is not permission to reset or delete volumes.
For incidents, record timestamps with timezone, measured impact, timeline, evidence, contributing conditions, mitigation, and concrete follow-up. Do not invent an on-call rotation, deadlines, or a paid observability platform.
A backup statement includes what is protected and whether restoration was tested. An available dashboard does not prove an alert was delivered.

## Setup and public case studies
Link to LOCAL_DEVELOPMENT.md instead of duplicating its commands and ports. Use .env.example as the safe configuration reference.
Portfolio copy should explain the real business workflow, supported behavior, and actual validation. Label fictional supplier data and distinguish simulated processing time from measured staff savings.
Keep screenshots and recordings free of credentials and private customer data.

