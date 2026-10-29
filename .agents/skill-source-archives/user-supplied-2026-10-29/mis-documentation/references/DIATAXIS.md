# Diataxis — Tutorials / How-to / Reference / Explanation

[Diataxis](https://diataxis.fr/) splits user- and dev-facing documentation into four quadrants. Each quadrant has a single purpose and a single reader-state. **Mixing quadrants in one doc is the canonical Diataxis mistake.**

This reference applies to user / dev-facing docs. The four quadrants map to the MIS folder layout like this:

| Quadrant     | Lives in                                                    |
|--------------|-------------------------------------------------------------|
| Tutorial     | `docs/guides/` (numbered prefix, e.g. `01-getting-started.md`) |
| How-to guide | `docs/guides/` (descriptive kebab, e.g. `deploy-to-staging.md`) |
| Reference    | `docs/references/`                                          |
| Explanation  | `docs/architecture/<topic>.md` (most explanations are architectural) |

Internal docs — ADRs, RFCs, plans, runbooks, postmortems — are not Diataxis.

## The two axes

```
                  PRACTICAL                          THEORETICAL
                  (doing the work)                   (thinking about the work)

      STUDYING    Tutorials                          Explanation
      (learning)  ─────────                          ───────────

      WORKING     How-to guides                      Reference
      (using)     ─────────────                      ─────────
```

| Quadrant      | Reader is…    | Doc's job is…                          | Style          |
|---------------|---------------|----------------------------------------|----------------|
| Tutorial      | Learning      | Get them through a complete, predictable journey | Hand-held, complete |
| How-to guide  | Working       | Solve a specific problem               | Recipe, terse  |
| Reference     | Working       | State the facts                         | Dry, exhaustive |
| Explanation   | Studying      | Build understanding                     | Discursive, opinionated |

## Quadrant 1 — Tutorials

**Reader's state:** "I'm new. Teach me by doing." They don't know what they don't know.

**Doc's job:** Get them to a small, real success — start to finish — so they trust the system enough to keep going.

Rules:

- **Pick one path. Hand them through it.** No options, no branches, no "if you're on Mac, do X". If you have two paths, write two tutorials.
- **Every step works.** A tutorial that breaks at step 12 trains the reader that the docs lie.
- **The end state is concrete.** "You'll have a deployed Hello-World service responding to GET /healthz."
- **No theory.** Theory belongs in Explanation. A tutorial earns the reader's trust; once trusted, they'll read the theory voluntarily.
- **One tutorial per area is enough.** More than one becomes overlapping how-to guides in disguise.

Filename: `docs/guides/<NN>-<short-name>.md` — numbered prefix marks it as a tutorial within `guides/`.

## Quadrant 2 — How-to guides

**Reader's state:** "I know roughly what I'm doing. I have a specific problem." They want a recipe.

**Doc's job:** Get them to the answer for their specific task.

Rules:

- **One task per guide.** "How to deploy to staging." Not "Deploying."
- **Assume competence.** Skip the basics. Link to the tutorial if they need it.
- **Terse, imperative.** Numbered steps. Code blocks. No prose paragraphs explaining the why — that's Explanation.
- **Failure modes inline.** "If this returns 401, see step 3 below." Don't punt to a separate troubleshooting doc.

Filename: `docs/guides/<short-task-name>.md` — kebab-case task name (no numbered prefix; numbering is reserved for tutorials).

Typical how-tos in an MIS repo:

- `setup.md` — local development setup (this is a how-to, not the onboarding doc)
- `deploy-to-staging.md`
- `add-a-feature-flag.md`
- `rotate-credentials.md`
- `connect-to-the-staging-database.md`

## Quadrant 3 — Reference

**Reader's state:** "I'm in the middle of writing code. I need a fact." Their flow is interrupted.

**Doc's job:** Be the source of truth, fast.

Rules:

- **Be exhaustive.** Every flag, every parameter, every status code.
- **Be machine-style.** Tables, parameter lists, type signatures. Not prose.
- **No opinions.** A reference page is not the place to say "we don't recommend this option" — that's Explanation. State the facts.
- **Generated where possible.** OpenAPI spec → reference. TypeScript types → reference. Hand-written reference rots faster than generated reference.

Filename / location varies — most reference is generated. Hand-written reference lives in `docs/references/`.

Typical reference docs:

- API reference (OpenAPI → ReDoc / Swagger UI)
- Configuration / env-var reference
- CLI command reference
- Public types reference (TypeScript / Python)
- Event / message schema reference

## Quadrant 4 — Explanation

**Reader's state:** "I want to understand why." They have time. They want depth.

**Doc's job:** Build mental models that survive contact with new problems.

Rules:

- **Opinionated.** State what you believe and why. Compare alternatives.
- **Historical / contextual.** Why was it built this way? What constraints shaped it?
- **Discursive.** Prose paragraphs. Diagrams where they help.
- **Not actionable.** If a reader walks away with steps to follow, you wrote a how-to.

Filename: `docs/architecture/<topic>.md`. Most explanations in an MIS repo are architectural, so they sit alongside the C4 diagrams. If a repo has explanations that aren't architectural (rare), put them in `docs/explanations/<topic>.md` and link from `docs/README.md`.

Typical explanation docs:

- `architecture/auth.md` — why we chose JWT-with-refresh
- `architecture/event-bus.md` — why we use Kafka for X but Redis Streams for Y
- `architecture/data-model.md` — the entities and their relationships, conceptually

## The "is this Diataxis?" test

When opening a new doc, ask: *which quadrant?* If the answer is "all of them", you haven't found the doc — you've found three or four docs in a trenchcoat.

| Doc kind                                  | Diataxis?         | Where it lives                       |
|-------------------------------------------|-------------------|--------------------------------------|
| Getting Started tutorial                  | Tutorial          | `docs/guides/01-getting-started.md`  |
| Setup guide (local env)                   | How-to            | `docs/guides/setup.md`               |
| API spec                                  | Reference         | (generated, or `docs/references/api.md`) |
| "Why we chose Postgres"                   | Explanation       | `docs/architecture/postgres.md`       |
| ADR documenting "we chose Postgres"       | **Not Diataxis**  | `docs/decisions/`                    |
| RFC proposing "switch to MySQL"           | **Not Diataxis**  | `docs/planning/rfcs/`                |
| Implementation plan for the MySQL migration | **Not Diataxis** | `docs/planning/plans/`              |
| C4 container diagram                      | **Not Diataxis**  | `docs/architecture/c4/containers.md`  |
| "What to do when checkout 500s page you"  | **Not Diataxis** (runbook)   | `docs/runbooks/`         |
| Postmortem of the 2026-05-20 payment outage | **Not Diataxis** | `docs/postmortems/`                 |
| Onboarding doc                            | **Not Diataxis** (it's a meta-index) | `docs/onboarding.md`  |
| Changelog                                 | **Not Diataxis**  | `CHANGELOG.md`                       |

## Style notes per quadrant

| Quadrant   | Sentence mood   | Voice    | Code blocks                          |
|------------|-----------------|----------|--------------------------------------|
| Tutorial   | Second person, present: "You'll create…" | Friendly | Many, all runnable as written        |
| How-to     | Imperative: "Run…", "Set…"               | Terse    | Many, copy-pasteable                 |
| Reference  | Indicative: "X returns Y"                | Neutral  | Few — schemas / signatures, not flow |
| Explanation| Indicative + opinion: "We chose X because…" | Voice OK | Few — illustrative, not runnable    |

## Anti-patterns

- A tutorial that ends "for more options, see Reference X". Stop. The reader is learning, not optimising.
- A how-to that opens with two paragraphs of background. Lead with the recipe.
- A reference with a "Quick Start" section. The quick start is a tutorial. Move it.
- An explanation that doesn't take a position. If you can't say why you'd do it this way, the doc has no purpose.
- A single doc titled "Authentication" that covers the API, the setup, the rationale, and the migration path. That's four docs.
