# Branch protection settings

Apply identical rules to both `main` and `dev`. The differences are the merge strategy and which branches can target them — both are configured at the repo level, not the protection level.

## Required settings

Configure under **Settings → Branches → Add branch protection rule** in the GitHub UI, or via `gh api` (snippet at the bottom).

### Rule pattern

Create **two rules**, one for each branch:

- Pattern: `main`
- Pattern: `dev`

### Required for both `main` and `dev`

- [x] **Require a pull request before merging**
  - [x] Require approvals — **1**
  - [x] Dismiss stale pull request approvals when new commits are pushed
  - [x] Require review from Code Owners
  - [x] Require approval of the most recent reviewable push
- [x] **Require status checks to pass before merging**
  - [x] Require branches to be up to date before merging
  - Required checks (minimum):
    - `lint`
    - `format`
    - `typecheck`
    - `test`
- [x] **Require conversation resolution before merging**
- [x] **Require linear history**
- [x] **Do not allow bypassing the above settings** (no admin overrides)
- [x] **Restrict who can push to matching branches** → no users / teams (i.e. force PR-only)

### Disabled for both

- [ ] Allow force pushes — **off**
- [ ] Allow deletions — **off**

## Repo-level settings (Settings → General)

- **Default branch**: `dev`
- **Allowed merge methods**:
  - [x] Allow squash merging — **default** (used for `dev` and hotfix → `main`)
  - [x] Allow merge commits — used **only** for `dev` → `main` promotion PRs
  - [ ] Allow rebase merging — **off** (rewrites SHAs, breaks external linkbacks)
- **Squash commit message**: "Pull request title and description"
- **Automatically delete head branches**: **on** (housekeeping)

## Apply via `gh api` (one-shot script)

Replace `OWNER/REPO` and run from a shell with `gh` authenticated as a repo admin.

```bash
REPO="OWNER/REPO"

for BRANCH in main dev; do
  gh api --method PUT \
    "repos/${REPO}/branches/${BRANCH}/protection" \
    -H "Accept: application/vnd.github+json" \
    -f required_status_checks[strict]=true \
    -F required_status_checks[contexts][]=lint \
    -F required_status_checks[contexts][]=format \
    -F required_status_checks[contexts][]=typecheck \
    -F required_status_checks[contexts][]=test \
    -F enforce_admins=true \
    -F required_pull_request_reviews[required_approving_review_count]=1 \
    -F required_pull_request_reviews[dismiss_stale_reviews]=true \
    -F required_pull_request_reviews[require_code_owner_reviews]=true \
    -F restrictions= \
    -F required_linear_history=true \
    -F allow_force_pushes=false \
    -F allow_deletions=false \
    -F required_conversation_resolution=true
done
```

## Audit checklist

Quarterly, the DevOps lead verifies for each MIS repo:

- [ ] `main` and `dev` both protected with the rules above
- [ ] `dev` is the default branch
- [ ] No human or service account has push access bypassing protection
- [ ] CODEOWNERS is present and references current teams
- [ ] Required CI checks match the protection contexts (drift breaks merge silently)
