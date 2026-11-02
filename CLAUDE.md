# CLAUDE.md

@AGENTS.md

`AGENTS.md` (imported above) is the only rule set for this repository. This file adds
only what is specific to Claude Code. If the two disagree, `AGENTS.md` wins; fix this file.

## Claude Code specifics

- **Skills are discovered automatically.** Project skills are mirrored from `.agents/skills/`
  to `.claude/skills/` (`npm run skills:sync`). Use the Skill tool with the lead skill from the
  routing table in `AGENTS.md`. Never edit `.claude/skills/` directly: edit `.agents/skills/`,
  then run `npm run skills:manifest` and `npm run skills:sync`. User-level skills never replace
  a project skill for the same job.
- **Hooks enforce rules** (`.claude/settings.json`, scripts in `scripts/hooks/`):
  - Stop: blocks finishing when application, script, test, migration or GAS files changed but
    `docs/WORK_LOG.md` did not, or when `npm run check:rules` fails (R14, R8-R10).
  - After Edit/Write: warns when a file lost more than 30 lines (R6).
  - Before Bash: blocks force-push, `git reset --hard`, history rewrites and deploy commands (R15).
  A hook message names the rule and the fix. Do not work around a hook; fix the cause.
- **Model note.** Rules are written to be followed literally. When a rule and a skill example
  disagree, the rule wins. When unsure whether something needs the user (R2), ask.
