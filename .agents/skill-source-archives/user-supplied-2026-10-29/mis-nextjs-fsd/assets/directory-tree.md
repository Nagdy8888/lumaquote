# Reference directory tree

The canonical layout for an MIS Next.js + FSD application. Keep this open while scaffolding the first few slices.

```
<repo-root>/
├── src/
│   ├── app/                            # Next.js App Router (routing only)
│   │   ├── layout.tsx                  # Root layout: global providers
│   │   ├── page.tsx                    # Home route
│   │   ├── login/
│   │   │   └── page.tsx                # → re-exports @/views/login
│   │   ├── dashboard/
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx                # → re-exports @/views/dashboard
│   │   └── api/
│   │       └── users/
│   │           └── [id]/
│   │               └── route.ts        # GET /api/users/:id
│   │
│   ├── views/                          # FSD "pages" layer — page compositions
│   │   │                               # (named views/ because Next.js reserves
│   │   │                               #  src/pages/ for the legacy Pages Router)
│   │   ├── login/
│   │   │   ├── index.ts                # public API: LoginView, metadata
│   │   │   ├── ui/login-view.tsx
│   │   │   └── model/metadata.ts
│   │   └── dashboard/
│   │       ├── index.ts
│   │       ├── ui/dashboard-view.tsx
│   │       └── model/load-data.ts
│   │
│   ├── widgets/                        # Self-contained UI blocks (reused across views)
│   │   ├── site-header/
│   │   │   ├── index.ts
│   │   │   └── ui/site-header.tsx
│   │   └── command-palette/
│   │       ├── index.ts
│   │       ├── ui/command-palette.tsx
│   │       └── model/use-palette.ts
│   │
│   ├── features/                       # User actions with business value
│   │   ├── login/
│   │   │   ├── index.ts                # public: LoginForm, useLogin, types
│   │   │   ├── ui/login-form.tsx
│   │   │   ├── model/
│   │   │   │   ├── use-login.ts
│   │   │   │   ├── submit-login.ts
│   │   │   │   └── types.ts
│   │   │   └── api/login.ts
│   │   ├── signup/
│   │   │   └── …
│   │   └── send-message/
│   │       └── …
│   │
│   ├── entities/                       # Business entities
│   │   ├── user/
│   │   │   ├── index.ts                # public: User, fetchUser, UserCard
│   │   │   ├── ui/user-card.tsx
│   │   │   ├── model/
│   │   │   │   ├── types.ts            # type User, UserSchema (Zod)
│   │   │   │   └── store.ts            # global user store, if any
│   │   │   └── api/
│   │   │       └── fetch-user.ts
│   │   └── product/
│   │       └── …
│   │
│   └── shared/                         # Reusable infra (no business knowledge)
│       ├── ui/                         # UI kit (Button, Input, Dialog, …)
│       │   ├── button/
│       │   │   ├── index.ts
│       │   │   └── button.tsx
│       │   └── input/
│       │       └── …
│       ├── lib/                        # Pure utilities (format-date, cn, …)
│       │   ├── format-date.ts
│       │   └── cn.ts
│       ├── api/                        # HTTP client, query keys, …
│       │   └── http.ts
│       ├── config/                     # Env vars, feature flags, constants
│       │   └── env.ts
│       └── types/                      # Generic ambient types
│           └── result.ts
│
├── public/                             # Static assets served at /
│
├── tsconfig.json                       # ← assets/tsconfig.json
├── eslint.config.mjs                   # ← assets/eslint.config.mjs
├── steiger.config.ts                   # ← assets/steiger.config.ts
├── next.config.ts
├── package.json
└── README.md
```

## What goes where — quick lookup

| Kind of file                              | Lives in                                    |
|-------------------------------------------|---------------------------------------------|
| Route entry (`page.tsx`, `layout.tsx`)    | `src/app/<route>/…`                         |
| Route API handler (`route.ts`)            | `src/app/api/<path>/route.ts`               |
| Page composition (the real page)          | `src/views/<view>/ui/<view>-view.tsx`       |
| Reusable UI block (header, sidebar, …)    | `src/widgets/<widget>/ui/…`                 |
| User-action form / button / orchestration | `src/features/<action>/ui/…` + `model/…`    |
| Entity type + Zod schema                  | `src/entities/<entity>/model/types.ts`      |
| Entity fetcher                            | `src/entities/<entity>/api/…`               |
| Entity card / row component               | `src/entities/<entity>/ui/<entity>-card.tsx`|
| UI kit primitives (Button, Input, …)      | `src/shared/ui/<primitive>/…`               |
| Generic util (formatDate, cn, …)          | `src/shared/lib/<util>.ts`                  |
| HTTP client                               | `src/shared/api/http.ts`                    |
| Env / feature-flag access                 | `src/shared/config/env.ts`                  |

## What never appears

- `src/pages/` — **reserved by Next.js for the legacy Pages Router.** Creating it alongside `src/app/` causes Next.js to detect two routers and error. The FSD "pages" layer lives at `src/views/` in this standard.
- `src/components/`, `src/hooks/`, `src/utils/` at the top level — these are technical-type folders that FSD replaces with business-meaning layers.
- `src/lib/` at the top level — that's `src/shared/lib/`.
- Per-route `components/` folders (`src/app/login/components/`) — components live in FSD slices.
- Nested slices (`features/auth/login/`) — flatten to `features/login/`.
- Default exports anywhere outside Next.js convention files.
