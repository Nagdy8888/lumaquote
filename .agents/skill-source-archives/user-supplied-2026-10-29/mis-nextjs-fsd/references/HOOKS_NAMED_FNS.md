# Named function expressions in hooks

Every callback passed to a React hook (`useEffect`, `useLayoutEffect`, `useMemo`, `useCallback`, `useInsertionEffect`) is a **named function expression**, not an anonymous arrow.

## Why

1. **Stack traces.** An anonymous arrow shows as `at <anonymous>` in errors and React's component-stack. A named expression shows as `at syncUserProfile`. When a production error trips a Sentry alert, the difference is "where is this?" vs "fix the obvious bug".
2. **React DevTools.** The Profiler tags effects by the callback's function name. Anonymous → "Anonymous". Named → "syncUserProfile". When a slow effect shows up in a flamegraph, the name is the only useful identifier.
3. **Reader scan-ability.** The reader sees the *intent* of the effect on the first line, before the dependency list. They don't have to read the body to understand what the effect is for.
4. **Diff readability.** Renaming a named effect produces a 1-line diff. Moving an anonymous effect produces a churny "this changed; what was its purpose?" diff.
5. **Grep-ability.** `grep "function syncUserProfile"` finds every effect named that way. Anonymous effects can only be found by reading.

## The rule

```tsx
// ❌ anonymous arrow
useEffect(() => {
  void fetchUser(userId).then(setUser)
}, [userId])

// ✅ named function expression
useEffect(function syncUserProfile() {
  void fetchUser(userId).then(setUser)
}, [userId])
```

Naming convention: **verb phrase that describes the effect's purpose**.

- `useEffect`: side-effect verbs — `syncUserProfile`, `subscribeToInbox`, `trackPageView`, `cleanupListeners`, `attachScrollHandler`.
- `useMemo`: compute verbs — `computeFilteredItems`, `deriveTotalPrice`, `buildSortedIndex`.
- `useCallback`: handler verbs — `handleSubmit`, `handleDelete`, `handleSearchChange`.

## Applies to

| Hook                  | Named function expression required? |
|-----------------------|:-----------------------------------:|
| `useEffect`           | ✅ |
| `useLayoutEffect`     | ✅ |
| `useInsertionEffect`  | ✅ |
| `useMemo`             | ✅ |
| `useCallback`         | ✅ |
| `useImperativeHandle` | ✅ (the imperative methods inside, too) |
| `useTransition`       | ✅ (the function passed to `startTransition`) |
| `useSyncExternalStore`| ✅ (`subscribe`, `getSnapshot`) |
| `setState` updater    | ✅ when the updater is multi-line: `setX(function nextX(prev) { … })` |

## Async work inside effects

`useEffect` callbacks can't be `async`. Extract the async work into a **named inner function** and call it:

```tsx
// ✅
useEffect(function syncUserProfile() {
  async function loadUser() {
    const u = await fetchUser(userId)
    setUser(u)
  }
  void loadUser()
}, [userId])
```

Don't `void loadUser()` as a one-liner without the outer named effect — you lose the outer name.

## Cleanup functions

The cleanup function returned from `useEffect` is **also** a named function expression:

```tsx
useEffect(function subscribeToInbox() {
  const handle = inbox.subscribe(handleMessage)
  return function unsubscribeFromInbox() {
    inbox.unsubscribe(handle)
  }
}, [])
```

The cleanup name mirrors the effect name with the inverse verb (`subscribe…` → `unsubscribe…`, `attach…` → `detach…`, `start…` → `stop…`).

## Event handlers in JSX

One-line arrow handlers in JSX are **acceptable** — the inline syntax is the documentation:

```tsx
<button onClick={() => setOpen(true)}>Open</button>
```

Anything multi-line is lifted out into a named function:

```tsx
function handleDelete() {
  if (!confirm("Delete?")) return
  void deleteItem(item.id)
}

return <button onClick={handleDelete}>Delete</button>
```

Rule of thumb: if the body has more than one statement, lift it.

## Render callbacks (`.map`, `.filter`, …)

Inside JSX, short arrows are fine:

```tsx
{items.map((item) => <Row key={item.id} item={item} />)}
```

For multi-line render callbacks, lift to a named function inside the component:

```tsx
function renderRow(item: Item) {
  // multi-line composition...
  return <Row key={item.id} item={item} />
}

return <>{items.map(renderRow)}</>
```

## What named function expressions look like

Two equivalent forms — both acceptable, but pick one per repo and stay consistent. The MIS default is **inline named function expression**:

```tsx
// ✅ inline named expression (MIS default)
useEffect(function syncUserProfile() {
  void fetchUser(userId).then(setUser)
}, [userId])

// ✅ extracted + invoked
useEffect(() => {
  syncUserProfile(userId, setUser)
}, [userId])

function syncUserProfile(id: string, set: (u: User) => void) {
  void fetchUser(id).then(set)
}
```

Inline-named is the default because it keeps the effect's body co-located with its name and dependencies. Extract only when the same work is reused across multiple effects.

## ESLint enforcement

`assets/eslint.config.mjs` ships with a `no-restricted-syntax` rule that flags anonymous arrows in the relevant hooks:

```js
// excerpt — see assets/eslint.config.mjs for the full config
{
  "no-restricted-syntax": ["error",
    {
      "selector": "CallExpression[callee.name=/^use(Effect|LayoutEffect|InsertionEffect|Memo|Callback)$/] > ArrowFunctionExpression:first-child",
      "message": "Pass a named function expression to this hook instead of an arrow. e.g. useEffect(function syncFoo() { ... }, deps)"
    },
    {
      "selector": "CallExpression[callee.name=/^use(Effect|LayoutEffect|InsertionEffect|Memo|Callback)$/] > FunctionExpression[id=null]",
      "message": "The function expression passed to this hook must be named. e.g. function syncFoo() { ... }"
    }
  ]
}
```

The rule fails the build on the first offending callsite — no warnings.

## Migration recipe (existing codebase)

When adopting this skill on an existing repo:

1. Run the lint rule with `--rule 'no-restricted-syntax: error'` to find every offender.
2. Convert in batches by *layer*, lowest first (`shared/` → `entities/` → … → `app/`).
3. One PR per layer. Title: `refactor(<layer>): name effect callbacks (FSD <layer>)`.
4. Don't bundle behaviour changes into the migration. Renames only.
