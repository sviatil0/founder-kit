# Third-party ecosystem

founder-kit stays small on purpose. Everything below is somebody else's work that pairs well
with it, grouped by when you will actually want it. Each entry has the exact install command,
one honest line on what it adds, and one on when to skip it.

## How the install commands work

**Official marketplace.** Most entries live in the official Claude Code catalog, which your
install already knows as `claude-plugins-official`. One command, inside a session:

```
/plugin install <name>@claude-plugins-official
```

If that errors with an unknown marketplace, open `/plugin`, browse the official catalog from
the menu, and install from there; the plugin names below are the same either way.

**Community marketplaces.** Add the marketplace first, then install from it:

```
/plugin marketplace add <owner>/<repo>
/plugin install <plugin-name>@<marketplace-name>
```

**Not plugins at all.** A few of the best tools here are CLIs or repos with skill files. They
are marked "not a plugin" and come with their real install path.

Install in tiers. Fifteen plugins competing for the same trigger phrases makes Claude worse,
not better; add a tier only when you feel the gap it fills.

---

## Tier 1: Day one

The four you install right after founder-kit.

- **superpowers** ; `/plugin install superpowers@claude-plugins-official`
  Adds the disciplines founder-kit assumes: brainstorming before building, writing a real plan
  before touching code, test-driven development, systematic debugging, git worktrees.
  Skip if: you only want the workflow skills and already have your own planning habit.

- **context7** ; `/plugin install context7@claude-plugins-official`
  Fetches current library and framework docs on demand, so Next.js and Supabase APIs come from
  the docs instead of from stale training data. The single highest-value add for a fast-moving
  stack.
  Skip if: your dependencies are pinned, boring, and you never hit an unfamiliar API.

- **github** ; `/plugin install github@claude-plugins-official`
  Real GitHub tools (issues, PRs, reviews, CI status) instead of shelling out to `gh` for
  everything. ship-flow and pr-writer both get faster and more reliable with it.
  Skip if: your code is not on GitHub.

- **code-review** ; `/plugin install code-review@claude-plugins-official`
  A reviewer for the diff you just wrote, which on a team of one is the review you otherwise
  never get. Run it before you merge your own PR.
  Skip if: you have a human reviewer who reads every diff.

## Tier 2: Build the UI

Add these when you start shipping screens rather than endpoints.

- **frontend-design** ; `/plugin install frontend-design@claude-plugins-official`
  Pushes visual direction, typography, and spacing away from the default template look, which
  is where most generated UI lands.
  Skip if: you have a designer or a locked design system.

- **vercel** ; `/plugin install vercel@claude-plugins-official`
  Deploys, preview URLs, env vars, runtime logs, and Next.js guidance from inside the session.
  Pairs directly with meeting-brief, which deploys to Vercel.
  Skip if: you host somewhere else.

- **supabase** ; `/plugin install supabase@claude-plugins-official`
  Schema, migrations, auth, and RLS help specific to Supabase, including the auth and cookie
  traps that eat a day when you hit them cold.
  Skip if: your database is plain Postgres or anything non-Supabase.

- **playwright** ; `/plugin install playwright@claude-plugins-official`
  Lets Claude drive a real browser: click through your flow, screenshot it, and confirm the
  change works instead of asserting that it should.
  Skip if: you have no UI, or you are strict about not letting an agent open a browser.

- **figma** ; `/plugin install figma@claude-plugins-official`
  Reads Figma files and turns frames into components, plus code-connect wiring.
  Skip if: your design lives in a doc or in your head.

- **ui-ux-pro-max** (community) ;
  `/plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill`
  then `/plugin install ui-ux-pro-max@ui-ux-pro-max-skill`
  A large opinionated library of styles, palettes, font pairings, and product-type layouts;
  useful when you want concrete options rather than taste guidance.
  Skip if: you installed frontend-design and want one voice on design, not two.

## Tier 3: Review and commit

The layer between "it works on my machine" and a merged PR.

- **pr-review-toolkit** ; `/plugin install pr-review-toolkit@claude-plugins-official`
  Specialist reviewers: silent failure hunting, test coverage analysis, comment accuracy, type
  design. Deeper than a single review pass, and slower.
  Skip if: Tier 1's code-review is already more feedback than you act on.

- **code-simplifier** ; `/plugin install code-simplifier@claude-plugins-official`
  Cleans up what you just wrote for clarity and consistency without changing behavior; good
  right before you open the PR.
  Skip if: the code is throwaway or a spike you plan to delete.

- **commit-commands** ; `/plugin install commit-commands@claude-plugins-official`
  One-shot commit, push, and PR-open commands with sane messages.
  Skip if: you want founder-kit's pr-writer to own PR bodies; overlapping tools will fight
  over the same step.

- **security-guidance** ; `/plugin install security-guidance@claude-plugins-official`
  A security pass over changes: auth gaps, injection, secret leakage, unsafe defaults. Worth
  running before your first real customer, not after.
  Skip if: nothing is deployed and no real data exists yet.

- **typescript-lsp** ; `/plugin install typescript-lsp@claude-plugins-official`
  Gives Claude language-server truth (definitions, references, diagnostics) instead of grep
  guesses; the payoff grows with repo size.
  Skip if: the project is small enough to read end to end.

## Tier 4: Power tools

Situational. Install one when you have the specific problem it solves.

- **skill-creator** ; `/plugin install skill-creator@claude-plugins-official`
  Build, edit, and evaluate your own skills; the right way to encode a workflow that is
  specific to your company.
  Skip if: you are not writing skills yet.

- **claude-md-management** ; `/plugin install claude-md-management@claude-plugins-official`
  Keeps `CLAUDE.md` honest as the project drifts, instead of letting it rot into a file nobody
  trusts.
  Skip if: your `CLAUDE.md` is still the one from `templates/`.

- **feature-dev** ; `/plugin install feature-dev@claude-plugins-official`
  Guided feature development with codebase-aware architecture passes; heavier than ship-flow
  and aimed at design rather than process.
  Skip if: ship-flow plus superpowers already covers how you start work.

- **railway** ; `/plugin install railway@claude-plugins-official`
  Deploys and manages services on Railway, which is the easier path for a long-running worker
  or a container that does not fit serverless.
  Skip if: everything you run fits on Vercel.

- **zapier** ; `/plugin install zapier@claude-plugins-official`
  Reaches thousands of SaaS tools through Zapier instead of writing one-off integrations.
  Skip if: you are not automating across tools yet.

- **slack** ; `/plugin install slack@claude-plugins-official`
  Reads and posts in Slack: channel digests, standups, announcement drafts.
  Skip if: your team is two people in one room.

- **telegram** ; `/plugin install telegram@claude-plugins-official`
  Same idea for Telegram, including driving Claude from your phone.
  Skip if: you do not want a chat channel into your dev environment.

- **graphify** (not a plugin; Python package) ; `pip install graphifyy`
  (or `uv tool install graphifyy`). Turns a folder of code, docs, or papers into a navigable
  knowledge graph plus a GraphRAG-ready JSON export; useful for onboarding onto a codebase you
  inherited, or for making a pile of research answerable. After installing, point Claude at
  the folder and ask for a knowledge graph.
  Skip if: the repo is small enough that grep and a directory listing already answer your
  questions.

- **video-use** (not a plugin; skill repo) ;
  `git clone https://github.com/browser-use/video-use ~/Developer/video-use`, then open that
  folder in Claude and follow its `install.md`. Conversational video editing: transcribe, cut,
  subtitle, grade. Needs `ffmpeg` on PATH and an ElevenLabs API key for transcription.
  Skip if: you are not making demo or launch videos, or you do not want another API key.

- **handoff** (community) ; `/plugin marketplace add quantsquirrel/claude-handoff-baton`
  then `/plugin install handoff@handoff`
  Saves the state of a session (decisions, failed approaches, constraints, next steps) so the
  next session resumes with the reasoning intact instead of the summary. This is the tool
  founder-kit deliberately does not ship its own version of.
  Skip if: your sessions are short and you keep context in issues, which ship-flow encourages
  anyway.

- **gastown** (not a plugin; Go CLIs) ; canonical repo https://github.com/gastownhall/gastown
  Install needs Go 1.24+, and the module path still resolves under the original author's
  namespace:
  ```bash
  go install github.com/steveyegge/gastown/cmd/gt@latest
  go install github.com/steveyegge/beads/cmd/bd@latest
  ```
  Then set up a workspace (`gt install ~/gt`) and read the repo's own docs; there is no npm or
  plugin path. It orchestrates many coding agents at once with git-backed work tracking, so
  crashed or restarted agents do not lose the thread.
  Skip if: you run one agent at a time. The coordination overhead only pays off when you are
  genuinely trying to keep several workers busy in parallel.

---

## Overlap warnings

- code-review (Tier 1) and pr-review-toolkit (Tier 3) review the same diff differently.
  Start with one.
- frontend-design and ui-ux-pro-max both claim design direction. Pick the voice you like.
- commit-commands and founder-kit's own pr-writer both want to write the PR. Let pr-writer
  own the body if you installed founder-kit for the workflow.
- superpowers has a planning and research surface that touches deep-research. deep-research is
  the one to use when you need citations and adversarial verification; superpowers' planning
  skills are the ones to use before you write code.
