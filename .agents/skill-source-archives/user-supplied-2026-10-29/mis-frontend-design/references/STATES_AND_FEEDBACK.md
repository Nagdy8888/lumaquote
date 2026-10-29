# States and feedback

App quality is measured by how the **non-happy paths** feel. Loading, empty, error, partial, optimistic — design these before you design the happy path; the happy path falls out of them.

## The state matrix

For every interactive surface, enumerate:

| State                  | When                                                           |
|------------------------|----------------------------------------------------------------|
| **Empty (first run)**  | The user has never had data here.                              |
| **Empty (cleared)**    | Filters / search return nothing (the user *did* have data, just not this).|
| **Loading (initial)**  | No data yet, request in flight.                                |
| **Loading (incremental)** | Some data shown, more being fetched (load-more, pagination). |
| **Partial**            | Some data loaded, some failed / pending.                       |
| **Optimistic**         | UI updated; server not yet confirmed.                          |
| **Error (recoverable)**| Request failed; retry is the right next step.                  |
| **Error (auth / permission)** | The user lacks access.                                  |
| **Error (validation)** | Input rejected; fix and retry.                                 |
| **Success**            | The action completed; user needs to know.                      |
| **Disabled**           | The action exists but isn't available right now (and **the UI tells the user why**).|
| **Read-only**          | The user can view but not modify.                              |

If a screen ships without a designed answer for each applicable row, it ships broken.

---

## Empty states

### Empty (first run) — the only place expressive design lives in the app

This is **the** brand moment inside the app surface. Treat it as such.

Anatomy:

- **Illustration or geometric mark** that lives in the brand voice.
- **One-sentence pitch** in the display face.
- **One primary CTA** — the next action the user should take.
- **Optional secondary link** — docs, video, "import existing data".
- **No "no data found" copy.** The user knows there's no data; tell them what to do.

Examples:

```
[ illustration of a stylised inbox ]
Your inbox is quiet.
Connect Gmail to start triaging — or send yourself a test message.
  [ Connect Gmail ]   Watch the 60-second tour →
```

### Empty (cleared)

The user filtered or searched into nothing. Calm; do **not** rebrand the empty state here.

Anatomy:

- Inline within the surface (the table body / list body), not a full-screen takeover.
- One sentence: `No orders match these filters.`
- A single affordance: `Clear filters` or `Show all`.
- No illustration. No CTA. The user is mid-task.

---

## Loading states

### Initial load → skeleton

For anything that may take > 1 second to fetch, show a **skeleton that matches the final layout** — same column widths, same row count (or 5–10 placeholder rows), same shape.

Why: the page doesn't *jump* when data arrives, and the user starts orienting before the data lands.

```tsx
{isLoading
  ? <TableSkeleton columns={columns} rows={8} />
  : <Table data={data} columns={columns} />}
```

Skeleton implementation:

- A muted block (`--color-surface-2`) with a subtle shimmer using `background-position` animation.
- **Respect `prefers-reduced-motion`** — drop the shimmer to a static block.
- Skeleton **shapes**, not generic bars. A skeleton row in an avatar-name-date table has an avatar circle, a wide label bar, a narrow date bar.

### Initial load → spinner

Spinners are for **< 1 second** waits where a skeleton would be over-engineered (button-in-progress, in-place refresh). Use a small inline spinner with the action label:

```
[  ⟲ Saving…  ]
```

### Incremental load

The user has data and is loading more (pagination, load-more, scroll-into-view).

- Show a pending row at the bottom matching the row height.
- **Never block the existing UI** with a full-surface spinner.
- Newly-loaded items fade in with `--dur-1`; **don't shift the scroll position**.

### Long-running operations

Anything > 5 seconds gets a **progress indicator** with:

- Step label ("Uploading 3 of 12…").
- Percentage when determinable.
- **Cancel button** when the operation is cancellable.
- **Background-able**: the user can navigate away; the progress moves to a notification / status bar.

---

## Partial

The most-skipped state. Common when:

- A dashboard pulls from 6 services and 2 are slow.
- A list of items each fetches a derived field, and some derived fields fail.

Pattern:

- Show **what you have**.
- Mark the rest with **inline indicators** (a small "—" with a `?` tooltip, or a one-line "Unable to load X. Retry" inside the row).
- **Do not** block the whole surface because a sub-resource failed.
- **A toast at the top is acceptable** for "Some data couldn't load; retry."

---

## Optimistic UI

Use when the server response is reliable and the latency is noticeable (> 200ms). The pattern:

1. **Update the UI immediately** as if the request succeeded.
2. **Fire the request.**
3. **On success**: nothing more to do (the UI already shows success).
4. **On failure**: revert the UI; show a **toast with the failure reason + Undo / Retry**.

```tsx
async function toggleStar(id: string) {
  setItems(prev => prev.map(it => it.id === id ? { ...it, starred: !it.starred } : it))
  try {
    await api.toggleStar(id)
  } catch (e) {
    setItems(prev => prev.map(it => it.id === id ? { ...it, starred: !it.starred } : it))
    toast.error("Couldn't update star. Retry?", { action: { label: "Retry", onClick: () => toggleStar(id) } })
  }
}
```

When to **not** use optimistic UI:

- The result depends on server-computed state the client doesn't know (server-assigned id, computed totals).
- The operation is destructive — show a "Saved" / "Deleted" confirmation only after the server confirms.

---

## Errors

The single biggest predictor of "this app feels broken" vs "this app feels solid" is error copy quality.

### Three rules

1. **Specific.** "Couldn't save changes — your session expired." beats "Something went wrong."
2. **Actionable.** Every error includes a next step: Retry, Sign in again, Contact support with this ID, Edit and try again.
3. **Surfaced in the right place.** Field errors inline; surface errors above the surface; system errors as a banner; catastrophic errors as a full-screen state.

### Anatomy by severity

**Inline (validation):**
```
  [ acme@acmecorp.   ]
  ⚠ This email already has an account. Sign in instead?
```

**Surface-level (request failed):**
```
  ┌─────────────────────────────────────────────────┐
  │ ⚠ Couldn't load orders.                          │
  │   The orders service is unreachable. Retry      │
  │   in a moment. If this keeps happening, share   │
  │   reference ID: ord_7d8c                         │
  │                          [ Retry ]               │
  └─────────────────────────────────────────────────┘
```

**System (auth, permission):**
```
  ┌─────────────────────────────────────────────────┐
  │ Your session has expired.                        │
  │              [ Sign in again ]                   │
  └─────────────────────────────────────────────────┘
```

**Catastrophic (uncaught error boundary):**

Full-surface friendly screen. Apologetic but not melodramatic. Reference ID in mono. Link to support.

### Banned error copy

- "Something went wrong."
- "Oops!" / "Uh-oh!" / "Whoops!"
- "An error occurred."
- "Please try again later."
- "Contact your administrator." (only when the user actually has an admin to contact)

### Reference IDs

Every non-validation error gets a **short reference id** the user can paste into a support ticket. Generate at the boundary (e.g. an `x-request-id` echoed in the response). Always render in mono.

---

## Success

The bar for success feedback: **inversely proportional to the visibility of the change itself**.

| Change visibility | Feedback                                                              |
|-------------------|----------------------------------------------------------------------|
| The change is **already visible** on screen (row added, name updated in-place) | Nothing. The change *is* the feedback. |
| **Off-screen** change (saved settings, sent invitation) | Toast with action ("View invitation"). |
| **Cross-context** change (started export, scheduled report) | Inline status + a notification when it completes. |
| **Irreversible high-stakes** change (deleted project, transferred ownership) | Modal confirmation **before**, toast after, undo where possible. |

### "Saved" indicators in forms

For auto-saving forms:

- A small `Saved ✓` next to the section heading, fades out after `--dur-3`.
- **Pending save**: `Saving…` with a small inline spinner.
- **Failed save**: `Save failed. Retry` inline + toast.

For explicit-save forms:

- Disabled save button when not dirty; enabled when dirty.
- Saving state on the button; success toast on complete.

---

## Disabled

The most-abused state. A disabled control without explanation is a wall.

Rules:

- **Always explain why** — tooltip on hover/focus: "You need 'admin' to do this."
- **Disabled does not mean invisible.** Lower contrast, not zero contrast.
- **Use a non-interactive alternative** when the user shouldn't be able to act, and reserve disabled for "you *could* act, but not right now."

Examples:

```
[ Delete project ] (disabled)
  └─ Tooltip: "Only owners can delete projects."
```

For form submit buttons specifically: see the form section in `APP_PATTERNS.md` — prefer "submit + show errors" over "disabled until valid".

---

## Read-only

When the user can view but not modify (permissions, billing not active, archived state):

- **Banner at the top** of the surface: "This project is archived. Restore to make changes." with a primary "Restore" action.
- **Form fields** show their value without input borders — clearly readable, clearly not editable.
- **Action buttons** are hidden or disabled (with a tooltip).

---

## Putting it together — design the matrix first

Before composing a screen, list every state the surface can be in:

```
ORDERS LIST
- empty (no orders ever)           → onboarding empty state
- empty (filtered to nothing)      → inline "clear filters"
- loading (initial)                → skeleton rows
- loading (more)                   → pending row at bottom
- partial (some columns failed)    → inline "—" with retry
- error (request failed)           → surface error + retry
- error (unauthorised)             → "you don't have access" page
- ready                            → the happy path
```

Compose all of them. Ship none of them as TODOs.
