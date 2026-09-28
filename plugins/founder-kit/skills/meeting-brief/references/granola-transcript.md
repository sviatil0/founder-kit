> **Optional, macOS-only.** This whole file is a convenience branch for people who record with
> Granola on a Mac. The skill's default path is a pasted or exported transcript file, which works
> on every platform with no dependencies. Skip this file entirely unless the user says they use
> Granola and is on macOS.

# Getting a Granola transcript

Granola has **no reliable public MCP or API**. Users often *think* there is a "Granola MCP"
(sometimes misspelled "graola"); there is not one connected in most environments, and Granola
ships none officially. Do not waste a turn hunting for a tool. The transcript lives in an
encrypted local cache, so decrypt it.

The bundled `scripts/granola_decrypt.py` does the whole thing. This file explains what it does
so you can fix it when Granola changes its format.

## Fast path

Use an **absolute path**; your cwd is usually the user's project, not the skill dir. The script
needs the `cryptography` package (not stdlib):

```bash
SKILL="<absolute path of this skill's directory>"   # the dir that contains SKILL.md
python3 -m pip install cryptography   # once; skip if already installed
python3 "$SKILL/scripts/granola_decrypt.py" --list                  # id, date, #segs, title/snippet
python3 "$SKILL/scripts/granola_decrypt.py" --match "acme pricing"  # best CONTENT match (see below)
python3 "$SKILL/scripts/granola_decrypt.py" --id 53861a67-...       # exact id
python3 "$SKILL/scripts/granola_decrypt.py" --match "..." --json    # {meta, segments[], text}
```

**Run the first invocation in the background.** It blocks on a one-time macOS keychain dialog
("security wants to use the Granola Safe Storage key"). Have the user approve it. The keychain is
read **only on the first run**; the DEK is then cached to `~/.cache/meeting-brief/dek-cache`
(mode 0600), so later runs never touch the keychain. (Clicking "Always Allow" is fine, but the
cache, not the ACL, is what prevents re-prompts, because each run is a fresh `security` and
`python3` process.)

If the user already exported or pasted a transcript, or shared a Granola "Share" link, just use
that and skip all of this.

## The decryption chain (macOS)

Data lives in `~/Library/Application Support/Granola/`.

1. **Keychain to safeStorage password.** Electron encrypts local files with a key stored in the
   macOS keychain under service `Granola Safe Storage`, account `Granola Key`:
   ```bash
   security find-generic-password -w -s "Granola Safe Storage" -a "Granola Key"
   ```
2. **Password to v10 AES key.** `AES-128-CBC` key = `PBKDF2-HMAC-SHA1(pw, salt="saltysalt",
   iterations=1003, dklen=16)`, IV = 16 space bytes (`0x20`). This is the standard Chromium and
   Electron `safeStorage` scheme; files it encrypts start with the ASCII bytes `v10`.
3. **Decrypt `storage.dek`** (starts with `v10`) with that key to get the **DEK**. The DEK comes
   out as **base64 ASCII** (about 44 chars). Base64-decode it to get the real **32-byte AES-256
   key**. This is the step people miss; using the DEK bytes directly fails.
4. **Decrypt `cache-v6.json.enc`** with the 32-byte key using **AES-256-GCM**, layout
   `[12-byte nonce][ciphertext][16-byte tag]`, which yields JSON. (These payload files are *not*
   `v10`-prefixed; only keychain-wrapped files like `storage.dek` are.)
5. **Read the transcript** at `state.cache.state.transcripts[<docId>]`, a list of segments:
   ```json
   {"text": "...", "source": "microphone|system", "start_timestamp": "...",
    "detected_speaker_name": null, "is_final": true}
   ```

## Finding the right meeting id

`transcripts` is keyed by document id, and the decrypted cache does **not** contain a
`documents` store with titles, so match by **transcript content**, which is more robust anyway.
`granola_decrypt.py --match "<query>"` scores every meeting by how often the query appears in its
text and picks the winner, so a name, company, or distinctive phrase from the call finds it even
with no title. `--list` shows each meeting's date, segment count, and a content snippet.

Titles are a nice-to-have: Granola writes analytics events with the calendar `summary` (title)
into its Local Storage leveldb, and the script extracts them **best-effort**. That store is
partly Snappy-compressed, so titles will not always survive intact. Do not depend on them; the
content snippet is the reliable identifier. To hunt manually:

```bash
grep -rlai "<name or phrase>" "$HOME/Library/Application Support/Granola/Local Storage/leveldb/"
strings <that-file> | grep -i "meeting/\|summary"   # app://ui/#/meeting/<doc-id> and titles
```

## Speaker attribution (important caveat)

Attribution is coarse. `source` is `"microphone"` (audio from the mic, meaning the person
recording) versus `"system"` (everything through the speakers, usually *everyone else*, lumped
together). `detected_speaker_name` is typically `null`. So you can reliably separate "our side"
from "their side", but not individual speakers on a multi-person call. Infer individuals from
content (a CEO talking about "my stores", a new hire introducing themselves) rather than trusting
the labels. Transcripts are speech to text, so **names are frequently misheard**; verify spellings
against email signatures or the calendar, never the transcript.

## When it breaks

- **Keychain read hangs (up to 90s) then times out.** The approval dialog is on the user's
  screen, waiting. Have them approve it. Run the script in the background so it does not block you;
  the DEK is cached after, so it is a one-time cost.
- **`security` returns empty or "Not authorized".** The dialog was dismissed or denied. Re-run
  and approve it.
- **Decryption fails after a previous successful run.** The cached key may be stale or poisoned.
  The script auto-clears `~/.cache/meeting-brief/dek-cache` and retries the keychain once on
  failure; if it still fails, delete that file by hand and re-run.
- **All segments share one non-mic/system source** (for example every `source` is `assemblyai`).
  This meeting has **no OURS/THEM split**; `merged_transcript` collapses it into a single labeled
  turn, and the script prints a `[warn]` to that effect. You must infer our-side versus their-side
  from the content itself (self-intros, "my stores", who is asking versus answering). Do not trust
  the labels.
- **`storage.dek` does not start with `v10`, or GCM decrypt fails on a clean cache.** Granola
  changed its format; `cache-v6.json.enc` decrypt is not guaranteed forever. Inspect headers with
  `xxd`, and try the sibling schemes (CBC with a 16-byte IV prefix; 32 or 16-byte key variants).
- **`transcripts` is empty but `cache-v6.json` (unencrypted, about 2KB) exists.** That plaintext
  file is a stub. The real data is only in `cache-v6.json.enc` (hundreds of KB). Do not be fooled
  by it.
- **Not on macOS.** This script is **macOS-only**. On Linux and Windows *both* the key read
  (step 1: Linux libsecret or `secret-tool`; Windows DPAPI) *and* the key derivation (step 2,
  where Windows wraps keys with DPAPI rather than PBKDF2 and `saltysalt`) differ, so the script
  must be ported, not tweaked in one line. Fall back to asking the user to paste or export the
  transcript; that path is always available.

## Privacy

The transcript is confidential meeting content. Keep it in the working or scratch directory, never
commit it, and never include the raw transcript file in a public deploy (see the deploy checklist
in `dashboard-build.md`). The cached DEK at `~/.cache/meeting-brief/dek-cache` is a decryption
key, so treat it as a secret and do not deploy or commit it either.
