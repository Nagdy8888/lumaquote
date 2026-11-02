---
name: setup-pre-commit
description: Configure repository-local commit hooks for the actual Python and TypeScript checks. Use when the user requests pre-commit, Husky, lint-staged, or commit-time validation setup.
---

# Set Up Commit Checks

Inspect existing hooks, package managers, lockfiles, Python tooling, CI commands,
and Git state before choosing a runner. Preserve the existing hook chain.

For this mixed Python/FastAPI and React/TypeScript project, choose one coherent
repository-local entrypoint. An existing pre-commit setup can orchestrate both;
an existing Husky setup can invoke the actual Python and Node commands. Do not
install both competing systems just because separate supplied skills mention them.

Configure only checks backed by real code and commands: lint, formatting,
typechecking, relevant tests, conflict markers, and secret detection as appropriate.
Do not invent passing no-op scripts for unimplemented packages. Keep fast hooks
useful while running broader release/evaluation gates in CI or the release task.

Respect the repository's formatter/configuration. Limit autoformatting to the
intended authored files; exclude provider keys, local restore payloads, generated
assets, supplied-source archives, and unmodified upstream utilities where relevant.
Use repository-local configuration; do not change global Git settings.

Verify the configured check command using a harmless temporary fixture or the
intended staged change without staging unrelated user files. Show actual failures
and command results. Setting up a hook does not authorize committing or pushing.

Use [contribution-workflow](../contribution-workflow/SKILL.md) for commit/PR
mechanics and [verify-quotation-release](../verify-quotation-release/SKILL.md)
for full release gates.
