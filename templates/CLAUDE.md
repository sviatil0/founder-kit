# <Project name>

Project conventions for Claude Code. This file loads automatically in every session from this
repo, so keep it short and true; a stale `CLAUDE.md` is worse than none. Replace every
`<placeholder>` and delete any line that does not apply to you.

## What this is

<One or two sentences: what the product does and who uses it. If Claude has to guess the
domain, it guesses wrong.>

## Stack

| Layer | Choice |
|---|---|
| Framework | <Next.js App Router, TypeScript strict> |
| Database | <Supabase Postgres> |
| Auth | <Supabase Auth> |
| Styling | <Tailwind + shadcn/ui> |
| Hosting | <Vercel> |
| Package manager | <pnpm> |
| Tests | <Vitest for units, Playwright for the critical path> |

Do not introduce a second library for a job one of the above already does. If something here
is genuinely the wrong tool, say so and propose the swap before writing code against it.

## Commands

```bash
<pnpm install>          # install
<pnpm dev>              # local dev server
<pnpm build>            # production build, must pass before any PR
<pnpm test>             # unit tests
<pnpm lint>             # lint and typecheck
<pnpm exec playwright test>   # end-to-end, critical path only
```

Database and deploy:

```bash
<supabase migration new my_change>   # new migration
<supabase db push>                   # apply migrations
<vercel --prod>                      # production deploy, or let git push do it
```

## The three rules

These are not style preferences. Breaking one of them is a bug.

1. **Never commit or push to `main`.** Work happens on `<feat|fix>/<issue-number>-<slug>`
   branches that land through a pull request. If you find yourself on `main` with changes,
   branch first.
2. **Validate at every boundary.** Anything crossing into the app from outside (route
   handlers, server actions, forms, webhooks, third-party responses) gets parsed with a schema
   before it is used. Never trust a request body, a query param, or an API response's shape.
3. **No secrets in code.** Keys live in env vars, `.env.local` stays gitignored, deploy-time
   secrets live in the host's env settings. Never print a secret, never commit one, never
   send a service-role key to the browser.

## How to work here

Before writing code for anything bigger than a typo, invoke these two skills:

- **`ship-flow`** for process: open an issue, post the plan on it, branch, small conventional
  commits, PR that closes the issue, squash merge. The issue trail is this project's memory.
- **`engineering-standards`** for the code itself: module boundaries, schema validation, row
  level security on every table, expand-then-contract migrations, no `useEffect` for derived
  state or data fetching, structured logging, real tests.

When the PR is ready, invoke **`pr-writer`** for the title and body. Paste the actual test
command and its actual output; never claim a check you did not run, and leave a checklist box
unchecked if it is not done.

## Definition of done

A change is done when: tests pass locally, lint and typecheck pass, the build succeeds, the
preview deploy was opened and the changed path clicked through, and the PR closes its issue.
Not when the code compiles.

## Project-specific notes

<Anything Claude keeps getting wrong: a gotcha in the data model, a naming convention, a
directory that is generated and must not be hand-edited, a service that is flaky in local dev.
Add lines here as you hit them; delete them when they stop being true.>
