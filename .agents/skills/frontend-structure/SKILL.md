---
name: frontend-structure
description: Organize and implement React/TypeScript code in the Vite frontend - feature boundaries, imports, hooks, TanStack Query ownership, mutations with pending/rollback state, and rendering performance. Use for any frontend code change that is not purely visual design.
---

# Frontend Structure

One entry point for how frontend code is organized and how it handles server data.
It replaces three earlier skills, kept unchanged as references:

- [react-feature-structure](references/react-feature-structure/GUIDE.md): feature folders, public entries, dependency direction.
- [client-crud-state](references/client-crud-state/GUIDE.md): TanStack Query mutations, pending rows, rollback, reconciliation.
- [react-best-practices](references/react-best-practices/GUIDE.md): rendering and bundle performance (upstream Vercel guidance; ignore Next.js-only rules).

Visual direction belongs to `frontend-design`; component mechanics to `shadcn`.

## Rules

- Layout: `app/frontend/src/app` composes routes and providers; `src/features/<feature>` owns UI,
  queries and mutations behind a small public entry; `src/shared` holds business-independent code only.
  Shared code never imports a feature (enforced by `npm run check:frontend`).
- Every named function, component, hook and class has a JSDoc contract (R4, enforced by `check:frontend`).
- TanStack Query is the only owner of server data. Scope keys to company and resource; clear on session change.
- Never show Approved, Sent or Delivered optimistically; those states come from the server.
- Client-side hiding is not authorization; the backend enforces every business transition.
- Checks: `npm run check:frontend`, `npm run typecheck`, `npm run test:ui`; browser flows with `npm run test:browser`.
