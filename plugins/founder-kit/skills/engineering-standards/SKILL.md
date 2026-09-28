---
name: engineering-standards
description: Engineering standards for a Next.js App Router, TypeScript, Supabase/Postgres, Vercel product. Covers module boundaries, naming, boundary validation with zod, Supabase RLS and key discipline, safe migrations, React and Server Component habits, resilience, structured logging, secrets hygiene, an OWASP-grounded security baseline, test discipline, stack consistency, and Conventional Commits. Fires on any code writing, so use it whenever you are about to write, refactor, review, or extend code, even a one-line change, and whenever starting a feature, a bug fix, or a refactor. Use when the user says "make this production-grade", "follow project style", "do this properly", "review this before I ship", "add an API route", "write the migration", or "why is this breaking in production". Use when touching user input, auth, a database schema, an env var, a webhook, or a third-party API; when adding a dependency; and when a code review flags a pattern violation.
---

# Engineering standards (Next.js App Router, TypeScript, Supabase, Vercel)

This is the engineering bar for the product you are building. Read it before writing or editing
code. It assumes a Next.js App Router app in TypeScript, data in Supabase/Postgres, deployed on
Vercel. If your stack is Python, Go, or anything else, the same rules hold; adapt the examples.

The goals: code that is **readable** (a fresh session picks it up cold), **testable** (each unit
runs in isolation), **resilient** (graceful when the network and third parties misbehave), and
**changeable** (low coupling, so swapping a provider or a table does not ripple through the app).

How to use this skill: do not recite the rules at the user. Read the task, work out which rules
actually bite, and apply them with judgment; a one-line change still gets its magic number named.
If a rule conflicts with an explicit user instruction, the user wins; say once which rule you are
setting aside and why it would normally apply.

## Quick checklist (before calling code done)

1. **Boundaries** (§1): one responsibility per file, no 600-line page, arguments that travel together are a type.
2. **Naming** (§2): every magic number and string is a named constant or union; identifiers say intent.
3. **Imports** (§3): at the top of the file; dynamic import only for code splitting or a documented cycle break.
4. **Validation** (§4): route handlers, server actions, forms, webhooks, and third-party responses parsed with zod, never cast.
5. **Supabase** (§5): row level security on every exposed table; service-role key never in client code; no interpolated SQL.
6. **Migrations** (§6): additive first, expand then backfill then contract, concurrent index, lock timeout set.
7. **React** (§7): Server Components by default; `useEffect` never for derived state or data fetching.
8. **Resilience** (§8): timeout plus jittered retry on third-party calls; webhooks idempotent and signature-verified.
9. **Logging** (§9): structured JSON through one logger, request id propagated, no secrets or personal data.
10. **Secrets** (§10): env vars only, validated at boot, `NEXT_PUBLIC_` treated as published, nothing committed.
11. **Security** (§11): authentication plus per-resource authorization inside every handler and action.
12. **Tests** (§12): a unit test per unit of logic as you write it; one Playwright smoke test on the critical path.
13. **Consistency** (§13): matched the libraries already in the repo; no second way to do an existing thing.
14. **Commits** (§14): Conventional Commits, imperative, subject 72 characters or fewer.

---

## 1. Module boundaries and encapsulation

**Why.** A file that owns four jobs cannot be tested, reviewed, or reused, and it becomes the file
everyone is afraid to touch. A page that fetches, computes, formats, and renders has no seam.

- One exported unit per file: one component, one service, one repository, one hook.
- Data access lives in a repository module; pages and route handlers compose, they do not query.
- Business logic goes in pure functions, away from I/O and JSX; that is what makes it cheap to test.
- Arguments that travel together are a type. Three functions taking `(orgId, invoiceId, currency)` want an `InvoiceRef`.
- Inject collaborators (a client, a clock, a fetcher) rather than importing a singleton deep in the tree; that is how you mock without patching. Export a narrow surface; never reach into another module's internals.

```tsx
// wrong: one file fetches, computes totals, formats currency, and renders 400 lines of JSX
export default async function InvoicesPage() {
  const rows = await db.raw('select * from invoices');
  // ...200 lines of totals math and an inline currency formatter...
}

// right: each collaborator has one job and its own file; the page composes
import { listInvoices } from '@/lib/invoices/repository';
import { summarize } from '@/lib/invoices/totals';
import { InvoiceTable } from '@/components/invoice-table';

export default async function InvoicesPage() {
  const invoices = await listInvoices();
  return <InvoiceTable invoices={invoices} summary={summarize(invoices)} />;
}
```

**Soft size limits** (signals, not laws): 300 lines per TS module, 150 per React component, 80 per
route handler or server action; past double that it is certainly two files. **Split at the seam,
not by line count:** the seam is where two responsibility groups stop referring to each other. Group
by domain (`lib/invoices/*`) rather than by kind (`lib/clients.ts`); two files that always change
together belong in one file. Propose a coming split in the plan, not as a surprise refactor.

## 2. Naming and constants

**Why.** A literal in a condition is a fact with no name and no single home, so it drifts: the
trial is 14 days in one file and 15 in another. A named constant makes the change one edit.

- Promote every magic number and magic string to a named constant, a string union, or a lookup object.
- Prefer `const` objects with `as const` or string unions over numeric enums; the values stay readable in the database and in logs.
- Names describe intent, not type: `maxRetryAttempts`, not `n`; `isTrialExpired`, not `flag2`. Booleans read as predicates, functions as verbs, collections as plurals.
- Keep constants next to the domain they own, not in a global `constants.ts` dumping ground.

```ts
// wrong
if (user.plan === 2 && daysSince > 14) await notify(user, 3);

// right
const TRIAL_LENGTH_DAYS = 14;
const PLANS = { free: 'free', pro: 'pro', team: 'team' } as const;
const NOTIFICATION = { trialEnding: 'trial_ending' } as const;

if (user.plan === PLANS.pro && daysSinceSignup > TRIAL_LENGTH_DAYS) {
  await notify(user, NOTIFICATION.trialEnding);
}
```

## 3. Imports at the top of the file

**Why.** An import buried in a function hides a dependency from every reader and every tool, and on
a serverless path it pays resolution cost per invocation instead of once at cold start.

- All static imports at the top, grouped: node builtins, external packages, internal aliases (`@/...`), then relative.
- Legitimate dynamic imports: `next/dynamic` for a heavy client-only component, a deliberate lazy chunk, or breaking an import cycle. Each gets a one-line comment saying which.
- Import types with `import type` so they are erased from the bundle.

```ts
// wrong: dependency hidden inside a handler, resolved on every request
export async function POST(request: Request) {
  const { Resend } = await import('resend');
  return Response.json(await new Resend(process.env.RESEND_API_KEY).emails.send(payload));
}

// right
import { Resend } from 'resend';
import type { CreateEmailOptions } from 'resend';

const resend = new Resend(env.RESEND_API_KEY);

export async function POST(request: Request) {
  return Response.json(await resend.emails.send(payload));
}
```

## 4. Validate at every boundary with zod

**Why.** A cast is a promise you cannot keep. `as { seats: number }` compiles happily while `seats`
arrives as `"abc"`, and the bad value travels until it corrupts a row or throws somewhere unrelated.

- Parse, never cast, at every boundary: route handler bodies, server action arguments and `FormData`, search params, cookies, webhook payloads, and every third-party response.
- Define the schema once per boundary and derive the type from it (`z.infer`), so type and check cannot diverge.
- `safeParse` when you want to return a clean error; `parse` when a failure genuinely is a bug.
- Client-side validation is for the user's benefit; the server-side parse is the authoritative one. Share the schema between form and action, and return field-level issues, never the raw error object.

```ts
// wrong: trusts the body, casts, and hopes
export async function POST(request: Request) {
  const body = (await request.json()) as { name: string; seats: number };
  return Response.json(await createOrg(body));
}

// right: parse once, and only the parsed value flows onward
const CreateOrgInput = z.object({
  name: z.string().min(1).max(MAX_ORG_NAME_LENGTH),
  seats: z.number().int().positive().max(MAX_SEATS),
});

export async function POST(request: Request) {
  const parsed = CreateOrgInput.safeParse(await request.json());
  if (!parsed.success) {
    const issues = parsed.error.flatten().fieldErrors;
    return Response.json({ error: 'invalid_input', issues }, { status: 400 });
  }
  return Response.json(await createOrg(parsed.data));
}
```

## 5. Supabase and Postgres discipline

**Why.** Supabase exposes your database over the network. RLS is not a hardening extra, it is the
access control layer; a table without it, or a secret key in the browser, means any visitor owns every row.

- **RLS on every table in an exposed schema**, enabled in the migration that creates the table, with an explicit policy per operation. Enabled with no policy denies everything; that is the safe place to start.
- **The service-role (secret) key is server-only.** Never in a client component, never behind a `NEXT_PUBLIC_` name. It bypasses RLS entirely; use it only in trusted server code that must act across users.
- Use the anon/publishable key through a request-scoped server client so the user's session, and therefore RLS, applies.
- **Never interpolate values into SQL.** Use the client's filter builders; in database functions, use bound parameters. Still scope queries by owner in code even with RLS on: defense in depth, and it documents intent.
- Select the columns you need rather than `*`, and check `error` on every call; these calls resolve rather than throw, so an unchecked error reads as empty data.

```ts
// wrong: secret key in the client bundle, RLS bypassed for every visitor
const supabase = createClient(url, process.env.NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY!);
const { data } = await supabase.from('invoices').select('*');

// right: request-scoped server client on the publishable key; RLS enforces ownership
const supabase = await createServerSupabaseClient(); // wraps the SSR helper, reads the session cookie
const { data, error } = await supabase
  .from('invoices')
  .select('id, total_cents, status')
  .eq('org_id', orgId);
if (error) throw new InvoiceQueryError(error.message);
```

```sql
alter table public.invoices enable row level security;

create policy "owners read their invoices"
  on public.invoices for select to authenticated
  using (user_id = auth.uid());
```

## 6. Migration safety

**Why.** A deploy is not atomic with a migration; for a window, old code runs against the new
schema. A rename or a drop in one step breaks every request in flight.

- **Additive first.** Add columns and tables; make new columns nullable or give them a default; never rename or drop in the same step that ships the code using them.
- **Expand, backfill, contract**, as separate deploys: add the new shape; ship code that writes both and reads the new one; backfill in batches; drop the old shape only once nothing reads it.
- `create index concurrently` (outside a transaction) on any table with traffic, and set a `lock_timeout` so a migration that cannot get its lock fails fast instead of queueing every query behind it.
- Migrations are files in the repo, reviewed like code, applied through the CLI; never hand-edit production schema in a dashboard. Write the reverse step when the change is reversible, and say so in the PR when it is not.

```sql
-- wrong: one migration, every running instance breaks the moment it lands
alter table public.profiles rename column name to full_name;

-- right, step 1 (expand): additive, old code keeps working
set lock_timeout = '3s';
alter table public.profiles add column full_name text;
-- step 2 (code deploy): write both columns, read full_name
-- step 3 (backfill): in batches, off the request path
update public.profiles set full_name = name where full_name is null;
-- step 4 (contract): a later deploy, once nothing reads name
alter table public.profiles drop column name;
```

## 7. React and Server Component habits

**Why.** Most React bugs here come from two habits: making things client components by reflex, and
using `useEffect` as a general purpose "run some code" hook. Effects that derive state cause an extra
render and a stale frame; effects that fetch reintroduce every race the data layer already solved.

- **Server Components are the default.** Add `'use client'` only for state, effects, event handlers, or browser APIs, and push it to the leaf that needs it.
- **Fetch on the server**, in the component that needs the data; pass plain data down.
- `useEffect` is for syncing with something outside React (a subscription, a non-React widget). Never for derived state, never for data fetching, never as a reaction to a prop change (lift state, use a `key` to remount, or compute in render).
- Minimize state: if it can be computed from props or other state, compute it in render.
- Hooks at the top level only; stable keys from ids, never an array index for a list that reorders.
- `useMemo`/`useCallback` when the value crosses into a memoized child or a dependency array, not on every local expression. Three boolean props want to be one union prop.
- An error boundary around each route subtree; a loading state for every async boundary.

```tsx
// wrong: one effect derives state, another fetches data
const [fullName, setFullName] = useState('');
useEffect(() => { setFullName(`${first} ${last}`); }, [first, last]);
useEffect(() => { fetch('/api/invoices').then((r) => r.json()).then(setInvoices); }, []);

// right: derive in render; fetch on the server
const fullName = `${first} ${last}`;

// app/invoices/page.tsx, a Server Component
export default async function InvoicesPage() {
  return <InvoiceTable invoices={await listInvoices()} />;
}
```

## 8. Resilience for anything over the network

**Why.** Third-party APIs rate limit, blip, and go down. A naked `fetch` turns someone else's bad
minute into your 500; a retry without backoff turns their recovery into a thundering herd.

- Every third-party call gets a **timeout** and a **bounded retry with exponential backoff plus jitter**, wrapped once in the client module rather than at each call site.
- Retry transient failures only: network errors, timeouts, 429, 5xx. Never retry 400, 401, 403, 404, or 422; they will fail again. Respect `Retry-After` when it is sent.
- Non-idempotent writes carry an idempotency key so a retry cannot double-charge.
- **Webhooks:** verify the signature before trusting the body, store the provider event id with a unique constraint and exit early if you have seen it, then acknowledge fast and do slow work in the background.
- Serverless functions have an execution limit; long work belongs in a queue or background job, not a request handler. Fail visibly: a swallowed error is a bug that reports itself as "nothing happened".

```ts
// wrong: no timeout, no retry, no idempotency; one upstream blip loses the order
const res = await fetch(`${BILLING_API}/charges`, { method: 'POST', body });

// right: bounded timeout, jittered retry on transient status codes only
const RETRYABLE_STATUS = new Set([408, 429, 500, 502, 503, 504]);

async function postCharge(body: string, key: string, attempt = 1): Promise<Response> {
  const res = await fetch(`${BILLING_API}/charges`, {
    method: 'POST',
    body,
    headers: { 'Idempotency-Key': key },
    signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
  });
  if (RETRYABLE_STATUS.has(res.status) && attempt < MAX_ATTEMPTS) {
    await sleep(BASE_DELAY_MS * 2 ** attempt + Math.random() * JITTER_MS);
    return postCharge(body, key, attempt + 1);
  }
  return res;
}
```

## 9. Structured logging

**Why.** When production misbehaves, logs are all you have. Free-text lines cannot be filtered by
request, user, or event, so an incident becomes a scroll; one JSON object per line can be queried.

- One logger module for the app; no scattered `console.log` on production paths (a scratch script is fine).
- One JSON object per line on stdout, which the platform collects. Always include `level`, a timestamp, an `event` name, and the ids needed to correlate.
- Derive a `requestId` at each server entry point (the incoming trace header if present, otherwise a generated id) and thread it through the call path.
- Log the shape, not the payload: ids, counts, durations, outcome. Never tokens, cookies, raw bodies, or personal data you would not paste into a support ticket. Log an error once, at the boundary that handles it, with a stack; return an error id to the client and keep the detail in the log.

```ts
// wrong: unstructured, unsearchable, and it leaks a token and an email address
console.log('created invoice for', user.email, 'token', session.access_token);

// right: one JSON line, correlated, safe to keep forever
export const log = {
  info: (fields: Record<string, unknown>) =>
    console.log(JSON.stringify({ level: 'info', ts: new Date().toISOString(), ...fields })),
  error: (fields: Record<string, unknown>) =>
    console.error(JSON.stringify({ level: 'error', ts: new Date().toISOString(), ...fields })),
};

log.info({ event: 'invoice.created', requestId, invoiceId, orgId, durationMs });
```

## 10. Secrets hygiene

**Why.** A leaked key is the highest-cost mistake available to you: it grants live access, and git
history keeps it forever, so scrapers find it long after you "removed" it.

- **Nothing secret in the repo.** No keys, no database URLs with passwords, no service account JSON, not in a comment and not in a test fixture. `.env.example` holds placeholder values only.
- `.env.local` and `.env*.local` are gitignored; real values live in the hosting platform's environment settings, set per environment (development, preview, production).
- **`NEXT_PUBLIC_` means published.** Anything with that prefix is in the browser bundle; never put a secret behind one, and never import the server env module from a client component.
- Validate the environment once at boot with a schema, so a missing variable fails the build or the cold start rather than a user's checkout.
- Never paste a secret into a chat, an issue, a commit message, or a log line. Turn on the host's secret scanning and push protection.
- If a key leaks: rotate first, investigate second; do not start by scrubbing history.

```ts
// wrong: key committed, and a secret hidden behind a public name
const STRIPE_KEY = 'sk_live_REDACTED_EXAMPLE';
const admin = createClient(url, process.env.NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY!);

// right: one validated server-only env module, values injected by the platform
const ServerEnv = z.object({
  SUPABASE_URL: z.string().min(1),
  SUPABASE_SERVICE_ROLE_KEY: z.string().min(1),
  STRIPE_SECRET_KEY: z.string().min(1),
});

export const env = ServerEnv.parse(process.env); // fails the boot, not the checkout
```

## 11. Security baseline (OWASP-grounded)

**Why.** Real breaches are rarely exotic: broken access control, injection, weak validation,
secrets in the wrong place. The same short list for a decade, all preventable by habit.

- **Authenticate inside every protected handler, route, and server action.** A server action is a public HTTP endpoint; nothing stops a caller from invoking it directly.
- Middleware and layouts are convenience, not the authorization boundary; deep links and direct action calls do not pass through your page guard.
- **Authorize per resource.** "Logged in" is not enough; "owns this invoice" or "is an admin of this org" is. Every read filters by owner, every write checks ownership before mutating.
- Parameterized access only (§5); no string-built SQL, ever. React escapes output by default, so avoid `dangerouslySetInnerHTML` unless the content is server-controlled and sanitized by a vetted library.
- Generic error bodies to clients plus an error id; stack traces and driver messages stay in logs. Rate limit auth endpoints and anything expensive; a CORS allowlist, never `*` with credentials.
- Lockfile committed, package manager audit in CI, dependency count kept low; every package is supply-chain surface. The OWASP Top 10 (https://owasp.org/www-project-top-ten/) is the full list; most real issues fit inside it.

```ts
// wrong: a server action that trusts its caller
'use server';
export async function deleteInvoice(id: string) {
  await supabaseAdmin.from('invoices').delete().eq('id', id);
}

// right: parse, authenticate, authorize the specific row, then act
'use server';
export async function deleteInvoice(rawId: unknown) {
  const id = z.string().uuid().parse(rawId);
  const supabase = await createServerSupabaseClient();
  const { data: auth } = await supabase.auth.getUser();
  if (!auth.user) return { error: 'unauthenticated' as const };

  const { error } = await supabase
    .from('invoices')
    .delete()
    .eq('id', id)
    .eq('user_id', auth.user.id); // ownership in the query, not only in the policy
  if (error) return { error: 'delete_failed' as const };
  revalidatePath('/invoices');
  return { ok: true as const };
}
```

## 12. Tests

**Why.** Tests are how you change code later without re-reading all of it. Written after the fact
they get skipped; written alongside each unit they expose bad boundaries immediately.

- A unit test per unit of logic, written as the logic is written, not "later".
- **Test behavior, not implementation.** Assert what a caller or user can observe, not which internal function was called.
- Push logic into pure functions, the cheapest thing to test. Mock at the boundary (the HTTP client, the database client), never the module under test.
- One Playwright smoke test through the critical path (sign in, do the core action, see the result) on every PR; it catches most "the whole app is broken" deploys.
- Tests that cost money or hit a live third party sit behind an env flag, out of the default run.
- A bug fix starts with a failing test that reproduces it: the only proof the fix works.

```ts
// wrong: asserts the implementation, so every refactor turns red for no reason
expect(summarizeSpy).toHaveBeenCalledWith(invoices);

// right: asserts the behavior the caller depends on
it('excludes voided invoices from the total', () => {
  const summary = summarize([paid(1000), voided(9999)]);
  expect(summary.totalCents).toBe(1000);
});
```

## 13. Consistency: match the stack already in use

**Why.** Two ways to do one thing is worse than either alone: another set of idioms, another
bundle, another upgrade path, another fork in the road for whoever reads the code next.

- Before reaching for a package, check what the repo already does for that job and use it the same way.
- One data-fetching story, one form library, one validation library, one styling approach, one store. A second arrives only with an explicit decision the user signs off on.
- Match the neighboring file's conventions (naming, layout, error style) even when your taste differs. A new dependency needs a reason you can say out loud: what it replaces, what it costs, why what you already have will not do.

```ts
// wrong: a third form library and a second data-fetching story, in one PR
import { useFormik } from 'formik';
import useSWR from 'swr';

// right: what the repo already uses, used the way the repo uses it
import { useForm } from 'react-hook-form'; // already in package.json
const invoices = await listInvoices();     // server-side fetch, as everywhere else
```

## 14. Conventional Commits

**Why.** The commit log is the only narrative of the codebase that survives. A consistent format
makes it scannable, makes changelogs generatable, and makes `git log` a usable debugging tool.

- `type(scope): subject`, with type one of `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `build`, `ci`.
- Imperative mood ("add", not "added"); subject 72 characters or fewer; no trailing period.
- The body (wrapped near 72 columns) explains why, not what; the diff already says what. A `BREAKING CHANGE:` footer when a contract changes.
- One logical change per commit. If the subject needs an "and", it is two commits.

```bash
# wrong
git commit -m "fixes + some cleanup"

# right
git commit -m "fix(invoices): exclude voided rows from the dashboard total"
```

---

## Applying this skill

When a task lands, scan it for which rules are in play:

| If the task is... | Rules that dominate |
|---|---|
| Starting a feature, bug fix, or refactor | §1 boundaries, §12 tests alongside, §14 commits; pair with the ship-flow skill for the issue and PR loop |
| Adding an API route or server action | §4 validation, §11 auth plus per-resource authorization, §9 logging, §8 timeouts downstream |
| Touching user input or any data boundary | §4 parse, never cast; §11 no interpolated SQL, generic error bodies |
| Reading or writing data | §5 RLS on, publishable key with the user's session, columns named, `error` handled |
| Changing the schema | §6 additive first, expand then backfill then contract, concurrent index, lock timeout |
| Building or editing a component | §7 Server Component by default, no `useEffect` for derived state or fetching, §1 size limits |
| Integrating a third party | §8 timeout plus retry plus idempotency, §10 key from validated env, §12 a test with the client mocked |
| Handling a webhook | §8 verify signature, dedupe on event id, acknowledge fast, work in the background |
| Adding a dependency | §13 check what exists first, then justify the addition out loud |
| Production is misbehaving | §9 structured logs and the request id first, then reproduce with a failing test (§12) |
| Writing the commit or the PR | §14 Conventional Commits; pair with the pr-writer skill for the body |

Apply the rules in the code rather than lecturing the user about them. Surface a rule only when
there is a real trade-off to decide ("I put the totals math in a pure module so it can be tested
without the database; fine?"), when you set one aside, or when following it changes the scope.
