# App patterns — tables, forms, navs, dialogs, settings

The set of recurring surfaces that decide whether an app feels excellent or generic. Each entry: when to use, anatomy, rules, anti-patterns.

## Navigation shell

The persistent chrome around every feature surface.

### Sidebar + main content (default)

- **Left sidebar**, fixed width (~240px), collapsible to icons (~56px) for power users.
- **Logo + workspace switcher** at the top; **profile / settings** at the bottom; **primary navigation** between.
- **Active state**: surface tint (`--color-accent-soft`) + foreground (`--color-accent`). Not a left-edge stripe by default — that reads as 2014.
- **No more than 7 primary nav items.** Past that, group or use the command palette.
- **Search / command palette trigger** in the top bar with the ⌘K affordance visible.

### Top nav

Use **only** when the app is content-heavy with shallow hierarchy (a docs app, a blog admin). Default to sidebar for tool-like apps.

### Breadcrumbs

For apps with hierarchical content > 2 levels deep. Each crumb is a real link. Truncate the middle, not the start or end.

## Data table

The most-used surface in most apps. Get it right and the app feels fast; get it wrong and nothing else matters.

### Anatomy

```
┌──────────────────────────────────────────────────────────────┐
│  Filter bar:  [search]  [filter chips]   [density] [columns] │
├──────────────────────────────────────────────────────────────┤
│ ☐  COLUMN A ↑   COLUMN B    COLUMN C    COLUMN D    ⋯       │
├──────────────────────────────────────────────────────────────┤
│ ☐  …            …           …           …                    │
│ ☐  …            …           …           …                    │
└──────────────────────────────────────────────────────────────┘
  Selected:  3 rows         [Delete] [Export] [More ⌄]
```

### Rules

- **Sticky header** when the table scrolls.
- **Hover row** raises a single affordance (the row-level action menu); no full row-background change on hover unless the row is itself a link.
- **Tabular numerals** in any numeric column.
- **Right-align numbers + currency**; left-align text; center icons / status pills.
- **Density modes** (comfortable / compact) controlled by a single token swap.
- **Bulk selection** uses a **selection bar at the top of the table**, not buttons inside the row menu. The selection bar lists count and primary actions.
- **Sort indicators** on the column header label, not floating elsewhere.
- **Empty state inside the table** when filters return no rows — with a "clear filters" affordance, not an illustration.
- **Loading**: skeleton rows matching the column widths. Never a centered spinner.
- **Row click**: either opens a detail (drawer / page) consistently — or doesn't do anything. Mixing is hostile.
- **URL state**: filters, sort, page, density are URL-addressable. Sharable + back-button works.

### Anti-patterns

- Pagination with `< 1 2 3 4 ... 50 >` when you have a "load more" feed. Pick a model and stick to it.
- Putting destructive actions in the row hover. Move to the row menu, and require type-to-confirm for permanent deletes.
- A `Show 10 / 25 / 50` selector hidden in a corner. It's a top-bar control.

## Form

### Layout

- **Single column** by default. Multi-column forms are read as forms only by designers; users skip fields.
- **Sections** with a small heading + helper sentence; max 5–7 fields per section.
- **Labels above** the input (not floating, not placeholder-as-label).
- **Helper text below** the input, muted, ~12–13px.
- **Required vs optional**: mark **optional** with `(optional)` rather than star-marking required. The default assumption is required.
- **Primary action right-aligned**, secondary action immediately left of primary. Cancel / discard is `text-button` style on the far left of the action row.

### Validation

- **Validate on blur**, not on every keystroke. Exception: format-as-you-type (phone, card).
- **Inline error below the field**, with the input border in `--color-danger` and an icon at the right edge.
- **Submit attempt**: validate all, focus first invalid, scroll into view.
- **Server errors** map back to the same inline location. Never a flash banner that doesn't say which field.

### Patterns

- **Email**: validate format on blur; offer "did you mean gmail.com?" on common typos.
- **Password**: meter shows strength; toggle visibility; never block paste.
- **Date**: native picker on mobile, custom on desktop. Allow typed input.
- **Money**: tabular numerals; currency symbol as adornment, not free text.
- **Multi-select**: combobox with chips for ≤ ~20 options; transfer list for larger sets.

### Anti-patterns

- Disabled submit button until form is valid. Use it as a **lever to show the user what's wrong**, not a wall. Submit-attempt-with-focus-first-error is the standard.
- Placeholder as label. Hides context once typed.
- Native browser-tooltip validation. Use your own inline error.

## Modal / dialog

Used for: high-attention confirmation, focused editing of a small thing, anything that should block the surface behind it.

- **Size**: to content. Don't force a fixed width.
- **Focus trap** with focus restored to the trigger on close.
- **ESC closes**. Click on backdrop closes for low-stakes; **doesn't close** for in-progress forms with unsaved changes (show a confirmation).
- **Primary action right-aligned**; danger variant uses `--color-danger` background.
- **Title at top, action row at bottom**, content scrolls between if needed.
- **`role="dialog"` + `aria-modal="true"` + `aria-labelledby`**. Use Radix Dialog / Headless UI Dialog rather than rolling your own.

### Destructive confirm

Permanent-destructive (delete account, delete project) requires **type-to-confirm** (`Type "<name>" to confirm`). Soft-destructive (delete one row with undo) uses an inline action + undo toast — no modal.

## Drawer / side panel

For: deeper context on a row without losing the table, or an inline edit form.

- **Right-aligned** by default. Width ~480px–640px.
- **The table behind stays visible** and dimmed (`--color-surface-1` with reduced opacity overlay).
- **URL-addressable** when stateful (`/orders?selected=abc123`). Back button closes the drawer.
- **ESC closes**. Tab cycles inside the drawer.
- **Pinning**: power users may "pin" a drawer to keep it open while navigating rows.

## Popover / dropdown

For: contextual menus, inline pickers, hover-detail.

- **Anchored to the trigger**; auto-flip to fit viewport.
- **Pointer enters**: opens after ~200ms hover. **Click**: opens immediately and persists until clicked outside.
- **Keyboard**: arrow keys cycle, Enter selects, ESC closes.
- Use **Radix Popover / Dropdown / Menu** primitives or a peer library — don't hand-roll the focus management.

## Command palette

⌘K (Ctrl+K). Required for any app with > 8 nav items.

- **Indexes**: navigation, primary actions, recent items, search results.
- **Fuzzy match** with highlight of matched characters.
- **Grouped sections** (Pages, Actions, Recent, Documents).
- **Per-item keyboard shortcut** displayed on the right.
- **Arrow keys + Enter**; **Tab is not for cycling items** — that's arrow keys' job.
- **Empty state**: helpful suggestions, not "no results".
- **Backed by URL** — `/?command=…` deep-link the palette is open.

## Settings

- **Sectioned single-column layout** with a sticky in-page nav on the left listing sections.
- **Each section is independently saveable**, with a "Save" / "Discard" row appearing only when the section is dirty.
- **Never nested tabs.** If you find yourself wanting them, split into multiple pages.
- **Dangerous settings** (delete account, transfer ownership) live in a "Danger zone" at the bottom, with red border and explicit copy.

## Notifications / toasts

- **Bottom-right** (or bottom-center on small viewports). Stack with the newest on top.
- **Auto-dismiss after 5–8s**, **paused on hover**, **dismissable**.
- **Include an action** when there is one — "Undo", "View", "Retry". Never "OK".
- **Variants**: neutral / success / warning / danger. Use sparingly; success toasts on every save are noise.
- **`aria-live="polite"`** for non-blocking; `assertive` only for true errors.

## Pagination vs infinite scroll

| Use pagination when | Use infinite scroll when |
|---------------------|--------------------------|
| Data is tabular and the user navigates by reference | Data is feed-like and the user grazes |
| The user might deep-link to a specific page | The "deep" position is not meaningful |
| Counts / "X of N" matter | Counts are estimates or unbounded |

Pagination controls live at the **bottom-left** (per-page selector + range) and **bottom-right** (page buttons). Never split them across the page.

## Tabs

- **Section tabs** (within a page): underline-style, left-aligned, secondary navigation only. Max 5 tabs.
- **No nested tabs.** If you need them, you need separate pages.
- **URL-addressable** — `/orders/123?tab=history`.

## Search

- **Cmd-K palette** for global search.
- **In-context search** within a feature uses a `<input type="search">` with a leading icon and a clear-button when populated.
- **Server-search returns < 200ms** — otherwise show a skeleton in the results area.
- **Highlight matched terms** in the results.

## Cards (use sparingly)

Cards are over-used. Default to **flat surfaces separated by space and hairlines**.

Cards are right when:

- The content is a **discrete repeatable unit** the user picks among (workspace switcher, plan tiles).
- The content has **its own background image** or strong identity (board cards in Trello-style apps).

Cards are wrong when:

- You're using them to "make the page look designed" — that's the SaaS-template aesthetic.
- The cards are all identical and span the page — that's a table.

## Putting it together

Every feature surface composes from these primitives. The work of design is choosing the **right primitive** and the **right state set** (next reference) — not inventing new ones.
