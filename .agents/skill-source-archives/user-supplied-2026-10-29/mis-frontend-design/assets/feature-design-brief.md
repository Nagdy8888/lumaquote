# Feature design brief — `<feature name>`

Filled out **before** any composition. Reviewed with one other designer / engineer before pixels.

---

## 1. Who, and how often

- **Primary user(s):** <role / persona>
- **Frequency of use:** <multiple times per day | daily | weekly | monthly | rare>
- **Devices:** <desktop primary | tablet | mobile primary>
- **Skill level:** <power user | comfortable | first-timer>

**Implications:**

- High-frequency surfaces optimise for speed and density.
- Low-frequency surfaces optimise for legibility and discoverability.
- Power users get keyboard shortcuts; first-timers get inline hints.

## 2. Job-to-be-done

> One sentence. If you can't write it, the feature isn't ready to design.

`<role> wants to <action> so that <outcome>.`

Example: *Account managers want to renew an expiring contract so that the customer doesn't churn.*

## 3. What the user is holding in their head when they arrive

What context, question, or worry brought them to this surface?

- …
- …

**The screen must address these without the user asking.**

## 4. The smallest successful interaction

The single path the screen should make trivial. Everything else is secondary.

Example: *Find the contract that expires next, see the renewal terms, click "Send renewal email."*

## 5. State matrix

Enumerate now. (See `references/STATES_AND_FEEDBACK.md`.)

- [ ] **Empty (first run)** — user has never had data here: <design / copy>
- [ ] **Empty (cleared)** — filters return nothing: <design / copy>
- [ ] **Loading (initial)** — <skeleton matching layout / spinner?>
- [ ] **Loading (incremental)** — <pagination / load-more behaviour>
- [ ] **Partial** — some sub-resources failed: <inline indicators?>
- [ ] **Optimistic** — UI updates before server confirms: <which actions?>
- [ ] **Error (recoverable)** — request failed: <retry affordance / copy>
- [ ] **Error (auth / permission)** — <where the user lands>
- [ ] **Error (validation)** — <inline pattern>
- [ ] **Success** — <inline ✓ / toast / modal — which?>
- [ ] **Disabled** — <why and how communicated>
- [ ] **Read-only** — <when this state applies>

## 6. Keyboard-only path

The full primary task, completed from the keyboard.

| Step | Keystroke | Result |
|------|-----------|--------|
| 1    | ⌘K        | open command palette |
| 2    | type "contract"  | filter to contract entries |
| 3    | Enter     | navigate to contracts list |
| 4    | j / k     | move row selection |
| 5    | Enter     | open contract detail drawer |
| 6    | r         | send renewal (with confirm) |
| 7    | y         | confirm |

## 7. Information architecture

- **Where does this live in the nav?** <primary / secondary / palette-only>
- **What does the URL look like?** `/contracts?status=expiring&selected=acme`
- **What's URL-addressable?** (filter, sort, pagination, selected item, density, tab)
- **What's shareable?** A teammate opens the link and lands on the same view.

## 8. Data realism

What does this look like with:

- 0 items?
- 1 item?
- 100 items?
- Long names / long descriptions?
- Multi-byte / RTL content?
- Failed sub-resources?

Sketch each (rough is fine).

## 9. Density and breakpoints

- **Comfortable density:** row height, field spacing.
- **Compact density** (if applicable): row height, field spacing.
- **Mobile (320–767):** what changes? (Stack columns? Hide secondary actions?)
- **Tablet (768–1279):** what changes?
- **Desktop (1280+):** the default.

## 10. Motion plan

- **Opening / closing this surface:** <which primitive — drawer / dialog / page transition>
- **In-place state changes:** <what fades, what slides, what stays still>
- **Reduced motion:** replace with <instant state change>

## 11. Accessibility commitments

- [ ] Tab order matches visual order.
- [ ] Primary task completable from keyboard.
- [ ] Esc closes the topmost overlay.
- [ ] Errors associated with their field (`aria-describedby`).
- [ ] Live region for async feedback.
- [ ] Color paired with a second signal.
- [ ] Contrast ≥ 4.5:1 / ≥ 3:1 verified.
- [ ] axe-clean on the default render.

## 12. Brand moment, if any

Most feature surfaces have none. **The first-run empty state** is usually the one place expressive design lives. Note here if this feature has one and what it does.

- **Where:** <e.g. empty-state illustration on first run>
- **What it does:** <one sentence>

## 13. Out of scope

What this feature deliberately doesn't do. Future tickets may pick these up.

- …
- …

## 14. Open questions for the team

- …
- …

## 15. Inspiration / references

Links to specific surfaces in other apps that solve a similar problem.

- <app> — <surface> — <what to borrow>
- <app> — <surface> — <what to borrow>

---

**Reviewed by:** <name> on <date>
**Decision:** ready to compose / needs another pass / shelved
