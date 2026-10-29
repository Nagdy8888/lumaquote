---
name: build-quotations
description: Implement product selection, authoritative price and stock checks, deterministic quotation calculations, revisions, and document output. Use for commercial quotation behavior.
---

# Build Quotations

Use the current authorized product, price, inventory, customer, and commercial-policy records. RAG supplies descriptive evidence; it does not determine current monetary values.

## Commercial correctness
Identify products by stable SKU and selected variant. Ask about missing consequential requirements instead of guessing technical compatibility.
Retrieve stock with location and observation time. Distinguish on-hand, available, and reserved when the source supports them; do not promise stock from a stale snapshot.
Record price-list/customer tier, currency, effective dates, units, minimum quantities, pack sizes, discounts, and tax configuration.
Use decimal arithmetic or integer minor units. Define line/order discount order, tax basis, inclusive/exclusive treatment, precision, and rounding from configured business rules.
Do not invent jurisdiction-specific taxes, eligibility, delivery promises, or discount authority. Missing commercial policy blocks finalization or requests staff input.
Disallow incompatible units/currencies and non-finite or negative values unless the business rule explicitly supports them.
Propose substitutions with evidence and explicit differences; require review for material changes.

## Quotation lifecycle
Create immutable revisions with source record versions/timestamps, line calculations, terms, validity, customer, and totals.
Generate the quotation document from the same canonical revision shown for approval. A preview/export must not silently recalculate different numbers.
Require authorized approval of the exact revision and recipient before sending. Recheck source freshness according to the business policy; changed consequential facts require revalidation and approval.
Keep acceptance, sales order creation, inventory reservation, and payment outside the quotation action unless explicitly implemented.
Use stable action identities for retries and retain an audit of revisions and delivery outcomes.

## Verify
Use independently calculated expected results for rounding, discounts, tax, packs, partial stock, expired prices, substitutions, revisions, and document parity.

