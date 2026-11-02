---
name: verify-engineering-coverage
description: Check overlooked security, reliability, data, and AI engineering concepts against implementation evidence. Use when planning a substantial quotation-app feature, reviewing security-sensitive changes, or declaring a workflow or release complete.
---

# Verify Engineering Coverage

The user asked for a research-backed safeguard against engineering concepts being
missed during AI-assisted development. Do not assume the user knows the terms or
require them to name controls before considering them.

This is a coverage workflow, not a claim that all software risks can be eliminated.
Use it with the implementation skills; it does not replace them or authorize an
unrequested full audit, infrastructure change, external send, or paid operation.

## Establish actual scope

Read the specification, actual diff/code, exposed route/RPC/Storage inventory,
selected environment, and business consequences. Cover direct Supabase access,
workers, model tools, WhatsApp events, browser behavior, and external integrations
when present, including less obvious paths around the main UI.

Read [the concept catalog](references/concepts.json). Its 42 entries define terms,
give a failure example, and state observable verification. Read
[research and applicability](references/research.md) to understand source limits.
During planning classify every entry for the feature. During a narrow change,
reuse the existing ledger and reconsider affected entries; do not generate a new
42-item document for a typo or unrelated copy edit.

## Maintain an evidence ledger

Use docs/engineering/coverage.json or the existing project coverage artifact.
Do not overwrite an existing ledger or an approved plan. A feature-specific ledger
may use a descriptive filename. For releases, the scope must describe the whole
requested release and its actual exposed surfaces, not a hand-picked safe subset.

Create a new ledger with scripts/check_coverage.py --init PATH --scope TEXT
--revision ID --environment NAME when needed. Use a commit or honest working-tree
snapshot identifier; no git repository is required.

Every catalog ID needs one assessment:

- NotAssessed: applicability or implementation has not yet been inspected.
- Planned: applies, but implementation or proof remains.
- Blocked: applies and a named blocker prevents completion.
- Covered: implemented and supported by current behavioral evidence.
- NotApplicable: a concrete scope/architecture reason explains its absence.

For Covered, record why, implementation/configuration evidence, and a passing test
or runtime artifact, tied to the current revision and environment. Preserve
observed limitations. A decorator, library installation, prompt rule, comment,
configuration setting, or unit test mocking every boundary does not alone prove
the behavior. Recheck relevant evidence after changes; do not relabel old results.

Do not mark NotApplicable because a feature is difficult, unimplemented, hidden
by the UI, or handled by a provider without verifying the provider boundary.
For example, cookie CSRF may be inapplicable under a verified bearer-only design;
authorization is still required. Local fixtures cannot establish public TLS or
live provider delivery.

Use the exact ledger schema in [the ledger guide](references/ledger.md).
Run scripts/check_coverage.py PATH for structural validation during work and
scripts/check_coverage.py PATH --release before a completion/readiness claim.
The release mode rejects unresolved entries and unsupported coverage claims.
The validator checks metadata and artifact existence, not whether the evidence is
truthful or sufficient: inspect the actual referenced implementation and results.

## Act on gaps

For each applicable concept, convert the gap into acceptance criteria and a task
in the existing plan. Implement authorized work and run meaningful deny, boundary,
race, and recovery checks. Use implement-abuse-controls for admission/spending,
secure-quotation-app for access/browser/file/tool controls, and the relevant
domain skill for business behavior.

Do not copy all of ASVS into the app or add expensive infrastructure by default.
Choose proportionate controls, document decisions, and retain the business scope.
If the user needs to choose a concrete spend/retention/public-deployment policy,
ask only for that missing choice while completing independent work.

## Report honestly

Summarize checked scope, proved coverage, justified exclusions, and remaining
gaps with evidence locations. Explain unfamiliar terms briefly when reporting
them. A failed coverage gate prevents a readiness claim, not progress on other
authorized tasks. Never claim ASVS certification, a complete security audit, or
production readiness from this catalog or a passing ledger validator.
