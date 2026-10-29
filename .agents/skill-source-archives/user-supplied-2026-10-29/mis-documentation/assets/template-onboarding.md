# Onboarding

Welcome. This doc gets you from day 1 to month 1. It is **not** the setup guide — that's [guides/setup.md](guides/setup.md). Setup gets the app running; onboarding gets *you* productive.

If anything here is wrong, fix it in the PR you open during week 1.

## Day 1 — accounts and access

Tick these off:

- [ ] GitHub access to the org and this repo
- [ ] AWS / GCP console access (read-only to staging is fine)
- [ ] Linear (or Jira) — added to the project
- [ ] Slack — channels: `#engineering`, `#incidents`, `#<team>`
- [ ] PagerDuty — added to the appropriate rotation (shadowing only for week 1)
- [ ] 1Password vault — `<vault-name>`
- [ ] Production / staging DB read-only credentials

## Day 1 — local environment

Run through [guides/setup.md](guides/setup.md). Expected end state: the app starts, you can log in as a seed user, and the smoke tests pass.

If a step is unclear, **edit the setup guide** as you go. PR it at end of day.

## Week 1 — read these

- [docs/README.md](README.md) — the docs index
- [System Context diagram](architecture/c4/context.md) — the 30-second view
- [Container diagram](architecture/c4/containers.md) — the services and datastores
- [ADR index](decisions/README.md) — skim the titles, read the last 5
- The most recent [postmortem](postmortems/) — see how incidents are handled

## Week 1 — ship a small PR

Goal: get one PR merged end-to-end. The PR can be small (typo, doc fix, tiny refactor). The point is to walk the full path: branch → commit → push → PR → review → merge → CI → deploy.

If you can't find something small, ask your onboarding buddy.

## Month 1 — ship a feature

By the end of month 1, you should have shipped a small feature end-to-end:

- Wrote an ADR (or contributed to a discussion).
- Designed the change.
- Implemented + tested it.
- Shipped to staging, then to production.

You should also have shadowed an on-call shift.

## Who to ask

| Topic                          | Ask                      |
|--------------------------------|--------------------------|
| This codebase / a specific service | Your onboarding buddy    |
| Architecture / cross-cutting   | <name> (Eng Lead)        |
| Product / priorities           | <name> (PM)              |
| Infra / deploys / on-call      | <name> (DevOps Lead)     |
| Security                       | <name> (Security)        |
| HR / benefits / time off       | <name> (People Ops)      |
| Anything else                  | `#engineering` in Slack  |

## Where to read

- [docs/README.md](README.md) — the index
- [Architecture](architecture/c4/context.md) — start here for system shape
- [ADRs](decisions/) — why things are the way they are
- [Runbooks](runbooks/) — what to do when alerts fire

## Where to write

- New docs: see `mis-documentation` skill in the MIS skills pack.
- Commit / PR conventions: see `mis-github-contribution`.
- Stack-specific standards: see the matching `mis-*` skill.

## Feedback

After your first week, schedule 30 min with your onboarding buddy to:

- List what was unclear.
- File issues against the docs (or fix them).
- Confirm month-1 goals.
