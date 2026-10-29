# Plan NNN: <short title>

- **Status:** active | shipped | archived
- **Owner:** @name (and team)
- **Date:** YYYY-MM-DD (created)
- **Target ship:** YYYY-MM-DD
- **From:** ADR-MMMM (or RFC-LLLL — link back to the decision this plan executes)

## Goal

<One paragraph: what does success look like? Concrete and measurable.>

## Non-goals

<What we are explicitly NOT doing in this plan. Useful to head off scope creep.>

-
-

## Phases

### Phase 1 — <name> (week N)

- [ ] Task 1 (@owner) — <Linear link>
- [ ] Task 2 (@owner)
- [ ] Task 3 (@owner)

**Exit criteria:** <How we know phase 1 is done. Measurable.>

### Phase 2 — <name> (week N+1)

- [ ] Task 4 (@owner)
- [ ] Task 5 (@owner)

**Exit criteria:** <…>

### Phase 3 — <name> (week N+2)

- [ ] Task 6 (@owner)

**Exit criteria:** <…>

## Dependencies

- <Other plans / RFCs / services this depends on. Name the owner.>
-

## Risks

| Risk                            | Likelihood | Impact | Mitigation                              |
|---------------------------------|------------|--------|-----------------------------------------|
| <e.g. migration window slipping>| medium     | high   | <e.g. feature-flag the new path>        |
|                                 |            |        |                                          |

## Rollout

<How we ship: feature flags, canary, dual-write, etc.>

## Verification

<How we know it actually worked in production. Dashboards, queries, success
criteria.>

## Rollback plan

<Exact steps to undo this if it goes wrong. Triggers that would prompt a
rollback.>

## Links

- Decision: ADR-MMMM / RFC-LLLL
- Tracker: <Linear / Jira link>
- Slack channel: `#<channel>`
- Related plans: <…>

## Updates

| Date       | Update                                                  |
|------------|---------------------------------------------------------|
| YYYY-MM-DD | Plan created                                             |
| YYYY-MM-DD | Phase 1 complete                                         |
