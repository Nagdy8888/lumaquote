---
name: automate-google-workspace
description: Implement Google Sheets, Drive, Gmail, and Apps Script integrations for supplier records and quotation operations. Use for Workspace synchronization and automation.
---

# Automate Google Workspace

Inspect existing Workspace resources and verify current official API, Apps Script deployment, scope, quota, trigger, and execution-identity behavior before using them.

## Ownership and authority
Document the source of truth for products, prices, inventory, quotation state, and customer records. A spreadsheet may be authoritative or a synchronized view; never treat conflicting copies as equally current.
Use stable IDs and schema/version checks rather than row positions. Define types, units, currency, and effective dates; reject ambiguous headers and malformed values.
Separate formula cells from input data. Prevent customer text becoming a spreadsheet formula, executable script, or unsafe document markup.
Use least-privilege OAuth or approved service identity. Keep secrets out of client bundles, sheets, exported logs, and source control.
Validate spreadsheet/file ownership and company scope server-side. An unguessable Apps Script deployment URL is not authentication.

## Reliable synchronization
Use bounded batched reads/writes, incremental checkpoints, backoff, and durable operation identities. Do not rely on an Apps Script in-memory variable or trigger firing exactly once.
Use locks where suitable and backend version checks where concurrent writers cross processes. A script lock alone does not coordinate independent API writers.
Track partial success and reconcile by stable IDs after timeouts. Alert on failed or stale synchronization rather than silently serving it as current.
For triggers, verify whose authority they run under and how failures are observed. Separate sandbox and live document identifiers.

## Business operations
Generate documents from an approved canonical quote revision and store the resulting file identity/access policy.
Email and WhatsApp share approval/delivery rules; a trigger must not bypass them.
Test with local adapters or authorized sandbox resources. Distinguish local verification from real Workspace access and execution.

