# Feature-Sliced Design — layers, segments, import rules

[Feature-Sliced Design](https://feature-sliced.design/) is an architectural methodology for frontend apps. It organises code by **business meaning** instead of technical type. This reference is the canonical MIS interpretation.

## Layers (top-to-bottom)

Each layer sits in `src/`. Higher layers may import from lower layers; same-layer and upward imports are forbidden.

| Order | Layer       | Holds                                                                                 |
|-------|-------------|---------------------------------------------------------------------------------------|
| 6     | `app/`†     | Next.js App Router — routing, root layouts, error/loading boundaries, global providers |
| 5     | `views/`‡   | Page-level compositions (one folder per page). Thin: compose widgets + features.       |
| 4     | `widgets/`  | Self-contained UI blocks reused on multiple views (sidebar, header, command palette).  |
| 3     | `features/` | User actions with business value (login, send-message, add-to-cart, edit-profile).     |
| 2     | `entities/` | Business entities and their canonical model + base UI (user, product, order, comment). |
| 1     | `shared/`   | Reusable infra with no business knowledge (UI kit, HTTP client, formatters, config).   |

† `src/app/` is the Next.js App Router directory. It overlaps with the FSD `app` layer concept but is route-driven. See `references/NEXT_APP_ROUTER.md`.

‡ Canonical FSD calls this layer `pages/`. We rename it to `views/` because **Next.js reserves `src/pages/` (and root `pages/`) for the legacy Pages Router** — creating a `pages/` folder alongside `src/app/` causes Next.js to detect both routers and error out. The role of the layer is unchanged.

### Import rule

A file in layer N may import from layers 1 … N-1 **only**. Same-layer (e.g. one feature from another) and upward imports are forbidden.

```
shared    ←  entities  ←  features  ←  widgets  ←  views  ←  app
                            ↑  cannot reach into a sibling
```

Enforced by `eslint-plugin-import` boundaries + the `steiger` FSD linter (`assets/steiger.config.ts`).

## Slices

A **slice** is one folder inside a layer. Each slice corresponds to a single business concept.

```
src/features/login/     ← slice
src/entities/user/      ← slice
src/widgets/sidebar/    ← slice
```

Rules:

- Slice names are nouns or short noun phrases, kebab-case.
- Slice folders live **directly** in their layer; no sub-categorisation (`features/auth/login/` is wrong — use `features/login/`).
- `shared/` does not have slices — it has segments at the top level (`shared/ui/`, `shared/lib/`, …).

## Segments (inside a slice)

| Segment    | Holds                                                                 |
|------------|-----------------------------------------------------------------------|
| `ui/`      | React components for this slice                                       |
| `model/`   | State (stores, hooks), business logic, types, schemas                  |
| `api/`     | Backend communication (fetch wrappers, RPC calls, query keys)         |
| `lib/`     | Utilities used **only** inside this slice                              |
| `config/`  | Slice-local constants, feature flags                                   |

Not every slice needs every segment. Add segments as needed; don't pre-create empty ones.

### Public API: `index.ts`

Each slice has an `index.ts` at the slice root. It re-exports only the symbols that may be consumed from outside the slice.

```ts
/**
 * @file features/login/index.ts
 * Public API for the login feature. Anything not re-exported here is private.
 */

export { LoginForm } from "./ui/login-form"
export { useLogin } from "./model/use-login"
export type { LoginCredentials } from "./model/types"
```

Imports from outside the slice **must** use the slice root:

```ts
// ✅
import { LoginForm } from "@/features/login"

// ❌  reaches past the public API
import { LoginForm } from "@/features/login/ui/login-form"
```

`shared/` is the one exception: import per-folder rather than from a single barrel (`@/shared/ui/button`, not `@/shared`). Keeps tree-shaking honest.

## Layer reference

### `app/` (Next.js App Router)

- Routing, `layout.tsx`, `page.tsx`, `error.tsx`, `loading.tsx`, `not-found.tsx`, `route.ts`.
- Global providers (theme, query client, auth context) live in the root `layout.tsx`.
- **No business logic.** A `page.tsx` body is a thin composition of one or more FSD `views/` slices.

### `views/` (FSD layer — canonical FSD calls this `pages/`)

- One folder per page-level composition. Mirrors the URL but is not a router.
- Composes widgets + features. Owns page-specific glue (data fetching coordination, query-param decoding, page-level SEO metadata).
- A FSD view is consumed from `src/app/<route>/page.tsx` as a single import.
- **Naming inside a slice:** the composition component is `*View` (e.g. `LoginView`) in a file named `<slice>-view.tsx`, not `*Page` / `*-page.tsx`. This keeps the FSD layer name and its symbols aligned, and keeps "page" reserved for Next.js routing files.

```tsx
// src/app/login/page.tsx
import { LoginView } from "@/views/login"
export default LoginView
```

> ⚠️ **Do not create `src/pages/`.** Next.js reserves that path for the legacy
> Pages Router; having both `src/app/` and `src/pages/` makes Next.js error.
> Use `src/views/` for the FSD layer described above.

### `widgets/`

- Self-contained, reusable UI blocks. Composed from features + entities.
- Examples: site header with auth dropdown, command palette, dashboard sidebar.
- A widget never speaks to the network directly — it composes features that do.

### `features/`

- A **user action** that produces business value. Verb-driven.
- Examples: `login`, `signup`, `add-to-cart`, `edit-profile`, `send-message`.
- A feature owns: the UI for the action (button, form, modal), the orchestration logic, and the API call.
- A feature may use entities + shared, but **never** another feature.

### `entities/`

- A **business entity** with its canonical type, base UI, and read-side API.
- Examples: `user`, `product`, `order`, `comment`.
- Holds the source-of-truth shape (`type User = …`), the canonical card / row component, fetchers for the entity, and a store if one is needed.
- An entity may use other entities **only** when the relationship is owned at the data layer (e.g. `comment` referencing `user` because `Comment` has a `User` field is fine).

### `shared/`

- Generic infra with no business knowledge. Holds the UI kit, HTTP client, hooks library, config.
- Segments at the top level: `shared/ui/`, `shared/lib/`, `shared/api/`, `shared/config/`, `shared/types/`.
- No slices in `shared/`.
- Import per-folder: `@/shared/ui/button`, `@/shared/lib/format-date`.

## Allow / deny matrix

|              | shared | entities | features | widgets | views | app |
|--------------|:------:|:--------:|:--------:|:-------:|:-----:|:---:|
| **app**      |   ✅   |    ✅    |    ✅    |   ✅    |   ✅  |  —  |
| **views**    |   ✅   |    ✅    |    ✅    |   ✅    |   ❌  |  ❌ |
| **widgets**  |   ✅   |    ✅    |    ✅    |   ❌    |   ❌  |  ❌ |
| **features** |   ✅   |    ✅    |    ❌    |   ❌    |   ❌  |  ❌ |
| **entities** |   ✅   |    ⚠️    |    ❌    |   ❌    |   ❌  |  ❌ |
| **shared**   |   ⚠️   |    ❌    |    ❌    |   ❌    |   ❌  |  ❌ |

Legend: ✅ allowed · ❌ forbidden · ⚠️ allowed within-layer only when there is a clear ownership relationship (entities → entities) or within `shared/` between sibling segments.

## When the rules feel wrong

If you find yourself wanting to break a rule, it usually means a slice belongs in a different layer:

- Two features keep needing the same logic → extract to `entities/` or `shared/`.
- A widget needs to call the network → it's actually a feature.
- A "feature" doesn't represent a user action → it's an entity or shared lib.
- An entity is pulling business decisions in → those decisions belong in a feature.

Refactor the slice's layer; don't bend the import rule.
