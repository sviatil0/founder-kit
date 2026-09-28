#!/usr/bin/env python3
"""Password-protect a static meeting dashboard for deployment.

Inlines the dashboard (index.html + local css/js/images) into a single HTML
document, encrypts it with AES-256-GCM (key from PBKDF2-HMAC-SHA256, 600k
iterations), and writes a self-contained locked page to <out>/index.html.
The browser decrypts with Web Crypto, so no server is needed; works on any static host
and on file://. A wrong password fails GCM authentication, so there is no
oracle beyond try-and-fail; the content is actually encrypted at rest, not
just hidden behind a client-side "if".

Usage:
  python3 password_protect.py <dashboard-dir> --password "correct horse..."
  python3 password_protect.py <dashboard-dir> --gen          # generates one
  python3 password_protect.py <dashboard-dir> --password X --out ./locked \
      --title "Meeting Brief"

Output dir defaults to <dashboard-dir>/protected/ (excluded from inlining).
Deploy the OUTPUT dir only; it contains a single encrypted index.html.

Requires: cryptography (same dependency as granola_decrypt.py).
"""
import argparse
import base64
import mimetypes
import os
import re
import secrets
import sys
from pathlib import Path

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
except ImportError:
    sys.exit("Missing dependency: python3 -m pip install cryptography")

ITERATIONS = 600_000  # must match the JS decryptor below

WORDS = ("acorn alder amber anchor aspen basalt bay beacon birch bloom bluff "
         "breeze brook canyon cedar cliff cloud coast comet coral cove crane "
         "creek crest dawn delta drift dune ember fable falcon fern flint fox "
         "gale garnet glade glen grove harbor hazel heron hollow indigo iris "
         "isle jasper juniper kestrel knoll lagoon lark laurel ledge linden "
         "lotus lumen maple marsh meadow mesa mist moss north oak ocean onyx "
         "opal orbit osprey otter pearl pine plume prairie quartz quill rain "
         "reef ridge river rowan sage shale shore sierra slate sparrow spruce "
         "stone summit swift tarn thicket tide timber topaz trail tundra vale "
         "vista wave willow wren zephyr").split()


def gen_password() -> str:
    return "-".join(secrets.choice(WORDS) for _ in range(3)) + f"-{secrets.randbelow(90) + 10}"


def inline(dash: Path, out: Path) -> str:
    """Return index.html with local css/js inlined and local images as data URIs."""
    html = (dash / "index.html").read_text(encoding="utf-8")

    def read_local(name: str) -> str | None:
        p = dash / name
        if p.is_file() and p.resolve().is_relative_to(dash.resolve()):
            return p.read_text(encoding="utf-8")
        return None

    def css_sub(m):
        body = read_local(m.group(1))
        return f"<style>\n{body}\n</style>" if body is not None else m.group(0)

    def js_sub(m):
        body = read_local(m.group(1))
        if body is None:
            return m.group(0)
        return "<script>\n" + body.replace("</script", "<\\/script") + "\n</script>"

    html = re.sub(r'<link[^>]*rel=["\']stylesheet["\'][^>]*href=["\']([^"\':]+)["\'][^>]*/?>', css_sub, html)
    html = re.sub(r'<script[^>]*src=["\']([^"\':]+)["\'][^>]*>\s*</script>', js_sub, html)

    # Local images (logo etc.) become data URIs wherever they are referenced (HTML or data.js).
    for p in dash.iterdir():
        if p.is_file() and p.suffix.lower() in (".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico") \
                and out.resolve() not in p.resolve().parents:
            mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
            uri = f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"
            for q in ('"', "'"):
                html = html.replace(f"{q}{p.name}{q}", f"{q}{uri}{q}")
    return html


def encrypt(html: str, password: str) -> str:
    salt, nonce = secrets.token_bytes(16), secrets.token_bytes(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt,
                     iterations=ITERATIONS).derive(password.encode())
    ct = AESGCM(key).encrypt(nonce, html.encode("utf-8"), None)
    return base64.b64encode(salt + nonce + ct).decode()


LOCKED_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="robots" content="noindex" />
<title>__TITLE__</title>
<style>
  :root { --ink:#0B0E13; --panel:#151A22; --line:rgba(255,255,255,.1); --tx:#EEF2F7;
          --tx2:#98A3B2; --blue:#4C8DFF; --red:#F26D5B; }
  * { box-sizing:border-box; margin:0; padding:0 }
  body { font-family:system-ui,-apple-system,'Segoe UI',sans-serif; min-height:100vh;
         display:grid; place-items:center; color:var(--tx);
         background:radial-gradient(900px 500px at 80% -10%, rgba(76,141,255,.12), transparent 60%), var(--ink); }
  .lock { width:min(400px, 92vw); background:var(--panel); border:1px solid var(--line);
          border-radius:16px; padding:34px 30px; text-align:center; }
  .eyebrow { font-family:ui-monospace,monospace; font-size:11px; letter-spacing:.22em;
             text-transform:uppercase; color:var(--blue); }
  h1 { font-size:21px; letter-spacing:-.01em; margin:10px 0 4px; }
  p  { color:var(--tx2); font-size:13.5px; margin-bottom:22px; }
  form { display:flex; gap:8px; }
  input { flex:1; background:var(--ink); border:1px solid var(--line); border-radius:10px;
          padding:12px 14px; color:var(--tx); font-size:15px; }
  input:focus { outline:2px solid var(--blue); outline-offset:1px; border-color:transparent; }
  button { background:var(--blue); color:#04101F; border:0; border-radius:10px;
           padding:12px 18px; font-size:14px; font-weight:700; cursor:pointer; }
  button:disabled { opacity:.55; cursor:wait; }
  .err { color:var(--red); font-size:13px; min-height:18px; margin-top:12px; }
  .shake { animation:shake .3s } @keyframes shake { 25%{transform:translateX(-6px)} 75%{transform:translateX(6px)} }
  @media (prefers-reduced-motion:reduce){ .shake{animation:none} }
</style>
</head>
<body>
<div class="lock" id="lock">
  <div class="eyebrow">Private brief</div>
  <h1>__TITLE__</h1>
  <p>Enter the password you were given to open this page.</p>
  <form id="f"><input type="text" name="username" autocomplete="username" value="brief" hidden />
    <input id="pw" type="password" autocomplete="current-password"
    autofocus aria-label="Password" /><button id="go">Open</button></form>
  <div class="err" id="err" role="alert"></div>
</div>
<script>
const PAYLOAD = "__PAYLOAD__";
const ITER = __ITER__;
const raw = Uint8Array.from(atob(PAYLOAD), c => c.charCodeAt(0));
const salt = raw.slice(0, 16), nonce = raw.slice(16, 28), ct = raw.slice(28);

async function deriveKey(pw) {
  const km = await crypto.subtle.importKey("raw", new TextEncoder().encode(pw), "PBKDF2", false, ["deriveKey"]);
  return crypto.subtle.deriveKey({ name:"PBKDF2", salt, iterations:ITER, hash:"SHA-256" },
    km, { name:"AES-GCM", length:256 }, true, ["decrypt"]);
}
async function open_(key) {
  const pt = await crypto.subtle.decrypt({ name:"AES-GCM", iv:nonce }, key, ct); // throws if wrong
  const kb = btoa(String.fromCharCode(...new Uint8Array(await crypto.subtle.exportKey("raw", key))));
  try { sessionStorage.setItem("brief-key", kb); } catch (e) {}
  const html = new TextDecoder().decode(pt);
  document.open(); document.write(html); document.close();
}
document.getElementById("f").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = document.getElementById("go"), err = document.getElementById("err");
  btn.disabled = true; err.textContent = "";
  try { await open_(await deriveKey(document.getElementById("pw").value)); }
  catch (ex) {
    btn.disabled = false; err.textContent = "That password didn't work.";
    const l = document.getElementById("lock"); l.classList.remove("shake");
    void l.offsetWidth; l.classList.add("shake");
  }
});
(async () => {  // reopen without retyping within the same tab session
  try {
    const kb = sessionStorage.getItem("brief-key");
    if (!kb) return;
    const key = await crypto.subtle.importKey("raw",
      Uint8Array.from(atob(kb), c => c.charCodeAt(0)), { name:"AES-GCM" }, true, ["decrypt"]);
    await open_(key);
  } catch (e) { try { sessionStorage.removeItem("brief-key"); } catch (_) {} }
})();
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dashboard", help="dashboard directory (contains index.html)")
    ap.add_argument("--password", help="password to lock with")
    ap.add_argument("--gen", action="store_true", help="generate a memorable password")
    ap.add_argument("--out", help="output dir (default: <dashboard>/protected)")
    ap.add_argument("--title", default="Meeting Brief", help="title shown on the lock screen")
    a = ap.parse_args()

    dash = Path(a.dashboard).resolve()
    if not (dash / "index.html").is_file():
        sys.exit(f"No index.html in {dash}")
    if bool(a.password) == bool(a.gen):
        sys.exit("Pass exactly one of --password or --gen")
    password = a.password or gen_password()
    if len(password) < 8:
        sys.exit("Password too short: use 8+ characters (or --gen).")

    out = Path(a.out).resolve() if a.out else dash / "protected"
    out.mkdir(parents=True, exist_ok=True)

    html = inline(dash, out)
    payload = encrypt(html, password)

    # self-test: decrypt what we just encrypted before shipping it
    raw = base64.b64decode(payload)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=raw[:16],
                     iterations=ITERATIONS).derive(password.encode())
    assert AESGCM(key).decrypt(raw[16:28], raw[28:], None).decode("utf-8") == html

    title = (a.title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    page = (LOCKED_PAGE.replace("__TITLE__", title)
            .replace("__ITER__", str(ITERATIONS)).replace("__PAYLOAD__", payload))
    (out / "index.html").write_text(page, encoding="utf-8")

    print(f"Locked page : {out / 'index.html'}")
    print(f"Password    : {password}" + ("   (generated; share it with the viewer)" if a.gen else ""))
    print(f"Deploy ONLY : {out}  (single encrypted file; sources stay out)")
    print("Verify      : open it, wrong password must fail, right one must render;")
    print("              grep the locked file for a known quote, it must NOT appear.")


if __name__ == "__main__":
    main()
