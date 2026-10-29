# Research basis and applicability

Reviewed on 2026-10-29. These are primary sources. The catalog is an original,
project-specific synthesis, not a copied standard or evidence that a particular
group of developers lacks knowledge. Top-ten lists identify risk themes; ASVS
provides a broader requirements framework. Neither list alone proves coverage.

Source IDs used by concepts.json:

- asvs: [OWASP ASVS 5.0.0](https://asvs.owasp.org/), for systematic application-security requirements.
- top10: [OWASP Top 10:2025](https://top10.owasp.org/2025/0x00_2025-Introduction/), including configuration, supply-chain, and exceptional-condition risks.
- api: [OWASP API Security Top 10:2023](https://api-security.owasp.org/editions/2023/en/0x11-t10/), for object/property/function authorization, resource consumption, sensitive flows, inventory, and third-party APIs.
- agency: [OWASP excessive agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/), for limiting tools, permissions, and autonomous consequences. Product provenance and retrieval checks are project-specific extensions.
- consumption: [OWASP unbounded consumption](https://genai.owasp.org/llmrisk/llm102025-unbounded-consumption/), for uncontrolled inference, resource exhaustion, and financial abuse.
- aws: [AWS idempotent retries](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/), for reasoning about retries and ambiguous side effects. Our outbox/lease checks are implementation decisions, not a claim that this article specifies the entire worker design.
- sre: [Google SRE monitoring](https://sre.google/workbook/monitoring/), for observable behavior and resource saturation. Backup/restore, capacity, and recovery criteria are explicit project requirements; verify implementation-specific recovery guidance separately.
- pg-constraints: [PostgreSQL 17 constraints](https://www.postgresql.org/docs/17/ddl-constraints.html), for persistent invariants. Money, units, migration, and date scenarios are project applications of data integrity.
- pg-transactions: [PostgreSQL 17 transaction isolation](https://www.postgresql.org/docs/17/transaction-iso.html), for concurrent data behavior.
- supabase: [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security), for grants, policies, and privileged-role boundaries.
- langgraph: [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence), for state that survives conversations and interruptions. Approval identity, retention, and outbound-effect safety remain application responsibilities.

Check current official references against pinned dependencies when implementing.
Do not claim exact ASVS requirement mapping without checking that requirement's
version and wording. The catalog spans engineering correctness as well as security;
not every concept is a vulnerability category or a mandatory feature.

Applicability examples:

- A UI-only quotation layout change rechecks rendering, accessibility, and truthful
  state; it reuses backend evidence unless the change alters requests or permissions.
- A new audio endpoint must assess authentication, object scope, byte/duration
  limits, decoding isolation, spending, concurrency, trace privacy, and failure paths.
- A staff approval route needs role/object/property controls plus revision checks,
  replay handling, durable decisions, and downstream send authorization.
- A local database setup cannot establish a production restore target, public TLS,
  or managed-provider protections. Those remain Planned/Blocked when in release scope.
