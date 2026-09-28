/* Vercel routing middleware: password gate for a static meeting brief.
   Proven pattern: POST /unlock sets an HttpOnly cookie
   holding SHA-256(password:salt); every other request without it gets a styled
   401 login page. The password lives only in this file; middleware runs
   server-side and is never served to the browser.

   Before deploying, replace every __PLACEHOLDER__:
     __PASSWORD__      the password (8+ chars; generate with
                       scripts/password_protect.py --gen if the user has none)
     __SALT__          any per-project string, e.g. "acme-brief-2026-v1"
     __ORG_LABEL__     small eyebrow line, e.g. "Prepared by <your company>"
     __TITLE__         lock-screen heading, e.g. "A private brief"
     __AUDIENCE_LINE__ e.g. "This page was prepared for Jane Doe. Enter the
                       password from the follow-up message to continue."
     __CONTACT_LINE__  fallback so a locked-out viewer can still reach the owner. Build it
                       from the Owner config (see SKILL.md), e.g.
                       'Lost the password? Reply to the email that sent you this link.'
                       or 'Lost the password? Call or text <owner phone>.'
   Restyle the login page to match the dashboard's palette (swap the CSS vars). */
import { next } from '@vercel/functions';

const PASSWORD = '__PASSWORD__';
const SALT = '__SALT__';
const COOKIE = 'brief_auth';
const MAX_AGE = 60 * 60 * 24 * 30; // 30 days

export const config = { matcher: '/(.*)' };

async function expectedToken() {
  const bytes = new TextEncoder().encode(`${PASSWORD}:${SALT}`);
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

function loginPage(withError) {
  const error = withError
    ? '<p class="err" role="alert">That password does not match. Try again.</p>'
    : '';
  return new Response(
    `<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow"><title>__TITLE__</title>
<style>
:root{--ink:#0B0E13;--panel:#151A22;--line:rgba(255,255,255,.1);--tx:#EEF2F7;
--tx2:#98A3B2;--blue:#4C8DFF;--red:#F26D5B}
body{margin:0;min-height:100dvh;display:flex;align-items:center;justify-content:center;
font-family:system-ui,-apple-system,'Segoe UI',sans-serif;color:var(--tx);
background:radial-gradient(900px 500px at 80% -10%,rgba(76,141,255,.12),transparent 60%),var(--ink)}
.gate{width:min(420px,calc(100vw - 40px));background:var(--panel);border:1px solid var(--line);
border-radius:16px;padding:34px 32px}
.label{font-family:ui-monospace,monospace;font-size:10.5px;letter-spacing:.22em;
text-transform:uppercase;color:var(--blue)}
h1{font-size:24px;letter-spacing:-.01em;margin:10px 0 6px}
p{font-size:14px;color:var(--tx2);margin:0 0 18px}
label{display:block;font-family:ui-monospace,monospace;font-size:10.5px;letter-spacing:.18em;
text-transform:uppercase;color:var(--blue);margin-bottom:6px}
input{width:100%;box-sizing:border-box;font-size:16px;padding:12px 14px;border:1px solid var(--line);
border-radius:10px;background:var(--ink);color:var(--tx)}
input:focus-visible{outline:2px solid var(--blue);outline-offset:1px}
button{margin-top:14px;width:100%;min-height:46px;font-size:14px;font-weight:700;border-radius:10px;
color:#04101F;background:var(--blue);border:0;cursor:pointer;touch-action:manipulation}
button:focus-visible{outline:2px solid var(--tx);outline-offset:2px}
.err{color:var(--red);font-size:13.5px;font-weight:600;margin:0 0 14px}
.help{font-size:12.5px;color:var(--tx2);margin:16px 0 0}
.help a{color:var(--blue)}
</style></head><body>
<main class="gate">
<span class="label">__ORG_LABEL__</span>
<h1>__TITLE__</h1>
<p>__AUDIENCE_LINE__</p>
${error}
<form method="post" action="/unlock">
<input type="text" name="username" autocomplete="username" value="brief" hidden>
<label for="pw">Password</label>
<input id="pw" name="password" type="password" autocomplete="current-password" autofocus required>
<button type="submit">Open the brief</button>
</form>
<p class="help">__CONTACT_LINE__</p>
</main></body></html>`,
    {
      status: 401,
      headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' },
    },
  );
}

export default async function middleware(request) {
  const url = new URL(request.url);
  const token = await expectedToken();
  const cookies = (request.headers.get('cookie') || '').split(';').map((c) => c.trim());
  const authed = cookies.includes(`${COOKIE}=${token}`);

  if (url.pathname === '/unlock' && request.method === 'POST') {
    let submitted = '';
    try {
      submitted = String((await request.formData()).get('password') || '');
    } catch {
      submitted = '';
    }
    if (submitted.trim() === PASSWORD) {
      return new Response(null, {
        status: 303,
        headers: {
          Location: '/',
          'Set-Cookie': `${COOKIE}=${token}; HttpOnly; Secure; Path=/; SameSite=Lax; Max-Age=${MAX_AGE}`,
          'Cache-Control': 'no-store',
        },
      });
    }
    return loginPage(true);
  }

  if (authed) return next();
  return loginPage(false);
}
