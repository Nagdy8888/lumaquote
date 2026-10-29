# Repo layout — where every doc lives

The canonical `docs/` tree for an MIS repo. Doc kinds are top-level siblings, organised by **purpose** rather than by Diataxis quadrant. The Diataxis quadrants apply *within* `guides/` + `references/` + `architecture/` rather than as folder names.

```
<repo-root>/
├── README.md                       # repo entry point — what is this, how to start, links into docs/
├── CHANGELOG.md                    # keep-a-changelog format
└── docs/
    ├── README.md                   # docs index — navigation tree
    ├── onboarding.md               # day-1 → day-30 path for a new engineer
    │
    ├── architecture/               # how the system fits together
    │   ├── README.md               # links to each C4 level + supporting docs
    │   ├── c4/
    │   │   ├── context.md          # C4 Level 1: System Context
    │   │   ├── containers.md       # C4 Level 2: Containers
    │   │   └── components/         # C4 Level 3: per container that needs it
    │   │       └── <container>.md
    │   └── <topic>.md              # architectural explanations (Diataxis "Explanation")
    │
    ├── decisions/                  # ADRs — decisions made (immutable once accepted)
    │   ├── README.md               # ADR index
    │   ├── 0001-use-postgres.md
    │   └── ...
    │
    ├── planning/                   # forward-looking work
    │   ├── rfcs/                   # RFCs — decisions in flight
    │   │   ├── README.md           # RFC index
    │   │   └── 0001-event-bus-redesign.md
    │   └── plans/                  # implementation plans (post-RFC roadmaps)
    │       ├── 001-initial-setup.md
    │       └── 002-migrate-to-redis-streams.md
    │
    ├── guides/                     # Diataxis: tutorials + how-tos
    │   ├── 01-getting-started.md   # tutorial (numbered if part of a learning path)
    │   ├── setup.md                # how-to: local development setup
    │   ├── deploy-to-staging.md    # how-to
    │   └── rotate-credentials.md   # how-to
    │
    ├── references/                 # Diataxis: reference docs
    │   ├── api.md                  # may be generated from OpenAPI
    │   ├── config.md               # env vars, feature flags
    │   └── cli.md
    │
    ├── runbooks/                   # operational procedures, one per alert / symptom
    │   ├── README.md               # index — every alert linked here
    │   ├── api-error-rate-high.md
    │   └── ...
    │
    └── postmortems/                # incident write-ups, blameless
        ├── 2026-05-20-payment-outage.md
        └── ...
```

## What goes where — quick lookup

| Doc kind                                       | Lives in                              |
|------------------------------------------------|---------------------------------------|
| Repo entry point / first read                  | `README.md` (root)                     |
| User-visible changes per release               | `CHANGELOG.md` (root)                  |
| Docs navigation index                          | `docs/README.md`                       |
| Day-1 → day-30 for a new engineer              | `docs/onboarding.md`                   |
| C4 System Context diagram                      | `docs/architecture/c4/context.md`      |
| C4 Containers diagram                          | `docs/architecture/c4/containers.md`   |
| C4 Components diagram (per container)          | `docs/architecture/c4/components/<container>.md` |
| Architectural explanation ("why we chose X")   | `docs/architecture/<topic>.md`         |
| ADR (decision made)                            | `docs/decisions/<NNNN>-<name>.md`      |
| RFC (decision in flight)                       | `docs/planning/rfcs/<NNNN>-<name>.md`  |
| Implementation plan (post-RFC roadmap)         | `docs/planning/plans/<NNN>-<name>.md`  |
| Tutorial (learning-oriented)                   | `docs/guides/<NN>-<name>.md`           |
| How-to guide (task-oriented)                   | `docs/guides/<task-name>.md`           |
| Reference (lookup, dry, exhaustive)            | `docs/references/<topic>.md`           |
| Runbook (alert-triggered procedure)            | `docs/runbooks/<alert-name>.md`        |
| Postmortem (incident writeup)                  | `docs/postmortems/YYYY-MM-DD-<summary>.md` |

## Why this layout

- **Top-level siblings by purpose** match how engineers search ("where do ADRs live?" → `decisions/`). A `docs/diataxis/` umbrella adds a hop without adding clarity.
- **`architecture/c4/` as a sub-folder** keeps C4 diagrams together while leaving room for non-C4 architectural docs (explanations, deployment diagrams) at `architecture/`'s top level.
- **`planning/rfcs/` and `planning/plans/` as siblings** reflects that both are forward-looking: RFCs decide *whether and how*, plans sequence *the doing*. Once an RFC is accepted, the resulting ADR lives in `decisions/` and the implementation plan lives in `planning/plans/`.
- **`guides/` mixes tutorials and how-tos** because the audience overlaps and the volume of each is usually small. Within the folder, naming convention separates them (numbered prefix = tutorial; descriptive kebab = how-to).
- **Diataxis "Explanation" quadrant maps to `architecture/`** because most explanations in an MIS repo are about the system's architecture. If a repo has non-architectural explanations, create `docs/explanations/` and link from the docs README.

## The docs README

`docs/README.md` is the navigation tree. Keep it tight — under ~80 lines. Pattern:

```markdown
# Docs

## Start here
- [Onboarding](onboarding.md) — day-1 → day-30
- [Setup](guides/setup.md) — local dev environment

## Architecture
- [System Context](architecture/c4/context.md)
- [Containers](architecture/c4/containers.md)
- [Components](architecture/c4/components/) — per container
- Explanations: [auth](architecture/auth.md), [event-bus](architecture/event-bus.md)

## Decisions
- [ADR index](decisions/README.md)

## Planning
- [RFCs](planning/rfcs/README.md)
- [Plans](planning/plans/)

## Guides
- [Tutorials](guides/) — numbered docs
- [How-to](guides/) — task-named docs

## Reference
- [API](references/api.md)
- [Config](references/config.md)
- [CLI](references/cli.md)

## Operations
- [Runbooks](runbooks/README.md)
- [Postmortems](postmortems/)
```

## The repo README

`README.md` at the repo root is the entry point for someone who just landed on the GitHub page. Pattern:

1. **One-paragraph "what is this"** — for a stranger.
2. **Quickstart** — 3-5 commands to get something running.
3. **Where to read next** — link into `docs/README.md` and 2-3 key docs.
4. **Status / badges** — CI, version.
5. **License + contact.**

The repo README is **not** the docs README. Resist the urge to inline architecture, ADRs, or runbooks here. Link out.

## Naming conventions

| Doc kind          | Filename pattern                                  | Example                                |
|-------------------|--------------------------------------------------|----------------------------------------|
| ADR               | `<NNNN>-<short-kebab-name>.md` (4-digit, monotonic) | `0007-jwt-with-refresh-tokens.md`     |
| RFC               | `<NNNN>-<short-kebab-name>.md` (4-digit, separate sequence from ADRs) | `0004-event-bus-redesign.md` |
| Plan              | `<NNN>-<short-kebab-name>.md` (3-digit, monotonic) | `012-redis-streams-migration.md`      |
| Tutorial          | `<NN>-<short-kebab-name>.md` (2-digit if part of a sequence) | `01-getting-started.md`     |
| How-to            | `<short-kebab-task>.md`                          | `deploy-to-staging.md`                 |
| Reference         | `<topic>.md`                                     | `api.md`, `config.md`                  |
| Runbook           | `<alert-name-kebab>.md` (match the alert name)   | `api-error-rate-high.md`               |
| Postmortem        | `YYYY-MM-DD-<short-kebab>.md` (date incident started) | `2026-05-20-payment-outage.md`    |
| Architecture doc  | `<topic>.md`                                     | `auth.md`, `event-bus.md`              |
| C4 level          | `context.md` / `containers.md` / `components/<container>.md` | —                            |

## Numbering rules

- **ADR / RFC / Plan sequences are monotonic.** Never reuse a number. If you abandon a draft, leave the gap.
- **ADR and RFC numbers are independent.** ADR-0001 and RFC-0001 are unrelated.
- **Plans are independent again.** Three sequences, no cross-overlap.

## What does *not* go in `docs/`

- API specs auto-generated at build time (OpenAPI YAML, GraphQL SDL). They live next to the code that produces them; the generated reference output lives in `docs/references/` or is rendered by a docs site.
- Tickets, sprint plans, retros. Those live in the tracker (Linear / Jira), not the repo.
- Customer-facing marketing docs. Different audience, different repo.
- Diagrams as opaque PNGs. Use Mermaid (source in Markdown) or commit the Structurizr DSL alongside.
