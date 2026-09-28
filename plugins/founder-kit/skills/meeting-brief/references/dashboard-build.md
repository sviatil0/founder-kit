# Building the brief

The output is a **single, dependency-free static site**: `index.html` + `styles.css` +
`data.js` (all the meeting content, one source of truth) + `app.js` (renders tabs from the
data). No framework, no build step, no CDN, so it opens by double-click, survives offline, and
deploys to any static host.

**Copy the starter into the project and edit the copy.** Never edit the skill's assets in place:

```bash
SKILL="<absolute path of this skill's directory>"   # the dir that contains SKILL.md
cp -r "$SKILL/assets/starter" ./<meeting>-brief && cd ./<meeting>-brief
```

Why this shape: a meeting brief must open reliably *right before the meeting*, be trivially
shareable, and never fail a build. Keeping content in `data.js` means you edit facts in one place
and the render stays untouched.

## Content model (data.js)

Put everything in a single `BRIEF` object so the render is dumb and the facts live in one spot:

```js
window.BRIEF = {
  meta: { partner, role, date, length, setting, outcome,
          followup: { booking, phone, line } },  // from the Owner config, never the recipient's
  pains:   [ { id, title, cat, quote, impact /*1-5*/, effort /*1-5*/, solvable /*bool*/, note } ],
  solvers: [ { pain_ids:[...], who, builds, proof } ],
  people:  [ { id, name, role, side /*camp*/, lead /*bool: emphasized card*/, note, research, quote } ],
  agreements: [ { text, quote } ],
  actions:    [ { text, owner, when, done } ],
  background: [ { year, title, detail } ],  // optional timeline
};
```

Adapt field names to the meeting, but keep the one-object discipline.

`meta.followup` drives the follow-up CTA the starter renders in the rail and at the end of the
Agreements & Actions tab: a "Book a follow-up" button (the owner's scheduling link) and a
"Call / text" link. This is the whole point of a follow-up brief; the recipient finishes reading
and the next step is one tap away. Fill both fields from the **Owner config** (see SKILL.md), not
from the recipient's details, and not with invented contact info. A field left empty simply does
not render its button, which is the correct graceful degradation when the owner has no scheduling
link or does not want to publish a phone number.

## Tabs (default: Pains, Solvers, People, Agreements & Actions)

Render each tab from the data. Keep the pains tab first and richest. See the SKILL.md "Default
structure" section for what each tab is for. Wire tabs with a tiny router (in the starter):
click a nav item, toggle which `.panel` has `.show`. Number keys 1 to n jump tabs. That is all the
JS interactivity you need.

## Diagram recipes (inline SVG / CSS, no chart lib)

Diagrams should be *load-bearing*; they help the reader decide, they do not decorate. Build them
by hand so there is no dependency and you control every pixel. The four that pull their weight
most often:

**1. Impact x effort matrix** (the single best "where do we push first?" visual for pains).
Plot each pain as a dot: x = effort, y = impact. Split into quadrants at the midpoints and label
them (Quick Wins / Big Bets / Easy Fills / Later). **Label BOTH axes** (`EFFORT` and a rotated
`IMPACT`); an unlabeled y-axis is unreadable. Color dots by whether it is solvable in one go.
Nudge overlapping dots apart by a fixed offset so labels stay readable. Around 40 lines of SVG.

**2. Theme breakdown.** Count pains per category, draw horizontal bars (pure CSS, width =
count/max). Shows where the pain concentrates in one glance.

**3. Relationship / camps map.** Three columns (their side, a bridge person, your side) with
name chips, so follow-up ownership is obvious. Pure CSS grid.

**4. Timeline.** Vertical rail with dated nodes for the person's background or the plan. Pure
CSS with a left border and absolutely-positioned dots.

The starter **ships** the matrix, theme bars, the relationship/camps map (in the People tab), a
vertical timeline, and a pain-to-solver flow, all wired into the default renderers. A **capability
grid** (each solver track listing the pain ids it covers) is easy to add if a meeting needs it.

**Overlap handling for the matrix:** group pains by identical (impact, effort), then offset
members of each group horizontally by about 27px either way so their labels do not collide.

## The design bar

Read the `frontend-design` skill if it is available; it is written for exactly this. The essence:

- **One signature grounded in the subject.** Do not reach for the default near-black plus
  one-accent look. Pull a motif from the meeting's own world and let it carry the design; keep
  everything else quiet. Examples: a retailer that grades goods "good/better/best" gets pains
  graded the same way; a logistics call gets a manifest motif; a clinician gets a chart/vitals motif.
- **Type with intent.** A characterful display face used with restraint, a clean body face, and a
  mono for data, labels and eyebrows. Load via Google Fonts with a system fallback so it degrades
  gracefully.
- **Dark, disciplined base** makes hand-drawn SVG and any "paper" motif pop, and reads as
  focused. But the base is not the point; the signature is.
- **Responsive and accessible floor:** collapses to one column on mobile, visible keyboard focus,
  `prefers-reduced-motion` respected. Do not announce it, just clear it.

## Verify before you ship (fidelity)

This is the step that separates a useful brief from an embarrassing one. After building:

- **Verify each quote by search, not by re-reading.** Take a distinctive 4 to 8 word substring and
  grep the raw transcript. No match means paraphrased or fabricated, so replace it with the
  verbatim line or drop the quote marks. Allowed cleanup: filler, repeats, speech-to-text
  homophones. Not allowed: changing meaning, adding specifics, merging utterances, changing speaker.
- **Escape on render.** The starter passes every field through `esc()`. A faithful quote can
  contain `<`, `&`, or `"` ("margins dropped <5%", "R&D") and unescaped it silently truncates. If
  you hand-write render code, escape too.
- **Do not misattribute.** On a multi-person call the labels often do not name individuals, so only
  attribute a quote to a named person when the content identifies them; otherwise attribute to the side.
- **For a normal single meeting, re-read the quotes yourself.** Only fan out verifier subagents
  (one per tab, each given the transcript plus that tab's data slice, told to flag only
  fabrications, distortions and misattributions) when the build spans many tabs and cards.
- **Coverage check.** List every major topic the meeting actually covered, then check each is
  represented somewhere in a tab. A key discussion silently missing reads to the user as a broken
  deliverable. Show the user the topic list and ask if anything is missing.
- **Copy passes the human bar.** No em dashes anywhere (house rule), no AI-isms ("really stuck
  with me", "I'm excited to..."), no flattery, and never echo the user's instructions in the copy;
  the recipient reads this cold, as if the user wrote it.
- **Confirm no placeholders survive.** Search `data.js` and `index.html` for starter stubs (`Full
  Name`, `Short pain title`, `YYYY`, `Partner Name`, `Their words`) before shipping, and confirm
  `meta.followup` holds the owner's real link, not an example one.
- **Screenshot each tab and read the rendered quotes** (Playwright or a browser MCP). Confirm
  they display as complete, faithful sentences; a truncated or symbol-mangled quote signals an
  escaping or data problem, not just cosmetics. Check for layout breaks and overlapping matrix dots.

## Lock and deploy: the default finish

Locking the brief behind a password and putting it live on Vercel is part of the normal
workflow, not an extra. The full protocol (password and naming rules, the middleware gate, scope
confirmation, live-site verification, analytics, and the one-block handoff) is in
`references/lock-and-deploy.md`. Follow it; every rule in it traces to a real past failure.
