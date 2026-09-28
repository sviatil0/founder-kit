# founder-kit — Design Spec (2026-09-28)

## Purpose

A public repo that any startup founder can add to Claude Code in two commands and get
the app-building workflow Stefan uses: ship discipline, engineering standards, deployed
meeting briefs, deep research, and image generation. Approved by Stefan 2026-09-28
(format: plugin marketplace; skills: all four sets; stack: Next.js + Vercel + Supabase;
publish: public GitHub now, account `sviatil0`).

## Success criteria

1. A founder with Claude Code installed runs
   `/plugin marketplace add sviatil0/founder-kit` then `/plugin install founder-kit@founder-kit`
   and all six skills appear in their skill list and fire on their trigger phrases.
2. Zero personal data: no names, accounts, phone numbers, booking links, employer or
   organization names, absolute home paths from the source machine.
3. Every external credential a skill needs is an env var the skill checks for, with
   setup instructions shown when missing.
4. THIRD_PARTY.md gives tiered install commands for the ecosystem plugins.

## Shape

```
founder-kit/
├── .claude-plugin/marketplace.json        # marketplace: founder-kit → ./plugins/founder-kit
├── plugins/founder-kit/
│   ├── .claude-plugin/plugin.json
│   └── skills/
│       ├── ship-flow/SKILL.md
│       ├── engineering-standards/SKILL.md
│       ├── pr-writer/SKILL.md
│       ├── meeting-brief/{SKILL.md, references/, scripts/, assets/}
│       ├── deep-research/SKILL.md
│       └── image-pipeline/SKILL.md
├── templates/{CLAUDE.md, settings.json}
├── README.md
├── THIRD_PARTY.md
├── LICENSE (MIT)
└── docs/superpowers/{specs,plans}/
```

## Vendored skills (6)

| Skill | Source (Stefan's machine) | Transformation |
|---|---|---|
| ship-flow | `~/.claude/skills/desync-dev-flow/SKILL.md`, `~/.claude/skills/tooling-workflow/SKILL.md` | issue → plan → branch → PR → merge, scaled to a 1–3 person startup, GitHub-native (`gh`), no Desync CI gates or repo names |
| engineering-standards | `~/.claude/skills/oop-best-practices/SKILL.md` (692 lines, Python/Tweeds) | rewritten for Next.js App Router + TypeScript + Supabase/Postgres + Vercel |
| pr-writer | `~/.claude/skills/desync-pr-writer/SKILL.md` | generic PR title/body discipline, checklist honesty, no Desync regex gates |
| meeting-brief | `~/.claude/skills/granola-meeting-dashboard/` (+ `isl-partner-dashboard` as optional variant reference) | transcript → password-locked Vercel brief; owner CTA becomes a config block; ISL content rules stripped, tier-page mechanics kept as `references/partner-variant.md` |
| deep-research | `~/.claude/skills/iterative-deep-research/SKILL.md` | near-verbatim port, trigger `/deep-research` |
| image-pipeline | `~/.claude/skills/nano-banana-pipeline/SKILL.md` | Stefan's Vertex account/project removed; runs on user's `GEMINI_API_KEY` (Google AI Studio), Vertex via their own gcloud as fallback |

Dropped from the original seven: `handoff` — discovered to be a third-party clone
(`quantsquirrel/claude-handoff-baton`); linked in THIRD_PARTY.md instead.

## Genericization rules (hard gate)

Forbidden strings anywhere in shipped files (case-insensitive):
`soleksii`, `oleksiienko`, `sviatoslav`, `stefan`, `nd.edu`, `notre dame`,
`x-fabric`, `desync`, `tweeds`, `clickup`, `innovation sprint`, `sprint lab`,
`dnipro`, `questbridge`, `cal.com/`, `/Users/soleksii`, any phone number.
Exception: `sviatil0` allowed only in repo URLs (plugin.json, README install lines).

## Third-party ecosystem (linked, not vendored)

Tiers in THIRD_PARTY.md, each with exact install command:
- **Day one:** superpowers, context7, github, code-review (official marketplace)
- **Build the UI:** frontend-design, vercel, supabase, playwright, figma (official); ui-ux-pro-max (`nextlevelbuilder/ui-ux-pro-max-skill`)
- **Review + commit:** pr-review-toolkit, code-simplifier, commit-commands, security-guidance, typescript-lsp (official)
- **Power tools:** skill-creator, claude-md-management, feature-dev, railway, zapier, slack, telegram (official); graphify (`pip install graphifyy`); video-use (`browser-use/video-use`); handoff (`quantsquirrel/claude-handoff-baton`); gastown

## Install-ease assessment

- Two slash commands, no build step, no symlinks; marketplace updates propagate on plugin update.
- Skills are prose + small Python scripts; only `meeting-brief` scripts need `python3` (stdlib + `requests`), only `image-pipeline` needs `GEMINI_API_KEY`, `deep-research` uses built-in WebSearch/WebFetch. Everything else: zero dependencies.
- Works on any machine with Claude Code ≥ plugin-marketplace support; nothing assumes macOS except Granola local-cache decrypt (optional path — pasted transcripts always work).

## Testing

1. Leak scan: forbidden-strings grep over `plugins/`, `templates/`, `README.md`, `THIRD_PARTY.md` returns nothing.
2. Manifest validation: both JSON files parse; `marketplace.json` plugins[0].source dir exists and contains `.claude-plugin/plugin.json`; names match (`founder-kit`).
3. Frontmatter check: every SKILL.md starts with `---`, has `name:` matching its dir and a `description:` containing "Use when" trigger language.
4. Live install: after push, `/plugin marketplace add sviatil0/founder-kit` from a clean session lists the plugin (Stefan runs interactively; pre-verified by fetching raw marketplace.json from GitHub).
