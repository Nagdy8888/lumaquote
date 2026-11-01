# Professional Mermaid documentation

Read root AGENTS.md, the affected guide and its actual code/SQL before drawing.
Use the installed mermaid-diagrams skill for syntax/type guidance. Documentation
owns the factual claims and completion evidence; imported examples do not override
application authority, schema relationships or current implementation status.

Use focused process/flow views for branching, sequences for participant order,
ER diagrams for actual stored relationships and state views for lifecycle behavior.
Show trust boundaries, approval/version checks and uncertainty where consequential.
Do not invent foreign keys to JSON content, draw planned providers as live or
equate accepted/queued/ready with delivered/confirmed/approved.

Keep canonical `.mmd` sources under docs/diagrams, catalog code bindings, explicit
owned guide markers and generated SVG previews together. Link through the diagram
and documentation indexes. Explain each view's purpose/scope near its embed and
retain detailed prose/inline contracts. Use descriptive accessible titles, short
labels, readable contrast, consistent styling and explicit full-size/source links.
Split crowded views instead of shrinking them to unreadable text.

For a relevant change, read bindings, edit the source and run `npm run test:diagrams`,
`npm run diagrams:render`, then `npm run diagrams:check`. Inspect the actual
PNG/SVG for clipped labels, stray nodes, misleading edges and readable normal-width
presentation. Syntax/hash/dimension checks cannot establish business correctness.
Fix failures before calling diagram work complete; record actual results/gaps in
WORK_LOG and existing evidence locations. Ordinary small prose changes need no
new diagram or arbitrary diagram count.

Render locally using the pinned dependency and existing Playwright Chromium.
Do not upload project diagrams to public renderers, install global tools or run
paid model calls for diagram validation. Keep secrets, private URLs and customer
data out of source/assets. CI checks committed diagram consistency; local changes
and unrun remote checks must remain separately identified.
