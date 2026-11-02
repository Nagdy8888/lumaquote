---
name: project-documentation
description: Maintain deep implementation references, inline contracts, setup guides, runbooks, and evidence for this project. Required for every repository file-changing task and completed implementation, setup, or verification step, as well as explicit documentation requests.
license: Proprietary - original supplied notices retained in the source archive.
---

# Project Documentation

Inspect root/applicable AGENTS.md, the documentation index and affected source before editing. Preserve approved plans, evidence and unrelated changes. Documentation is part of the implementation step, not a later phase. Pure read-only answers without a completed operational step do not require a work-log entry.

Read [the deep documentation standard](references/deep-documentation.md) before the first file-changing or completed operational step in each turn. Read [document patterns](references/document-patterns.md) for the requested artifact. Apply depth to the affected contracts; a small change does not require new guides, an RFC or a fixed amount of prose.

## Required working loop

- Read the affected implementation reference through `docs/README.md`; verify its claims against actual source, schemas and configuration.
- Include meaningful adjacent contracts and the relevant focused `docs/reference/` explanation with each coherent change. A log, generated schema or one-line purpose label cannot replace them.
- Update affected setup/API/runbook/test guidance and append the actual step, changed paths, purpose, verification and gaps to `docs/WORK_LOG.md` before the next step. The entry covers its documentation changes too; do not log recursively.
- Before reporting completion or a phase commit, review all affected new/changed/renamed/deleted paths for documentation coverage and validate links, examples and applicable inline/architecture contracts. A passing presence check does not prove the prose is accurate or sufficiently deep.
- Keep prior runtime evidence dated. For prose/comment-only changes, use appropriate static/contract checks and evidence of unchanged behavior when useful; do not invent a runtime rerun or invoke paid providers solely for documentation validation.

## Professional visual documentation

For architecture, relationships, nontrivial workflows and states, apply [mermaid-diagrams](references/mermaid-diagrams/GUIDE.md) and read [the visual documentation standard](references/visual-documentation.md). Maintain the relevant canonical sources, exact embeds and readable SVG previews with the code. Run diagram tests/render/freshness checks and inspect actual output; a syntactically valid diagram can still be misleading or unreadable. Keep this skill responsible for app claims/prose/evidence and Mermaid responsible for diagram syntax, without duplicating their policies.

## Ownership
- README is an entry point linking to setup, the actual workflow, and evidence.
- Setup/how-to explains a specific task; reference records contracts/configuration; explanation gives rationale; tutorials teach through a verified path.
- An ADR captures a material accepted decision. An RFC discusses an unresolved decision. An implementation plan sequences agreed work and preserves existing to-dos.
- Architecture views show actual actors, running processes, data stores, and external boundaries. Use C4 when it clarifies the system and keep editable diagram source.
- Runbooks support diagnosis, remediation, and verification for actual operational conditions. [Runbook prompts](assets/runbook-prompts.md) and [decision prompts](assets/decision-prompts.md) are optional starting points.
- Release notes describe implemented user-visible changes. Incident writeups separate facts, hypotheses, impact, and follow-up without assigning personal blame.

## Evidence and scope
Use real commands, URLs, owners, package versions, and observed results. Mark unavailable verification explicitly. Do not invent incident channels, Kubernetes resources, issue IDs, SLA claims, cloud deployments, or client results.
Do not copy secrets, populated environment files, private audio URLs, or raw traces. Clearly separate synthetic evaluation, local checks, sandbox integrations, and real pilots.
Update affected docs in the implementation task without automatically publishing, committing, or rewriting unrelated material. Validate relative links and meaningful command examples.
Use [contribution-workflow](../contribution-workflow/SKILL.md) for requested PR/release operations and [verify-engineering-coverage](../verify-and-review/references/engineering-coverage/GUIDE.md) for evidence-backed readiness.
