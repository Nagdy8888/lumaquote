# Postmortems

Every **sev1** or **sev2** incident produces a postmortem within **5 working days**. Postmortems are how the team learns; skipping them means paying for the same incident twice.

## The blameless rule

Postmortems describe **systems** failing, not **people**.

- ❌ "Alice deployed the bad change at 14:02."
- ✅ "The deploy pipeline allowed a change without a passing test suite to reach production."

If a postmortem names a person as a cause, rewrite it. Naming individuals creates an incentive to hide future incidents, which is exactly the opposite of what postmortems exist for.

Specific replacements:

| Don't say                       | Say instead                                                |
|---------------------------------|------------------------------------------------------------|
| "X forgot to..."                | "The process did not require..."                            |
| "X misread the alert"           | "The alert was ambiguous because..."                        |
| "X didn't follow the runbook"   | "The runbook step Y was unclear, leading to..."             |
| "Engineer judgement error"      | "The information available to the engineer didn't include..." |

It's fine to **name systems, services, and tools**. The blameless rule is about *people*.

## File layout

```
docs/postmortems/
├── 2026-05-20-payment-outage.md
├── 2026-04-08-checkout-500s.md
└── ...
```

- **Filename:** `YYYY-MM-DD-<short-kebab-summary>.md`. Date = the day the incident started, not the day the postmortem was written.
- **One file per incident.** Don't bundle related incidents — each gets its own writeup, with cross-links.

## Required sections

Template: `assets/template-postmortem.md`. Sections, in order:

1. **Summary** — 3 sentences: what happened, impact, fixed by
2. **Status** — `draft | reviewed | published`
3. **Severity** — sev1 / sev2
4. **Impact** — duration, users affected, revenue / SLA impact, data loss?
5. **Timeline** — events in UTC: detection, triage, mitigation, resolution, comms
6. **Root cause(s)** — 5-whys or fault tree; multiple causes are normal
7. **Contributing factors** — things that made it worse but weren't the cause
8. **Detection** — how we found out + how long it took
9. **What went well** — keep the team honest about successes
10. **What went poorly** — system gaps
11. **Action items** — each has an owner, a due date, a tracker link
12. **Lessons learned** — captured for the next on-caller
13. **Links** — incident channel, related ADRs / RFCs / runbooks

## Timeline format

Every postmortem has a timeline in **UTC**. Format:

```
| Time (UTC) | Event                                                  |
|------------|--------------------------------------------------------|
| 14:02      | Deploy of `api@a1b2c3d` reaches production.            |
| 14:07      | `api-5xx-rate` alert fires (sev2 page).                |
| 14:08      | On-call acks page; opens `#incident-2026-05-20`.        |
| 14:14      | On-call identifies the bad deploy in `gh run list`.      |
| 14:16      | Rollback initiated.                                      |
| 14:21      | Error rate returns to baseline.                          |
| 14:25      | Incident channel marked resolved.                        |
| 14:40      | Status page incident closed.                             |
```

Rules:

- **UTC always.** Local time confuses readers in other timezones.
- **Granularity ≤ 5 min** during the active part of the incident.
- **Include comms milestones** (status page updates, customer notifications). They are part of the incident.

## Root cause analysis

Use **5-whys** for most incidents:

```
The API returned 5xx for 14 minutes.
  Why? The new deploy referenced a column that didn't exist.
    Why? A migration hadn't run yet.
      Why? Migrations and code deploys are separate pipelines.
        Why? They were split to support faster code rollouts.
          Why? We hadn't yet built a coupled-rollout mechanism.

Root cause: code deploys can reach production before their required
migrations have been applied.
```

Use a **fault tree** when multiple causes combined (a single 5-whys chain misrepresents what happened):

```
                       Outage
                          │
            ┌─────────────┼─────────────┐
            ▼                           ▼
  Bad code reached prod        Alert routing misconfigured
        │                                │
        ▼                                ▼
  Migration not applied         New oncall rotation not in PagerDuty
```

Most outages have **more than one cause.** A postmortem that finds a single root cause is usually under-reading the incident.

## Action items

Each action item has:

- **Owner** — a named individual (or team if cross-cutting)
- **Due date** — concrete, usually within 30 days
- **Tracker link** — Linear / Jira / GitHub issue
- **Priority** — P0 / P1 / P2

Example:

```markdown
## Action items
1. **[P0]** Block deploys when required migrations haven't run.
   Owner: @bob (Platform). Due: 2026-06-03. [MIS-412](https://linear.../MIS-412).
2. **[P1]** Add a runbook for "deploy/migration drift" alerts.
   Owner: @alice (Platform). Due: 2026-06-10. [MIS-413](https://linear.../MIS-413).
3. **[P2]** Add a postmortem-driven test asserting migration ordering.
   Owner: @bob (Platform). Due: 2026-06-24. [MIS-414](https://linear.../MIS-414).
```

Rules:

- **Every action item is tracked.** A postmortem that produces action items not in a tracker is theatre.
- **Action items have owners, not "the team".** "Platform" is a team; "Platform @ Bob is the owner" is an owner.
- **P0 / P1 items have due dates within 30 days.** If they can't be done in 30 days, they're not P0 / P1.

## Process

1. **During the incident**, someone takes raw notes in the incident channel. These notes are the seed of the timeline.
2. **Within 2 working days**, the incident commander drafts the postmortem (status `draft`).
3. **Within 5 working days**, the draft is reviewed:
   - On-call participants confirm the timeline.
   - The owner team reviews root causes and action items.
   - A facilitator (anyone outside the owner team) reads for blamelessness.
4. **After review**, status moves to `reviewed`, then `published`. Published postmortems are shared in `#engineering`.
5. **30 days after publishing**, the owner team confirms which action items shipped. Slipped items get re-prioritised, not silently dropped.

## Postmortems and other docs

- A postmortem **may produce an ADR** if the team decides on a structural change ("we will couple code and migration deploys").
- A postmortem **always updates the relevant runbook** if the runbook fell short.
- A postmortem **may produce an RFC** if a non-trivial design change is needed.
- A postmortem **may produce a how-to** if the gap was "no one knew how to do X under pressure".

## Anti-patterns

- Identifying a single root cause. Most outages have multiple causes.
- Action items as wishes ("be more careful with deploys"). Action items are things you can ship.
- Naming individuals as causes. Rewrite.
- Postmortems sitting at `draft` for weeks. Time-box the review.
- "Lessons learned: we learned not to do this again." Lessons are concrete: what specifically would you do differently?
- No comms milestones in the timeline. Comms are part of the incident.
- Skipping postmortems for sev2 "because the fix was obvious". The fix is rarely the most valuable artefact; the lessons are.
