# RFCs — Request for Comments

An **RFC** captures a decision *in flight*. It's the doc the team uses to debate a non-trivial change before it commits to one. When the RFC is **accepted**, the team writes an ADR (or several) that captures what was decided.

| Doc | Captures | State                                |
|-----|----------|--------------------------------------|
| RFC | A proposal **before** consensus | draft / review / accepted / rejected |
| ADR | A decision **after** consensus  | proposed / accepted / superseded     |

If the call is uncontested, skip the RFC and write the ADR. RFCs exist for the cases where you want feedback first.

## When to write an RFC

Write one when **any** of these are true:

- The change spans multiple services or teams.
- Credible alternatives exist and the team isn't already aligned.
- The blast radius is large enough that you want explicit sign-off, not implicit "no one objected in standup".
- You expect substantial pushback or want to head it off in writing.
- The decision constrains future work for months.

Don't write one for:

- Decisions one engineer can make in their own area.
- Reversible-in-an-afternoon changes.
- Pure style choices.

## File layout

```
docs/planning/rfcs/
├── README.md                       # index
├── 0001-event-bus-redesign.md
├── 0002-jwt-refresh-rotation.md
└── ...
```

- **Filename:** `<NNNN>-<short-kebab-name>.md`. Numbering separate from ADRs (RFC-0001 and ADR-0001 are unrelated).
- **One proposal per RFC.** Split if it's really two changes.

## Required sections

Template: `assets/template-rfc.md`. Sections, in order:

1. **Title** — `RFC-NNNN: <proposal>`
2. **Status** — see lifecycle below
3. **Authors** — who is driving this
4. **Date** — last-updated date
5. **Summary** — one paragraph: what and why
6. **Motivation** — the problem and why now
7. **Detailed design** — the proposal at full depth
8. **Drawbacks** — what we lose by adopting this
9. **Alternatives** — what else was considered, with honest comparison
10. **Open questions** — what is *not* yet resolved
11. **Rollout plan** — how we'd ship it (phases, feature flags, migrations, rollback)
12. **Links** — related ADRs, RFCs, issues

## Status lifecycle

```
   draft  ───►  review  ──┬─►  accepted  ──►  ADR-MMMM (decisions extracted)
                          ├─►  rejected
                          └─►  withdrawn
```

| Status      | Meaning                                                                            |
|-------------|------------------------------------------------------------------------------------|
| `draft`     | The author is still writing. Don't review yet.                                      |
| `review`    | Open for comments. Authors set a review-end date.                                    |
| `accepted`  | Consensus reached. ADR(s) being written. Implementation can begin.                   |
| `rejected`  | The team explicitly decided not to do this. RFC stays as the record of why.          |
| `withdrawn` | The author pulled the RFC (changed mind, no longer relevant). Stays for history.     |

Rules:

- **`accepted` is followed by an ADR** that captures the specific decisions. The RFC stays as the deliberation record; the ADR is the canonical decision.
- **Rejected and withdrawn RFCs are kept**, not deleted. They document the option-space that was explored.
- **Status changes are dated.** Add a `History:` block at the bottom if statuses change multiple times.

## Writing rules

- **Summary is a paragraph, not a sentence.** It should stand alone — a reader who opens only the Summary should know what the proposal is and roughly why.
- **Motivation is the *problem*, not the solution.** Half of RFCs fail in review because the motivation is "we should do X" rather than "we have problem Y".
- **Detailed design includes the boring parts** — data shapes, migration plan, error semantics, observability changes.
- **Drawbacks is mandatory and honest.** An RFC with no drawbacks listed will get drawback-only reviews.
- **Open questions invite review.** Phrase them as questions, not as "TBD".

## Review process

1. Author moves the RFC from `draft` → `review` and sets a **review end date** (usually 1–2 weeks out).
2. Reviewers add inline comments on the doc.
3. Author addresses comments — either fold the resolution into the RFC body or respond inline.
4. On the review-end date, the author requests a decision. **One named decider** marks `accepted` / `rejected`. Bikeshedding past the deadline becomes a follow-up RFC.
5. If accepted: spawn ADR(s) referencing this RFC and start implementation.
6. If rejected: update the RFC with the reason and the dissenting opinions, then leave it.

## Example skeleton (truncated)

```markdown
# RFC-0004: Move from Postgres LISTEN/NOTIFY to a real event bus

- **Status:** review
- **Authors:** @alice
- **Date:** 2026-04-01
- **Review end:** 2026-04-12

## Summary
We are outgrowing Postgres LISTEN/NOTIFY as our cross-service event
transport. This RFC proposes Redis Streams as the replacement.

## Motivation
The fulfilment service has seen three production incidents this quarter
where missed NOTIFY events caused order drops...

## Detailed design
...

## Drawbacks
- New operational dependency (we already operate Redis, but as a cache,
  not as a system of record for events).
- Per-stream ordering is weaker than Kafka's partition ordering, but
  matches our per-order ordering requirement.

## Alternatives
- **Kafka (MSK):** ...
- **SQS FIFO:** ...
- **Keep LISTEN/NOTIFY + add a retry table:** ...

## Open questions
- Do we want consumer-group semantics or fan-out?
- What's the retention policy?

## Rollout plan
1. Phase 1 (week 1-2): ship the new bus behind a flag, dual-write.
2. Phase 2 (week 3): cut over reads, leave dual-write running.
3. Phase 3 (week 4): turn off LISTEN/NOTIFY.

## Links
- Will produce: ADR-0002
- Related: ADR-0001 (Postgres choice)
```

## RFCs and ADRs together

```
                       ┌──────────────┐
                       │  RFC drafted │
                       └──────┬───────┘
                              │
                              ▼
                       ┌──────────────┐
                       │   review     │
                       └──────┬───────┘
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
           accepted        rejected      withdrawn
                │
                ▼
          ┌──────────────┐
          │  ADR(s)      │  ← canonical record of what was decided
          │  written     │
          └──────────────┘
```

The ADR's `Links` section points back at the RFC. Anyone reading the ADR who wants the full deliberation reads the RFC.

## Anti-patterns

- Long-lived `review` status. If an RFC hasn't been decided in 2 weeks, force a decision or withdraw it.
- An RFC that proposes implementing a decision that's already been made elsewhere. That's not an RFC, that's a plan — use a regular PR description.
- "We'll figure that out later" sprinkled through Detailed Design. Mark it in Open Questions instead.
- RFCs deleted after rejection. Keep them; the option-space matters.
- Implementation PRs opened against `draft` RFCs. Wait for `accepted`.
- One mega-RFC for an unrelated cluster of changes. Split into separately-decidable RFCs.
