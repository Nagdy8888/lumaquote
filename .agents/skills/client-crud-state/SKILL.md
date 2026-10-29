---
name: client-crud-state
description: Implement responsive create, update, delete, and rename interactions in React lists using TanStack Query, row-level pending states, canonical responses, and safe reconciliation.
license: User-supplied material; original notices retained in the source archive.
---

# Client CRUD State

TanStack Query owns remote collections and detail records in this project. Keep temporary form/selection/pending UI state local to the feature; do not add a parallel provider or store containing another authoritative copy of server rows.

## Mutation contract
- Scope query and mutation keys to the authorized company, resource, and relevant filters. Clear or separate caches on session/company changes.
- Track pending operations by stable row/action identity; distinguish concurrent edits. Use a client operation ID for a not-yet-created row and reconcile it with the returned server ID.
- Prefer canonical mutation responses for server-assigned IDs, revisions, timestamps, computed fields, and permissions. Do not invent server timestamps or make submitted price/approval fields authoritative.
- Patch known affected query/detail caches when the response is sufficient. Invalidate or refetch the affected scope when sorting, pagination, aggregates, permissions, or cross-user changes require it. Avoid both unconditional full-list refetches and blanket bans on refetching.
- Cancel or version-check overlapping fetches so older results cannot overwrite a newer mutation. Reconcile SSE events and repeated responses by server revision and operation identity.
- Optimistic edits require snapshots, rollback, and a reconciliation path. A pending marker without an optimistic data change is often clearer for deletion or business-critical transitions.
- Approval, authorization, stock reservation, sending, and delivery status require server confirmation. Never optimistically display Approved, Sent, or Delivered. For an unknown network outcome, reconcile instead of retrying an external action with a new identity.
- Surface errors with a recovery action and preserve user input. Clear the matching pending operation in success and failure paths without clearing unrelated rows.

## Verify
Exercise concurrent row changes, duplicate completion, failed mutation, stale fetch/SSE arrival, paginated/filter views, cross-company cache isolation, navigation after delete, and keyboard/screen-reader pending feedback.
Use [React feature structure](../react-feature-structure/SKILL.md) for ownership and [shadcn](../shadcn/SKILL.md) for component mechanics. Server-side correctness remains governed by quotation, approval, and security skills.

