# Sales workspace design

Use the approved product identity across repeat-use screens. Establish one visual direction with semantic tokens, consistent hierarchy, and deliberate density. The supplied app-design guidance is integrated here; it is not a competing design system.

## Expression and working surfaces
The user explicitly requested a striking portfolio presentation and purposeful 3D. A product/lighting scene, onboarding, or showcase moment may carry that expression. Conversation, quotation editing, and approval surfaces should be efficient and legible without losing visual quality.
Do not impose categorical bans on font families, precise font sizes, all animation, or all display typography. Choose typography intentionally, verify licensing, and meet readability and loading goals.
Use shadcn's actual semantic tokens and theme structure rather than installing a second token system or outdated Tailwind configuration. Keep component styling and application tokens aligned.
One useful 3D scene is preferable to a heavy canvas behind every screen. Lazy-load it, support reduced motion and static fallbacks, and avoid presenting fictional renders as verified technical simulations.

## States and interactions
Design initial, loading, empty, filtered-empty, partial, error, pending, and confirmed states for the main tasks. Show what is available while independent work continues.
Use layout-matched skeletons where helpful and localized pending indicators for row operations. Do not impose an arbitrary timing rule as a universal requirement.
Keep the conversation and relevant catalog evidence visible while reviewing an offer. Display revision, substitutions, warnings, recipient, and commercial terms at the actual approval boundary.
Use the server's canonical state for approvals and delivery. Pending does not mean approved, and accepted by a provider does not mean delivered.
Preserve entered information after failure and offer a safe next action. Destructive confirmation should match the action's consequences; type-to-confirm is not mandatory for every deletion.
Use motion to explain cause and effect; allow the requested showcase expression where it serves the surface. Avoid repetitive distracting choreography on working screens.

## Accessibility and verification
Support keyboard completion, visible focus, correctly labeled forms, overlay focus management, non-color status signals, live feedback, and responsive layouts. Keep shortcuts optional unless they solve a demonstrated navigation need.
Inspect desktop and narrow-screen states plus reduced-motion/3D fallbacks. Record actual browser checks; code review alone is not visual verification.
Use impeccable for focused refinement, shadcn for component APIs, web-design-guidelines for accessibility review, and client-crud-state for data reconciliation. Preserve this shared direction across all of them.

