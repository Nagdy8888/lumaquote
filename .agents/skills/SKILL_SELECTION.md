# Skill selection and provenance

Which skill to use for which task is decided by the routing table in
[AGENTS.md](../../AGENTS.md). This file records what the skills are and where they came from.
The earlier long version (with the October 2026 selection history) is archived at
[docs/archive/SKILL_SELECTION-until-2026-11-03.md](../../docs/archive/SKILL_SELECTION-until-2026-11-03.md).

## Active skills (19, consolidated 2026-11-03, decision D32)

| Skill | Origin | Contains (merged references) |
|---|---|---|
| `plan-quotation-app` | project | `references/agent-organization.md` |
| `build-quotations` | project | - |
| `implement-human-approval` | project | - |
| `process-voice-notes` | project | - |
| `ingest-supplier-evidence` | project | - |
| `evaluate-quotation-agent` | project | - |
| `automate-google-workspace` | project | - |
| `integrate-whatsapp` | project | `references/whatsapp-webhooks/` (Hookdeck, MIT) |
| `secure-quotation-app` | project | `references/abuse-controls/` (project), `references/security-audit/` (Cloudflare) |
| `verify-and-review` | project (new) | `references/review-quotation-code/`, `references/verify-quotation-release/`, `references/engineering-coverage/` (42-concept ledger and validator) |
| `project-documentation` | adapted | `references/mermaid-diagrams/` (softaworks, MIT, adapted) |
| `frontend-design` | upstream | `references/web-design-guidelines/` (Vercel) |
| `frontend-structure` | project (new) | `references/react-feature-structure/`, `references/client-crud-state/`, `references/react-best-practices/` (Vercel) |
| `impeccable` | retained local | kept top-level because its tools hardcode `.agents/skills/impeccable/scripts` |
| `langgraph` | project (new) | `references/fundamentals/`, `references/human-in-the-loop/`, `references/persistence/` (LangChain, pinned commit `126c384d`) |
| `langsmith-trace` | upstream | - |
| `fastapi` | upstream | - |
| `shadcn` | upstream | - |
| `contribution-workflow` | adapted | - |

A merged skill keeps its original files unchanged under the lead's `references/<name>/`, with its
`SKILL.md` renamed `GUIDE.md` so tools do not list it as a separate skill. Only project-authored
files had their relative links rewritten.

## Retired 2026-11-03

`codebase-design`, `setup-pre-commit` and `resolving-merge-conflicts` moved to
`../retired-skills-2026-11-03/` with `SKILL.md` renamed `SKILL.md.disabled`. Earlier retirements are
in `../retired-skills-2026-10-28/`. Retired copies are reference only; never load them as guidance.

## Provenance

- [upstream-manifest.json](upstream-manifest.json): source, commit, license and original file
  hashes of imported skills; `active_path` and `renamed_files` show where each file lives now.
- [project-manifest.json](project-manifest.json): current hashes of project-authored and adapted skills.
- `npm run skills:check` verifies upstream bytes are unchanged, project hashes are current, the
  Claude Code mirror matches, frontmatter is valid, project links resolve and `AGENTS.md` routes
  every active skill. Licenses stay in `_licenses/`.

Skills are development instructions, not application capabilities. They do not authorize
sending messages, account changes, paid calls, commits or deployment beyond the user's request.
