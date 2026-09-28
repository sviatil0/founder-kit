# The partner variant: tier pages and a repeatable program pitch

Use this when the brief is not a one-off meeting recap but a **recurring offer** you put in front
of many prospects: a partner program, a sponsorship lane, a pilot, a paid engagement with a few
shapes to it. The generic flow in SKILL.md still owns the mechanics (transcript, fidelity, gate,
deploy). This file adds the layer that makes a brief sell between calls without a human in the room.

## Start from the last one, never from empty

Keep your shipped briefs in one place and start each new one by copying the closest previous
brief wholesale, then rewriting `data.js` and re-theming `styles.css`. The structure is the asset;
rewriting it from scratch each time is how tabs, keyboard routing and the gate quietly regress.

Architecture stays identical across every brief you ship:

- `index.html` plus `data.js` (all content in one `window.BRIEF` object, the single source of
  truth) plus `app.js` (render layer, every interpolated field through `esc()`) plus `styles.css`
  plus `middleware.js` (the password gate) plus `package.json`.
- **Content changes go in `data.js` only.** A new section means one `renderX()` in `app.js` plus
  one `TABS` entry, nothing else.
- Make tabs hash-routable (`#program`) so you can link a prospect straight to the tier tab, and
  keyboard-navigable (keys 1 to 9). Both are cheap and both get used.
- `.vercelignore` excludes transcripts, screenshots, `.env*`, and any browser-automation output dir.
- Password convention `<partner>-<topic>-<MMDD>`, a **fresh salt per project**, and the lock
  screen restyled to the partner's palette.
- Deploy from the project directory with the Vercel CLI, then verify the production URL returns
  401 so you know the gate survived.
- Before deploying, sanity-check locally: `node --check` both JS files, serve with
  `python3 -m http.server`, screenshot the changed tab, and actually look at it.

## Keep a facts file so the numbers never drift

The same handful of facts appears on every partner brief: cohort dates, headcount, placement
counts, event stats, the names of the people a partner would work with. Those facts change, and
stale ones ship silently. Two briefs have gone out with a stale event date because the number was
retyped from a sibling project instead of read from a source.

So: **one facts file, checked into the repo, is the only place a recurring number lives.**

- Write it as plain markdown (`program-facts.md`) with one line per fact and a date next to each:
  `Cohort 4 kickoff: 2026-09-14 (verified 2026-09-01)`.
- Every brief reads from it. Never retype a number from another brief's `data.js`; that is a copy
  of a copy.
- Treat the file as a starting point, not gospel. **Re-verify anything load-bearing** before it
  goes on a page: the date a prospect would put in their calendar, a headcount you are being
  judged on, a name you are about to spell in front of its owner.
- When you correct a fact, correct the facts file in the same turn. Otherwise the next brief
  reintroduces the error.
- If a number cannot be verified before the deadline, leave it off the page. A missing stat costs
  nothing; a wrong one costs the relationship.

## Never invent dollar amounts

Hard rule, no exceptions: **no price, fee, budget, sponsorship figure, prize pool or salary
number goes on a partner page unless the owner gave you that exact number for that exact page.**

- Naming a number early caps the ceiling. The page's job is to establish that the work is worth
  talking about; a human walks the decision maker through cost on a call.
- If a tier needs a cost shape, say what the partner **brings** in kind ("about one hour a week
  from one engineer") rather than in currency.
- Pricing and tier structure are set once, program-wide, by the owner. They are not negotiated per
  partner inside a page you generated.
- If the transcript contains a number the prospect floated, it stays in your notes, not on the
  page, unless the owner confirms publishing it.

## The tier model (three lanes, stacked)

The canonical shape that works: **three tiers that stack rather than compete**, and a free floor.

| Lane | What it is | What the partner brings | What they get | Decide by |
|---|---|---|---|---|
| Observer | The free floor. No commitment, stays informed. | Nothing but an email address | Updates, an invite to the public moment | Open |
| Event partner | One bounded event or sprint. | A problem statement, a judge or mentor, a few hours | Their problem worked on, visibility, a shortlist of people | A real date |
| Program partner | The full engagement across a cycle. | Recurring time and a named owner on their side | Sustained work, first look at the people, a named role in the story | A real date |

Mechanics that matter:

- **Each lane gets three fields and only three:** what they bring, what they get, when they decide.
  Anything else belongs on another tab.
- **The lanes stack.** Observer is a step to event partner, not a rejection. Say so on the page.
- **The floor is free.** A prospect who cannot commit should still be able to say yes to something.
- **The deadline sits on the lane, not on the problem.** "Judges confirmed by the 12th" is a real
  constraint; "solve this before the 12th" reads as pressure.
- One tier tab, not three pages. Side-by-side columns collapse to stacked cards on mobile.

## Tab canon for a partner brief

Pick 5 to 8 from this menu. The **first tab always proves you listened**, so it is never the pitch.

1. **What we heard.** Their problems as cards with verbatim quotes, the impact x effort matrix, and
   one flagged wedge: where you would start.
2. **Their constraint.** Whatever they raised first (data sensitivity, budget timing, headcount)
   taken seriously on its own tab. Ducking it reads as not listening.
3. **Where we would start.** The wedge argued: why this one, what gets built, what gets measured
   so the next conversation has numbers.
4. **How it runs.** A phase timeline with the per-phase ask spelled out in hours, not dollars.
5. **The program.** The full story of the thing you are inviting them into: stages, funnel,
   outcomes, the people. This block is nearly identical across briefs, so it lives in the facts
   file and gets adapted per partner only in the fit lines.
6. **Ways in (tiers).** The table above, rendered as cards.
7. **Who you would work with.** People cards grouped in camps (theirs, yours, any shared network),
   with the lead on each side flagged.
8. **Agreed and next.** Agreements with the backing quote, actions with owners and dates, and the
   follow-up CTA from the Owner config.

## Hedge anything outside your lane

Legal, compliance, regulatory, procurement and security claims get framed as **your read**, with
the decision explicitly left to their team: "our read is that no regulated data needs to leave
your environment for phase one; your compliance team owns that call, and we will have it checked
in parallel." Never assert those as fact on a page. One overconfident compliance sentence can end
a deal that the rest of the brief had won.

## Definition of done

Local screenshot reviewed, deployed, production URL 401-gated, the facts file updated with
anything you corrected, and a final message to the owner containing: the URL, the password, what
changed since they last looked, and the open loop (who sends what to whom). **Never send it
yourself**; the owner sends.
