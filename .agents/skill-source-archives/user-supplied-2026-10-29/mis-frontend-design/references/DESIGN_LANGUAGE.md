# Design language — typography, color, motion, spacing

The MIS app design language is **calm, modern, opinionated**. Restrained on repeat-use surfaces, expressive at brand moments. References: Linear, Notion, Vercel dashboard, Raycast, Stripe dashboard, Arc, Cron / Notion Calendar.

## Typography

### Two tiers + mono

Pick one per tier; max three families total across the app.

| Tier        | Used for                                   | Picks                                                                |
|-------------|--------------------------------------------|----------------------------------------------------------------------|
| **Utility** | UI labels, body, tables, forms (~95% of surfaces) | Söhne, ABC Diatype, Geist Sans, Switzer, General Sans, IBM Plex Sans, Aeonik. **Not Inter**, **not Roboto**, **not system-ui**. |
| **Display** | Hero, onboarding, empty-state titles, brand moments | GT Sectra, PP Editorial New, Tiempos, ABC Marfa, Söhne Breit, Migra, GT Super, JetBrains Mono Display (for tech-toned brands). |
| **Mono**    | Code, ids, numerical data, command palette | Berkeley Mono, JetBrains Mono, Geist Mono, Commit Mono, IBM Plex Mono, ABC Diatype Mono. |

### Pairing rules

- **Neutral utility + characterful display.** Söhne + GT Sectra. ABC Diatype + PP Editorial New. Geist + Migra.
- **Don't pair two display faces.** Display is a guest, not the show.
- **Mono is functional.** Numbers in tables, ids, code, kbd shortcuts. Never as the brand voice.

### Weights

- Two weights per family minimum, three max.
- Utility: **regular 400 / medium 500 / semibold 600**. Skip 700+ unless the brand calls for it.
- Display: usually one weight is enough — display does work through scale, not weight.

### Size scale

Five sizes max; use the scale, never an off-grid pixel value.

```
12  — micro: meta, kbd, table cell numbers
14  — body / UI default
16  — emphasis / section heading inline
20  — h3 / card heading
28  — h2 / page heading
44  — h1 / brand moment (display face)
```

(For brand-moment surfaces, extend to 56 / 72 — but only on those surfaces.)

### Line height

| Context                  | Line-height |
|--------------------------|-------------|
| Body / paragraphs         | 1.5         |
| UI labels / dense tables  | 1.3         |
| Headings                  | 1.15 – 1.2  |
| Numerical tables          | 1.0 with `font-variant-numeric: tabular-nums` |

### Letter spacing

- Body: 0.
- All-caps labels: `0.04em – 0.08em`.
- Display: slight negative (`-0.01em` to `-0.03em`) for confident headlines.
- **Never** apply `letter-spacing` to running body text "for style" — it slows reading.

### Numerals

Tabular numerals for any table column, KPI tile, timestamp, money, percentage:

```css
.numeric { font-variant-numeric: tabular-nums lining-nums; }
```

## Color

### Palette posture

- **One neutral curve** (8–10 stops) defines surfaces, borders, foreground, muted text.
- **One accent**, used sparingly. Accent = primary action + brand moments. Not "the link color." Not every button.
- **Status colors** (danger, warning, success, info) used on **foreground / icons**, not as solid surface fills — except in toasts and banners.
- **Two hues max** in the identity (neutral + accent). A third hue is a signal something is wrong.

### Semantic tokens

Tokens carry *meaning*, not values. Components reference `--color-fg-muted`, never `#71717a`.

```
--color-bg                  base canvas
--color-surface-1           card / sheet
--color-surface-2           elevated sheet (popover, dropdown)
--color-fg                  primary text
--color-fg-muted            secondary text
--color-fg-subtle           tertiary / placeholder
--color-border              hairlines
--color-border-strong       dividers in dense UI
--color-accent              primary action / brand
--color-accent-fg           text on accent
--color-accent-soft         tinted background (e.g. selected row)
--color-danger / -fg / -soft
--color-warning / -fg / -soft
--color-success / -fg / -soft
--color-info / -fg / -soft
```

### Dark mode as a peer theme

Dark mode is not `filter: invert()`.

- **Recompute the neutral curve** for dark — usually slightly desaturated and shifted cool.
- **Surfaces lighten with elevation**, not darken — `surface-2` is brighter than `surface-1`.
- **Borders are lighter** in dark mode than the strict inverse would suggest (relative contrast holds).
- **Accent often shifts** — a lighter / desaturated variant on dark.

### Picking the accent

- **Saturated > pastel.** Pastels read as generic SaaS.
- **One step off the "obvious" hue.** Not pure blue (#3b82f6) — try a teal-leaning blue, a violet-leaning indigo, a green-leaning lime. The shift is what reads as designed.
- **Test on accent-on-light AND accent-on-dark, foreground AND background.** Half of accent failures are contrast on one of the four.

### Banned posture

- Purple gradient on white. Stop.
- Five "category colors" with no system. Tag colors are fine; ambient identity colors are not.
- Tailwind `bg-blue-500 / bg-green-500 / bg-red-500` straight from defaults. Use the named tokens and a custom curve.
- Drop-shadow stacks pretending to be elevation. One subtle shadow + a border is more refined.

## Motion

### Purpose, not decoration

Every animation answers one of:

1. **Where did it come from / go to?** (sheet slides, drawer reveals).
2. **What just happened?** (success check, error shake, undo countdown).
3. **What is happening right now?** (pending row, progress, skeleton shimmer).

If a motion doesn't answer one of these, delete it.

### Durations + easing

```
--dur-1: 120ms   /* micro: hover, focus, color shift */
--dur-2: 180ms   /* standard: drawer, popover, dropdown, toast */
--dur-3: 260ms   /* deliberate: page transition, layout shift */
--ease-out:  cubic-bezier(0.2, 0.8, 0.2, 1)   /* appearing */
--ease-in:   cubic-bezier(0.4, 0, 1, 1)        /* leaving */
--ease-soft: cubic-bezier(0.4, 0.0, 0.2, 1)    /* swap-in-place */
```

- **Appearing** uses `ease-out` (snap forward, settle).
- **Leaving** uses `ease-in` (start gentle, accelerate away).
- A symmetric ease for both reads amateurish.

### Framer Motion patterns (React)

```tsx
import { motion, AnimatePresence } from "framer-motion"

<AnimatePresence>
  {isOpen && (
    <motion.div
      initial={{ x: "100%", opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: "100%", opacity: 0 }}
      transition={{ duration: 0.18, ease: [0.2, 0.8, 0.2, 1] }}
    />
  )}
</AnimatePresence>
```

For lists, use `layout` for cheap, correct reordering animations rather than hand-rolled keyframes.

### Reduced motion

`prefers-reduced-motion: reduce` is not negotiable. Replace motion with instant state changes — **don't just shorten durations**.

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    transition-duration: 0.001ms !important;
  }
}
```

## Spacing

### One scale, four-base

```
--space-1:  4px
--space-2:  8px
--space-3: 12px
--space-4: 16px
--space-5: 24px
--space-6: 32px
--space-7: 48px
--space-8: 64px
```

Use the scale. Never `7px`. Never inline `padding: 13px`.

### Density modes

App tables and feature surfaces should support two density modes:

- **Comfortable** (default): row height ~44px, generous form spacing.
- **Compact**: row height ~32px, tighter forms. For power users.

Switching is a single token swap (`--row-height`, `--field-gap`), not a per-component prop.

## Radius and shadow

Radius scale, three steps:

```
--radius-1:  6px   /* inputs, chips, small buttons */
--radius-2: 10px   /* cards, popovers, modals */
--radius-3: 14px   /* sheets, large media */
```

Shadows are **two-layer at most**:

```
--shadow-1: 0 1px 2px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.04);
--shadow-2: 0 4px 12px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.05);
--shadow-3: 0 16px 32px rgba(0,0,0,0.10), 0 0 0 1px rgba(0,0,0,0.05);
```

Border + subtle shadow > heavy multi-layer drop shadow. Always.

## Iconography

- **One icon library per app.** Lucide is the safe default; Phosphor or Radix Icons when the brand calls for a different weight.
- **Single stroke weight.** Don't mix 1px / 1.5px / 2px icon sets.
- **Sizes follow type scale**: 14 / 16 / 20 / 24. Never `15px`.
- **Color matches the adjacent text** — icons inherit `currentColor`. Custom icon colors are rare and intentional.

## Charts and data viz

- **Use one chart family** (Recharts, Tremor, or a hand-rolled D3 wrapper).
- **One accent for the primary series**, neutrals for secondary / context.
- **Tabular numerals in tooltips and axes.**
- **No gridlines on both axes.** Pick one direction.
- **Empty / loading / error states** for charts, same as any data surface.

## Putting it together — a starter palette

```css
:root {
  /* Neutral curve (zinc-leaning, slightly warm) */
  --neutral-50:  #fafafa;
  --neutral-100: #f4f4f5;
  --neutral-200: #e4e4e7;
  --neutral-300: #d4d4d8;
  --neutral-500: #71717a;
  --neutral-700: #3f3f46;
  --neutral-900: #18181b;

  /* Semantic */
  --color-bg:           var(--neutral-50);
  --color-surface-1:    #ffffff;
  --color-surface-2:    #ffffff;
  --color-fg:           var(--neutral-900);
  --color-fg-muted:     var(--neutral-500);
  --color-border:       var(--neutral-200);

  /* Accent — teal-leaning blue */
  --color-accent:       #0a7ea4;
  --color-accent-fg:    #ffffff;
  --color-accent-soft:  rgba(10, 126, 164, 0.10);
}

[data-theme="dark"] {
  --color-bg:        #0a0a0b;
  --color-surface-1: #131316;
  --color-surface-2: #1c1c20;
  --color-fg:        #ededef;
  --color-fg-muted:  #9b9ba3;
  --color-border:    #26262b;
  --color-accent:    #38bdf8;
}
```

Use this as a starting point in `assets/tokens.css`, then **shift the accent and tune the neutral curve** per app — never ship the literal values above.
