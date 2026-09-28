# Researching the people and using the company's brand

Two enrichments make a meeting brief feel bespoke and better informed: **web research on
the attendees**, and the **other company's real brand color and logo**. Both are optional and both
are gated on the user confirming who is involved (SKILL.md step 3). Researching or branding the
wrong person or company is worse than skipping it, and transcripts mishear names.

## Researching the people

Goal: sharpen the People tab and the read on the person's pains with *public professional*
context, meaning who they are, what they have done, and what they likely care about.

**Confirm first.** Only research names the user confirmed. Get the correct spelling and the
company, so you research the right person (there are many "John Smith"s).

**How.** For each key attendee (prioritize the external partner or decision maker), search the web
for role history, current title, company, tenure, notable projects, public talks and press. If the
`deep-research` skill is available, use it for the important person; otherwise a few targeted
`WebSearch` or `WebFetch` calls are enough. Good queries pin the person to their org:
`"<name>" <company> CEO`, `"<name>" linkedin <company>`, `<name> <company> interview`.

**Write it down** in `people[].research` in `data.js`: one to three sentences of the most relevant
facts, not a dump. Prefer facts that inform the pitch, such as their background, what they have
built, their stated priorities. Attribute confidence honestly; if you are unsure it is the same
person, say so and keep it vague rather than guess.

**Guardrails (important).**

- **Public professional info only.** Role, employer, public statements, published bio. Do not
  compile personal or sensitive data (home, family, finances, anything not professionally public).
- **Verify identity.** Common names collide. If you cannot confirm it is the same individual, do
  not attach the research.
- **Do not state rumor as fact.** Cite sources to the user; flag anything shaky.
- This is meeting prep, not a background check. The bar is "would this person be comfortable
  seeing what you wrote about them." If not, cut it.

## Using the company's brand

For a partner-facing brief, the other company's brand color and logo *are* the signature; they
make it instantly feel made for them.

**Whose brand? Default: theirs.** When the meeting is with a person from a company, brand the
brief with THAT company's color and logo. This holds even when the owner is pitching their own
product or program: bringing a company on board still wears **that company's** brand, because the
brief is made for them.

The one exception: the owner is **speaking on behalf of another company**, for example presenting
a client's or portfolio company's product to an investor. Then the brief wears the *represented*
company's design system, since it acts as that company's material. If the transcript leaves it
ambiguous which hat the owner wore, ask; it changes the whole design.

**Fetch candidates:**

```bash
SKILL="<absolute path of this skill's directory>"   # the dir that contains SKILL.md
python3 "$SKILL/scripts/brand_fetch.py" acme.com
```

It prints logo candidates (apple-touch-icon is usually the crispest square mark), a `theme-color`,
the social-share `og:image`, and fallbacks (a logo CDN that may 404, and a favicon service).
Best-effort; sites vary. If nothing good comes back, web-search `"<company> logo png"` or
`"<company> brand guidelines"` and eyeball it.

**Derive the palette.** A script cannot reliably read colors out of a logo, but you can. Download
the best logo, view it (Read the image), and pick one or two accent colors from it. Prefer the
`theme-color` meta if present, since it is the site's declared brand color. Aim for one confident
accent that reads on a dark background; if the brand color is too light or too dark for the base,
use it as an accent on key elements rather than as body text.

**Apply it.** In `data.js` `meta`:

- `brandColor: "#00539B"`. The starter sets `--blue` to this, so the whole accent system adopts it.
- `logo: "logo.svg"`. Drop the downloaded file next to `index.html` (or use a URL); it renders in
  the header. Prefer SVG or PNG with transparency.

Keep it disciplined: brand color as the accent plus the logo in the header is enough. Do not
repaint every surface; the dark base still carries the design, and the brand is the accent and
the mark.

**Copyright and deploy caveat.** Using a company's logo in a private, gated prep brief for a
meeting *with that company* is normal. If the brief will be **deployed publicly**, a third
party's logo is more sensitive, so tell the user, and prefer a private or gated deploy, or drop
the logo and keep just the brand color. (See the deploy checklist in `dashboard-build.md`; the
logo file, if a downloaded asset, is fine to ship, but the *raw transcript* never is.)
