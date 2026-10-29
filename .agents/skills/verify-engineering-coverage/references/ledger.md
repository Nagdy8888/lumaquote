# Coverage ledger format

The root object has schema_version (1), scope (a meaningful description), revision
(the assessed code/config snapshot), environment, and assessments.
Assessments contain every catalog ID exactly once. Each has id, status, reason,
and evidence (an array). Keep status names exactly as defined in SKILL.md.

An evidence object has kind, path, result, revision, and environment.
Allowed kinds are code, config, design, test, and runtime. Allowed results are
observed, passed, failed, and not_run. Paths point to existing, redacted files
relative to the workspace root, not credentials, private URLs, or a shell command.
The validator rejects paths outside the workspace and symlinks resolving outside it.

Covered requires:

- At least one observed/passed implementation item (code, config, or design).
- At least one passing behavioral item (test or runtime).
- Every claimed evidence item is current for the assessed revision/environment,
  with no failed/not_run item hidden under a Covered status.

A test source file is not proof of a test result. Point behavioral evidence at a
result/log/report artifact with the actual invocation and outcome. A design document
cannot prove the app enforces the design. Reviewers must inspect evidence content;
the script cannot verify these semantics.

For NotApplicable, reason must name the architectural absence or excluded scope.
For Planned or Blocked, reason identifies the gap/decision and its next action.
Keep NotAssessed honest during discovery. Do not use a passing structural check as
a security verdict.

Work-mode validation allows unfinished assessments and prints their counts.
Release mode requires Covered or justified NotApplicable for every concept in the
stated release scope. It rejects empty or partial inventories. A release-specific
ledger must be reconciled with all implemented surfaces by the reviewing agent.

Use the initializer rather than hand-copying an incomplete example. It refuses to
overwrite an existing file and initializes all entries to NotAssessed; that fresh
ledger intentionally fails release validation.
