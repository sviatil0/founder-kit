# founder-kit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and publish `sviatil0/founder-kit`, a Claude Code plugin marketplace giving founders six genericized app-building skills plus a curated third-party ecosystem guide.

**Architecture:** Single repo, marketplace manifest at root pointing at one plugin at `plugins/founder-kit/`, six skill directories under `plugins/founder-kit/skills/`. Content tasks are independent (disjoint file paths) and run as parallel Opus 5 subagents; scaffold, verification, and publish are done by the orchestrator.

**Tech Stack:** Claude Code plugin/marketplace JSON manifests, Markdown SKILL.md files, Python 3 stdlib scripts (vendored), git + gh CLI.

**Spec:** `docs/superpowers/specs/2026-09-28-founder-kit-design.md` (same repo: read it first; the forbidden-strings list and skill table there govern every task).

## Global Constraints

- Forbidden strings (case-insensitive) in ANY shipped file: `soleksii`, `oleksiienko`, `sviatoslav`, `stefan`, `nd.edu`, `notre dame`, `x-fabric`, `desync`, `tweeds`, `clickup`, `innovation sprint`, `sprint lab`, `dnipro`, `questbridge`, `cal.com/`, `/Users/soleksii`, phone numbers. Exception: `sviatil0` only inside repo URLs.
- No em-dashes in any written output; use semicolons or commas.
- Every SKILL.md: YAML frontmatter with `name:` equal to its directory name and `description:` that starts with what it does and contains explicit "Use when" trigger phrases.
- Every credential dependency is an env var; the skill must include a "missing credential" branch that prints setup instructions and stops gracefully.
- Skills must not assume macOS except in clearly optional branches.
- Source skills live on this machine under `/Users/soleksii/.claude/skills/`; READ them, never modify them, and never copy their text verbatim where the spec says rewrite.
- Commit messages: Conventional Commits, ending with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>` (orchestrator commits; subagents do NOT commit).

## Review Focus

1. Founder invokes image-pipeline with no `GEMINI_API_KEY` set → expects printed setup steps and a graceful stop, not a retry loop (pinned in Task 5 verification).
2. Founder has no Granola → meeting-brief must work from a pasted or file transcript; Granola decrypt is an optional branch (pinned in Task 4 verification).
3. Marketplace/plugin name mismatch or wrong `source` path → install silently fails; names must all equal `founder-kit` and the source dir must contain `.claude-plugin/plugin.json` (pinned in Task 6 verification).
4. Personal-data leak in vendored assets (starter HTML, scripts, references) → forbidden-strings grep over every shipped byte, not just SKILL.md files (pinned in Task 6).
5. Descriptions too weak to trigger → each SKILL.md description must name at least three concrete user phrasings (pinned in per-task verification greps for `Use when`).

---

### Task 1: Scaffold (DONE, orchestrator)

**Files:** Created: `.claude-plugin/marketplace.json`, `plugins/founder-kit/.claude-plugin/plugin.json`, `LICENSE`, `docs/superpowers/specs/2026-09-28-founder-kit-design.md`, this plan.

- [x] **Step 1:** git init, directory tree, manifests, MIT license, spec, plan.
- [ ] **Step 2:** Commit: `chore: scaffold founder-kit marketplace, spec, plan`

### Task 2: ship-flow + pr-writer skills (Opus subagent A)

**Files:**
- Create: `plugins/founder-kit/skills/ship-flow/SKILL.md`
- Create: `plugins/founder-kit/skills/pr-writer/SKILL.md`
- Read-only sources: `/Users/soleksii/.claude/skills/desync-dev-flow/SKILL.md`, `/Users/soleksii/.claude/skills/tooling-workflow/SKILL.md`, `/Users/soleksii/.claude/skills/desync-pr-writer/SKILL.md`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: skill names `ship-flow`, `pr-writer` referenced by Task 6 README catalog.

- [ ] **Step 1: Write `ship-flow/SKILL.md`** (~150-250 lines). Frontmatter description: enforce issue → plan → branch → PR → merge for a 1-3 person startup; "Use when starting any feature, bug, or refactor; when about to write code with no tracked issue; when creating branches or opening PRs; when asked to 'just quickly add' something." Body sections, each with concrete `gh` commands: (1) Why: solo founders lose context, the issue trail IS the memory; (2) The loop: create issue (`gh issue create --title --body` with problem/acceptance criteria), post plan as issue comment before coding, branch `feat/<issue-num>-<slug>` off main, small conventional commits, PR closes issue, merge squash, delete branch; (3) Red flags table (committing to main, coding without issue, PR without plan, mega-PR > ~400 lines diff → split); (4) Scaling note: on a team of one the reviewer is a fresh Claude session or /code-review; (5) Definition of done: tests pass, lint passes, preview deploy checked, issue auto-closes.
- [ ] **Step 2: Write `pr-writer/SKILL.md`** (~80-150 lines). Description: "Generate PR titles and bodies that reviewers and CI accept first try. Use when opening any PR, when asked to 'write the PR', or when a PR check fails for body or linkage reasons." Body: title = conventional commit summary ≤ 72 chars; body template with `## Summary`, `## Changes`, `## Testing` (paste actual command + output, never claim untested things), `## Screenshots` (UI only), `Closes #<n>`; honesty rules (unchecked boxes stay unchecked); pre-flight: diff read end-to-end, tests actually run.
- [ ] **Step 3: Verify:** `grep -c 'Use when' both files` ≥ 1 each; forbidden-strings grep clean; frontmatter `name:` matches dirs.

### Task 3: engineering-standards skill (Opus subagent B)

**Files:**
- Create: `plugins/founder-kit/skills/engineering-standards/SKILL.md`
- Read-only source: `/Users/soleksii/.claude/skills/oop-best-practices/SKILL.md` (692 lines, Python/FastAPI/Tweeds; the STRUCTURE and rule taxonomy are the value; the stack examples must be replaced)

**Interfaces:** Produces skill name `engineering-standards` for Task 6 catalog.

- [ ] **Step 1: Write the skill** (~300-450 lines) targeting Next.js App Router + TypeScript + Supabase/Postgres + Vercel. Keep the source's framing ("read the task, identify which rules bite, apply with judgment; explicit user instruction wins"). Required sections, each with a short wrong-vs-right TypeScript example: encapsulation and module boundaries (one component or service per file, soft 300-line limit, split at the seam); naming (no magic numbers, constants/enums, intention-revealing names); imports top-of-file only; validation at every boundary with zod (API routes, server actions, forms); Supabase discipline (RLS on every table, no service-role key in client code, parameterized queries via the client, never string-interpolated SQL); migration safety (expand → contract, additive first, backfill, then drop; never destructive in one step); React habits (never useEffect for derived state or data fetching; server components default, client components only for interactivity; minimize state); resilience (retry with exponential backoff on third-party calls, timeouts, idempotency for webhooks); structured logging (JSON, request id, no console.log soup in production paths); secrets hygiene (env vars only, `.env.local` gitignored, Vercel env for deploys, never commit keys); OWASP baseline (authN+authZ on every protected route and server action, output encoding, dependency audit); testing discipline (unit test per unit of logic, Playwright smoke for the critical path, test the behavior not the implementation); Conventional Commits.
- [ ] **Step 2: Re-read for stack correctness** (no Pydantic/Alembic/Python references except a one-line "if your stack is Python, adapt these same rules" note).
- [ ] **Step 3: Verify:** forbidden-strings grep clean; `grep -c 'useEffect' file` ≥ 1; `grep -ci 'RLS' file` ≥ 1; frontmatter valid.

### Task 4: meeting-brief skill (Opus subagent C)

**Files:**
- Create: `plugins/founder-kit/skills/meeting-brief/SKILL.md` (rewrite, ~150-200 lines)
- Create: `plugins/founder-kit/skills/meeting-brief/references/`: port `dashboard-build.md`, `lock-and-deploy.md`, `research-and-branding.md`, `granola-transcript.md` from source, scrubbed; write new `partner-variant.md`
- Create: `plugins/founder-kit/skills/meeting-brief/scripts/`: copy `password_protect.py`, `brand_fetch.py`, `granola_decrypt.py`, `requirements.txt`, scrubbed
- Create: `plugins/founder-kit/skills/meeting-brief/assets/`: copy `starter/` and `gate/` trees, scrubbed
- Read-only sources: `/Users/soleksii/.claude/skills/granola-meeting-dashboard/` (EXCLUDE `.git/`, `__pycache__/`, `.dek-cache`, `.gitignore`), `/Users/soleksii/.claude/skills/isl-partner-dashboard/SKILL.md`

**Interfaces:** Produces skill name `meeting-brief` for Task 6 catalog.

- [ ] **Step 1: Copy scripts and assets** minus excluded dirs; scrub every file of forbidden strings, personal booking links, phone numbers, hardcoded passwords or account slugs.
- [ ] **Step 2: Rewrite SKILL.md.** Description: build a password-locked, Vercel-deployed visual brief from any meeting transcript (Granola, Zoom, Otter, Fireflies, or pasted text); "Use when the user says 'build a dashboard from our call', 'make a brief from my meeting with <name>', 'turn this transcript into something I can share'." Body keeps the source mechanics (pains → people → agreements → action items structure, brand research, password gate, Vercel deploy) but: add an `## Owner config` section instructing the skill to look for a `founder-kit.config.md` in the user's project or ask once for name, booking link, phone, and default password scheme, then reuse; make Granola decrypt an optional branch behind "if the user uses Granola on macOS"; default path is a provided transcript file or paste.
- [ ] **Step 3: Write `references/partner-variant.md`** distilled from the ISL skill's MECHANICS only (tier pages, multi-tab layout, program-fact canon pattern as "keep a facts file so numbers never drift", no-sponsorship-figures rule generalized to "never invent dollar amounts"); zero ISL/organization names.
- [ ] **Step 4: Verify:** `grep -rniE '<forbidden pattern>' skills/meeting-brief/` clean, including assets and scripts; `python3 -m py_compile` passes on all three scripts; no `.git`, `__pycache__`, `.dek-cache` inside the copied tree.

### Task 5: deep-research + image-pipeline skills (Opus subagent D)

**Files:**
- Create: `plugins/founder-kit/skills/deep-research/SKILL.md`
- Create: `plugins/founder-kit/skills/image-pipeline/SKILL.md` (+ port the script file next to the source SKILL.md if it is generic; drop it if account-bound)
- Read-only sources: `/Users/soleksii/.claude/skills/iterative-deep-research/SKILL.md`, `/Users/soleksii/.claude/skills/nano-banana-pipeline/`

**Interfaces:** Produces skill names `deep-research`, `image-pipeline` for Task 6 catalog.

- [ ] **Step 1: Port deep-research** near-verbatim; rename `name:` to `deep-research`, trigger `/deep-research`; scrub any personal references; keep the rubric loop, fan-out, adversarial verification, report format intact.
- [ ] **Step 2: Rewrite image-pipeline.** Keep the judged loop (ideas → best → prompts → best → images → best → compare vs brief → loop; Claude is the judge, the image model only renders). Replace the account-bound execution section entirely: primary path `GEMINI_API_KEY` from Google AI Studio calling the Gemini image model via REST (`curl` example with the key from env, model name current per https://ai.google.dev/gemini-api/docs/image-generation; verify the model id against those docs, do not trust memory); fallback path "authenticated gcloud + Vertex if the user already has it". Missing-key branch: print "Get a free key at https://aistudio.google.com/apikey, then `export GEMINI_API_KEY=...`" and stop.
- [ ] **Step 3: Verify:** forbidden-strings grep clean on both; `grep -c 'GEMINI_API_KEY' image-pipeline/SKILL.md` ≥ 2 (usage + missing-key branch); `grep -c 'Use when\|use when' each` ≥ 1.

### Task 6: README, THIRD_PARTY, templates (Opus subagent E)

**Files:**
- Create: `README.md`, `THIRD_PARTY.md`, `templates/CLAUDE.md`, `templates/settings.json`

**Interfaces:** Consumes the six skill names from Tasks 2-5 (catalog table); consumes install lines `/plugin marketplace add sviatil0/founder-kit` and `/plugin install founder-kit@founder-kit`.

- [ ] **Step 1: Write README.md** (~150-250 lines): what this is (one paragraph, founder-voiced); Install (the two slash commands, plus `claude` CLI note); 10-minute setup checklist (Claude Code, git + gh auth, node + pnpm, vercel login, supabase account, optional GEMINI_API_KEY); skill catalog table (name, one-line what, trigger phrases); "how skills fire" explainer (descriptions match your words; you can also name them); recommended third-party installs (top 4 with commands, link to THIRD_PARTY.md); using templates/; updating (`/plugin update founder-kit`); MIT license line.
- [ ] **Step 2: Write THIRD_PARTY.md** with four tiers exactly per spec section "Third-party ecosystem"; official-marketplace plugins install as `/plugin install <name>@claude-plugins-official`; community ones need `/plugin marketplace add <owner>/<repo>` first; graphify is `pip install graphifyy` + its skill; one honest line per entry on what it adds and when to skip it.
- [ ] **Step 3: Write templates/CLAUDE.md**: a starter project-conventions file a founder drops in their app repo (stack declaration, run commands placeholder, the three rules that matter: never push main, validate at boundaries, no secrets in code; pointer to invoke ship-flow + engineering-standards).
- [ ] **Step 4: Write templates/settings.json**: valid Claude Code settings JSON with a conservative `permissions.allow` list (`Bash(npm run *)`, `Bash(pnpm *)`, `Bash(git status)`, `Bash(git diff *)`, `Bash(git log *)`, `Bash(gh pr view *)`, `Bash(vercel logs *)`) and a comment-free structure (JSON has no comments; explanations live in README).
- [ ] **Step 5: Verify:** both templates parse (`python3 -m json.tool templates/settings.json`); README contains both install lines verbatim; forbidden-strings grep clean (`sviatil0` allowed in URLs).

### Task 7: Verification gate (orchestrator)

- [ ] **Step 1: Leak scan:** `grep -rniE 'soleksii|oleksiienko|sviatoslav|stefan|nd\.edu|notre dame|x-fabric|desync|tweeds|clickup|innovation sprint|sprint lab|dnipro|questbridge|cal\.com/' plugins/ templates/ README.md THIRD_PARTY.md` → empty (then a separate check that `sviatil0` appears only in URLs).
- [ ] **Step 2: Manifest validation:** both JSONs parse; plugin `source` dir exists with plugin.json; all three `name` fields equal `founder-kit`; every `skills/*/` dir contains SKILL.md whose frontmatter `name:` equals the dir name.
- [ ] **Step 3: Script sanity:** `python3 -m py_compile` on every vendored `.py`.
- [ ] **Step 4: Fix anything found, then commit** `feat: founder-kit v0.1.0: six skills, ecosystem guide, templates`.

### Task 8: Publish (orchestrator)

- [ ] **Step 1:** `gh repo create sviatil0/founder-kit --public --source . --push` (repo description: "Claude Code skill kit for startup founders").
- [ ] **Step 2:** `curl -s https://raw.githubusercontent.com/sviatil0/founder-kit/main/.claude-plugin/marketplace.json | python3 -m json.tool` → parses.
- [ ] **Step 3:** Report the two founder install lines to Stefan; he runs `/plugin marketplace add sviatil0/founder-kit` interactively as the live test.
