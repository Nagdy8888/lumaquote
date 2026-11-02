---
name: evaluate-quotation-agent
description: Create synthetic supplier datasets and evaluate end-to-end quotation and conversation behavior. Use for fixtures, quality metrics, regression gates, and evidence for portfolio claims.
---

# Evaluate the Quotation Agent

Create a fictional supplier dataset with coherent IDs, units, currency, effective dates, catalogs, price lists, inventory, policies, customer messages, and quote histories.
Label generated records and audio as synthetic. Do not use real personal details or imply a client relationship.
Maintain hidden expected outcomes separately from runtime retrieval and agent-accessible tools. Do not leak answer keys through filenames, metadata, prompts, or shared storage.

## Scenario coverage
Exercise complete conversations, including ambiguous text/audio, missing requirements, exact model codes, partial stock, obsolete products, unsupported substitutions, price changes, customer revisions, staff rejection/takeover, and resumed approvals.
Include authorization failures, duplicate/out-of-order webhooks, outages, restart recovery, uncertain delivery, and prompt injection.
Use independent expected calculations and explicit acceptable clarifications. Do not grade a response solely by resemblance to a model-generated reference answer.
Keep development and holdout scenarios distinct. Freeze prompts/configuration before reporting holdout results.

## Measurements
Measure extracted consequential fields, supported product matches, correct clarification, deterministic totals, source provenance, valid approvals, duplicate sends, and successful recovery.
Report sample sizes, scenario coverage, failures, latency, and model usage/cost basis. Separate estimates from provider-billed cost.
Measure staff preparation time and corrections in a defined workflow. Simulated processing speed is not measured employee time savings.
Keep customer outcomes such as conversion, revenue, and reduced overdue requests as pilot hypotheses unless observed in a real business study.
Compare added retrieval/agent complexity against a simple baseline. Do not optimize for a staged LinkedIn happy path while omitting difficult cases.

## Evidence
Use [langsmith-trace](../langsmith-trace/SKILL.md) for instrumentation and diagnosis under the redaction/project-scope rules in [plan-quotation-app](../plan-quotation-app/SKILL.md). Keep answer keys outside runtime access and inference traces. Installation does not verify connectivity or authorize remote dataset publication.
Version fixtures, expected results, code, prompts, model/configuration, and run artifacts. Keep failures visible.
End-to-end results must identify whether channels, transcription, Workspace, and model calls were local substitutes, provider sandboxes, or live integrations.

