# Proposal: working rules, skill routing and documentation (draft for approval)

Status: **Approved 2026-11-03 with amendments** (decisions D32-D34 in
[DECISIONS.md](../DECISIONS.md)): documentation stays deep for every addition or change,
with maintained diagrams and a graphify knowledge graph of the repository; old work-log
months are not archived. The rules in force live in [AGENTS.md](../../AGENTS.md); this file
keeps the reasoning. Written 2026-11-03. Goal: any model (including Sonnet 5.5) can work on this repository
without repeating past mistakes, because the rules are short, numbered, and checked
by scripts and hooks rather than remembered.

## 1. What went wrong so far (evidence from the work log and this session)

| # | Mistake | Where it happened | Why prose rules did not stop it |
|---|---|---|---|
| M1 | Plan drifted from reality: said "Real Google OAuth" after the GAS-only decision, Drive "unfinished" after it was built, missing two phases of progress | `IMPLEMENTATION_PLAN.md`, fixed 2026-11-02 | No check compares the plan with evidence |
| M2 | Evaluation rule widened after seeing results (18 -> 40 media checkpoints) | Work log 2026-11-02 | No rule that scoring rules freeze before a run |
| M3 | A bad slice edit deleted three sections of `TOOLING_AND_TESTS.md` | Work log 2026-11-02 | Caught only by luck from `git diff` |
| M4 | A mutation helper left three source files mutated | Work log 2026-11-02 | Mutations were done in the working tree, not in an isolated copy |
| M5 | Mojibake (`â€“`) committed in the plan | Plan line 51 | No encoding check on docs |
| M6 | A privacy rule in a skill silently overrode what the user wanted (no detailed LangSmith traces) | `observability.py`, `plan-quotation-app` | User decisions live in many files; nobody sees the conflict |
| M7 | Tests flaked on a minute boundary; gate killed by memory pressure | Work log 2026-11-02 | Not a rule problem; recorded honestly. Keep that behaviour |
| M8 | Claude Code does not discover `.agents/skills`, so skills are loaded only if the model remembers to open them | `CLAUDE.md` | Discovery depends on memory |
| M9 | 37 skills, overlapping (5 UI skills, 4 security/review skills, 2 WhatsApp skills, 3 LangGraph skills of 160-585 lines) | `.agents/skills/` | Too much to read; models skim or pick the wrong one |

## 2. Principles

1. **A rule that matters is a check.** Each rule below names how it is enforced:
   `script` (fails `npm run verify`), `hook` (Claude Code blocks the action), or
   `review` (a human/model checklist item, used only when automation is impossible).
2. **One home per fact.** Each kind of information has exactly one file that owns it
   (section 5). Other files link; they do not restate.
3. **Short beats complete.** The always-loaded rules fit on one page. Detail lives in
   skills that load only for their task.
4. **User decisions win and are visible.** Every user decision goes into one register;
   a skill or rule that conflicts with it must be updated in the same change.

## 3. The rulebook (replaces most of AGENTS.md + CLAUDE.md prose)

Each rule: what, and how it is checked.

**Before work**
- R1. Read `AGENTS.md`, `docs/DECISIONS.md` and the skill the router (section 4) names for the task. *Check: review.*
- R2. If the task changes security, money, data deletion, paid calls, external messages, accounts or scope: ask the user first, then record the answer in `docs/DECISIONS.md`. *Check: review.*
- R3. Never guess an API. Read the pinned version in the lockfile and the official docs (context7 or vendor site) before using it. *Check: review.*

**While editing**
- R4. Every Python and TS function/class has a contract comment (purpose, inputs/outputs, side effects, errors). *Check: script (`check:architecture`, extend to TS).*
- R5. Layering: `core` never imports features; routes delegate; `main.py` only composes. *Check: script (existing).*
- R6. After any edit to an existing file, look at `git diff --stat`; a file that lost more than 30 lines needs a stated reason. *Check: hook (warn after Edit/Write when deletions > 30).*
- R7. Experiments that change source (mutation tests, probes) run in a git worktree or with `git stash`, never in the main tree; the main tree must be clean of them afterwards. *Check: script (`check:clean-mutations` compares with HEAD for files listed in the experiment).*
- R8. Text files are UTF-8, LF; no mojibake sequences (`â€`, `Ã`). *Check: script (`check:docs`) + `.gitattributes`.*

**Evidence and claims**
- R9. Every claim of a result names its label: `local`, `local-substitute`, `sandbox`, `live`, `synthetic`. No other words. *Check: script (`check:evidence` validates a common header in every `docs/evidence/*.json`).*
- R10. A plan checkbox is ticked only with an evidence file linked on the same line, whose label matches the item (a live item needs `live`). *Check: script (`check:plan`).*
- R11. Evaluation scoring rules and oracle changes are committed **before** the run they score. A change after seeing results is labeled `post-hoc` and reported separately. *Check: script (summarizer refuses to score a run whose oracle hash differs from the one recorded at run start).*
- R12. "All checks pass" means one complete `npm run verify:full` on the final tree. Partial runs are reported as partial. *Check: review.*
- R13. Never print, log, commit or trace secrets or phone numbers. *Check: script (`check:secrets`, existing) + trace masking test.*

**Finishing**
- R14. A task that changed files ends with: docs updated (section 5), one work-log entry in the fixed template, and the narrowest relevant checks run. *Check: hook (Stop hook blocks finishing when `app/`, `scripts/`, `supabase/`, `gas/` or `tests/` changed but `docs/WORK_LOG.md` did not).*
- R15. Commit only at a completed phase or when the user asks; stage only own files; no force-push, no history rewrite, no deploy. *Check: hook (PreToolUse on `git push --force`, `git reset --hard`, deploy commands: block).*

## 4. Skill routing

### 4.1 Make skills discoverable
Keep `.agents/skills/` as the canonical source (Codex reads it). Add a script that copies
the active skills into `.claude/skills/` so Claude Code lists them automatically with their
descriptions, plus a `check:skills` step that fails when the two copies differ.
No more "remember to open the file by hand".

### 4.2 Consolidate 37 -> about 20 skills
Proposed (user decides each line in section 7):

| Keep / merge | Into | Why |
|---|---|---|
| `plan-quotation-app` | keep | Product scope and architecture |
| `build-quotations`, `implement-human-approval`, `process-voice-notes`, `ingest-supplier-evidence`, `evaluate-quotation-agent` | keep | Domain rules |
| `integrate-whatsapp` + `whatsapp-webhooks` | `integrate-whatsapp` (webhooks becomes a reference file) | Two skills for one channel |
| `automate-google-workspace` | keep | GAS-only rules |
| `secure-quotation-app` + `implement-abuse-controls` + `security-audit` | `secure-quotation-app` (others become references) | One security entry point |
| `review-quotation-code` + `verify-quotation-release` + `verify-engineering-coverage` | `verify-and-review` (ledger validator kept) | One "is it done/ready" entry point |
| `project-documentation` + `mermaid-diagrams` | `project-documentation` (Mermaid becomes a reference) | Docs and diagrams are one job |
| `frontend-design` + `impeccable` + `web-design-guidelines` | `frontend-design` (others become references) | One lead UI workflow (already required by SKILL_SELECTION) |
| `react-feature-structure` + `client-crud-state` + `react-best-practices` | `frontend-structure` | One React structure skill |
| `fastapi`, `shadcn`, `langsmith-trace` | keep as upstream references | Pinned vendor docs |
| `langgraph-fundamentals` + `-human-in-the-loop` + `-persistence` | keep as one `langgraph` skill with three references | Load only the part needed |
| `contribution-workflow` | keep | Git rules |
| `codebase-design`, `setup-pre-commit`, `resolving-merge-conflicts` | retire (archive) | Generic; models already know this |

Merging moves files and keeps licenses/hashes in the manifests; no content is lost.

### 4.3 One routing table
A single table (in `AGENTS.md`) maps task type to exactly one lead skill plus at most two
supporting skills. Example rows: "backend route" -> `fastapi` + `secure-quotation-app`;
"agent node" -> `langgraph` + `plan-quotation-app`; "any doc or diagram" -> `project-documentation`.
`SKILL_SELECTION.md` shrinks to provenance and history.

## 5. Documentation: one home per fact

| Fact | Owner file | Rule |
|---|---|---|
| What to build, status per item | `docs/IMPLEMENTATION_PLAN.md` | Checkbox + one status line + evidence link per item; no narrative history |
| How to test | `docs/TESTING_PLAN.md` | Unchanged |
| User decisions (dated, who, why) | **new** `docs/DECISIONS.md` | Append-only register; skills/rules link to entries |
| How the code works now | `docs/reference/*.md` | Present tense, no history; updated with the code |
| What happened, when | `docs/WORK_LOG.md` | Append-only, fixed template (below); older months archived to `docs/work-log/2026-10.md` |
| Open user actions | `docs/MORNING_ACTIONS.md` | Only open items; done items move to the work log |
| Proof | `docs/evidence/*.json` | Common header: date, commit, label (R9), command, result |
| Diagrams | `docs/diagrams/*.mmd` | Unchanged pipeline |

Work-log entry template (max ~8 lines):

```
### YYYY-MM-DD - <what changed> (phase N, <label>)
- Why: <user request or plan item>
- Changed: <paths>
- Checked: <command> -> <result>; not run: <list>
- Evidence: <file or none>
- Open: <gaps / user actions>
```

## 6. Claude Code enforcement (project `.claude/settings.json`)

- **Stop hook** (R14): run `scripts/agent_gate.py --quick`: fails if code changed without a
  work-log entry, if `check:docs` or `check:plan` fail. Fast (< 10 s), no database.
- **PostToolUse hook on Edit/Write** (R6): warn when a file lost > 30 lines.
- **PreToolUse hook on Bash** (R15): block force-push, `reset --hard`, history rewrite, deploy.
- New npm scripts: `check:docs` (encoding, links, plan/evidence rules), `check:skills`
  (sync), all added to `npm run verify`.

Hooks are guard rails, not a replacement for judgment; each block message says which rule
and how to fix it.

## 7. Questions for the user (decide before anything is built)

1. Approve the rulebook R1-R15 as written, or edit specific rules?
2. Approve the skill consolidation table (37 -> about 20), all or line by line?
3. Approve the documentation homes, including a new `DECISIONS.md` and archiving old work-log months?
4. Approve Claude Code hooks in a committed `.claude/settings.json` (they apply to anyone using Claude Code here)?
5. Should `AGENTS.md` keep its current long prose, or be replaced by the one-page rulebook plus routing table (old text archived)?
