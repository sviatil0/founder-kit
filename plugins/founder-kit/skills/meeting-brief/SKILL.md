---
name: meeting-brief
description: >-
  Turn any meeting transcript into a polished, interactive visual brief, password-locked and
  deployed live on Vercel, ending in your own booking link as the follow-up CTA. Use when the
  user wants a built, shareable artifact out of a call: "build a dashboard from our call",
  "make a brief from my meeting with <name>", "turn this transcript into something I can
  share", "make a locked page for the partner", "meeting prep page for the CFO call", "write up
  the customer interview as a page". Works from a pasted transcript, an exported file (Zoom,
  Teams, Otter, Fireflies, Meet captions, a plain text file), or a local Granola cache on macOS
  as an optional branch. Anchor on the words meeting, call, interview or transcript, not on the
  word dashboard. Do NOT use for a plain text summary or a quick list of action items in chat
  (the user wants something built, not a paragraph), and NOT for data or metrics dashboards,
  slide decks, or anything not grounded in a specific conversation. The default output centers
  on the other side's PAINS, the PEOPLE who could solve them, what was AGREED, and the ACTION
  ITEMS, enriched with research on the attendees and the other company's real brand color and
  logo, and finished as one live URL plus one password.
---

# Meeting Brief

Turn a meeting into one shareable brief that answers what actually matters after a call:
**what are their pains, who can solve them, what did we agree, what do we do next?** Everything
else is supporting context. The finished thing is **password-locked, live on Vercel, and ends
in a follow-up CTA** (your booking link and phone) so the recipient's next step is one tap.

The hard parts are keeping every quote faithful and landing the deploy as exactly one URL plus
one password, so that is where most of the guidance lives. The UI is the easy part; there is a
starter template so you never rebuild the shell. Set `SKILL` once and use absolute paths, since
your cwd is the user's project, not the skill dir:

```bash
SKILL="<absolute path of this skill's directory>"   # the dir that contains this SKILL.md
```

## Owner config

Every brief ends with the **owner's** follow-up CTA and a lock screen that names the owner. Those
details are per-user, so they are configuration, never hardcoded.

1. **Look for a config file** before asking anything, in this order: `./founder-kit.config.md`,
   `./.claude/founder-kit.config.md`, `~/.founder-kit.config.md`. Read the first one that exists.
2. **If none exists, ask once**, in one message, for these five fields, then offer to write
   `founder-kit.config.md` in the project root so you never ask again:

   | Field | Used for | If the user declines |
   |---|---|---|
   | `owner_name` | lock-screen eyebrow, "prepared by" line | use the company name alone |
   | `owner_org` | lock-screen org label | omit the label |
   | `booking_link` | the "Book a follow-up" button | omit the button; the CTA still renders the rest |
   | `phone` | the "Call / text" button and the locked-out contact line | omit it; contact line becomes "reply to the email that sent you this link" |
   | `password_scheme` | how to derive each brief's password | default to `<company>-<topic>-<MMDD>` |

3. **Never invent any of these.** No placeholder phone numbers, no example booking URLs on a page
   that ships. An empty field renders nothing, which is the correct graceful degradation.
4. Write them into `data.js` under `meta.followup`, and into `middleware.js` `__ORG_LABEL__` and
   `__CONTACT_LINE__`. Confirm before shipping that no example value survived.

## Workflow

1. **Get the transcript. Default path: the user provides it.** Ask for a pasted transcript or a
   file path, and accept whatever the recording tool exported (Zoom, Teams, Otter, Fireflies,
   Meet captions, a plain `.txt`, `.vtt`, `.srt` or `.md`). No dependencies, works on every
   platform. Keep speaker labels if present; if absent, say so and plan to attribute by content.

   **Optional branch, only if the user says they use Granola and is on macOS:** the transcript
   lives in an encrypted local cache and there is no reliable API, so decrypt it. Full method and
   troubleshooting in `references/granola-transcript.md`.
   ```bash
   python3 -m pip install cryptography   # once; the script needs it and it is not stdlib
   python3 "$SKILL/scripts/granola_decrypt.py" --list                  # id, date, #segs, snippet
   python3 "$SKILL/scripts/granola_decrypt.py" --match "<name/phrase>" # best CONTENT match
   ```
   `--match` scores by transcript **content** and is date-blind, so run `--list` first and confirm
   the id if two meetings match the same name. Run the first invocation in the background; it
   blocks on a one-time keychain dialog. On Linux or Windows, or if any of this fails, stop and
   ask for a pasted transcript.

   **Confirm it is the right meeting before building anything.** A whole brief has been built from
   the wrong recording. Echo back the title, date, who is talking, and a two-line gist, and get a
   yes. Never build from a meeting that is still in progress; if the newest recording's timestamp
   is within the last hour, ask.

2. **Read the whole transcript before designing anything.** Pull, with real quotes:
   - **Pains.** Every problem, frustration, constraint, "I wish we could...". Over-collect; this is the point.
   - **Solvers.** Who or what (person, team, product, capability) could address each pain.
   - **Agreements.** Anything decided or committed ("yes, I'm interested", "let's do X", "send me Y").
   - **Action items.** Concrete next steps, with owner and timeframe where stated.
   - **Context.** Who the person is, their stakes and scale. Supporting, not central.

3. **Confirm who is involved. ASK before researching or branding.** Transcripts mishear names, and
   researching or branding the wrong person or company is worse than skipping it. Extract the
   candidate attendees and the company from the transcript, then ask the user to confirm:
   - the **full name and role** of each key person, especially the external one, and
   - the **company** whose brand to use (and its domain), and whether to use their branding at all.

   Use the answers as ground truth. If the user already named everyone, just confirm spelling.

4. **Optional, if the user wants it: research the people and pull the brand.** See
   `references/research-and-branding.md`.
   - **People research.** Web-search each confirmed attendee for *public professional* background
     to sharpen the People tab and the read on their pains. Cite sources, flag uncertainty, public
     professional information only, and never compile sensitive personal data.
   - **Branding.** `python3 "$SKILL/scripts/brand_fetch.py" <company-domain>` returns logo and
     theme candidates. Download the logo, look at it, derive two or three accent colors, and set
     `meta.brandColor` and `meta.logo` in `data.js`. The brand color *is* the signature for a
     recipient-facing brief. **Default to the other company's brand** when the meeting is with
     someone from a company, even when the user is pitching their own product. Sole exception: the
     user speaks on behalf of a third company, in which case wear that company's identity.

5. **Build the brief.** Copy the starter into the project and edit the copy. Never edit the
   skill's assets in place:
   ```bash
   cp -r "$SKILL/assets/starter" ./<meeting>-brief && cd ./<meeting>-brief
   ```
   Fill in `data.js`; the render reads it. Structure, diagram recipes and the design bar are in
   `references/dashboard-build.md`. Fill `meta.followup` from the Owner config.

6. **Verify fidelity. Do not skip.** A brief that misquotes the other side is worse than none. See
   "Fidelity" below. Also run the coverage check (every major topic from the call is in a tab) and
   the human-copy bar (no em dashes, no AI-isms, recipient-facing) from
   `references/dashboard-build.md`. Then screenshot each tab and actually read the rendered quotes.

7. **Lock and deploy. Default, not optional.** Gate the site with a password (proven Vercel
   middleware in `assets/gate/`), confirm the Vercel account and scope *before* the first deploy,
   ship, verify the live site through the gate, and hand off **one URL plus one password** in a
   single block. Full protocol: `references/lock-and-deploy.md`. Skip deploying only if the user
   explicitly wants it local, then offer the single-file encrypted variant
   (`scripts/password_protect.py`) so the lock still holds. **Never send the brief to the
   recipient yourself**; stage the message and let the user send.

## Default structure: pains, solvers, people, agreements and actions

Lead with pains; that is what the user came for. A good default is four or five tabs:

1. **Their pains.** The core. Each pain as a card with a real quote, plus diagrams that help
   *prioritize* (an impact x effort matrix, a themes breakdown). Answer "where do we push first?"
2. **Solvers and fixes.** Map each pain to who or what could address it. If the user's own product
   is the solver, show what it would build and the proof it can deliver.
3. **The people.** Everyone in and around the room, which side they are on, who to pull in next,
   and their background if researched. Relationships drive follow-up.
4. **Agreements and actions.** What was agreed (with the sealing quote) and the action items with
   owners and timing. This is what the user acts on tomorrow.
5. **Background** (optional). Who the person is, their arc, the stakes. A timeline works well.

Adapt to the meeting: a one-on-one collapses to decisions plus actions; a user interview becomes
themes plus quotes. Fewer focused tabs beat many thin ones.

For a recurring offer pitched to many prospects (a partner program, a pilot, sponsorship lanes),
read `references/partner-variant.md`: tier-page mechanics, the facts-file pattern, and the rule
that no dollar amount goes on a page you generated.

## Design: make it theirs

The brief should look made for *this* meeting. Two levers, used with restraint:

- **The other company's brand** if you fetched it: brand color as the accent, logo in the header.
  This alone makes a recipient-facing brief feel bespoke. If the `frontend-design` skill is
  available, use it.
- **A signature from the subject's world** when there is no brand to borrow. A retailer that grades
  goods "good/better/best" gets pains graded the same way; a logistics call gets a manifest motif.
- **Diagrams earn their place.** Impact x effort matrix, theme bars, a relationship map, a
  timeline. Hand-build them as inline SVG or CSS, no chart library.
- **Copy like a human.** Plain, specific, active. **No em dashes**, no AI-isms ("really stuck with
  me", "genuine pleasure"), no flattery, and never reference the user's request in the copy; the
  recipient reads this cold, as if the user made it.

## Fidelity: quotes are load-bearing

The user may put this in front of the actual person. So:

- **Verify each quote by search.** Take a distinctive four to eight word substring and grep the raw
  transcript. No match means paraphrased or fabricated, so replace it with the verbatim line or
  drop the quotation marks. Allowed cleanup: filler, repeats, obvious speech-to-text homophones.
  Not allowed: changing meaning, adding specifics, merging utterances, changing the speaker.
- **Do not misattribute.** Many tools collapse everyone but the recorder into one channel, so on a
  multi-person call you cannot trust who said what. Only attribute a quote to a named person when
  the content itself identifies them (a self-intro, "my stores", a name addressed); otherwise
  attribute it to the side and confirm with the user. A transcript-only checker cannot catch a
  wrong-person attribution, so catch it here.
- **Get the name right.** Use the spelling the user typed, then the calendar or file title. When in
  doubt, ask before shipping; never fall back to the speech-to-text spelling.
- **For a normal single meeting, re-read the quotes yourself.** Only fan out verifier subagents
  (one per tab, each given the transcript plus that tab's data slice, told to flag only
  fabrications, distortions and misattributions) when the build spans many tabs and cards.

## When a tool or credential is missing, stop gracefully

Print the fix and stop. Never loop or silently degrade.

- **No transcript at all.** Ask for a paste or a file path. Do not reconstruct a meeting from
  memory or from the user's summary and present it as quotes.
- **`cryptography` not installed** (Granola and single-file-encrypt paths only):
  `python3 -m pip install cryptography`, or `python3 -m pip install -r "$SKILL/scripts/requirements.txt"`.
- **Not on macOS, or Granola decrypt fails.** Say so once and ask for an exported transcript.
  Everything downstream is identical.
- **`vercel` CLI missing or not logged in.** `npm i -g vercel` then `vercel login`. If the user
  does not want an account, build locally and lock with `scripts/password_protect.py`, which needs
  no host.
- **More than one Vercel scope.** Ask which one before the first deploy. Do not guess.

## Bundled resources

`scripts/`: `granola_decrypt.py` (decrypts a local Granola cache, macOS only, optional path;
`--list`, `--match "<query>"`, `--id`, `--json`; needs `cryptography`), `brand_fetch.py`
(best-effort brand asset finder for a domain, stdlib only), `password_protect.py` (inlines the
brief into one AES-256-GCM-encrypted `index.html` that unlocks in the browser, `--gen` makes a
memorable password; for emailing the brief as a file or hosting off Vercel).

`assets/starter/` is a dependency-free brief shell (tabs, escaped render, matrix, bars, camps,
timeline and flow helpers, brand-color and logo hooks, follow-up CTA wired to `meta.followup`).
`assets/gate/` is the Vercel password gate (styled 401 login page, HttpOnly SHA-256 cookie, 30
days); copy it next to the brief, fill the `__PLACEHOLDER__`s from the Owner config, restyle it.

`references/`, read the one you need: `dashboard-build.md` (content model, tabs, inline-SVG
diagram recipes, design bar, fidelity and coverage checklist), `lock-and-deploy.md` (password and
naming rules, the gate, Vercel scope, live verification, analytics, one-block handoff),
`research-and-branding.md` (attendee research and brand application, with guardrails),
`partner-variant.md` (recurring-offer variant: tier pages, multi-tab canon, the facts-file
pattern, no invented dollar amounts), `granola-transcript.md` (optional, macOS only: the
decryption chain, finding the meeting, speaker attribution, troubleshooting).
