---
name: react-feature-structure
description: Organize React and TypeScript features, imports, hooks, query ownership, and public interfaces in the approved Vite application. Use for frontend scaffolding or substantive feature organization.
license: Proprietary - original supplied notices retained in the source archive.
---

# React Feature Structure

The application uses React Router and Vite with FastAPI as its business API. Preserve that choice and inspect actual source paths before editing. No Next.js server components, App Router route handlers, or Next.js-specific configuration are introduced by this skill.

Use [feature boundaries](references/feature-boundaries.md) when organizing a feature.
Start with a small layout that matches actual code. Feature-sliced ideas guide dependency direction; they do not require every possible layer or empty folder.
Routing composes screens. Features own user interactions and their API/query contracts. Shared UI contains business-independent primitives; integration clients do not import screens.
Use strict TypeScript appropriate to the selected toolchain, validated external data, and generated/shared API contracts when available. Do not copy a framework-specific tsconfig or ESLint configuration without adapting and running it.
Document public interfaces, side effects, non-obvious invariants, and ordering. Avoid mandatory file banners or docstrings that merely restate obvious types.

TanStack Query owns remote state; apply [client-crud-state](../client-crud-state/SKILL.md) for mutations and reconciliation. Use [react-best-practices](../react-best-practices/SKILL.md) for rendering/performance, [shadcn](../shadcn/SKILL.md) for components, and [frontend-design](../frontend-design/SKILL.md) for visual direction.
Keep session/company cache boundaries explicit. Client-side hiding is not authorization; business transitions remain server-enforced.

