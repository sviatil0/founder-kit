/* Starter render layer. Renders the default Pains -> Solvers -> People -> Agreements/Actions
   tabs from BRIEF, with hand-built SVG/CSS diagrams. Customize freely; give the design a
   signature grounded in THIS meeting's subject, and wire in the company's brand color/logo
   (see the skill's design + branding notes).
   NOTE: content renders via innerHTML, so every interpolated field is passed through esc().
   A real quote can contain <, &, or " and without escaping it silently truncates or corrupts. */
const B = window.BRIEF;
const $ = (s, r = document) => r.querySelector(s);
const el = (t, c, h) => { const n = document.createElement(t); if (c) n.className = c; if (h != null) n.innerHTML = h; return n; };
const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const initials = (name) => ((name || "?").split(/[ ·]/).filter(Boolean).slice(0, 2).map(w => w[0]).join("").toUpperCase()) || "?";
const clamp = (v) => Math.max(1, Math.min(5, Number(v) || 1));

/* side -> color. Extend for your camps. Brand color can override --blue in CSS. */
const SIDE = { them: "#4C8DFF", us: "#37D6A4", bridge: "#F6A93B", other: "#7B8494" };
const catColor = (c, i) => ["#4C8DFF", "#37D6A4", "#F6A93B", "#E4D8BB", "#F26D5B"][i % 5];
const empty = (msg) => `<p class="note" style="opacity:.6">${esc(msg)}</p>`;

/* ---- FOLLOW-UP CTA (booking link + phone from meta.followup, filled from Owner config) ---- */
function cta(compact) {
  const f = (B.meta || {}).followup || {};
  if (!f.booking && !f.phone) return "";
  const tel = f.phone ? `tel:${String(f.phone).replace(/[^\d+]/g, "")}` : "";
  const book = f.booking ? `<a class="cta-btn" href="${esc(f.booking)}" target="_blank" rel="noopener">Book a follow-up</a>` : "";
  const call = f.phone ? `<a class="cta-btn ghost" href="${esc(tel)}">Call / text ${esc(f.phone)}</a>` : "";
  if (compact) return `<div class="cta cta-rail">${book}${call}</div>`;
  return `<div class="cta cta-card"><div class="dia-h">Keep it moving</div>
    <p class="note">${esc(f.line || "Grab a slot or just call.")}</p>
    <div class="cta-row">${book}${call}</div></div>`;
}

/* ---- DIAGRAM: impact x effort matrix ---- */
function matrix(pains) {
  if (!pains.length) return empty("No pains captured yet.");
  const W = 560, H = 420, L = 58, R = 18, T = 20, Bm = 44, pw = W - L - R, ph = H - T - Bm;
  const xv = v => L + ((v - 0.5) / 5) * pw, yv = v => T + (1 - (v - 0.5) / 5) * ph;
  const xd = xv(3.5), yd = yv(3.5);
  const groups = {};
  pains.forEach(p => { (groups[`${clamp(p.impact)}-${clamp(p.effort)}`] ||= []).push(p); });
  let dots = "";
  Object.values(groups).forEach(g => g.forEach((p, i) => {
    const cx = xv(clamp(p.effort)) + (i - (g.length - 1) / 2) * 27, cy = yv(clamp(p.impact));
    const c = p.solvable ? SIDE.us : SIDE.bridge;
    dots += `<g><circle cx="${cx}" cy="${cy}" r="15" fill="${c}" fill-opacity="0.18" stroke="${c}" stroke-width="1.5"/>`
      + `<text x="${cx}" y="${cy + 3.4}" text-anchor="middle" font-family="ui-monospace,monospace" font-size="9" font-weight="700" fill="${c}">${esc(p.id)}</text></g>`;
  }));
  const q = (x, y, t, c) => `<text x="${x}" y="${y}" font-family="ui-monospace,monospace" font-size="10" letter-spacing="1.5" fill="${c}">${t}</text>`;
  return `<svg viewBox="0 0 ${W} ${H}" class="svg" role="img" aria-label="Impact by effort matrix">
    <rect x="${L}" y="${T}" width="${xd - L}" height="${yd - T}" fill="${SIDE.us}" fill-opacity="0.05"/>
    <rect x="${xd}" y="${T}" width="${L + pw - xd}" height="${yd - T}" fill="${SIDE.bridge}" fill-opacity="0.05"/>
    <line x1="${xd}" y1="${T}" x2="${xd}" y2="${T + ph}" stroke="rgba(255,255,255,.14)" stroke-dasharray="3 4"/>
    <line x1="${L}" y1="${yd}" x2="${L + pw}" y2="${yd}" stroke="rgba(255,255,255,.14)" stroke-dasharray="3 4"/>
    <line x1="${L}" y1="${T + ph}" x2="${L + pw}" y2="${T + ph}" stroke="rgba(255,255,255,.08)"/>
    ${q(xv(1.2), yv(5.35), "QUICK WINS", SIDE.us)} ${q(xv(4.0), yv(5.35), "BIG BETS", SIDE.bridge)}
    ${q(xv(1.2), yv(0.9), "EASY FILLS", "#5C6674")} ${q(xv(4.3), yv(0.9), "LATER", "#5C6674")}
    <text x="${L + pw / 2}" y="${H - 10}" text-anchor="middle" font-family="ui-monospace,monospace" font-size="9.5" fill="#5C6674" letter-spacing="1.5">EFFORT →</text>
    <text x="14" y="${T + ph / 2}" text-anchor="middle" transform="rotate(-90 14 ${T + ph / 2})" font-family="ui-monospace,monospace" font-size="9.5" fill="#5C6674" letter-spacing="1.5">IMPACT →</text>
    ${dots}</svg>`;
}

/* ---- DIAGRAM: theme bars ---- */
function bars(pains) {
  if (!pains.length) return empty("No pains to break down.");
  const c = {}; pains.forEach(p => { c[p.cat || "Other"] = (c[p.cat || "Other"] || 0) + 1; });
  const rows = Object.entries(c).sort((a, b) => b[1] - a[1]);
  const max = Math.max(1, ...rows.map(r => r[1]));
  return `<div class="bars">` + rows.map(([cat, n], i) =>
    `<div class="bar-row"><span class="bar-lab">${esc(cat)}</span>
     <span class="bar-track"><span class="bar-fill" style="width:${n / max * 100}%;background:${catColor(cat, i)}"></span></span>
     <span class="bar-n">${n}</span></div>`).join("") + `</div>`;
}

/* ---- DIAGRAM: horizontal flow ---- */
function flow(nodes) {
  return `<div class="flow">` + nodes.map((n, i) =>
    `<div class="flow-node">${esc(n)}</div>${i < nodes.length - 1 ? '<div class="flow-arm">→</div>' : ''}`).join("") + `</div>`;
}

/* ---- DIAGRAM: relationship camps (groups people by side) ---- */
function camps(people) {
  const bySide = {};
  people.forEach(p => { (bySide[p.side || "other"] ||= []).push(p); });
  const cols = Object.entries(bySide).map(([side, ps]) =>
    `<div class="camp"><div class="camp-h" style="color:${SIDE[side] || SIDE.other}">${esc(side)}</div>
     <div class="camp-names">${ps.map(p => `<span class="camp-chip" style="border-color:${SIDE[side] || SIDE.other}">${esc(p.name)}</span>`).join("")}</div></div>`).join("");
  return `<div class="camps">${cols}</div>`;
}

/* ---- DIAGRAM: vertical timeline ---- */
function timeline(items) {
  return `<div class="vtl">` + items.map(b =>
    `<div class="vtl-item"><div class="vtl-year">${esc(b.year)}</div><div class="vtl-dot"></div>
     <div><div class="vtl-title">${esc(b.title)}</div><div class="vtl-detail">${esc(b.detail || "")}</div></div></div>`).join("") + `</div>`;
}

/* ---- TABS ---- */
function renderPains() {
  const cards = B.pains.map(p => `
    <article class="card pain">
      <div class="pain-top"><span class="mono">${esc(p.id)}</span><span class="tag">${esc(p.cat || "")}</span></div>
      <h3>${esc(p.title)}</h3><p class="quote">"${esc(p.quote)}"</p>
      <p class="note">${esc(p.note || "")}</p>
      <div class="pain-foot"><span class="mono">impact ${clamp(p.impact)}/5 · effort ${clamp(p.effort)}/5</span>
        <span class="pill ${p.solvable ? "yes" : "no"}">${p.solvable ? "solvable now" : "bigger lift"}</span></div>
    </article>`).join("");
  return `<span class="eyebrow">Their pains</span><h2>What's actually hurting</h2>
    <div class="dia-2"><div class="dia-card"><div class="dia-h">Where to push first</div>${matrix(B.pains)}</div>
    <div class="dia-card"><div class="dia-h">Where the pain clusters</div>${bars(B.pains)}</div></div>
    <div class="divider"></div><div class="grid">${cards || empty("Add pains to data.js.")}</div>`;
}
function renderSolvers() {
  const cards = B.solvers.map(s => `
    <div class="card"><h4>${esc(s.who)}</h4><p>${esc(s.builds)}</p>
    <p class="note"><b>Proof:</b> ${esc(s.proof || "n/a")}</p>
    <div class="chips">${(s.pain_ids || []).map(id => `<span class="mono chip">${esc(id)}</span>`).join("")}</div></div>`).join("");
  return `<span class="eyebrow">Solvers</span><h2>Who could fix what</h2>
    ${flow(["A real pain", "Someone who can build", "A shipped fix"])}
    <div class="grid" style="margin-top:18px">${cards || empty("Add solvers to data.js.")}</div>`;
}
function renderPeople() {
  const cards = B.people.map(p => `
    <div class="card person ${p.lead ? "lead" : ""}"><div class="person-top">
      <div class="avatar" style="background:${SIDE[p.side] || SIDE.other}">${initials(p.name)}</div>
      <div><div class="person-name">${esc(p.name)}</div><div class="note">${esc(p.role || "")}</div></div></div>
      <p class="note">${esc(p.note || "")}</p>${p.research ? `<p class="note"><b>Background:</b> ${esc(p.research)}</p>` : ""}
      ${p.quote ? `<p class="quote">"${esc(p.quote)}"</p>` : ""}</div>`).join("");
  return `<span class="eyebrow">The people</span><h2>Who's in the room</h2>
    ${camps(B.people)}<div class="divider"></div><div class="grid">${cards || empty("Add people to data.js.")}</div>`;
}
function renderActions() {
  const ag = B.agreements.map(a => `<div class="card"><p><b>${esc(a.text)}</b></p>${a.quote ? `<p class="quote">"${esc(a.quote)}"</p>` : ""}</div>`).join("");
  const ac = B.actions.map(a => `<div class="row"><span class="dot ${a.done ? "done" : ""}"></span>
    <div><div class="${a.done ? "strike" : ""}">${esc(a.text)}</div><div class="mono">${esc(a.owner || "")}${a.when ? " · " + esc(a.when) : ""}</div></div></div>`).join("");
  return `<span class="eyebrow">Agreements</span><h2>What we agreed</h2><div class="grid">${ag || empty("No agreements recorded.")}</div>
    <div class="divider"></div><span class="eyebrow">Action items</span><h2>What's next</h2><div class="rows">${ac || empty("No action items.")}</div>
    <div class="divider"></div>${cta(false)}`;
}

const TABS = [
  { id: "pains", label: "Their Pains", render: renderPains },
  { id: "solvers", label: "Solvers", render: renderSolvers },
  { id: "people", label: "The People", render: renderPeople },
  { id: "actions", label: "Agreements & Actions", render: renderActions },
];
if (B.background && B.background.length)
  TABS.push({ id: "bg", label: "Background", render: () => `<span class="eyebrow">Background</span><h2>Their arc</h2>${timeline(B.background)}` });

function mount() {
  // fill the brand header from meta (kept out of the render loop so it always runs)
  const m = B.meta || {};
  if ($("#b-name")) $("#b-name").textContent = m.partner || "";
  if ($("#b-sub")) $("#b-sub").textContent = [m.date, m.role].filter(Boolean).join(" · ");
  if (m.brandColor) document.documentElement.style.setProperty("--blue", m.brandColor);
  if (m.logo && $("#b-logo")) { $("#b-logo").src = m.logo; $("#b-logo").style.display = "block"; }

  const nav = $("#nav"), stage = $("#stage");
  nav.insertAdjacentHTML("afterend", cta(true));
  TABS.forEach((t, i) => {
    const b = el("button", "nav-btn" + (i ? "" : " active"), `<span class="mono num">${String(i + 1).padStart(2, "0")}</span>${esc(t.label)}`);
    b.onclick = () => go(t.id); b.dataset.id = t.id; nav.appendChild(b);
    const p = el("section", "panel" + (i ? "" : " show")); p.id = "p-" + t.id;
    try { p.innerHTML = `<div class="wrap">${t.render()}</div>`; }
    catch (e) { p.innerHTML = `<div class="wrap">${empty("This tab failed to render; check its data in data.js. " + e.message)}</div>`; }
    stage.appendChild(p);
  });
}
function go(id) {
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.toggle("active", b.dataset.id === id));
  document.querySelectorAll(".panel").forEach(p => p.classList.toggle("show", p.id === "p-" + id));
  window.scrollTo({ top: 0, behavior: "smooth" });
}
document.addEventListener("keydown", e => {
  const n = +e.key; if (n >= 1 && n <= TABS.length && !/input|textarea/i.test(document.activeElement.tagName)) go(TABS[n - 1].id);
});
mount();
