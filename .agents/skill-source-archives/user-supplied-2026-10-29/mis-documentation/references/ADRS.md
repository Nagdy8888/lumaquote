# ADRs — Architecture Decision Records

An **ADR** captures a decision *after* it has been made, with enough context that a future engineer can understand why. ADRs are the canonical record of "why does the code look like this?"

MIS uses the [MADR](https://adr.github.io/madr/) (Markdown Any Decision Records) format — terse, Markdown, one file per decision.

## File layout

```
docs/decisions/
├── README.md                      # auto- or hand-maintained index
├── 0001-use-postgres.md
├── 0002-event-bus-on-redis-streams.md
├── 0003-jwt-with-refresh-tokens.md
├── 0004-deprecate-v1-api.md       # may say "supersedes 0001"
└── ...
```

Rules:

- **Filename:** `<NNNN>-<short-kebab-name>.md`. Four-digit zero-padded sequence.
- **Numbering is monotonic** and never reused. If you reserve 0007 and abandon it, leave the gap.
- **One decision per ADR.** Two tangled decisions → two ADRs that link each other.

## Required sections

Template: `assets/template-adr.md`. Sections, in order:

1. **Title** — `ADR-NNNN: <decision in imperative or noun form>`
2. **Status** — see lifecycle below
3. **Date** — accepted date (YYYY-MM-DD)
4. **Context** — what is the issue we're seeing that motivates this decision
5. **Decision** — what we are going to do
6. **Consequences** — what becomes easier, what becomes harder, neutral effects
7. **Alternatives considered** — what else we looked at and why we rejected it
8. **Links** — RFC that produced this ADR, related ADRs, affected code

## Status lifecycle

```
            proposed  ───►  accepted  ──┬─►  superseded by ADR-MMMM
                                        └─►  deprecated
```

Values:

| Status                      | Meaning                                                                 |
|-----------------------------|-------------------------------------------------------------------------|
| `proposed`                  | Under review. Don't act on it yet.                                       |
| `accepted`                  | The decision is in force. Code should reflect it.                        |
| `superseded by ADR-MMMM`    | Replaced by a newer decision. The new ADR's `Context` explains why.     |
| `deprecated`                | No longer applies but not replaced. The code should be migrating away.   |

Rules:

- **ADRs are immutable after `accepted`.** To change a decision, write a new ADR that supersedes the old one — don't edit the old.
- **Editing typos, broken links, or `Status` is fine.** Editing `Context` / `Decision` / `Consequences` is not.
- **When you supersede an ADR, edit the old one's `Status` to `superseded by ADR-MMMM`.** That's the *one* allowed edit to the old ADR's body.

## Writing rules

- **Context describes the world that motivated the decision** — constraints, forces, the problem. Not "here's what we did" (that's Decision).
- **Decision is the verb sentence:** "We will use Postgres." "We will adopt the C4 model."
- **Consequences are honest.** Include the bad ones. "We give up the operational simplicity of SQLite for dev parity."
- **Alternatives considered are real options**, not strawmen. If "Option B" never had a champion, leave it out.

## Example skeleton (truncated)

```markdown
# ADR-0002: Event bus on Redis Streams

- **Status:** accepted
- **Date:** 2026-04-12
- **Supersedes:** —
- **Superseded by:** —

## Context
We need an event bus between the order service and the fulfilment service.
Throughput is < 5k events/sec, ordering matters per-order, and we run a
single AWS region. The team has Redis operational expertise; Kafka would
be a new dependency.

## Decision
We will use Redis Streams as the event transport. Consumers use
consumer-group semantics for at-least-once delivery; deduplication
happens in the fulfilment service.

## Consequences
**Positive**
- Reuses our existing Redis cluster; no new operational surface.
- Per-stream ordering meets the per-order ordering requirement.

**Negative**
- Multi-region replication is harder than Kafka's. Acceptable while
  we run single-region.
- Long-term storage / replay is limited; we cap retention at 7 days.

**Neutral**
- Consumers need to implement idempotency; we'd have wanted that with
  Kafka too.

## Alternatives considered
- **Kafka (MSK):** Best fit at higher throughput, but ops cost is high
  for our current load. Re-evaluate at > 10k events/sec.
- **SQS:** Doesn't preserve per-key ordering without FIFO + dedup keys,
  which adds latency.

## Links
- Followed RFC-0004
- Affects services: order, fulfilment
- Related: ADR-0001 (Postgres choice)
```

## When to write an ADR

Write one when **any** of these are true:

- The decision constrains future code substantially (technology choice, schema, protocol).
- The decision would surprise a reader of the code six months later.
- The decision was contested and the team wants a record of why we landed where we landed.
- The decision affects a public contract (API, event schema, CLI).

Don't write one for:

- Pure stylistic preferences captured in lint rules.
- Single-file refactors.
- Anything reversible in an afternoon by one engineer.

## Discovery

The README in `docs/decisions/` is the index — one line per ADR with status + one-line summary:

```markdown
# ADR index

| #     | Title                                  | Status     |
|-------|----------------------------------------|------------|
| 0001  | Use Postgres                           | accepted   |
| 0002  | Event bus on Redis Streams             | accepted   |
| 0003  | JWT with refresh tokens                | accepted   |
| 0004  | Deprecate /v1 API                      | accepted   |
```

Optionally automate this with `adr-tools` (`adr new`, `adr generate toc`).

## ADRs and RFCs

If a decision was preceded by an RFC, the ADR's **Links** section references it. The RFC carries the deliberation; the ADR carries the decision.

Some decisions go straight to ADR (no RFC) — fine when the call is uncontested. See `RFCS.md` for when to prefer one over the other.

## Anti-patterns

- Editing the body of an accepted ADR. Write a new one that supersedes.
- An ADR with no `Consequences` section, or with only positive consequences.
- An ADR titled "Refactor X". ADRs document decisions, not work.
- A 10-line ADR with no Context. The Context is the most valuable section.
- ADRs split across multiple repos for one decision. Pick one canonical location.
- Reusing numbers when an ADR is abandoned. Leave the gap.
