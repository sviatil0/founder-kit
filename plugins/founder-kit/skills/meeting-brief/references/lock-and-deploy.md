# Lock and deploy (the default finish)

A finished brief is **password-locked, live on Vercel, and reported as exactly one URL plus
one password**. Past sessions failed here more than anywhere except fidelity: two half-deployed
URLs and the user asking which link to use, deploys landing on the wrong Vercel account, a
password the user had to ask for twice, and an invented password whose words meant nothing to
anyone. The rules below each trace to one of those failures.

## 1. Pick the password and names before deploying

- **Derive, do not invent.** Project name from the contact or company: `acme-brief`,
  `northwind-brief`. Password memorable and self-explaining: `<company>-<topic-word>-<MMDD>`
  (for example `acme-pricing-0707`), or `scripts/password_protect.py --gen` for a random
  word-triple. Opaque creative words confuse the user when they forward them.
- **Surface the password immediately and in the final summary.** The user shares it in a
  follow-up message; if they have to ask "what's the password?", that is a failure.

## 2. Gate the site (default: Vercel middleware)

Copy the proven gate into the brief directory (it has protected real partner briefs in production):

```bash
SKILL="<absolute path of this skill's directory>"   # the dir that contains SKILL.md
cp "$SKILL/assets/gate/middleware.js" "$SKILL/assets/gate/package.json" ./<meeting>-brief/
```

Then in `middleware.js` replace every `__PLACEHOLDER__` (password, salt, org label, title,
audience line, contact line; the header comment explains each). Two details that matter:

- The **contact line** on the lock screen should give a locked-out recipient a real path back to
  the owner instead of a dead end. Build it from the **Owner config** (see SKILL.md): the owner's
  phone if they publish one ("Lost the password? Call or text <owner phone>."), otherwise
  "Lost the password? Reply to the email that sent you this link." Never invent contact details.
- **Restyle the lock page** to the brief's palette (swap the CSS vars). It is the first
  thing the recipient sees, and a mismatched gate reads as phishing.

How it works: every request without the auth cookie gets a styled 401 login page; POSTing the
right password to `/unlock` sets an HttpOnly `brief_auth` cookie holding SHA-256(password:salt),
valid 30 days. The password lives only in `middleware.js`, which executes server-side and is
never served. The static files behind it stay editable, so redeploys do not touch the gate.

**Alternative: single encrypted file** (no Vercel needed, or the user wants to email the
brief as an attachment). `python3 "$SKILL/scripts/password_protect.py" <brief-dir> --gen`
inlines everything into one AES-256-GCM-encrypted `protected/index.html` that decrypts in the
browser. True encryption at rest, and it works from `file://`. Use it when the deliverable is a
file rather than a URL; the middleware gate is otherwise better (multi-file stays editable, the
cookie persists).

## 3. Deploy: scope first, then ship

**Confirm the account before the first deploy.** This is the number one past friction: a free-tier
limit hit on one account mid-session, and deploys landing on the wrong team.

```bash
vercel whoami                        # if it errors: vercel login
vercel teams ls                      # then ASK the user which scope if more than one
vercel deploy --prod --yes --scope <team>
```

Notes learned the hard way:

- `vercel deploy --yes` with no git repo defaults to **production**, and non-interactive mode
  needs an explicit `--scope`; it will not guess the team.
- Keep a `.vercelignore` excluding the raw transcript and private sources:
  ```
  assets/transcript.txt
  *.pdf
  .env*
  node_modules
  .vercel
  ```
  The middleware gate protects served pages, but the transcript has no business being in the
  deployment at all.
- **Redeploy after every content edit.** A stale URL presented as final is a fidelity failure in
  the user's eyes. One canonical URL; never leave a second half-alive deployment for the user to
  guess between.

## 4. Verify the LIVE site, not the local copy

```bash
URL=https://<project>.vercel.app
curl -s -o /dev/null -w '%{http_code}\n' "$URL/"          # 401: the gate, not the content
curl -s "$URL/" | grep -ci "password"                     # lock page renders
curl -s "$URL/data.js" -o /dev/null -w '%{http_code}\n'   # 401: assets gated too
# unlock and confirm the CONTENT is the latest version:
TOKEN=$(curl -s -D - -o /dev/null -X POST --data-urlencode "password=<pw>" "$URL/unlock" \
        | sed -n 's/^set-cookie: brief_auth=\([^;]*\).*/\1/Ip')
curl -s -H "Cookie: brief_auth=$TOKEN" "$URL/data.js" | grep -c "<distinctive new phrase>"
```

Then **screenshot the deployed page through the gate** (Playwright or an agent browser) at desktop
and about 390px mobile widths; a broken grid shipped to a live URL has happened before. Check
every tab, the CTA buttons, and the lock screen itself.

## 5. Visitor analytics (the user asks every time)

Two options; offer both, implement what they pick.

- **Vercel Web Analytics.** Page views and visitors in the Vercel dashboard. Two steps, and the
  order matters: (1) the user enables Analytics for the project at
  `https://vercel.com/<scope>/<project>/analytics` (you cannot toggle it via CLI, so give them
  the link), then (2) add the tracking snippet and **redeploy** so `/_vercel/insights` is
  provisioned. For a plain static site add to `index.html`:
  `<script defer src="/_vercel/insights/script.js"></script>`.
- **Unique-viewer counter** (self-contained, counts distinct IPs). A serverless function backed
  by a private Vercel Blob store storing only salted SHA-256 IP hashes, never raw IPs.
  Provision with `vercel blob create-store <name> --access private`; the function get/puts a
  `views.json` blob; keep `BLOB_READ_WRITE_TOKEN` out of the deploy. Vercel ignores a client
  `x-forwarded-for`, so counts cannot be spoofed. Delete the blob before real visitors arrive.

## 6. Hand off in one block

End with a single message the user can act on without asking anything back:

```
Live: https://<project>.vercel.app      (only URL; old previews deleted)
Password: <password>                     (30-day cookie once entered)
Analytics: https://vercel.com/<scope>/<project>/analytics
This version includes: <the 2-3 things that changed since they last looked>
```

Offer a short companion message (link plus password, human tone, no em dashes) they can send to
the recipient: one draft, not options, and copy it to the clipboard if they want it there.
**Never send it yourself**; stage the draft and let the user send.
