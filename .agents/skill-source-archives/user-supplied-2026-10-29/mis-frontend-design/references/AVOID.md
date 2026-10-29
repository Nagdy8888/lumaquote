# Anti-patterns — refuse on sight

Each item here has a reason. Read the reason; don't just memorise the list.

## Aesthetic anti-patterns

### Inter as the entire type system

**Why it's banned as the brand voice:** Inter is the unmarked, default choice for nine in ten new web apps. The result is that every new web app reads as "designed in 2022 by someone who picked the most-recommended free font." It signals lack of intention even when the rest of the design is good.

**What to do instead:** Use a neutral grotesque with character (Söhne, ABC Diatype, Geist, Switzer) as the utility face. Inter is acceptable *only* paired with a strong display face, and never as the sole typeface.

### Purple-to-pink gradient on white

**Why it's banned:** It's the visual signature of mid-2020s AI-generated UI. The combination is so overused that it actively reads as "auto-generated."

**What to do instead:** Pick one accent off the obvious centre of its hue (teal-leaning blue, violet-leaning indigo, green-leaning lime). Apply it sparingly. Gradients are fine when the colour relationship is intentional and used in moderation.

### `font-family: system-ui`

**Why it's banned:** "Looks native on every OS" is not a feature in a web app. It's a missed opportunity to have a typographic identity. Apps that look the same on every OS look like nothing.

**What to do instead:** Self-host a font, or use a font CDN (Google Fonts, Fontshare, Use-Type). Match the font choice to the brand.

### Identical card layout on every screen

**Why it's banned:** Cards are a heuristic, not a design system. When every screen is "rounded white surface with shadow and 24px padding," the app has no information hierarchy.

**What to do instead:** Default to flat surfaces separated by hairlines + space. Use cards where the content is a discrete repeatable unit the user picks among.

### Drop shadows as the primary depth signal

**Why it's banned:** Stacks of soft drop shadows pretending to be material elevation read as 2018-Google-Material. They also crush down badly in dark mode.

**What to do instead:** Combine a subtle 1-layer shadow with a 1px hairline border. The border does most of the elevation work; the shadow is a hint.

### Scattered scroll-triggered animations

**Why it's banned on app surfaces:** The user scrolls a list fifty times a day. Each scroll spawning fade-in animations is hostile after the third time. Decorative motion belongs on landing pages, not app surfaces.

**What to do instead:** Motion explains cause-and-effect (drawer opening, row updating, toast appearing). No motion when the user is grazing.

### Bouncing / springy micro-interactions everywhere

**Why it's banned:** Springs are delightful once and grating forever. They also add a "toy" feel to apps that should feel like instruments.

**What to do instead:** `ease-out` for appearing, `ease-in` for leaving, ~180ms. Use springs only on demonstrably delightful, infrequent interactions (the first time a checklist completes, an empty state illustration).

### Five+ category colors with no system

**Why it's banned:** A rainbow palette across the app means no design language. It reads as "the designer was given seven brand colours and used all of them."

**What to do instead:** One neutral curve + one accent + status colours (danger/warning/success) used on foreground/icons only. Tag colours are fine as user data; ambient identity colours are not.

### Marketing-style heroes inside the app

**Why it's banned:** Big italic display headlines, generous negative space, scroll-triggered reveals — these are landing-page moves. Inside the app they signal "I haven't designed the actual feature yet."

**What to do instead:** Onboarding screens, empty states, and major announcements (changelog) are the only places brand-grade typography lives inside an app.

## Interaction anti-patterns

### Spinner as the only loading state

**Why it's banned:** A centred spinner gives the user nothing about what's loading or how big the result will be. The page jumps when data arrives.

**What to do instead:** Skeleton matching the final layout for anything > 1s. Inline spinner for in-progress button actions < 1s.

### Disabled submit button until form valid

**Why it's banned:** The user doesn't know what's wrong, so they tab through every field looking for what they missed.

**What to do instead:** Submit-attempt validates all, focuses first invalid, shows inline errors. Use disabled state only when the form is genuinely not actionable yet (no fields filled at all).

### Placeholder as label

**Why it's banned:** Placeholder disappears once typed. The user loses context. Screen readers don't read it consistently.

**What to do instead:** Real `<label>` above the input. Placeholder is for an *example value*, not the field name.

### "Something went wrong"

**Why it's banned:** Useless to the user. Signals "we don't know what happened either."

**What to do instead:** Be specific (which operation, which condition). Be actionable (next step). Include a reference ID for support.

### Color as the only signal

**Why it's banned:** ~5% of users are colour-blind. Plus, in screenshots, prints, and lower-end displays, colour distinctions disappear.

**What to do instead:** Pair colour with icons, text labels, or pattern. Status pills, validation, charts — always two signals.

### Modals that confirm low-stakes actions

**Why it's banned:** Modal == "stop and look." Saving a small edit is not a stop-and-look event.

**What to do instead:** Optimistic UI + inline confirmation + undo toast. Reserve modals for high-attention work and irreversible operations.

### Hover-only affordances

**Why it's banned:** Touch users can't hover. Keyboard users see them inconsistently. Tooltips that are the *only* place a label lives are unreachable on touch.

**What to do instead:** Affordances are visible at rest, perhaps with a subtle hover/focus enhancement.

### Toasts as the only confirmation

**Why it's banned:** Toasts auto-dismiss; a user who looks away misses the confirmation.

**What to do instead:** Pair toasts with in-place changes whenever possible. If the change is already visible on screen, the change *is* the confirmation.

### Tooltips for primary information

**Why it's banned:** Tooltips require hover/focus. Primary information shouldn't require a gesture to reveal.

**What to do instead:** Tooltips for hints, abbreviations, and supporting context only. Primary information is visible.

### Confirmation by reload

**Why it's banned:** Full-page reload after a small action is jarring and slow. It also loses scroll position and breaks optimistic UI.

**What to do instead:** Update the affected item in place; re-fetch only the relevant slice if needed.

### Browser-default validation tooltips

**Why it's banned:** They look generic, disappear on click, and don't match the app's style.

**What to do instead:** `noValidate` on the form, custom inline errors styled in the design system.

## Structural anti-patterns

### Nested tabs

**Why it's banned:** Tabs within tabs confuse the user about where they are in the hierarchy.

**What to do instead:** Split into separate pages. If the content really is one level deep, use a single tab row. If it's two levels, use a left-side nav.

### Settings spread across nested modal stacks

**Why it's banned:** Each modal pushes the user further from context. Closing one closes the trail.

**What to do instead:** Settings as a single page with sectioned single-column layout and sticky in-page nav.

### Sidebar with 12+ items

**Why it's banned:** The user can't scan a list of twelve. They start using browser-find.

**What to do instead:** Group into < 7 primary items, push the rest into the command palette.

### Charts without their state matrix

**Why it's banned:** "Loading…", "No data", and "Error fetching" are not implemented; the user sees an empty chart frame.

**What to do instead:** Charts get the same state matrix as any other surface: empty / loading / partial / error / success.

### Tables without sort, filter, or URL state

**Why it's banned:** Users can't return to "the view I had open" — including via back button or share link.

**What to do instead:** Sort, filter, page, and density in the URL. Sharable views are a feature, not a luxury.

### Hidden bulk actions

**Why it's banned:** Power users can't find them; new users don't know they exist.

**What to do instead:** Selection bar at the top of the table, summarising the count and the actions.

## Implementation anti-patterns

### Raw hex / px values in components

**Why it's banned:** Tokens are the design system's source of truth. Hardcoded values cause theme drift and dark-mode bugs.

**What to do instead:** Every colour, radius, spacing, duration references a token. Add a token before using a new value.

### Inline `style={{ … }}` for design properties

**Why it's banned:** Bypasses the token system; impossible to theme; hard to audit.

**What to do instead:** Tailwind classes, CSS Modules, or styled components that reference tokens.

### `tabindex` greater than 0

**Why it's banned:** Reorders tab flow in a way that surprises everyone, including the author six months later.

**What to do instead:** Tab order = DOM order. If you need a different order, restructure the DOM.

### `outline: none` without a replacement

**Why it's banned:** Removes the keyboard user's only signal of where they are.

**What to do instead:** Custom `:focus-visible` ring using the accent colour.

### Hand-rolled focus management

**Why it's banned:** Modal focus traps, popover focus restore, and list keyboard navigation are easy to get 80% right and impossible to get 100% right by hand. The remaining 20% breaks for screen-reader users.

**What to do instead:** Use Radix UI, React Aria, or Headless UI for any widget with non-trivial focus behaviour.

## A meta anti-pattern

### Optimising the happy path before the non-happy paths

**Why it's banned:** The happy path is 5% of the user's time in the app. The other 95% is loading, empty, error, partial, optimistic, success. An app polished on the happy path and ignored elsewhere feels broken.

**What to do instead:** Enumerate states first ([STATES_AND_FEEDBACK.md](STATES_AND_FEEDBACK.md)), design them, then compose the happy path out of the same primitives.
