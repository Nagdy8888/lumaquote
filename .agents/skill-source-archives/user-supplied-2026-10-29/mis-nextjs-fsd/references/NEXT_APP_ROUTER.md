# Next.js App Router on top of FSD

Next.js owns `src/app/` for routing. FSD owns the rest of `src/`. This file is how they coexist.

## Two `app/`s? No — just Next's

The FSD layer called "app" (global wiring) and Next's `app/` (routing) overlap conceptually. We keep **only** Next's `src/app/` directory and treat it as the FSD app layer:

- Global providers (theme, query client, auth context) live in `src/app/layout.tsx`.
- Route segments live in `src/app/<route>/`.
- Everything else (FSD `views/`, `widgets/`, `features/`, `entities/`, `shared/`) lives in `src/` as siblings.

> ⚠️ **Why `views/` and not `pages/`.** Next.js reserves `src/pages/` (and root
> `pages/`) for the legacy Pages Router. If you create a `src/pages/` folder
> alongside `src/app/`, Next.js detects both routers, surfaces a conflict, and
> the build fails (or routes resolve incorrectly). The canonical FSD layer name
> is "pages", but in a Next.js App Router project the layer is renamed to
> **`views/`** to keep the slot free for Next.js's own use. Do not rename it
> back — the linter rules and Steiger config below assume `views/`.

## Page composition: thin `page.tsx`, fat FSD `views/` slice

The Next.js `page.tsx` is a **router-bound entry point** — its only job is to wire the URL to a FSD view slice. Business logic, layout composition, data orchestration, and SEO metadata live in the FSD `views/<view-name>/` slice.

```tsx
// ✅ src/app/login/page.tsx — 3 lines, no logic
import { LoginView } from "@/views/login"
export { metadata } from "@/views/login"
export default LoginView
```

```tsx
// ✅ src/views/login/ui/login-view.tsx — composition lives here
/**
 * @file views/login/ui/login-view.tsx
 * Login view composition: brand panel + login feature + footer widget.
 */
import { LoginForm } from "@/features/login"
import { SiteFooter } from "@/widgets/site-footer"

/**
 * Renders the login view layout.
 */
export function LoginView() {
  return (
    <main>
      <LoginForm onSuccess={(id) => { /* navigate */ }} />
      <SiteFooter />
    </main>
  )
}
```

```ts
// src/views/login/index.ts
export { LoginView } from "./ui/login-view"
export { metadata } from "./model/metadata"
```

## Server vs Client Components

Next.js App Router defaults to **Server Components**. Mark client boundaries with `"use client"` at the top of the file (right after the `@file` docstring).

Rules:

- **Default to Server Components.** Push `"use client"` as low as possible — to the leaf that actually needs interactivity.
- **Hooks (`useState`, `useEffect`, …) require `"use client"`.** Pure presentational components don't.
- **A Server Component may render Client Components**, but a Client Component cannot import a Server Component (it can receive one as `children`).
- **`async` Server Components** are allowed for data fetching at the page / layout level.

```tsx
/**
 * @file features/login/ui/login-form.tsx
 * Client-side login form: handles input state and submit.
 */
"use client"

import { useState } from "react"
// ...
```

## Routing files inventory

Next-owned file names that may appear in `src/app/<route>/`:

| File              | Purpose                                          | Default export required? |
|-------------------|--------------------------------------------------|--------------------------|
| `page.tsx`        | Route entry point (URL → component)              | **Yes**                  |
| `layout.tsx`      | Persistent shell wrapping the segment            | **Yes**                  |
| `loading.tsx`     | Streaming fallback                               | **Yes**                  |
| `error.tsx`       | Error boundary (client component)                | **Yes**                  |
| `not-found.tsx`   | 404 boundary                                     | **Yes**                  |
| `route.ts`        | API / route handler (GET/POST/…)                 | No (named exports per verb) |
| `template.tsx`    | Like layout but re-instantiates on navigation    | **Yes**                  |
| `metadata.ts`     | Static metadata or `generateMetadata`            | Named exports            |

**Default exports are mandatory for the entries above** and are the **only** allowed default exports in the codebase.

## Data fetching

- **Server-side fetch in views / layouts:** call the entity / feature API directly from an `async` Server Component. No client query library needed.
- **Client-side fetch:** wrap the entity `api/` call with TanStack Query (or equivalent) inside the feature's `model/`. Don't fetch directly from the UI component.
- **Cache control:** explicit. Use Next's `fetch(..., { next: { revalidate: N } })` or `cache: "no-store"`. No defaults — write the intent.
- **Mutations:** Server Actions are allowed but the action lives in the feature's `api/`, not inline in the JSX.

## Route handlers (`route.ts`)

API endpoints under `src/app/api/<path>/route.ts`. Body should:

1. Validate input with Zod (or equivalent).
2. Delegate to a feature's `api/` or `model/` — no business logic in the handler.
3. Return `NextResponse.json(...)` with explicit status codes.

```ts
/**
 * @file app/api/users/[id]/route.ts
 * GET /api/users/:id — returns the user or 404.
 */
import { NextResponse } from "next/server"
import { z } from "zod"
import { getUser } from "@/entities/user"

const Params = z.object({ id: z.string().uuid() })

/**
 * Handles GET /api/users/:id.
 *
 * @returns 200 with the user, 400 for invalid id, 404 if not found.
 */
export async function GET(_req: Request, ctx: { params: { id: string } }) {
  const parsed = Params.safeParse(ctx.params)
  if (!parsed.success) return NextResponse.json({ error: "invalid_id" }, { status: 400 })

  const user = await getUser(parsed.data.id)
  if (!user) return NextResponse.json({ error: "not_found" }, { status: 404 })
  return NextResponse.json(user)
}
```

## Metadata

Page metadata lives in the FSD `views/<view>/model/metadata.ts` and is re-exported from the slice's `index.ts`:

```ts
/**
 * @file views/login/model/metadata.ts
 * SEO metadata for the login view.
 */
import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Sign in",
  description: "Sign in to your MIS account.",
}
```

The Next-owned `app/login/page.tsx` re-exports it: `export { metadata } from "@/views/login"`.

## Don'ts

- Don't put business logic in `app/**`. `app/` is plumbing.
- Don't create per-route folders (`app/login/components/`) — components live in FSD slices.
- Don't import from `@/app/...` anywhere else. The app layer is a sink, not a source.
- Don't disable React Server Components defaults by sprinkling `"use client"` at the layout level. Push it down.
