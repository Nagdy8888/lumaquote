# TypeScript rules

This is the canonical TS contract for MIS Next.js apps. The settings ship in `assets/tsconfig.json`; the rationale is here.

## `tsconfig.json` — required compiler options

```jsonc
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "jsx": "preserve",

    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,

    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,

    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

Why each non-default matters:

- **`noUncheckedIndexedAccess`** — `arr[i]` is `T | undefined` instead of `T`. Eliminates a huge class of runtime crashes on empty arrays / missing keys.
- **`exactOptionalPropertyTypes`** — `{ foo?: string }` no longer silently allows `{ foo: undefined }`. Distinguishes "missing" from "present-and-undefined".
- **`verbatimModuleSyntax`** — forces `import type` for type-only imports. Catches misuse at compile time and keeps emitted JS clean.
- **`noUnusedLocals` / `noUnusedParameters`** — dead variables fail the build. Prefix with `_` to opt out (`_unusedParam`).

## Naming conventions

| Kind                                | Convention            | Examples                             |
|-------------------------------------|-----------------------|--------------------------------------|
| File names                          | kebab-case            | `login-form.tsx`, `use-login.ts`     |
| React components                    | PascalCase            | `LoginForm`, `UserCard`              |
| Types & interfaces                  | PascalCase            | `LoginCredentials`, `UserProps`      |
| Functions, methods, variables       | camelCase             | `submitLogin`, `userId`              |
| Hooks                               | camelCase, `use*`     | `useLogin`, `useUserProfile`         |
| React event handlers                | camelCase, `handle*`  | `handleSubmit`, `handleDelete`       |
| Boolean variables                   | `is* / has* / should*`| `isPending`, `hasAccess`             |
| Module-level immutable constants    | UPPER_SNAKE_CASE      | `MAX_RETRY`, `DEFAULT_PAGE_SIZE`     |
| FSD slice folders                   | kebab-case noun       | `login/`, `user-profile/`            |
| Zod schemas                         | PascalCase + `Schema` | `LoginCredentialsSchema`             |

## Types vs interfaces

- **`interface`** for object shapes that may be extended or implemented (component props, public API contracts).
- **`type`** for unions, intersections, mapped/conditional types, and aliases.
- Don't mix purely for style. Pick the one that fits the shape.

```ts
// ✅ extensible component contract
export interface ButtonProps {
  variant?: "primary" | "secondary"
  onClick?: () => void
}

// ✅ union — must be a type alias
export type LoadingState = "idle" | "pending" | "success" | "error"
```

## No `any`

`any` opts the value out of the type system. Use `unknown` and narrow.

```ts
// ❌
function parse(input: any) { return JSON.parse(input) }

// ✅
function parse(input: unknown): UserSchemaT {
  if (typeof input !== "string") throw new TypeError("expected string")
  return UserSchema.parse(JSON.parse(input))
}
```

The two acceptable escape hatches:

1. **`unknown`** — for genuinely unknown input. Narrow before use.
2. **`// @ts-expect-error <reason>`** — must include a written reason. Build fails if the comment becomes stale (the error went away).

`@ts-ignore` is **not** allowed (it silently rots).

## `import type` is mandatory

```ts
// ✅
import type { User } from "@/entities/user"
import { fetchUser } from "@/entities/user"

// or merged with verbatimModuleSyntax
import { fetchUser, type User } from "@/entities/user"
```

Enforced by `verbatimModuleSyntax: true`.

## Discriminated unions over enums

TS enums emit runtime objects, don't tree-shake, and have surprising behaviour (numeric reverse mapping). Tagged unions are zero-cost and exhaustive-checkable.

```ts
// ❌
enum Status { Pending, Success, Error }

// ✅
type Status =
  | { kind: "pending" }
  | { kind: "success"; data: Result }
  | { kind: "error"; error: Error }

function render(s: Status) {
  switch (s.kind) {
    case "pending": return <Spinner />
    case "success": return <View data={s.data} />
    case "error":   return <ErrorBanner error={s.error} />
    default: {
      const _exhaustive: never = s
      throw new Error(`unhandled status: ${_exhaustive}`)
    }
  }
}
```

The `never` fallthrough makes the compiler reject any future addition that isn't handled.

## Boundary validation with Zod

Any value crossing into the app from outside (network response, URL params, form data, localStorage, `window.postMessage`) goes through a schema **before** it becomes a typed value.

```ts
import { z } from "zod"

export const UserSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  createdAt: z.coerce.date(),
})

export type User = z.infer<typeof UserSchema>

export async function fetchUser(id: string): Promise<User> {
  const res = await fetch(`/api/users/${id}`)
  const json: unknown = await res.json()
  return UserSchema.parse(json)
}
```

Never `as User` your way past unknown data. The whole point of strict TS is the boundary; respect it.

## Path aliases

One alias only: `@/*` → `./src/*`. Cross-layer imports use it:

```ts
// ✅
import { Button } from "@/shared/ui/button"
import { useLogin } from "@/features/login"

// ❌ — relative reach across layers is forbidden by ESLint
import { Button } from "../../../shared/ui/button"
```

Within a slice, relative imports are fine and preferred (they survive moves):

```ts
// inside features/login/ui/login-form.tsx
import { submitLogin } from "../model/submit-login"
```

## Function signatures

- **Always type the return type of exported functions.** Inference is fine internally; at the public boundary it's a contract.
- **Avoid optional positional params past the first.** Use a single options object after the first one or two required args.
- **Default to readonly.** `readonly string[]`, `ReadonlyArray<…>`, `readonly` props. Mutate only when you mean to.

```ts
// ✅
export function paginate<T>(
  items: readonly T[],
  options: { page: number; pageSize: number },
): { items: readonly T[]; total: number } {
  // ...
}
```

## Generics

- Single-letter names (`T`, `K`, `V`) for trivial generics; descriptive (`TUser`, `TResponse`) when the type's role matters.
- Constrain generics (`<T extends User>`) when the body assumes shape. Unconstrained generics are usually a mistake.
- Don't generify when a union would do.

## React-specific

- **Props interfaces named `<Component>Props`.** Always exported.
- **No `React.FC`.** Use a plain function with typed props — `FC` implies `children` and breaks generic components.
- **Children typing:** `children: React.ReactNode` (not `JSX.Element` which is too narrow).
- **Refs:** use the new (React 19) `ref` as a prop, not `forwardRef`.

```tsx
export interface CardProps {
  title: string
  children: React.ReactNode
}

export function Card({ title, children }: CardProps) {
  return <section><h2>{title}</h2>{children}</section>
}
```

## ESLint enforcement

`assets/eslint.config.mjs` ships with the strict ruleset:

- `@typescript-eslint/no-explicit-any: error`
- `@typescript-eslint/consistent-type-imports: error`
- `@typescript-eslint/no-unused-vars: ["error", { argsIgnorePattern: "^_" }]`
- `@typescript-eslint/explicit-module-boundary-types: error`
- `no-restricted-syntax` rules for hooks (see `HOOKS_NAMED_FNS.md`)
- `import/no-default-export` (allowlisted for Next convention files only)
- FSD boundary rules via `eslint-plugin-import` + `steiger`
