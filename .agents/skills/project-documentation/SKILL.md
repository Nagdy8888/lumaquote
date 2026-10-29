---
name: project-documentation
description: Write or update project documentation, architecture decisions, setup guides, runbooks, and release notes. Use for documentation tasks and documentation changes required by implemented behavior.
license: Proprietary - original supplied notices retained in the source archive.
---

# Project Documentation

Inspect existing documents and conventions before adding another file. Preserve approved plans and evidence. Documentation size should match the change; a routine implementation does not require an RFC, onboarding program, or directory tree.

Read [document patterns](references/document-patterns.md) for the requested artifact.

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
Use [contribution-workflow](../contribution-workflow/SKILL.md) for requested PR/release operations and [verify-engineering-coverage](../verify-engineering-coverage/SKILL.md) for evidence-backed readiness.

