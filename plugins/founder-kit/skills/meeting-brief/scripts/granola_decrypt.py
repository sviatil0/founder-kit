#!/usr/bin/env python3
"""Decrypt the local Granola cache and pull a meeting transcript.

Granola (as of 2026) has NO public MCP or API you can rely on. Transcripts live
in an encrypted local cache. This script walks the decryption chain and prints
either the list of available meetings or one meeting's transcript.

Chain (macOS):
  keychain "Granola Safe Storage" / "Granola Key"  -> Electron safeStorage password
  PBKDF2-SHA1(pw, salt="saltysalt", iters=1003, 16) -> AES-128-CBC key (v10 files)
  storage.dek (starts with "v10")                   -> decrypt -> DEK (base64 ascii)
  base64-decode(DEK)                                -> 32-byte AES-256 key
  cache-v6.json.enc                                 -> AES-256-GCM [12B nonce][ct][16B tag] -> JSON

Requires the `cryptography` package (not stdlib): `python3 -m pip install cryptography`.

Usage (use an absolute path; your cwd is usually the user's project, not the skill dir):
  SKILL=<absolute path of this skill's directory>
  python3 $SKILL/scripts/granola_decrypt.py --list                 # meetings: id, date, #segs, title/snippet
  python3 $SKILL/scripts/granola_decrypt.py --match "acme pricing" # transcript for best CONTENT match
  python3 $SKILL/scripts/granola_decrypt.py --id <doc-id>          # transcript for an exact id
  python3 $SKILL/scripts/granola_decrypt.py --match "..." --json   # structured JSON (segments + meta)

Notes:
  - The keychain is read only once (first run); the DEK is then cached to
    ~/.cache/meeting-brief/dek-cache (mode 0600), so later runs never touch the keychain.
    Approve the single macOS dialog (Always Allow is fine, but it is not what suppresses
    re-prompts; the cache is). The cache file is a decryption key: never commit or deploy it.
  - Speaker attribution is coarse: segment.source is "microphone" (the person recording) vs
    "system" (everyone else), OR a transcriber name like "assemblyai" with no side split at all.
    detected_speaker_name is usually null.
"""
import os, sys, json, base64, hashlib, subprocess, argparse, glob, re
from urllib.parse import unquote
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
except ImportError:
    sys.exit("This script needs the 'cryptography' package. Install it with:\n"
             "    python3 -m pip install cryptography")

G = os.path.expanduser("~/Library/Application Support/Granola")
DEK_CACHE = os.path.expanduser("~/.cache/meeting-brief/dek-cache")


def keychain_pw():
    r = subprocess.run(
        ["security", "find-generic-password", "-w",
         "-s", "Granola Safe Storage", "-a", "Granola Key"],
        capture_output=True, text=True, timeout=90)
    if r.returncode != 0:
        raise SystemExit(f"keychain read failed (rc={r.returncode}). "
                         f"Approve the macOS dialog, or check that Granola is installed. {r.stderr.strip()}")
    return r.stdout.strip()


def _unpad(b):
    if not b:
        return b
    p = b[-1]
    return b[:-p] if 0 < p <= 16 else b


def _dek():
    if os.path.exists(DEK_CACHE):
        return open(DEK_CACHE, "rb").read()
    pw = keychain_pw()
    sk = hashlib.pbkdf2_hmac("sha1", pw.encode(), b"saltysalt", 1003, 16)
    blob = open(os.path.join(G, "storage.dek"), "rb").read()
    assert blob[:3] == b"v10", "storage.dek is not v10; Granola format may have changed"
    dec = Cipher(algorithms.AES(sk), modes.CBC(b" " * 16)).decryptor()
    dek = _unpad(dec.update(blob[3:]) + dec.finalize())
    os.makedirs(os.path.dirname(DEK_CACHE), exist_ok=True)
    with open(DEK_CACHE, "wb") as f:
        f.write(dek)
    os.chmod(DEK_CACHE, 0o600)   # it is a decryption key: owner-only
    return dek


def _decrypt_cache():
    dek = _dek()
    key = base64.b64decode(dek + b"=" * (-len(dek) % 4))
    if len(key) not in (16, 24, 32):
        raise ValueError(f"unexpected DEK length {len(key)} after base64 decode")
    blob = open(os.path.join(G, "cache-v6.json.enc"), "rb").read()
    nonce, ct, tag = blob[:12], blob[12:-16], blob[-16:]
    dec = Cipher(algorithms.AES(key), modes.GCM(nonce, tag)).decryptor()
    pt = dec.update(ct) + dec.finalize()
    return json.loads(pt)["cache"]["state"]


def load_cache():
    """Decrypt the cache; if a stale/poisoned key cache is the cause, drop it and retry once."""
    try:
        return _decrypt_cache()
    except Exception:
        if os.path.exists(DEK_CACHE):
            os.remove(DEK_CACHE)
            print("[warn] cached key failed to decrypt; cleared the key cache and retrying keychain",
                  file=sys.stderr)
            return _decrypt_cache()
        raise


def _titles_from_leveldb():
    """Best-effort: Granola writes analytics events into its Local Storage leveldb
    that pair a meeting id with a URL-encoded 'summary' (the calendar title).
    Titles are NOT stored in the decrypted cache, so this is the only local source."""
    titles = {}
    base = os.path.join(G, "Local Storage", "leveldb")
    files = glob.glob(os.path.join(base, "*.ldb")) + glob.glob(os.path.join(base, "*.log"))
    for f in files:
        try:
            blob = open(f, "rb").read().decode("latin-1", "ignore")
        except Exception:
            continue
        # events contain: .../meeting/<id>... and ..."summary"%3A"<title>"...
        for m in re.finditer(r'meeting/([0-9a-f-]{36})', blob):
            mid = m.group(1)
            window = blob[max(0, m.start() - 4000): m.end() + 4000]
            # events store titles as \"summary\"%3A\"<title>\" (JSON-escaped + URL-encoded).
            # Title itself has no bare " or \, so capture up to the closing escaped quote.
            sm = re.search(r'summary\\?"?%3A\\?"?([^"\\]{3,140}?)\\?"', window) \
                 or re.search(r'"summary"\s*:\s*"([^"]{3,140})"', window)
            if sm and mid not in titles:
                t = unquote(sm.group(1)).strip()
                if t and t.lower() not in ("null", "undefined"):
                    titles[mid] = t
    return titles


def meetings(state):
    """Return [{id, title, date, n, snippet}] for every meeting that has a transcript.
    Titles come from leveldb (best-effort); date/snippet come from the segments so a
    meeting is always identifiable even when no title is found."""
    titles = _titles_from_leveldb()
    out = []
    for mid, segs in (state.get("transcripts", {}) or {}).items():
        segs = segs or []
        date = (segs[0].get("start_timestamp", "") if segs else "")[:10]
        snippet = " ".join((s.get("text") or "").strip() for s in segs[:6])[:90]
        out.append({"id": mid, "title": titles.get(mid, ""), "date": date,
                    "n": len(segs), "snippet": snippet})
    return out


def _label(seg):
    """Normalize a segment's speaker. detected_speaker_name wins; otherwise fall back
    to the source, which may be 'microphone'/'system' or a transcriber name (e.g.
    'assemblyai'). Attribution is coarse; see the reference notes."""
    if seg.get("detected_speaker_name"):
        return seg["detected_speaker_name"]
    src = seg.get("source") or "?"
    return {"microphone": "OURS(mic)", "system": "THEM"}.get(src, src)


def merged_transcript(segments):
    """Merge consecutive same-speaker segments into readable turns."""
    lines, cur, buf = [], None, []
    for s in segments:
        spk = _label(s)
        if spk != cur:
            if buf:
                lines.append(f"[{cur}] " + " ".join(buf))
            cur, buf = spk, [(s.get("text") or "").strip()]
        else:
            buf.append((s.get("text") or "").strip())
    if buf:
        lines.append(f"[{cur}] " + " ".join(buf))
    return "\n\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--match", help="match on meeting content (and title if present)")
    ap.add_argument("--id", help="exact document id")
    ap.add_argument("--json", action="store_true", help="emit structured JSON")
    a = ap.parse_args()

    state = load_cache()
    ms = meetings(state)
    trs = state.get("transcripts", {})

    if a.list or (not a.match and not a.id):
        for m in sorted(ms, key=lambda x: x["date"], reverse=True):
            label = m["title"] or f'“{m["snippet"]}…”'
            print(f'{m["id"]}\t{m["date"]}\t{m["n"]:>4} segs\t{label}')
        return

    mid = a.id
    if not mid and a.match:
        q = a.match.lower()
        # Match by CONTENT first; titles are often missing, but the query almost
        # always appears in the meeting it belongs to (a name, a company, a phrase).
        def score(m):
            title_hit = 5 if q in (m["title"] or "").lower() else 0
            text = " ".join((s.get("text") or "") for s in trs.get(m["id"], [])).lower()
            return title_hit + text.count(q)
        ranked = sorted(ms, key=score, reverse=True)
        if ranked and score(ranked[0]) > 0:
            mid = ranked[0]["id"]
            print(f'[matched] {mid}: {ranked[0]["title"] or ranked[0]["snippet"]}', file=sys.stderr)
    if not mid or mid not in trs:
        raise SystemExit("no transcript matched. Run --list to see available meetings.")

    segs = trs[mid]
    sources = {s.get("source") for s in segs}
    if not sources & {"microphone", "system"}:
        print(f"[warn] this meeting has no microphone/system split (sources={sources or '{}'}); "
              f"speaker separation is unavailable; infer OURS/THEM from the content itself.",
              file=sys.stderr)
    if a.json:
        meta = next((m for m in ms if m["id"] == mid), {"id": mid})
        json.dump({"meta": meta, "segments": segs, "text": merged_transcript(segs)}, sys.stdout, indent=2)
    else:
        print(merged_transcript(segs))


if __name__ == "__main__":
    main()
