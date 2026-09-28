---
name: ship-flow
description: "Enforces the issue then plan then branch then PR then merge loop for a 1-3 person startup shipping on GitHub, using gh commands. Keeps every change traceable so a fresh session, or a cofounder, can pick the work back up. Use when starting any feature, bug, or refactor; when about to write code that has no tracked issue; when creating a branch or opening a pull request; when asked to 'just quickly add this', 'how should I ship this', 'open a PR for this', 'what is our dev workflow', or 'can you fix this real quick'."
---

# ship-flow: how a small team ships

A two-person startup does not need a process org. It needs one loop, followed every
time, so no change is untraceable and no context lives only in someone's head:
**issue, plan, branch, commits, PR, merge.** All `gh` and `git`, nothing to install.

## Why bother when it is just you

1. **The issue trail is the memory.** Your agent's context window ends at the end of
   this session. The issue does not. Six weeks from now the only record of why the
   auth flow works the way it does is the issue and the plan comment on it.
2. **A written plan is the only thing a reviewer can check the diff against.** Without
   it, review degrades into "does this look plausible", which catches nothing.
3. **A scoped issue produces a scoped diff, and a scoped diff merges today.** Most
   unshipped work is a branch that grew until nobody wanted to read it.

Skip the loop for genuinely trivial things (a typo in a comment, a version bump) and
say out loud that you are skipping it. Skipping it silently is how the habit dies.

## Step 1: an issue exists before any code

No issue, no work. Write it before you open the editor, even if you write it and
implement it in the same ten minutes.

```bash
ISSUE_URL=$(gh issue create \
  --title "Magic-link sign-in fails for addresses with a plus tag" \
  --label bug \
  --body "$(cat <<'EOF'
## Problem
Sign-in with an address like `me+test@example.com` returns a 400. The plus is being
dropped before the token lookup, so the token never matches.

## Acceptance criteria
- [ ] A plus-tagged address receives a working magic link
- [ ] A regression test covers the plus-tag case
- [ ] Existing sign-in behavior is unchanged

## Out of scope
Rate limiting on the sign-in endpoint (separate issue).
EOF
)")
ISSUE_NUM=${ISSUE_URL##*/}
echo "opened #$ISSUE_NUM"
```

Use a heredoc for the body. Passing `--body "line one\nline two"` writes a literal
backslash-n and the issue renders as one mangled line.

**Every issue carries:** a problem statement, acceptance criteria a reviewer can
actually verify, and what is explicitly out of scope. **Sizing rule:** if the
acceptance criteria will not fit in roughly five checkboxes, it is two issues. Split
it before you start, not after the diff gets ugly.

If you keep a GitHub Project board, add it and let it land in your backlog column:

```bash
gh project item-add <project-number> --owner <your-login-or-org> --url "$ISSUE_URL"
```

## Step 2: post the plan on the issue, then write code

Before the first file edit, post the approach as an issue comment. This is the gate
that makes the rest of the loop worth anything.

```bash
gh issue comment "$ISSUE_NUM" --body "$(cat <<'EOF'
## Implementation Plan

**Approach:** Normalize the address once, at the edge, and look tokens up by the
normalized form. Rejected normalizing at every call site: that fails the moment one
new call site forgets.

**Files**
- `lib/auth/email.ts`: add `normalizeEmail`, single source of truth
- `app/api/auth/magic-link/route.ts`: normalize before the token lookup
- `lib/auth/email.test.ts`: new

**Tests**
- Plus-tag address round-trips (the failing reproduction; it goes red first)
- Uppercase and trailing-whitespace addresses; a plain address is unchanged

**Acceptance criteria mapping**
- Working link for a plus-tagged address: the round-trip test
- Regression test exists: `email.test.ts`; existing behavior: the plain-address case

**Risks:** nothing stored raw yet, so no backfill. Check that before assuming.
EOF
)"
```

Scale the depth to the change: a one-line fix gets a two-line plan; anything touching
auth, money, migrations, or deletion gets the full template plus a risk paragraph.

**If reality contradicts the plan mid-build, post a follow-up comment saying what
changed and why.** Otherwise the reviewer is comparing the diff against fiction.

For a bug, the first test is a **failing reproduction**: it goes red, you fix the code
until it goes green, and it stays as the permanent regression guard.

## Step 3: branch off main

```bash
git fetch origin main
git switch main
git pull --ff-only
git switch -c "fix/$ISSUE_NUM-plus-tagged-email"
git push -u origin HEAD

gh issue comment "$ISSUE_NUM" --body "Branch: \`fix/$ISSUE_NUM-plus-tagged-email\`. Starting."
```

**Naming:** `<type>/<issue-number>-<slug>`, types `feat` `fix` `chore` `refactor`
`docs` `test` `perf` `ci`. The issue number in the branch name means `git branch` alone
tells you what every branch is for.

If your repo keeps a long-lived integration branch, substitute it for `main` here and
in the PR base. The invariant holds: **never commit to the branch that deploys prod.**

## Step 4: commit small, in conventional form

```
<type>(<scope>): <what changed where> (#42)
```

```bash
git add lib/auth/email.ts lib/auth/email.test.ts   # never a blind `git add .`
git diff --cached                                   # read what you are about to ship
git commit -m "fix(auth): normalize email before magic-link token lookup (#42)"
```

Commit at every working state: a function that behaves, a test that passes, a
component that renders. Dense history is what lets `git bisect` find the break.

- **If the subject needs the word "and", it is two commits.**
- Subject says what changed where. `fix`, `update`, `wip`, `changes`, and `stuff` say
  nothing and will read as noise in the squash message.
- Body only when the "why" is not obvious from the diff. Blank line first, wrap at 72.
- No secrets, no `.env` values, no generated artifacts in the diff.

Keeping current with `main` while you work:

```bash
git fetch origin main
git merge origin/main     # resolve conflicts here, not in the PR
git push
```

Merge rather than rebase once a branch is pushed and CI, a reviewer, or a preview
deploy has seen it. Rebasing a branch nobody has fetched is fine.

## Step 5: the gates, run locally, before the PR exists

Run the real commands and keep the output; the PR body will quote it.

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build          # the check that catches what unit tests do not
```

Substitute your own commands; the point is that they are the same ones CI runs and
that you ran them. A green badge on a PR you never ran locally is a claim, not evidence.

**Never weaken, skip, or delete a test to get green.** A red test means the code is
wrong until proven otherwise. Changing a test is legitimate only as a deliberate spec
change that you call out in the PR body.

## Step 6: open the PR; the PR closes the issue

Use the `pr-writer` skill for the title and body. The one mechanical requirement:

```
Closes #42
```

GitHub auto-closes only on `closes`, `fixes`, or `resolves` plus `#N`. `Refs #42`,
`Part of #42`, and a bare `#42` close nothing; the issue is still open a month later.

```bash
gh pr create --base main --head "$(git branch --show-current)" \
  --title "fix(auth): normalize email before magic-link token lookup (#42)" \
  --body-file /tmp/pr-body.md

gh pr checks --watch        # then open the preview URL and click the changed path
```

## Step 7: squash merge, delete the branch

```bash
gh pr merge --squash --delete-branch
git switch main && git pull --ff-only
git branch -d "fix/42-plus-tagged-email"
```

Squash keeps `main` at one commit per change, which is what makes it bisectable and
readable as a changelog. The `Closes #42` line closes the issue on merge; confirm it did.

## Red flags: stop and correct

| Situation | Required action |
|---|---|
| About to commit on `main` | Stop. Branch first, even for a one-liner. |
| About to write code with no issue | Stop. Open the issue (step 1). |
| About to write code with no plan comment on the issue | Stop. Post the plan (step 2). |
| Diff is over roughly 400 changed lines | Split the PR. Nobody reviews a 1,200-line diff; they skim it and approve. |
| PR body has no `Closes #N` | Edit the body before merging, or the issue stays open forever. |
| Commit subject is `fix`, `wip`, `update`, or `changes` | Rewrite it. It becomes the squash-commit subject on `main`. |
| Tempted to edit a test so it passes | Stop. Fix the code, or declare the spec change in the PR. |
| About to `git push --force` to `main` or a shared branch | Never. |
| A secret, key, or `.env` value appears in `git diff --cached` | Unstage it, rotate the key if it was ever pushed, add the path to `.gitignore`. |
| Work is stuck and you are quietly moving on | Comment `Blocked: <reason>. Waiting on <who or what>.` on the issue and label it `blocked`. Silent blockage is the one failure that compounds. |
| Unrelated changes in the same working tree | Stage and commit them separately. |

## Who reviews when you are the only engineer

On a team of one, the reviewer cannot be you five minutes later; you will read what
you meant, not what you wrote. In descending order of strength:

1. **A fresh session.** Run `/code-review`, or open a new session with nothing but the
   diff and the issue, and ask one question: where does the diff differ from what the
   plan promised? A context-free reader catches what the author structurally cannot.
2. **A different model for the second pass.** Cheap, and it disagrees in useful places.
3. **A delay.** Anything touching auth, billing, migrations, or data deletion sits
   overnight before it merges. Most bad merges are the ones made at speed.

Never approve and merge in the same minute as the final commit. On a team of two or
three the other person reviews, one reviewer only, and the metric to watch is review
latency: a day of waiting is what pushes people back toward committing on `main`.

Open the PR even when nobody else will read it: it is a durable, diffable,
commentable record of one change. A direct push to `main` is none of those.

## Definition of done

A change is not done until all of these are true. This is the checklist to read before
you merge, not after.

- [ ] Tests pass locally, including a new test for the behavior you added or fixed
- [ ] Lint, typecheck, and build all pass locally, not just in CI
- [ ] The preview deployment was opened and the changed path was actually exercised
- [ ] Every acceptance criterion on the issue is verified, one by one
- [ ] README, env-var docs, and setup instructions updated in the same PR if affected
- [ ] Dead code deleted, not commented out; git history is the backup
- [ ] No secret, key, or credential added to the repo
- [ ] `Closes #N` in the PR body, and the issue actually closed on merge
- [ ] Board card moved, if you keep a board
