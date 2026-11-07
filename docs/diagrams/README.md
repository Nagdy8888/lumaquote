# Visual guide to LumaQuote

These source-backed diagrams explain the current local app. Each guide embeds
a static SVG preview, a full-size link and expandable Mermaid. Editable `.mmd`
sources and [catalog.json](catalog.json) are the maintained source of truth.

## Workflow and architecture

- [Request to reviewed offer](rendered/sales-workflow.svg): clarification,
  authoritative records, salesperson decision and revalidated local delivery.
- [Process boundaries](rendered/system-boundaries.svg): native application,
  private local Supabase, offline parser and optional external providers.
- [Exact approval sequence](rendered/quotation-approval.svg).
- [Authenticated mutation and replay](rendered/staff-operation.svg).

## Data and runtime

- [Catalog and commercial evidence](rendered/evidence-data.svg).
- [Offer and approval relationships](rendered/workflow-data.svg).
- [Conversation and exact attachment bindings](rendered/conversation-data.svg).
- [Durable agent graph](rendered/agent-graph.svg).
- [Expired-job recovery](rendered/job-recovery.svg).
- [Estimated allowance admission](rendered/estimated-allowance.svg).
- [Media states](rendered/media-lifecycle.svg).
- [Catalog discovery](rendered/catalog-retrieval.svg).
- [Frontend draft conflicts](rendered/frontend-draft.svg).
- [Authenticated live updates](rendered/frontend-live-updates.svg).
- [Signed GAS snapshots](rendered/google-snapshot.svg).
- [Drive export of approved PDFs](rendered/drive-export.svg).
- [WhatsApp ingress and gated egress](rendered/whatsapp-channel.svg).
- [Quotation answer and order lifecycle](rendered/order-lifecycle.svg): accept, decline, expiry,
  pending order and the stock hold.
- [Verification scopes](rendered/verification-scope.svg).
- [Working-rule enforcement](rendered/rule-enforcement.svg).

## Layer views

Embedded in the [layer guides](../layers/README.md):

- [Layers and dependency direction](rendered/layer-map.svg) and
  [one request through every layer](rendered/request-trace.svg).
- [Frontend composition and server state](rendered/frontend-layer.svg).
- [Staff API request pipeline and status codes](rendered/api-pipeline.svg).
- [Processes and the features they call](rendered/backend-modules.svg).
- [One worker tick](rendered/worker-tick.svg).
- [Data-layer identities and stores](rendered/data-access.svg).
- [Integration gates and proof levels](rendered/integrations-map.svg).
- [The verify gate](rendered/verify-gate.svg).

ER edges show selected actual SQL relationships, not invented foreign keys to
JSON lines or graph thread IDs. Ready media is unconfirmed; queued work is not
delivered; local delivery is not a WhatsApp receipt. The diagrams complement
the detailed [implementation references](../README.md) and their evidence limits.

## Maintaining a view

Read its code/SQL bindings in the catalog, edit the canonical source, then run:

```powershell
npm run test:diagrams
npm run diagrams:render
npm run diagrams:check
```

If the existing Playwright browser is missing, run `npx playwright install chromium`.
Rendering is local: no Docker image, global CLI, hosted diagram service or paid
provider is required. External browser requests are blocked. CI installs Chromium
with dependencies and runs the diagram tests/freshness check.

Render mode updates only owned guide markers and generated SVG/manifest files;
PNG inspection previews live in ignored `.local/diagram-previews`. Check mode
does not repair stale files. It checks exact embeds, source/code/renderer bindings,
stored SVG integrity, actual syntax/rendering, accessible title/description and
positive bounded dimensions. Inspect actual previews for readability, stray nodes,
cropped labels and misleading arrows: parse success alone is insufficient.

Use one focused question per view, short meaningful labels, readable contrast and
explicit optional/planned/unverified boundaries. Split crowded views. Never upload
credentials, private URLs or customer data to a renderer. Code hashes flag stale
bindings; they do not prove semantic correctness without source review.

Mermaid 11.17.2 is a pinned development-only dependency compatible with the native
Node setup. Inputs are repository-owned, strict mode/HTML-label restrictions are
enabled and no math is used. The observed low KaTeX advisory and pre-existing clasp
advisory remain recorded in WORK_LOG; this is not a public-renderer safety claim.

The [documentation skill](../../.agents/skills/project-documentation/SKILL.md) owns
app claims, prose and quality. The [Mermaid skill](../../.agents/skills/project-documentation/references/mermaid-diagrams/GUIDE.md)
supplies syntax guidance adapted from
[the pinned GitHub source](https://github.com/softaworks/agent-toolkit/tree/3027f20f3181758385a1bb8c022d4041dfb4de84/skills/mermaid-diagrams).
Its MIT notice, original instructions and commit/file provenance are preserved.
