# Docstrings — file & function level

Every `.ts` and `.tsx` file in an MIS Next.js repo has two mandatory docstring layers:

1. **A file-level docstring** at the top of the file.
2. **A TSDoc block** above every exported function, component, hook, type, and interface.

Enforced by `eslint-plugin-jsdoc` (config in `assets/eslint.config.mjs`).

## File-level docstring

Position: very top of the file. Before `"use client"`, before imports.

Format:

```ts
/**
 * @file <fsd-path>/<file-name>
 * <one-sentence summary of what this file exports and its role in the slice>.
 */
```

Rules:

- `@file` tag is mandatory. The value is the path relative to `src/`, ending in the file name.
- Summary is one sentence (≤ ~100 chars). End with a period.
- For multi-export files, the summary covers the file's role, not each export.
- No blank line between the docstring and `"use client"` / first import.

Example:

```tsx
/**
 * @file features/login/ui/login-form.tsx
 * Login form: collects credentials, calls the auth submit action, surfaces errors inline.
 */
"use client"

import { useState } from "react"
// ...
```

## Function / component / hook docstring

Position: immediately above the declaration. No blank line between the docstring and the declaration.

Format:

```ts
/**
 * <one-line summary in imperative mood, ending with a period>.
 *
 * <optional longer description, wrap at ~80 chars>.
 *
 * @param <name> - <what it is; units / constraints if non-obvious>
 * @returns <what comes back; omit if void or trivially obvious>
 * @throws <ErrorClass> when <condition> — omit if no throws
 * @see {@link OtherSymbol}
 */
```

Tag rules:

- `@param` for every parameter, in order. Omit the type — TS owns the type.
- `@returns` is **required for non-void exports**. Omit it for void / trivial returns.
- `@throws` for every error class the function may surface. Document the condition.
- `{@link Symbol}` to cross-reference. The TS language server resolves these in tooltips.

### Functions

```ts
/**
 * Submits the user's login credentials and returns the session token.
 *
 * @param credentials - the email + password pair entered by the user
 * @returns the session token issued by the server
 * @throws AuthError when the credentials are rejected (HTTP 401)
 * @throws NetworkError when the server is unreachable
 */
export async function submitLogin(credentials: LoginCredentials): Promise<SessionToken> {
  // ...
}
```

### React components

```tsx
/**
 * Renders the login form and orchestrates the submit flow.
 *
 * @param props - see {@link LoginFormProps}
 */
export function LoginForm({ onSuccess }: LoginFormProps) {
  // ...
}
```

### Hooks

```ts
/**
 * Tracks the in-flight state of a single login attempt.
 *
 * @returns the submit handler plus `isPending` and `error` flags
 */
export function useLogin() {
  // ...
}
```

### Types & interfaces

```ts
/**
 * Credentials submitted to the auth endpoint.
 */
export interface LoginCredentials {
  /** The user's email address; validated by {@link LoginCredentialsSchema}. */
  email: string
  /** Plaintext password. Sent over TLS; never logged. */
  password: string
}
```

Each field gets a `/** */` doc comment. Single-line is fine for simple fields.

### Default exports (Next convention files)

```tsx
/**
 * @file app/login/page.tsx
 * Login route — composes the FSD login page slice.
 */
import { LoginView } from "@/views/login"
export { metadata } from "@/views/login"

/**
 * The login route's default export.
 *
 * @returns the rendered login view
 */
export default LoginView
```

## Internal helpers (non-exported)

Non-exported helpers inside a file get a **single-line** docstring:

```ts
/** Lowercases the email and trims whitespace. */
function normaliseEmail(input: string): string {
  return input.trim().toLowerCase()
}
```

Full TSDoc is only required for non-exported helpers when:

- The function has non-obvious behaviour (throws, side-effects, race-y).
- Multiple developers will touch it.
- It's > ~15 lines.

## What not to write

- **Don't restate the signature.** "Function that takes a string and returns a number" is noise — the signature already says that.
- **Don't write essays.** A docstring is not a design doc. If you need a design doc, write one and link it (`@see`).
- **Don't add change-log entries** ("Added 2025-09-01 by Alice"). That's what `git blame` is for.
- **Don't @-tag everything.** `@public`, `@internal`, `@beta` are noise unless they actually change tool behaviour.
- **Don't auto-generate.** Generated docstrings are uniformly bad ("Returns the result of the operation").

## Formatting

- Wrap at ~80 chars.
- One blank line between summary and longer description.
- One blank line between description and the first `@` tag.
- Use Markdown sparingly (`backticks` for code refs, `**bold**` for emphasis). Avoid headings inside docstrings.
- Use sentence case. End sentences with periods.

## ESLint rules

`eslint-plugin-jsdoc` rules in `assets/eslint.config.mjs`:

- `jsdoc/require-jsdoc` — exported symbols, components, hooks, classes.
- `jsdoc/require-file-overview` — the `@file` block (with custom message).
- `jsdoc/require-description`
- `jsdoc/require-param-description`
- `jsdoc/require-returns-description`
- `jsdoc/no-undefined-types` (off — TS owns types)
- `jsdoc/require-param-type` (off — TS owns types)
- `jsdoc/require-returns-type` (off — TS owns types)

The "types in TSDoc" rules are off because TypeScript provides the types; the docstring carries the semantics.

## Quick checklist

Before opening a PR:

- [ ] Every changed file has a `@file` docstring.
- [ ] Every changed exported symbol has a TSDoc block.
- [ ] `@param` covers every parameter; `@returns` is present unless void.
- [ ] Docstrings explain *intent*, not the signature.
- [ ] No essays, no change-log entries, no auto-generated boilerplate.
