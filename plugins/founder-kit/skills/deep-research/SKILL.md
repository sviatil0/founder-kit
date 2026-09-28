---
name: deep-research
description: >
  Iterative deep research: take any rough research request, iterate on the
  prompt through a rubric-based refinement loop until it is high-quality and
  user-approved, then execute a full fan-out research process (decompose into
  sub-questions, multi-source web search, primary source fetching, adversarial
  claim verification), and deliver a structured markdown report with citations,
  confidence levels, and open questions. Use when the user wants thorough,
  cited, multi-source research on any topic, especially when the request is
  vague and needs sharpening before research begins. Use when the user says
  "do deep research on X", "find me cited sources on Y", "research the market
  for Z before I build it", "compare these competitors and show your sources",
  or asks a broad question no single search can answer.
  Trigger: /deep-research
trigger: /deep-research
---

# /deep-research

Three-phase skill: refine the research prompt until it passes a quality rubric,
execute a full fan-out research pass, then write a structured markdown report to
disk.

---

## Phase 1: Prompt Refinement Loop

**Goal:** produce a research prompt that is specific enough to yield actionable,
verifiable findings. Do not skip this phase even if the request looks reasonable;
run at least one rubric pass.

### Rubric (all 8 items must be satisfied before proceeding)

An item counts as **satisfied** once it is either answered by the user or filled
with an explicitly-flagged default assumption (see step 3). The user-approval
checkpoint in step 5 is the real backstop, so a reasonable, clearly-stated
assumption is enough to clear an item and move on.

- [ ] **Scope clear**: the domain and boundaries are explicit (not "AI" but "LLM fine-tuning for low-resource languages")
- [ ] **Objectives measurable**: success can be assessed; "understand X" is replaced with "identify X, compare Y, quantify Z"
- [ ] **Audience + output format defined**: who reads the report and in what form (executive briefing, technical deep-dive, comparative table, etc.)
- [ ] **Constraints specified**: budget/time/region/technology limitations stated or confirmed as "none"
- [ ] **Timeframe + region**: temporal scope (last 2 years, historical, etc.) and geographic scope (global, US only, EU, etc.)
- [ ] **Success criteria**: what does a complete answer look like? What questions must be answered for the research to be "done"?
- [ ] **Sub-questions enumerated**: at least 3 concrete sub-questions that, if answered, fully address the main question
- [ ] **Sources + credibility bar stated**: peer-reviewed only? Industry reports acceptable? Blogs/forums? News? Primary sources required?

### Refinement process

1. Read the user's request. Score it against the rubric. Note every failing item.
2. **If 3 or more items fail:** ask the user targeted clarifying questions, one question per failing dimension, grouped into a single message. Wait for answers. Re-score. Repeat until 2 or fewer items fail.
3. **If 2 or fewer items fail:** draft an improved prompt yourself. Fill gaps with reasonable defaults; flag each assumption explicitly (e.g., "Assuming global scope, correct?"). Then self-critique the draft against the rubric and revise once more.
4. Present the refined prompt to the user in a clearly labelled block:

   ```
   ## Refined Research Prompt
   [full prompt text]

   Rubric status: all 8 items satisfied
   Assumptions: [list any you made]
   ```

5. Ask: "Shall I proceed with this prompt, or would you like to adjust anything?"
6. If the user modifies it, re-run the rubric pass and confirm again. Loop until the user says "go", "proceed", "yes", or equivalent.

**Do not begin Phase 2 until the user explicitly approves the refined prompt.**

---

## Phase 2: Execute the Research Fan-Out

You own execution. Work from the approved prompt verbatim; do not re-summarize it
into something narrower.

### Fan-out steps

1. **Decompose.** Turn the approved prompt into 3 to 6 sub-questions. Start from
   the sub-questions enumerated in the rubric, then add any the research needs.
2. **Search wide per sub-question.** Run 2 to 4 web searches per sub-question with
   deliberately different phrasings (vendor language, critic language, academic
   language). One query per sub-question is not a fan-out.
3. **Fetch primary sources.** Open the actual filing, paper, changelog, docs page,
   or dataset rather than an article summarizing it. A secondary source is a
   pointer to evidence, not the evidence.
4. **Cross-check every key claim** against at least 2 independent sources before
   you write it down as fact.
5. **Track citations as you go**: title, publisher, date, URL. Reconstructing
   citations at the end is how wrong attributions happen.
6. **Flag contradictions and uncertainty** instead of averaging them away.

### Optional parallelism

If a subagent/Task tool is available, dispatch one agent per sub-question with the
same credibility bar and verification standard, then collect their findings. You
still do the cross-checking and synthesis yourself; a subagent's summary is input,
not a verified finding. If the session offers a separate dedicated research harness
under a different name, you may delegate the mechanics to it and keep Phases 1 and
3 for yourself; pass the approved prompt verbatim.

### Adversarial verification standard

For every key factual claim in the output:

- Confirmed by 2 or more independent primary or authoritative sources: **High confidence**
- Confirmed by 1 primary + 1 secondary source: **Medium confidence**
- Single source only, or sources agree but share the same provenance: **Low confidence, flag it**
- Sources contradict each other: **Contradiction, report both sides explicitly**

Actively look for the counter-case. If every source you found agrees, you probably
searched in one voice; run one more search phrased from the opposing side.

---

## Phase 3: Deliver Markdown Report

Write the full report to disk. Default output path:

```
./research/<slug>-<YYYY-MM-DD>.md
```

Where `<slug>` is a 3-5 word kebab-case summary of the topic derived from the
refined prompt (e.g., `llm-finetuning-low-resource-languages-2026-06-22.md`).

`./research/` is relative to the current working directory; create it first with
`mkdir -p ./research`, and report the **absolute** path of the file you write so
the user can find it regardless of where the session started.

### Report template

```markdown
# [Research Title]

**Date:** YYYY-MM-DD
**Prompt:** [the approved refined prompt, verbatim]
**Scope:** [timeframe, region, audience]
**Credibility bar:** [source types accepted]

---

## Executive Summary

[3-5 sentences. What was found, key takeaways, confidence level overall.]

---

## Findings

### Sub-question 1: [text]

[Findings. Inline citations as [Source Name, Year](URL).]

**Confidence:** High / Medium / Low, [one-sentence reason]

### Sub-question 2: [text]

[Findings with citations.]

**Confidence:** High / Medium / Low, [one-sentence reason]

[... repeat for all sub-questions ...]

---

## Contradictions and Uncertainty

| Claim | Source A says | Source B says | Assessment |
|-------|---------------|---------------|------------|
| ...   | ...           | ...           | ...        |

[If none: "No material contradictions found."]

---

## Open Questions

Things the research could not conclusively answer, and why:

- [Question 1]: [reason: no sources, conflicting data, out of scope, etc.]

---

## Sources

1. [Full citation: Author/Org, Title, Publication, Date, URL]
2. ...

---

*Report generated by /deep-research. Verify critical claims independently
before acting.*
```

### After writing the file

1. State the absolute path of the written file.
2. Paste the **Executive Summary** section into chat.
3. List the sub-question findings as one-line bullets with their confidence levels.
4. Offer to dive deeper into any sub-question or expand the source list.

---

## Quick Reference

```
/deep-research                  # start with the user's current message as input
/deep-research "topic"          # explicit topic seed
```

## What this skill guarantees

Plain web search gives you answers. This skill adds three things on top:

1. the prompt-refinement loop with rubric gating, so the research answers the
   question the user actually has;
2. the user-approval checkpoint before any research burns time;
3. a structured, cited `.md` file written to `./research/`, so the work survives
   the session.

## Failure modes to avoid

- **Starting research before approval.** The rubric exists to prevent a
  well-executed answer to the wrong question.
- **One search per sub-question.** That is a lookup, not research.
- **Citing a summary as a primary source.** Follow the link to the original.
- **Laundering a single source into a confident claim.** Mark it Low and say so.
- **Silent scope drift.** If the research forces a scope change, say so in the
  report and in chat.
