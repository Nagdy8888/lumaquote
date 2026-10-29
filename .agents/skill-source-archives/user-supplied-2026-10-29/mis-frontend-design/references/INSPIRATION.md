# Inspiration — what to study, and what to take from each

Apps to study **as users**, not as decoration. Spend 30 minutes inside each before borrowing anything. The goal is to internalise what makes a calm, confident app feel that way — not to copy a screenshot.

## The shortlist

### Linear — `linear.app`

Take from it:

- **Keyboard-first interaction.** Every action has a shortcut. The shortcut is shown in the menu and in the command palette.
- **Calm dark theme as the default**, with a refined light theme as a peer.
- **Confident neutral curve.** Surfaces lighten with elevation; borders are hairlines.
- **Cmd-K is the navigation.** The sidebar is just a hint; the palette is the way.
- **Inline editing is the norm**, not modals. A modal in Linear means "this is the rare big thing."
- **Optimistic UI everywhere.** Click feels instant.

Don't take: their exact accent (do your own colour work).

### Notion — `notion.so`

Take from it:

- **Content-first composition.** The interface is the document; chrome shrinks to give the content room.
- **Slash commands** for in-context creation.
- **Subtle, restrained motion.** Drawers and popovers fade-and-shift in `~180ms`; nothing bounces.
- **Tables and databases** with multiple density modes and column controls.
- **Empty states with personality** — illustrations and copy that feel like Notion.

Don't take: the over-nested workspace navigation pattern unless your data model truly needs it.

### Vercel dashboard — `vercel.com`

Take from it:

- **Monospace for ids, deploys, environment values.** It signals "this is data, copy it."
- **Tight grids on data surfaces**, generous breathing room on overview surfaces.
- **Inline timeline indicators** (deploy progress, status badges) — calm, never spammy.
- **Dark mode is the default and the dark mode is opinionated** — high-contrast, slight cool shift.

Don't take: the marketing-page-style hero on the in-app dashboards. Vercel keeps these on the docs / marketing site; the app stays dense.

### Raycast — `raycast.com`

Take from it:

- **Command palette as the entire app.** Worth studying even if you're not building a launcher — the patterns (groups, recents, per-item actions, contextual extensions) transfer.
- **Keyboard-first list interactions** (j/k, Enter, Cmd+K for actions on the focused item).
- **Per-item keyboard hints** rendered on the right of every list row.

Don't take: the macOS-native feel (overdone outside the launcher context).

### Stripe Dashboard — `dashboard.stripe.com`

Take from it:

- **Gold standard for data-heavy app UI.** Tables, filters, drill-downs, dual-axis charts.
- **Sticky filter bars** at the top of long lists.
- **Side-panel drawers** for row detail with URL state and pinning.
- **Inline state indicators** (succeeded, pending, refunded) using foreground colour + icon, never full-row tint.
- **Money formatted everywhere with tabular numerals.**

Don't take: the dense sidebar (Stripe earns it because every nav item is high-frequency).

### Arc Browser — `arc.net`

Take from it:

- **Brand moments inside a tool app.** The empty new-tab state, the first-run onboarding, the easel feature — Arc proves a tool can be expressive at the right moments without being expressive everywhere.
- **Sidebar that respects the user's mental model** (tabs as the primary structure).
- **Custom keyboard shortcuts** as a first-class feature (`Cmd-T` is configurable).

Don't take: the colour-everywhere palette (specific to Arc's identity; would feel costume-y in most apps).

### Cron / Notion Calendar — `calendar.notion.so`

Take from it:

- **Calm, dense data layout.** A week view shows a lot without feeling crowded.
- **Keyboard navigation** through events and dates.
- **Inline event creation** without modal interruption.
- **Quiet system updates** — no toast spam.

### Height — `height.app`

Take from it:

- **Aggressively dense lists with retained legibility.**
- **Status pills that work in both light and dark mode** without recolouring.
- **Bulk-action selection bar at the top of the list.**

### Superhuman — `superhuman.com`

Take from it:

- **Keyboard-only operability** of a complex CRUD app (email).
- **Speed as a feature** — every action under 100ms perceived; instant feedback then server reconciliation.
- **In-app shortcuts cheat sheet** as a first-class surface.

### Pitch — `pitch.com`

Take from it:

- **Calm dark theme** for content creation.
- **Subtle motion on drag, resize, and selection** that explains state without distracting.
- **Right-aligned side drawer** for properties and settings panels.

## How to study an app

1. **Use it for a real task** — don't just look at screenshots.
2. **Note the keyboard set** the app expects you to know.
3. **Trigger every state you can** — empty, loading, error, success, partial. Force errors by going offline.
4. **Tab through one full flow** — does focus management feel right?
5. **Open DevTools** and inspect the type scale, the spacing scale, the colour tokens. (You'll see CSS variables on every app worth studying.)
6. **Identify two things to borrow.** No more. Otherwise you're cosplaying.

## What to avoid as "inspiration"

- **Award-show landing pages** (Awwwards, FWA winners). Most are for marketing sites and use techniques that read as "trying too hard" in an app context.
- **Dribbble shots**. Designed without state matrices, without keyboard considerations, without data realism. Use them for colour ideas; do not use them as functional inspiration.
- **Other AI-generated UI**. The whole point of this skill is to escape it.
- **Material 3 / Carbon / Fluent as full systems.** Excellent for component reference, but applying them whole-cloth reads as "this is someone else's brand."

## Where to find original references

- The actual apps above. Use them.
- **Designer YouTube** for product breakdowns (e.g. interface walkthroughs of Linear, Stripe, Vercel).
- **Mobbin** (paid) for state-by-state captures of real app flows.
- **Refactoring UI** book — practical, principled, app-leaning.
- **Linear's design blog** + the Vercel team's blog for engineering-led design writing.

## What to read

- **Refactoring UI** — Adam Wathan + Steve Schoger.
- **Practical UI** — Adham Dannaway.
- **Inclusive Components** — Heydon Pickering (web a11y patterns).
- **Designing Web Interfaces** — Bill Scott + Theresa Neil (older, but the patterns are durable).
- **The Design of Everyday Things** — Don Norman (foundational; affordances, signifiers, feedback).
