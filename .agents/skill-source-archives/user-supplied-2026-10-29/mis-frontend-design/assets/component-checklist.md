# Component QA checklist

Use before considering any new component "done". Print, paste into the PR, work top-to-bottom.

## Visual

- [ ] All colour values reference `--color-*` tokens (no raw hex, no Tailwind defaults like `text-blue-500`).
- [ ] Spacing uses the `--space-*` scale (no `padding: 13px`).
- [ ] Type uses the size scale (`text-xs` / `sm` / `md` / `lg` / `xl` / `2xl`).
- [ ] Weights limited to 400 / 500 / 600 (or the project's three-weight set).
- [ ] Radius uses the radius scale.
- [ ] Borders use `--color-border` (or `--color-border-strong` in dense UI).
- [ ] Shadow stack is at most two layers (border + soft shadow).

## States — design AND implement all that apply

- [ ] Default (rest)
- [ ] Hover
- [ ] Focus (visible focus ring via `:focus-visible`)
- [ ] Active / pressed
- [ ] Disabled — with a tooltip explaining *why*
- [ ] Loading (pending action) — inline spinner with label, or skeleton
- [ ] Empty (no data)
- [ ] Error (validation or async)
- [ ] Success (inline ✓, toast, or no-op if the change is visible)
- [ ] Read-only (where applicable)

## Motion

- [ ] Duration from the scale: `--dur-1` / `--dur-2` / `--dur-3`.
- [ ] Easing matches direction: `--ease-out` appearing, `--ease-in` leaving.
- [ ] `prefers-reduced-motion: reduce` replaces motion with instant state change.
- [ ] No motion on repeat-use scroll surfaces (lists, tables).
- [ ] Motion answers cause-and-effect or async work — not decoration.

## Keyboard

- [ ] Component reachable by Tab in visual order.
- [ ] Primary action triggerable from the keyboard (Enter / Space).
- [ ] Esc dismisses any overlay this component opens.
- [ ] Arrow keys cycle items if this is a list / menu / combobox.
- [ ] Focus restores to the trigger after dismiss.
- [ ] Per-action shortcut shown next to the action label where applicable.

## Accessibility

- [ ] Uses the right semantic element (`<button>` for action, `<a>` for nav, `<input type="checkbox">` for toggle, etc.).
- [ ] Icon-only buttons have an `aria-label`.
- [ ] Form fields have an associated `<label>`.
- [ ] Error messages associated via `aria-describedby`.
- [ ] Required fields have `required` / `aria-required`; optional ones marked `(optional)`.
- [ ] Async feedback uses `aria-live` regions (toast: polite; error: assertive).
- [ ] Colour is paired with a second signal (icon, text, or pattern).
- [ ] Contrast ≥ 4.5:1 for body, ≥ 3:1 for UI components / large text.
- [ ] Hit target ≥ 44×44 px on touch.

## Dark mode

- [ ] Tested in both light and dark themes.
- [ ] Borders and accents adjusted for dark, not just inverted.
- [ ] Shadows reduced in dark mode (border carries the weight).
- [ ] Custom illustrations / icons render correctly on both themes.

## Data realism

- [ ] Tested with **empty** data.
- [ ] Tested with **one** item.
- [ ] Tested with **many** items (long list, long table, long names).
- [ ] Tested with **really long strings** that overflow (truncate or wrap intentionally).
- [ ] Tested with **really small numbers and really large numbers** (tabular nums; alignment).
- [ ] Tested with **non-ASCII** content (accents, RTL, emoji, CJK).
- [ ] Tested with **failed sub-resources** (partial state).

## Responsive

- [ ] Works at 320px wide (smallest supported mobile).
- [ ] Works at 768px (tablet).
- [ ] Works at 1280px and up (desktop default).
- [ ] Works at 200% zoom on a 1280px viewport (a11y).
- [ ] No horizontal scroll except inside scroll-intended containers (tables, code).

## Performance

- [ ] No unnecessary re-renders (verified with React DevTools profiler, if React).
- [ ] No large client-side libraries imported for tiny UI work (don't import all of lodash for one `debounce`).
- [ ] Images are sized, lazy-loaded, and use modern formats where applicable.
- [ ] Animations use `transform` / `opacity`, not layout-triggering properties.

## Stories & tests

- [ ] Story / preview covers default + each state.
- [ ] Unit test covers the public behaviour (interactions, callbacks).
- [ ] A11y test (`axe`, `jest-axe`) covers the default render.

## Tokens / system hygiene

- [ ] No new design token introduced silently — added to `tokens.css` with a name that matches the system.
- [ ] No raw value inline that should be a token.
- [ ] Class names don't reference colours that should be semantic (`bg-blue-500` → `bg-accent`).

## Final eye-test

- [ ] Looks like it belongs in the app (not pasted from a different design system).
- [ ] You'd be comfortable showing this in a portfolio.
- [ ] You'd be comfortable using this fifty times a day.
