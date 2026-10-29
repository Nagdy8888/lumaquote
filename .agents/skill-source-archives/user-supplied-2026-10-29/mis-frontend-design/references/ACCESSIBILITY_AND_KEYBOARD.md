# Accessibility and keyboard-first UX

Apps are tools; tools must be operable from the keyboard, by assistive technology, at every zoom level, and under low vision / motor impairment. This is not optional — both because the law requires it and because keyboard UX is what separates "fine" apps from beloved ones.

## The baseline (WCAG 2.2 AA, MIS minimum)

- **Color contrast ≥ 4.5:1** for body text, ≥ 3:1 for large text and UI components / graphical objects.
- **Focus visible** on every focusable element, with a focus ring distinguishable from hover.
- **Tab order matches visual order.** No `tabindex` > 0 in the codebase.
- **No keyboard traps.** Every modal, drawer, popover restores focus to its trigger on close.
- **Form fields have a real `<label>`** (not just placeholder).
- **Errors are programmatically associated** with their field (`aria-describedby`).
- **Live regions** announce async feedback (`aria-live="polite"` for toasts; `assertive` for errors only).
- **All interactive elements have a name** announced by AT (button text, `aria-label`, or `aria-labelledby`).
- **Touch targets ≥ 44×44 px** on touch devices.
- **No text in raster images** that conveys information not also present in text.
- **`prefers-reduced-motion: reduce`** disables non-essential motion (use instant state changes, not "fast" motion).

## Focus management

### Focus rings — visible, branded

```css
:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
  border-radius: inherit;
}
```

- `:focus-visible` (not `:focus`) so mouse users don't see rings, keyboard users do.
- `outline`, not `box-shadow` — outline works on inputs with custom borders without breaking layout.
- **Never `outline: none` without a replacement.** Removing focus rings without giving the user another visual cue is a bug.

### When to manage focus programmatically

- Opening a **modal / drawer / popover**: focus moves to the first focusable element inside.
- Closing: focus restores to the trigger.
- **Form submit with errors**: focus moves to the first invalid field.
- **Navigation that swaps a region** (tabs, accordion): announce + manage focus per the ARIA pattern.

Use **Radix UI**, **Headless UI**, or **React Aria** primitives for these — don't roll focus management by hand.

### Skip links

Every page has a "Skip to main content" link as the first focusable element. Visually hidden until focused, then visible.

```css
.skip-link {
  position: absolute;
  left: -10000px;
}
.skip-link:focus {
  position: static;
  outline: 2px solid var(--color-accent);
}
```

## Keyboard shortcuts — the conventional set

Don't reinvent. The set below is conventional across modern apps (Linear, Notion, Vercel, Raycast, GitHub).

| Shortcut         | Action                                |
|------------------|---------------------------------------|
| ⌘K / Ctrl+K      | Command palette                       |
| ⌘/ / Ctrl+/      | Open shortcuts cheat sheet            |
| ⌘Enter           | Submit current form / send / publish  |
| Esc              | Dismiss topmost overlay; cancel edit  |
| ⌘S / Ctrl+S      | Save (in apps with explicit save)     |
| ⌘F / Ctrl+F      | Search within page (do not hijack browser find casually) |
| g, then …        | Navigation prefix: `g h` home, `g s` settings, etc. |
| j / k            | Next / previous in lists              |
| n                | New (context-dependent: new item, new doc) |
| /                | Focus the global search input         |
| ?                | Open the shortcuts cheat sheet (same as ⌘/) |

### Implementation rules

- **Document them in-app** with a `?` keystroke. A shortcuts cheat sheet is a sign of a serious app.
- **Don't bind a shortcut that browsers own** (⌘T, ⌘W, ⌘L) unless you have a very good reason.
- **Show shortcuts in tooltips and menu items** — discoverability matters.
- **Use a library**: `cmdk` for the palette, `react-hotkeys-hook` or `tinykeys` for global shortcuts. Don't hand-roll keydown listeners on `window`.

### Per-surface shortcuts

- **Tables**: j/k row navigation, x to select, Enter to open, ⌘A to select all.
- **Editors**: standard text editing + bold (⌘B) / italic (⌘I) etc., **don't** override Tab unless the editor is a code editor.
- **Modals / drawers**: Esc closes; Enter activates the primary action **if** focus is in the action row (not on a textarea).

## Screen-reader semantics

### Use the right element

- **`<button>` for actions**, **`<a>` for navigation**. Not `<div onClick>`. Not "button" with a navigation behaviour.
- **`<input type="checkbox|radio|date|email|…">`** when applicable — they bring keyboard + screen-reader behaviour for free.
- **Headings (`<h1>`–`<h6>`)** form a meaningful outline of the page. One `<h1>` per page; no skipped levels.
- **Lists** for repeated items (`<ul>`, `<ol>`). A "list" of `<div>`s is not a list to a screen reader.

### ARIA — sparingly, correctly

> The first rule of ARIA is: don't use ARIA. The second rule is: use semantic HTML.

When you must use ARIA:

- **`aria-label`** on icon-only buttons.
- **`aria-labelledby` / `aria-describedby`** to associate labels and helper text.
- **`aria-live="polite"`** on toast regions; `"assertive"` only for errors that demand interruption.
- **`aria-expanded`, `aria-controls`, `aria-haspopup`** on disclosure widgets (use the library primitive).
- **`role="dialog"` + `aria-modal="true"`** on modals — or, again, use a primitive.

### Common AT failures

- **Icon-only buttons without a label.** `<button><TrashIcon /></button>` is announced as "button". Add `aria-label="Delete"`.
- **Custom select that's actually a div.** Use `<select>` or a proper combobox (React Aria, Downshift, cmdk).
- **Toggle that doesn't announce state.** Use `role="switch"` with `aria-checked` (or just an `<input type="checkbox">`).
- **Loading state announced as text but role unchanged.** Add `aria-busy="true"` on the region.
- **Error toast that's not announced.** Wrap in `aria-live="assertive"` (use the library — `sonner`, `react-hot-toast` get this right).

## Color and contrast

- **Pair color with a second signal.** Status pills have icons. Required fields have text labels. Charts have patterns or labels.
- **Test contrast against actual surfaces** (`--color-fg` on `--color-surface-1`, on `--color-surface-2`, on `--color-accent`). Half of contrast failures are foreground-on-accent.
- **Dark mode contrast is its own audit.** Don't assume inverting passes.
- **Disabled state**: ≥ 3:1 contrast even when disabled. Faded grey on white usually fails.

## Reduced motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
    scroll-behavior: auto !important;
  }
}
```

…but **also** disable parallax, autoplay videos, and the skeleton shimmer behind that media query. The rule above handles `transition`/`animation` but not custom JS-driven motion — wrap Framer Motion components with `useReducedMotion()` and provide instant variants.

## Touch and pointer

- **Hit targets ≥ 44×44 px** on touch. A 16×16 icon needs 14px padding on each side.
- **Don't rely on hover.** Anything reachable on hover must be reachable on tap / focus.
- **`pointer: coarse`** media query for touch-specific spacing.

## Zoom and reflow

- **Page must remain usable at 200% zoom** with no horizontal scrolling at standard widths.
- **No fixed pixel widths on text containers**. Use `max-width` + `width: 100%`.
- **`<meta name="viewport" content="width=device-width, initial-scale=1">`** with no `maximum-scale=1.0` — users may need to pinch-zoom.

## Forms — extra care

- **Real `<label>`s, programmatically associated** with the input (`for` / `htmlFor` or wrap).
- **Error association**: `aria-describedby="<error-id>"` so screen readers announce the error when focusing the field.
- **Required**: `aria-required="true"` (or just `required`), and a visible `(optional)` marker on the optional ones.
- **Autocomplete**: set `autocomplete="email"`, `"current-password"`, `"one-time-code"`, etc. — let password managers help.

## Testing

- **Tab through the page from top to bottom.** Can you reach everything? In the right order?
- **Open every overlay with the keyboard.** Tab inside; Esc closes; focus restores.
- **Use a screen reader** (VoiceOver on macOS, NVDA on Windows). Browse the main flow.
- **Run axe-core** in CI (`@axe-core/playwright` or `jest-axe`) on every page.
- **Check at 200% zoom + dark mode + `prefers-reduced-motion`** as part of QA.

## Tooling

| Tool                 | Use for                                  |
|----------------------|------------------------------------------|
| **axe DevTools** browser ext | Quick scan of a page                     |
| **`@axe-core/playwright`**    | Automated a11y checks in E2E tests        |
| **`jest-axe`**                | Component-level a11y in unit tests        |
| **VoiceOver / NVDA / TalkBack** | Real assistive technology testing |
| **Radix UI / React Aria / Headless UI** | Get the primitives' a11y for free |
| **`cmdk`**                    | Command palette with correct a11y        |
| **`sonner` / `react-hot-toast`** | Toasts with `aria-live` done right    |

## Anti-patterns

- `outline: none` without a replacement focus ring.
- `<div onClick>` as a button.
- Tooltip-only labels on icon buttons.
- Placeholder-as-label.
- Disabled submit buttons with no explanation.
- Color-only validation (red border, no message, no icon).
- Toasts that don't announce.
- Hover-only menus on desktop apps with touch users.
- Hand-rolled focus management for modals.
- `aria-label` on top of visible text (redundant; sometimes overrides).
- Skipping heading levels (`<h1>` → `<h3>`).
