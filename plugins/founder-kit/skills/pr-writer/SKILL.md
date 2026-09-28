---
name: pr-writer
description: "Generates pull request titles and bodies that a reviewer and CI accept on the first try: conventional-commit title, filled template, real test evidence, and a working Closes link. Use when opening any PR, when asked to 'write the PR', 'write the PR description', 'open a PR for this branch', or 'summarize these changes for review', and when a PR check goes red for body, template, or issue-linkage reasons rather than code reasons."
---

# pr-writer: PR bodies that pass first time

Most PRs that bounce do so for shape, not substance: no linked issue, a gutted
template, a test checkbox ticked with nothing behind it, a title that reads `fix`. All
of it is mechanical, so generate it mechanically.

## Gather these four things first

1. **Issue number(s)** this PR closes. If there is no issue, stop and use the
   `ship-flow` skill; a PR with nothing to close is untraceable a month from now.
2. **A diff summary in reviewer language.** Read the whole diff first
   (`git diff origin/main...HEAD`). Do not write the summary from the commit subjects;
   they describe intent, the diff describes reality.
3. **Local test evidence:** the exact command you ran and the exact result line. Not
   "tests pass". A docs-only PR states why no suite applies.
4. **Change type:** fix, feature, breaking, chore, or docs.

If your repo has `.github/pull_request_template.md`, its sections win over the template
below; map the same content into its headings.

## Title

```
<type>(<scope>): <imperative summary of what changed where> (#42)
```

- Types: `feat` `fix` `chore` `refactor` `test` `docs` `perf` `ci`.
- Scope is the area of the codebase: `auth` `billing` `api` `db` `ui` `deploy`.
- 72 characters or fewer, imperative mood, no trailing period.
- It becomes the squash-commit subject on `main`, so it has to still make sense as a
  standalone line in `git log` a year from now.

| Bad | Why | Good |
|---|---|---|
| `fix bug` | Says nothing; unreadable in history | `fix(auth): normalize email before magic-link lookup (#42)` |
| `Updates` | No type, no scope, no content | `chore(deps): upgrade the framework to 15.2.1 (#61)` |
| `WIP` | Not mergeable; open a draft instead | `feat(billing): add annual plan toggle to checkout (#57)` |

## Body template

Write it to a file, then pass `--body-file`. Passing `--body "a\nb"` writes a literal
backslash-n and the whole body renders as one line.

```markdown
## Summary
Two or three sentences: what this PR does and why now. No filler, no restating the
title. A reviewer should be able to decide from this paragraph alone what to look at
hardest.

## Changes
- `lib/auth/email.ts`: new `normalizeEmail`, the single place addresses are canonicalized
- `app/api/auth/magic-link/route.ts`: normalize before the token lookup
- `lib/auth/email.test.ts`: new, covers plus tags, casing, and whitespace

## Testing
- `pnpm test lib/auth` -> `14 passed, 0 failed`
- `pnpm lint && pnpm typecheck` -> clean
- `pnpm build` -> succeeded
- Preview deploy: signed in with `me+test@example.com`, link worked, session created

## Risk and rollback
Additive; no schema change. Revert this PR to roll back.

## Screenshots
<!-- UI changes only. Before and after, or delete this section. -->

Closes #42
```

Rules for the sections:

- **Summary** answers "why" as well as "what". A reviewer who understands the motive
  reviews the design; one who only sees the change reviews the syntax.
- **Changes** is per file or per module, one line each, phrased as what a reader will
  find there. Skip mechanical noise (lockfile churn, generated files) with a single
  line saying you skipped it.
- **Testing** is pasted evidence, not a claim. If you did not run it, do not list it.
- **Risk and rollback** matters most for the PRs people merge fastest: migrations,
  auth, billing, anything that deletes. One sentence is enough; the value is having
  thought about it.
- **Closes** must use `Closes`, `Fixes`, or `Resolves` plus `#N`, one line per issue.
  `Refs #42`, `Part of #42`, and a bare `#42` do not close anything.

## Honesty rules

These are the difference between a checklist that means something and theatre.

- **An unchecked box stays unchecked.** It is a to-do list, not a formality. Leaving
  "all tests pass" unticked until CI is green is correct behavior, not an omission.
- **Never tick a box for work you did not do.** A ticked, false box is worse than a
  missing section: it actively misleads the one person who would have caught the bug.
- **N/A gets annotated, never silently ticked:** `- [ ] Tests added (N/A: docs only)`.
- **Never claim a test result you did not see.** Copy the terminal line. If the suite
  did not run because of an unrelated breakage, say that explicitly in Testing.
- **Declare spec changes.** If the diff edits an existing test's expectations, the body
  says which test, what the new expected behavior is, and why the old one was wrong.
  Otherwise it reads as making a red test green.

## Pre-flight check, before `gh pr create`

```bash
BODY=/tmp/pr-body.md          # write the body here first

grep -qiE '(closes|fixes|resolves) #[0-9]+' "$BODY" \
  && echo "linkage: OK" || { echo "FAIL: no Closes/Fixes/Resolves #N"; exit 1; }

for s in '## Summary' '## Changes' '## Testing'; do
  grep -q "$s" "$BODY" || echo "MISSING SECTION: $s"
done

# every linked issue exists and is open
for N in $(grep -oiE '(closes|fixes|resolves) #[0-9]+' "$BODY" | grep -oE '[0-9]+'); do
  gh issue view "$N" --json number,state --jq '"#\(.number) \(.state)"' \
    || echo "FAIL: #$N does not exist"
done

# the branch is not behind its base
git fetch origin main
git log --oneline origin/main ^HEAD | head -1 | grep -q . \
  && echo "WARNING: behind origin/main; merge it before opening the PR"
```

Then open it:

```bash
gh pr create --base main --head "$(git branch --show-current)" \
  --title "fix(auth): normalize email before magic-link lookup (#42)" \
  --body-file "$BODY"
gh pr checks --watch
```

## When a check is already red for body reasons

1. Fix the body in the file, then push it up: `gh pr edit <n> --body-file /tmp/pr-body.md`.
2. **Re-running the failed job will not pick up the new body.** A rerun replays the
   original webhook payload, which still carries the old text. Fire a fresh event:
   `git commit --allow-empty -m "ci: retrigger checks (#42)" && git push`.
3. Re-check with `gh pr checks <n>`.
4. If the failure is a missing linked issue, create the issue first and post its plan
   comment, then edit the body. Never delete the failing check to get green.
