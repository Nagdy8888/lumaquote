# Frontend work plan (for Sonnet execution)

Date: 2026-11-03. Status: proposed, not started. Author: Claude (Opus) planning pass.
Scope: `app/frontend/src` plus the browser review script, evidence and docs it needs.
Plan home: this file holds the task breakdown only. Status still goes in
[IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) (phase 5), history in
[WORK_LOG.md](../WORK_LOG.md), current behavior in [FRONTEND.md](../reference/FRONTEND.md).

## How to start

Give Sonnet this prompt in the main repository folder:

```
Execute docs/proposals/2026-11-03-frontend-plan.md from F0 through the merge and cleanup,
following its "Run to completion" section. Do not stop or ask me to continue.
```

## Why this plan exists

The frontend already covers the full manual slice (sign-in, inbox, thread, quotation
editing, approval, catalog, connections, optional 3D). Phase 5 items 1 and 4 stay open,
and a code read on 2026-11-03 found these concrete gaps:

| # | Gap | Where | Source of the requirement |
|---|---|---|---|
| G1 | UI polls every 5-8 s; the backend SSE stream `GET /api/events` is never used | `features/workspace/api.ts`, `features/conversations/api.ts` | D03 (SSE for UI updates) |
| G2 | Connections page copy still says Google OAuth consent / Drive folder | `features/integrations/ConnectionsPage.tsx` lines 28-30 | D10 (Apps Script only), FRONTEND.md gap note |
| G3 | Agent/export job state (`workspace.jobs`) is returned but never shown | thread header, Overview | plan-quotation-app: "show actual workflow state" |
| G4 | Voice notes play in a bare `<audio>`; no waveform | `features/conversations/MediaPreview.tsx` | plan-quotation-app: "audio waveform/playback" |
| G5 | Approve is one click with no restated amount | `features/quotations/ui/ReviewActions.tsx` | plan-quotation-app: "confident approval interactions" |
| G6 | On portrait (<=680 px) the inbox stacks list, thread and quotation; approval sits far below | `conversations.css`, `quotations.css` | phase 5 item 4, shot 8 |
| G7 | Capture mode replaces names only; message bodies can still show emails or phone numbers | `ConversationThread.tsx`, `workspace-context.ts` | phase 5 item 1, R13, FRONTEND.md |
| G8 | Unknown routes render Overview; no not-found page | `app/App.tsx` | FRONTEND.md "Composition and routes" |
| G9 | No whole-app desktop/portrait/axe/overflow review with evidence | `tests/browser/` | phase 5 item 4, TESTING_PLAN section 12 |

Out of scope (do not do these): migrating feature CSS to Tailwind utilities, a new
visual direction, new backend endpoints or schema changes, server-side catalog search
in the UI, deployment, paid AI calls, live WhatsApp/Google steps. If a task seems to
need one of these, skip that part, record the question (see "Run to completion") and
continue with the rest (R2).

## Run to completion (user instruction, 2026-11-03)

The user wants this plan finished in one unattended run. Sonnet does not stop, pause or
hand back until everything below is true:

- tasks F0-F9 are done, and the PR is merged and cleaned up as in "Merge and clean up"; or
- every task still open is blocked by something only the user can do (an account, a
  consent, a decision under R2), each blocker is written down as described below, and
  every other task is done.

Rules for the run:

1. **No check-ins.** Do not end a turn to report progress, ask "should I continue?",
   offer options or wait for approval between tasks. The branch, commits, push, PR and
   merge are already authorized (D39). Status goes in commits, the work log and the PR
   body, not in a message that waits for a reply.
2. **No questions unless R2 requires one.** Where the plan gives a default, use it. Where
   it does not, choose the option that changes the least, follows `DESIGN.md` and
   existing code, and note the choice in the work log. Only a question about security,
   money, data deletion, paid calls, external messages, accounts or scope is a real
   question. Write it in `docs/MORNING_ACTIONS.md` and keep working on everything that
   does not depend on the answer.
3. **Blocker ladder.** When a check fails or something does not work:
   a. Read the full error, find the cause, and fix it. Try up to three different
      approaches; a retry of the same command is not a new approach.
   b. Still blocked: undo the uncommitted partial change in that task with
      `git checkout -- <file>` (R7), mark the task "Blocked: <exact error, what was
      tried>" in the PR body and the work log, add a line to `docs/MORNING_ACTIONS.md`,
      and move on to the next task that does not depend on it.
   c. After the last task, return to every blocked task once more before the merge gate.
   Never weaken a test, delete an assertion, skip or bypass a hook, or use `--force` to
   get past a blocker.
4. **Hooks.** If a Claude Code hook blocks a command or the Stop hook blocks finishing,
   read its message, fix the cause it names (for example add the missing work-log entry
   or fix `check:rules`) and continue. A hook block is not a reason to stop.
5. **Track progress outside your memory.** Keep tasks F0-F9 in your todo list. After each
   task, update the PR body's Changes section with a status per task (`Done`,
   `Blocked: ...`, `Not started`). Do not use Markdown checkboxes in repository files for
   this (R10).
6. **Resume after context loss.** If the conversation is summarized or restarted, re-read
   `AGENTS.md`, this plan, `git log --oneline origin/main..HEAD` in the worktree and the PR
   body (`gh pr view --json body`), then continue at the first task that is not `Done`.
   Do not redo finished tasks.
7. **Long commands.** `npm run test:browser` and `npm run verify:full` take minutes. Wait
   for them with a long timeout or run them in the background and wait for the
   notification; do not end the turn while they run. If `verify:full` is stopped by memory
   pressure, close other heavy processes you started (dev servers), then run it again
   once; if it still cannot finish, that is a blocker under rule 3.
8. **The only end states.** (a) PR merged, branches and worktree deleted, final report;
   or (b) the merge gate cannot be met because of a blocker only the user can clear: the
   PR stays open (ready or draft as appropriate), and the final report lists each
   blocker, what was tried and what the user must do. Nothing else ends the run.

## Execution protocol for Sonnet (read before every task)

1. Re-read `AGENTS.md`, `docs/DECISIONS.md` and the lead skill named in the task (R1).
   Frontend code tasks: lead `frontend-structure`, supporting `shadcn`. Visual tasks:
   lead `frontend-design`, supporting `impeccable`.
2. Do one task at a time, in the order below. Do not start the next task until the
   current task's "Done when" list holds and its checks pass.
3. Read every file you will edit before editing it. Keep the existing contract comment
   style: every new function, hook and component gets a one-paragraph `/** ... */`
   contract stating purpose, inputs/outputs, side effects, authority and failure
   behavior (R4). `npm run check:frontend` enforces presence.
4. Layering (R5): `shared/` never imports from `features/`. A feature may import
   `shared/` and, where it already does, another feature's public hook
   (`features/conversations/api`). Do not add new cross-feature imports beyond those
   listed in a task.
5. Never compute money in the browser. Display only server strings through `money()`.
   Never show approval or delivery before the server confirms it.
6. Never generate a new operation key on retry of the same approval or upload.
7. Do not edit `shared/api/generated.ts` by hand. Do not edit `.claude/skills/`.
8. Work only in the plan's worktree on branch `feat/frontend-phase5` (see "Branch, pull
   request and merge" below). Never switch branches in the main working tree: other
   sessions are editing there. Stage only files your task lists, by name (R15).
9. After each task: `git diff --stat` (R6), the task's checks, a FRONTEND.md update,
   and one WORK_LOG.md entry in the template from `AGENTS.md`. Label results `local`
   or `local-substitute` (R9). Do not tick a plan checkbox unless the task says so and
   the evidence link is on the same line (R10). Then commit and push as described below.
10. If a check fails, follow the blocker ladder in "Run to completion". Do not weaken a
    test, skip a hook or delete a failing assertion.

Standard checks for a frontend code task (run from the repository root):

```
npm run typecheck --workspace @lumaquote/frontend
npm run test:ui
npm run check:frontend
npm run check:rules
```

Run `npm run test:browser` only in tasks that say so; it needs local Supabase
(`npm run db:start`) and takes several minutes.

## Branch, pull request and merge (decision D39)

The user decided on 2026-11-03 that this plan is done on its own branch, pushed to
GitHub, reviewed through one pull request, merged after the checks pass, and the
branch then deleted. This is the authorization for those git and GitHub steps (R15);
it covers this plan only.

Repository facts (verified 2026-11-03):

- Remote `origin` = `https://github.com/Nagdy8888/lumaquote.git`, default branch `main`,
  no branch protection, `gh` signed in as `Nagdy8888`.
- CI workflow `.github/workflows/ci.yml` ("Application checks", job `local-contracts`)
  runs on every push and pull request: lint, architecture, frontend contracts,
  diagrams, typecheck, unit tests, `test:ui` and build. It does **not** run local
  Supabase, integration or browser tests. Those must pass locally before merge.
- The Claude Code guard hook blocks `git rebase`, force-push, `reset --hard` and amends.
  Do not try to work around it: update the branch with `git merge`, never rebase.

Branch and worktree (done in F0):

- Branch name: `feat/frontend-phase5`, created from `origin/main`.
- Worktree path: `C:\Nagdy\Mustafa\Work\Upwork\lumaquote-frontend` (a sibling of the
  repository). All plan work happens there.

Commits:

- One commit per task (F1 ... F8), plus the F0 plan commit and the F9 close-out commit.
- Conventional Commit subjects as the repository already uses, for example
  `feat(frontend): stream workspace refreshes over authenticated SSE`,
  `fix(frontend): replace legacy OAuth copy on connections page`,
  `test(browser): add whole-app UI review with evidence`.
- Body: what changed and why in two or three lines, the checks run with their results.
  End every message with the attribution line
  `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` (use the model actually
  running the task).
- Stage files by name (`git add <path> ...`), never `git add -A` or `git add .`.
  Never commit `.env`, `.env.local`, `.local/` or screenshots outside `docs/evidence/`.

Push and pull request:

- After the F1 commit: `git push -u origin feat/frontend-phase5`, then open a draft PR:
  `gh pr create --draft --base main --head feat/frontend-phase5 --title "Frontend phase 5: live updates, approval, portrait inbox, UI review" --body-file <file>`.
  Write the body file in the scratch or temp directory, not in the repository.
- PR body sections: Problem (gaps G1-G9 with a link to this plan), Changes (one line per
  task, filled in as tasks land), Validation (local checks and CI, reported separately,
  with labels `local` / `local-substitute`), Limitations (what stays open). End the body
  with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
- After every later task: push, then update the Changes and Validation sections with
  `gh pr edit <number> --body-file <file>`.
- After each push, check CI with `gh pr checks <number> --watch`. If CI fails, fix it in
  the next commit on the same branch before starting the next task.

Keeping the branch current:

- Before F8 and again before merging, run `git fetch origin` and
  `git merge origin/main` in the worktree. If `docs/WORK_LOG.md` conflicts, keep both
  sides' entries in date order. For a conflict in a file this plan changed, keep both
  intents and rerun that task's checks. For a conflict in a file this plan did not
  change, take `origin/main`'s version. If a conflict cannot be resolved without
  dropping someone else's change, abort with `git merge --abort` and treat it as a
  blocker (rule 3 in "Run to completion").
  Rerun the standard checks after a merge that brought in changes.

Merge gate (all must hold; otherwise do not merge and report what failed):

1. Every task F1-F8 is done or explicitly listed as open in the PR body with a reason.
2. CI "Application checks" is green on the latest pushed commit (`gh pr checks`).
3. Locally on that same commit: `npm run test:browser`, the F8 UI review test and one
   complete `npm run verify:full` passed (R12). A partial or memory-stopped run is not a
   pass; report it and do not merge.
4. `git status` in the worktree is clean and the branch is pushed (local and remote
   commit IDs match: `git rev-parse HEAD` equals `git rev-parse origin/feat/frontend-phase5`).
5. The PR is marked ready: `gh pr ready <number>`.

Merge and clean up (in this order):

1. `gh pr merge <number> --merge` (a merge commit keeps the per-task commits and their
   work-log references; do not use `--rebase`).
2. Delete the remote branch: `git push origin --delete feat/frontend-phase5`.
3. Remove the worktree from the main repository folder:
   `git worktree remove C:\Nagdy\Mustafa\Work\Upwork\lumaquote-frontend`.
   If it refuses because of untracked files, list them with `git status` in the
   worktree and ask the user; do not use `--force`.
4. `git fetch origin --prune`, then confirm the merge with
   `git merge-base --is-ancestor feat/frontend-phase5 origin/main` (exit 0), then delete
   the local branch with `git branch -d feat/frontend-phase5`.
5. Do **not** pull or merge into the main working tree while it has uncommitted changes
   from other sessions. Tell the user that `main` on GitHub moved and that the main
   tree's untracked copy of this plan file and its uncommitted `WORK_LOG.md` /
   `IMPLEMENTATION_PLAN.md` edits must be reconciled before `git pull`.
6. Report: PR URL, merge commit ID, CI result, local check results, and that the remote
   branch, local branch and worktree are deleted.

## Tasks

### F0 - Baseline, branch and worktree

- Goal: know the starting state and set up the isolated branch.
- Steps (from the main repository folder):
  1. `git fetch origin` then
     `git worktree add C:\Nagdy\Mustafa\Work\Upwork\lumaquote-frontend -b feat/frontend-phase5 origin/main`.
  2. In the worktree: `npm ci`; `py -3.12 -m venv .venv` (Python 3.12, same as CI and the main `.venv`);
     `.venv\Scripts\python -m pip install -r requirements.lock.txt` (the npm scripts use
     the worktree's own `.venv` through `scripts/python.cjs`).
  3. Copy `.env.local` from the main repository folder into the worktree with `cp`.
     Never print, cat or diff it (R13, D13). Do not copy `.env` unless a check fails for a
     missing provider setting; paid flags stay off.
  4. Local Supabase is one shared instance. If `npx supabase status` already shows it
     running, do not start or stop it from the worktree.
  5. Copy this plan file from the main repository folder into the worktree's
     `docs/proposals/`, add the phase 5 link line to `docs/IMPLEMENTATION_PLAN.md`, the
     D39 and D40 rows to `docs/DECISIONS.md` and a work-log entry, run `npm run check:rules`, and
     commit them as `docs: add frontend phase 5 work plan`. (The main tree already has
     these edits uncommitted; the worktree starts from `origin/main` without them.)
  6. Run the four standard checks in the worktree and note pass/fail counts.
- Done when: the worktree builds, the plan commit exists, and the counts are recorded in
  the F1 work-log entry's "Checked" line. If any baseline check already fails on a clean
  `origin/main`, record it in the work log and the PR body as a pre-existing failure, do
  not count it against this plan, and continue; fix it only if a later task touches the
  failing area.

### F1 - Truthful copy and a not-found route (G2, G8)

- Lead skill: `frontend-structure`.
- Files: `features/integrations/ConnectionsPage.tsx`, new
  `features/not-found/NotFoundPage.tsx`, `app/App.tsx`, `docs/reference/FRONTEND.md`.
- Steps:
  1. Read `docs/reference/GOOGLE_SYNC.md` and `gas/README.md`. Replace the Google card
     copy: no "OAuth", no backend Google client. Say Apps Script sends signed snapshots
     after edits and on an approximately one-minute timer; Drive export of the
     approved PDF runs through Apps Script and has not run in Google yet. Keep the
     server status badge (`data.integrations`) as the only status source.
  2. Check the WhatsApp and LangSmith cards against `docs/reference/WHATSAPP.md` and
     decision D24 the same way; change only statements that are false.
  3. Create `NotFoundPage`: page heading "This page does not exist.", one sentence,
     a button link to `/` and one to `/inbox`. Use existing `page-heading` and
     `Button` styles; no new CSS file unless needed.
  4. In `App.tsx` route `*` to `NotFoundPage` instead of `Overview`.
- Done when: no "OAuth" string remains in `app/frontend/src` (check with grep);
  `/does-not-exist` shows the new page inside the shell; FRONTEND.md's legacy-copy
  paragraph is replaced with the current statement and the routes paragraph names
  the not-found page.
- Checks: standard four.

### F2 - Authenticated live updates over SSE (G1)

- Lead skill: `frontend-structure`; supporting `secure-quotation-app`.
- Facts to rely on (verified 2026-11-03): `GET /api/events` requires the bearer header
  (`HTTPBearer` in `core/http.py`), so the browser `EventSource` API cannot be used.
  The stream sends `event: refresh` with `data: {"revision": <int>}` every ~3 s,
  `event: revoked` when membership fails, and closes after 30 events (~90 s).
- Files: new `shared/api/events.ts`, new `shared/api/events.test.ts`, new
  `features/workspace/useLiveUpdates.ts`, `features/workspace/api.ts`,
  `features/conversations/api.ts`, `app/AppShell.tsx`, `docs/reference/FRONTEND.md`,
  one new diagram `docs/diagrams/frontend-live-updates.mmd`.
- Steps:
  1. `shared/api/events.ts`: export `parseEventStream(chunk, buffer)` (pure: splits
     on blank lines, returns `{events: {event, data}[], rest}`) and
     `openEventStream({ path, token, signal, onEvent })` that calls `fetch` with
     `Authorization: Bearer <token>` and `Accept: text/event-stream`, reads
     `response.body` with a `TextDecoder`, and resolves when the stream ends. It must
     not log the token or event data. Non-2xx rejects with `ApiError(message, status)`
     from `shared/api/client.ts`.
  2. `features/workspace/useLiveUpdates.ts`: a hook that, while a session exists,
     loops: open the stream; on `refresh` whose `revision` differs from the last seen
     value, call `queryClient.invalidateQueries({ queryKey: ["workspace"] })` and
     `({ queryKey: ["conversation"] })`; on `revoked`, sign out through
     `shared/auth/client`; on normal end, reconnect after 1 s; on error, reconnect with
     backoff 2 s, 4 s, 8 s ... capped at 30 s; abort on unmount or session change.
     Return `{ connected: boolean }`.
  3. Keep polling as the fallback but slow it while connected: pass `connected` into
     `useWorkspace` and `useConversation` and use `refetchInterval: connected ? 30000 : <current>`.
     Do not remove polling.
  4. Call `useLiveUpdates()` once in `AppShell`. Show the state in the topbar next to
     "Local workspace": "Live" when connected, "Refreshing every few seconds" when not.
     Text label, not color alone (Textual State Rule in DESIGN.md).
  5. Reconnect rate: one stream per ~90 s is far under the 120 reads/min limit; do not
     open more than one stream per tab.
- Tests (`events.test.ts`, Vitest): parser handles split chunks, multiple events in one
  chunk, CRLF and LF, and ignores comment lines; the hook invalidates only on a changed
  revision and stops after unmount (mock `fetch` with a `ReadableStream`).
- Done when: with `npm run dev:api` and `npm run dev:ui` running, a change made through
  a second tab appears in the first tab within ~5 s without waiting for polling; the
  network panel shows one `/api/events` request per ~90 s; the diagram renders.
- Checks: standard four, plus `npm run diagrams:render` and `npm run diagrams:check`;
  open the SVG and confirm no clipped labels.

### F3 - Show real job state (G3)

- Lead skill: `frontend-structure`.
- Facts: `workspace.jobs` holds the 20 newest jobs as
  `{id, conversation_id, kind: "agent"|"drive_export", status: "queued"|"running"|"done"|"failed"|"blocked", error_code}`.
  There is no timestamp and no progress percentage; do not invent either.
- Files: new `features/conversations/JobState.tsx`, `ConversationThread.tsx`,
  `shared/ui/status.tsx` (labels only), `features/overview/Overview.tsx`,
  `conversations.css`, FRONTEND.md.
- Steps:
  1. `JobState` takes the jobs for one conversation (filter in `InboxPage` from
     `data.jobs` and pass down; `ConversationThread` does not read workspace context
     itself today, keep it that way). Show only the newest agent job when its status is
     `queued`, `running`, `failed` or `blocked`: "Assistant is working" (running),
     "Assistant queued" (queued), "Assistant stopped: <error_code with _ as spaces>"
     (failed/blocked). Render nothing for `done`.
  2. Use `role="status"` and the existing `Status` badge. A spinner icon is allowed only
     for `running` and must stop under `prefers-reduced-motion`.
  3. Add labels to `status.tsx` for `running` ("Running") and `done` ("Done").
  4. Overview: add one metric "Assistant jobs running" counting `running` jobs. Keep the
     existing honest-count wording.
- Tests: Vitest for `JobState` (each status, `done` renders nothing, error code text).
- Done when: a conversation with a queued agent job shows the state line; FRONTEND.md
  documents that the list is bounded to 20 jobs and carries no timing.
- Checks: standard four.

### F4 - Voice-note waveform player (G4)

- Lead skill: `frontend-design`; supporting `frontend-structure`. Read
  `docs/reference/MEDIA.md` first.
- Files: new `features/conversations/AudioWaveform.tsx`, new
  `features/conversations/waveform.ts` (pure peak computation), new
  `features/conversations/waveform.test.ts`, `MediaPreview.tsx`, `conversations.css`,
  `docs/reference/MEDIA.md`, FRONTEND.md.
- Steps:
  1. `waveform.ts`: `computePeaks(channel: Float32Array, buckets: number): number[]`
     returning 0..1 peak per bucket. Pure, no DOM.
  2. `AudioWaveform` receives the already-authorized blob URL that `MediaPreview`
     creates (do not fetch again, do not create a second object URL). Decode with
     `AudioContext.decodeAudioData` on the fetched bytes, compute 64 peaks, draw bars in
     an inline SVG (copper for played part, mineral for remaining). Close the
     `AudioContext` after decoding.
  3. Keep the native `<audio controls>` element as the accessible control; the waveform
     is `aria-hidden="true"` and clicking it seeks (mouse only, keyboard seeks through
     the native control). Show elapsed / total time as text.
  4. If decoding fails or `AudioContext` is missing, render nothing extra; playback
     still works. Respect reduced motion: no animated transitions on the progress bars.
  5. Capture mode still hides media entirely (existing rule); do not change that.
- Tests: `computePeaks` on silence, a single spike and fewer samples than buckets.
- Done when: a local-test voice note shows bars and the played part follows playback;
  the blob URL is revoked exactly once (existing `MediaPreview` lifecycle unchanged).
- Checks: standard four.

### F5 - Explicit approval confirmation (G5)

- Lead skill: `implement-human-approval`; supporting `frontend-structure`.
- Files: `features/quotations/ui/ReviewActions.tsx`, new
  `features/quotations/ui/ReviewActions.test.tsx`, `quotations.css`, FRONTEND.md.
- Steps:
  1. Replace the single "Approve & queue delivery" click with an inline two-step
     control (no `window.confirm`, no browser dialog): step 1 button "Review approval";
     step 2 shows a panel restating quote number, revision, customer (or "this customer"
     in capture mode), server total via `money(quote.content.total)` and channel, with
     buttons "Approve revision N & queue delivery" and "Cancel".
  2. Move keyboard focus to the step-2 panel heading when it opens and back to the
     "Review approval" button on Cancel. `Escape` cancels.
  3. If the displayed `quote.revision` or `quote.id` changes while step 2 is open,
     close step 2 and show "This quotation changed. Review the new revision." The
     decision payload still sends `expected_revision: quote.revision` (unchanged).
  4. Keep the existing disabled rules (pending, owner is staff).
- Tests: step 2 shows the server total string; approve calls `onDecide("approve")`
  once; a revision change closes step 2; Escape and Cancel close without a call.
- Browser test impact (verified 2026-11-03): `tests/browser/manual-workflow.cjs` lines
  98, 107 and 131 use the button name `Approve & queue delivery`. Update them: the
  disabled/enabled checks (98, 107) move to "Review approval"; the click (131) becomes
  "Review approval" then "Approve revision N & queue delivery". Change nothing else in
  that file and list the edit in the work log.
- Done when: the browser workflow test passes with those selector changes only.
- Checks: standard four, then `npm run test:browser`.

### F6 - Portrait inbox with a section switcher (G6)

- Lead skill: `frontend-design`; supporting `impeccable`.
- Files: `features/conversations/InboxPage.tsx`, `conversations.css`,
  `quotations.css`, FRONTEND.md.
- Steps:
  1. At `max-width: 680px` only, show a two-option segmented control under the
     conversation list: "Conversation" and "Quotation" (use `shared/ui/toggle-group`).
     Selection is local state in `InboxPage`, default "Conversation", reset when the
     selected conversation changes.
  2. Hide the unselected panel with CSS at that width only; above 680 px the three
     columns stay exactly as now. Both panels stay mounted so quotation draft state is
     not lost when switching.
  3. When a quote is in `review`, show a small "Needs approval" badge on the
     "Quotation" option so the approval is discoverable.
- Done when: at 390 x 844 there is no horizontal overflow, the approval button is
  reachable in one tap from the conversation view, and desktop layout is pixel-unchanged
  (compare screenshots at 1440 x 1050 before and after).
- Checks: standard four, then `npm run test:browser`.

### F7 - Capture-mode body masking (G7)

- Lead skill: `secure-quotation-app`; supporting `frontend-structure`.
- Files: new `shared/lib/mask.ts`, new `shared/lib/mask.test.ts`,
  `features/conversations/ConversationThread.tsx`, `ConversationComposer.tsx` (only if
  it renders recipient values), `features/quotations/QuotationsPage.tsx` (check),
  FRONTEND.md.
- Steps:
  1. `maskForCapture(text)`: replace emails with `[email]`, phone-like sequences
     (`+` and 8-15 digits with spaces, dashes, dots or brackets; bare 10-15 digit runs)
     with `[phone]`. Reuse the regexes in `tests/browser/scene-review.cjs` `PRIVATE` as
     the reference so the review script and the mask agree. Do not mask SKUs
     (`AB-123`), prices, quantities or dates.
  2. Apply it to message bodies and delivery previews only when `capture` is true.
     Never mask in normal mode; staff need the real text.
  3. Grep the frontend for `recipient`; make sure it never renders in capture mode.
- Tests: emails, international and local phone formats, SKU/price/date untouched.
- Done when: FRONTEND.md states exactly what capture mode masks and what it still does
  not (PDF content, media is hidden not masked).
- Checks: standard four.

### F8 - Whole-app visual and accessibility review with evidence (G9)

- Lead skill: `verify-and-review`; supporting `project-documentation`.
- Files: new `tests/browser/ui-review.cjs`, new `tests/integration/test_ui_review.py`
  (copy the pattern of `tests/integration/test_scene_review.py` and `run_review` from
  `browser_servers`), new `docs/evidence/ui-review-<date>.json`,
  `docs/reference/TOOLING_AND_TESTS.md`, FRONTEND.md.
- Steps:
  1. Script signs in like `scene-review.cjs`, then for each route `/`, `/inbox`,
     `/quotations`, `/catalog`, `/integrations`, `/requests/new`, `/does-not-exist`
     and each viewport 1440 x 1050 and 390 x 844: run axe (ids and impact only), check
     horizontal overflow, save a screenshot under `.local/ui-review/` (ignored path),
     and with capture mode on scan visible text against the `PRIVATE` patterns.
  2. Keyboard pass on `/inbox` desktop: Tab from the skip link reaches the conversation
     list, the composer and the approval control; record the count of Tab presses.
  3. Collect console errors and page errors.
  4. The pytest wrapper asserts zero axe violations, no overflow, no privacy matches,
     no console errors. Mark it `@pytest.mark.browser`.
  5. Write the evidence file with the common header (`date`, `commit`, `label:
     "local-substitute"` because it is headless Chromium with software WebGL,
     `command`, `result`).
  6. Look at every screenshot yourself. List anything clipped, overlapping or
     misleading in the work log, and fix only issues inside this plan's scope.
- Done when: the test passes and the evidence file exists. Then, and only then, update
  phase 5 item 4 status line in IMPLEMENTATION_PLAN.md with the evidence link. Tick the
  item only if desktop/portrait/accessibility/performance are all covered; performance
  needs a measured number (for example Navigation Timing `domContentLoaded` and LCP from
  `PerformanceObserver` per route), otherwise leave it unticked and say what is missing.
- Checks: `npm run test:browser` plus the new test (`node scripts/python.cjs -m pytest tests/integration/test_ui_review.py -q`).

### F9 - Close-out

- Steps: `npm run graph:update` (modules were added, D33); `npm run verify:full` once on
  the final tree (R12; report partial if memory pressure stops it, as on 2026-11-02);
  update `docs/SHOWCASE_SHOT_LIST.md` shot 6 and 8 wording if the approval or portrait
  UI changed; final work-log entry; commit `docs: close out frontend phase 5 plan`.
- Then follow "Merge gate" and "Merge and clean up" above, using the
  `contribution-workflow` skill. If a gate item fails, work it through the blocker ladder
  first; do not merge while any gate item fails, and end only in one of the two end
  states in "Run to completion".

## Acceptance for the whole plan

- Every gap G1-G9 is either closed with a test or evidence, or listed as open in the
  work log with the reason.
- No browser-side money calculation, no optimistic approval or delivery, no token or
  event data in logs.
- Desktop layout unchanged except where a task says otherwise.
- `npm run verify:full` result reported exactly (R12).
- The PR is merged into `main` with a merge commit, and the remote branch, local branch
  and worktree are deleted; or, if a gate failed, the PR stays open and the reason is
  reported.

## Open questions for the user (not blocking any task; use the stated default)

1. Should the Overview hero copy ("Good conversations. Brilliant outcomes.") stay, or
   be replaced with plainer product copy? This plan leaves it unchanged.
2. After F2, keep the 30-second fallback polling, or remove polling once SSE has been
   stable? This plan keeps it.
