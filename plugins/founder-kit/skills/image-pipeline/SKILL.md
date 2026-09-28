---
name: image-pipeline
description: >
  Judged image-generation pipeline (ideas -> best idea -> prompts -> best prompt
  -> images -> best image -> compare against the brief -> loop) that turns a
  one-line brief into a finished asset using the Gemini image models over a
  plain REST call. Claude does every reasoning stage, including looking at the
  rendered images and scoring them; the image model only renders pixels.
  Use when the user says "generate an image for the landing page hero",
  "make me an app icon / og:image / illustration", "I need a texture or
  background for this component", "create an infographic from these numbers",
  or otherwise asks for AI-generated images, textures, or graphics for a
  project. Trigger: /image-pipeline
trigger: /image-pipeline
---

# /image-pipeline

Turn a one-line image **brief** into a finished image through a judged,
self-correcting loop. You (Claude) run every reasoning stage yourself: ideation,
selection, prompt writing, scoring, and the final visual comparison, using your
own vision. The image model is called for one thing only: rendering pixels. Never
outsource the judgment to a text model; you are the judge.

---

## Step 0: Credentials (do this before anything else)

The pipeline needs one env var: `GEMINI_API_KEY`.

```bash
if [ -z "$GEMINI_API_KEY" ]; then echo "MISSING"; else echo "present"; fi
```

### If the key is missing

Print exactly this, then **stop**:

```
Image generation needs a Google AI Studio API key.

1. Get a free key at https://aistudio.google.com/apikey
2. export GEMINI_API_KEY=your_key_here
   (add it to your shell profile or .env.local so it persists)
3. Re-run /image-pipeline

Already using Google Cloud? See the Vertex fallback in the image-pipeline skill
and say so, and I will use your existing gcloud login instead.
```

Then end the turn. Do not call the API, do not retry, do not poll for the
variable, do not loop. One check, one message, stop. The user has to go get a key
in a browser; nothing you do in this session can produce one. If you already did
the ideation stages before noticing, keep them in the reply so the work is not
lost, then stop.

### If the key is present

Do not echo it, do not paste it into a file, do not include it in any output you
write to disk. Reference it only as `$GEMINI_API_KEY` inside commands.

---

## The model

Verified against `https://ai.google.dev/gemini-api/docs/image-generation`:

| Model id | Use it for |
|---|---|
| `gemini-3.1-flash-image` | **Default.** Fast, built for high-volume generation. Start here. |
| `gemini-3-pro-image` | Professional asset production. Escalate here only if flash falls short after a round or two, or the image carries a lot of text. |
| `gemini-2.5-flash-image` | Older low-latency model. Use only if you have a reason to pin it. |

These models render legible text reasonably well but not perfectly. For
infographics, keep on-image text short, spell it in the prompt verbatim, and
verify every word in the scoring stage.

Generated images carry a SynthID watermark. That is expected.

---

## Primary path: REST with `GEMINI_API_KEY`

Endpoint and request shape per the docs above.

**1. Build the request body** with `jq` so long prompts with quotes and newlines
cannot break the shell:

```bash
SCRATCH=./.image-pipeline   # scratchpad dir for this run
mkdir -p "$SCRATCH"

jq -n \
  --arg model "gemini-3.1-flash-image" \
  --arg prompt "$PROMPT" \
  --arg aspect "4:5" \
  '{
     model: $model,
     input: [ { type: "text", text: $prompt } ],
     response_format: {
       type: "image",
       mime_type: "image/png",
       aspect_ratio: $aspect,
       image_size: "2K"
     }
   }' > "$SCRATCH/body.json"
```

**2. Call the API:**

```bash
curl -s -X POST "https://generativelanguage.googleapis.com/v1beta/interactions" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  --data-binary @"$SCRATCH/body.json" \
  -o "$SCRATCH/resp.json"
```

The docs also show an optional `-H "Api-Revision: <date>"` header for pinning the
API revision. Add it if you want the request shape frozen; copy the current value
from the docs page rather than guessing one.

**3. Save the image.** The image block carries base64 in `data` with its
`mime_type`; pull the first image block out of the response wherever it is nested:

```bash
jq -r '[.. | objects | select(.type == "image" and has("data")) | .data] | first' \
  "$SCRATCH/resp.json" | base64 --decode > "$SCRATCH/round1_a.png"
```

**4. If no image came back,** the response usually explains why (safety refusal,
malformed field, quota). Read it instead of retrying blindly:

```bash
jq -r '[.. | objects | select(.type == "text") | .text] | join("\n")' "$SCRATCH/resp.json"
jq -r '.error // empty' "$SCRATCH/resp.json"
```

- HTTP 400 or a field complaint: the body is wrong. Fix it, then one more attempt.
- 401 or 403: the key is invalid or the API is not enabled on that key. Say so and
  stop; point the user back at https://aistudio.google.com/apikey.
- 429 or 5xx: transient. **At most 3 attempts total per image**, with a few
  seconds between them, then stop and report. Never sit in a retry loop.
- Safety refusal: change the prompt, do not re-send the same one.

**Options worth knowing:** `aspect_ratio` accepts the documented ratios, which
include `1:1`, `16:9`, `9:16`, `4:5`, `5:4`, `3:4`, `2:3`, plus extreme banner
ratios such as `4:1` and `1:4`; check the docs page for the full current list.
`image_size` accepts `512px`, `1K`, `2K`, `4K` (uppercase `K`). To generate N
candidates, run the same call N times; each call is an independent render.

**Editing an existing image** (iterating on a render, restyling a screenshot):
send an extra input block alongside the text:
`{"type": "image", "mime_type": "image/png", "data": "<base64>"}`.

---

## Fallback path: Vertex AI through an existing gcloud login

Only for users who already have an authenticated Google Cloud setup and would
rather bill it through their own project. Never set this up for them, and never
assume a project or an account; read both from their environment.

```bash
gcloud auth print-access-token >/dev/null || { echo "gcloud is not authenticated"; exit 1; }
PROJECT="$(gcloud config get-value project 2>/dev/null)"
REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
```

Then call the Vertex endpoint for the same model family:

```
POST https://${REGION}-aiplatform.googleapis.com/v1/projects/${PROJECT}/locations/${REGION}/publishers/google/models/<model>:generateContent
Authorization: Bearer $(gcloud auth print-access-token)
```

The Vertex request and response shape is the `generateContent` shape, not the
AI Studio shape used above, and which image models are enabled varies by project.
Check the current Vertex image-generation docs before composing the body, and if
the model is not provisioned on their project, say so plainly and fall back to the
API-key path instead of hunting through regions.

If neither path is available, stop and print the missing-key message from Step 0.

---

## The pipeline

Work through the stages in order. Keep a short running note (a scratchpad file in
`$SCRATCH`) of the brief, the chosen idea, the winning prompt, and each round's
verdict, so a later round does not repeat a dead end.

**0. Frame the brief.** Restate in one or two sentences: what the image is for,
where it will live, the subject, the mood, hard constraints (aspect ratio, "no
text", palette, "no people"), and what "good" means for THIS image. If the brief is
vague, pin it yourself and state your choice; only ask the user when a constraint
genuinely blocks you.

**1. Generate ideas.** Produce **4 to 6 distinct visual concepts** for the brief,
different angles rather than variations of one. Each: a one-line concept plus one
line on why it fits.

**2. Choose the best idea.** Score the ideas against the brief (fidelity to
purpose, distinctiveness, feasibility for the model, brand fit). Pick **one**,
occasionally two if they are genuinely competing. State why in one line.

**3. Generate prompts.** For the chosen idea write **3 to 4 full image prompts**
that vary composition, framing, lighting, and finish. A good prompt names: subject,
style/medium, composition, lighting, palette, aspect, and negative constraints
("no text", "no people", "no lettering") when needed. Be concrete and sensory;
avoid vague adjectives.

**4. Choose the best prompts.** Pick the **1 to 2** most likely to deliver the
idea. Say why.

**5. Generate images.** Run the REST call for each chosen prompt, **2 to 3 renders
per prompt**, so scoring has real choices. Write them to `$SCRATCH` with names that
encode the round and the prompt (`round1_a-1.png`, `round1_a-2.png`).

**6. Score the images, and LOOK at them.** Read each generated PNG (the Read tool
renders it) and score every candidate against a rubric: (a) fidelity to the chosen
idea, (b) aesthetic quality, (c) technical correctness (anatomy, artifacts,
tiling/seams if relevant), (d) brand and palette fit, (e) text legibility and
spelling if the image carries text. Pick the single best. **Never score an image
you have not actually viewed**, and never describe an image you did not open.

**7. Compare the winner against the brief.** Hold the best image next to the
ORIGINAL brief and idea. Does it deliver the purpose? List concrete gaps ("stars
too sparse", "text misspelled", "wrong crop", "reads generic"). Be honest; this
gate is what makes the loop work.

**8. Loop or stop.**
- Winner satisfies the brief: stop. Output the final image path, the exact prompt
  used, and one line on why it works.
- Material gaps remain: revise. Small gap, tweak the winning prompt and rerun
  stages 3 to 5. The idea itself is wrong, return to stage 2 and pick another.
  Regenerate, then re-judge.
- **Cap at 3 to 4 rounds.** If still short at the cap, deliver the best so far,
  name the residual gap, and say what a different approach (or the pro model)
  would need. Do not loop forever.

---

## Output

Deliver: the final image path, the winning prompt (so it is reproducible), the
round count, and a one-line rationale. If the images are for a website or
dashboard, hand them off where they belong (for example, copy into `public/`), but
only wire them into a design after the user has seen the result.

---

## Notes

- **Cost.** Each render bills the user's Google account. A few candidates per
  prompt, 1 to 2 prompts, 3 to 4 rounds is plenty; do not fan out to dozens of
  images without a reason.
- **No helper script ships with this skill.** Everything is two `jq` calls and a
  `curl`, which keeps the model id and the request shape visible and easy to
  update when the docs move.
- **Requirements:** `curl` and `jq`. If `jq` is missing, build the JSON body with
  `python3 -c` and parse the response the same way; do not hand-concatenate JSON
  around a user-supplied prompt.
- **Safety.** Public and professional content only. Never generate a real person's
  likeness, a real brand's logo, or anything deceptive. Decline and explain rather
  than producing a near-miss.
- **Provenance.** Tell the user the output is AI-generated and watermarked with
  SynthID if they are about to publish it somewhere that cares.
