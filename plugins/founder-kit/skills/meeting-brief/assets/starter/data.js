/* Single source of truth. Replace this placeholder content with the real meeting.
   Keep everything in one BRIEF object so the render stays dumb and facts live in one place.
   impact/effort are 1-5. Quotes must trace to the transcript (see fidelity in the skill).
   Quote strings must NOT include outer quotation marks (app.js wraps them). Escape any
   interior " as \\" or use typographic quotes; all fields are HTML-escaped on render. */
window.BRIEF = {
  meta: {
    partner: "Full Name",
    role: "Title, Org",
    date: "Month D, YYYY",
    length: "31 min",
    setting: "Intro call",
    outcome: "One-line result of the meeting",
    brandColor: "",   // e.g. "#00539B": the other company's brand color; overrides the accent
    logo: "",         // e.g. "logo.svg" (drop the file in this dir) or a URL; shows in the header
    // The follow-up CTA rendered in the rail and on the Agreements & Actions tab.
    // Fill these from the OWNER config (see SKILL.md "Owner config"), never from the
    // recipient's details. Leave a field empty and its button is simply not rendered.
    followup: {
      booking: "",                    // owner's scheduling link, e.g. "https://cal.example.com/you/30min"
      phone: "",                      // owner's phone, shown as-is; link uses tel: with digits (and a leading + if typed)
      line: "Ready when you are: grab a slot, or just call.",
    },
  },

  // THE CORE: every pain the person voiced, with a real quote.
  pains: [
    { id: "P1", title: "Short pain title", cat: "Data", impact: 5, effort: 3, solvable: true,
      quote: "What they actually said that reveals this pain.",
      note: "Why it matters / context." },
    { id: "P2", title: "Another pain", cat: "Revenue", impact: 4, effort: 4, solvable: false,
      quote: "Their words.", note: "..." },
    { id: "P3", title: "A third", cat: "People", impact: 3, effort: 2, solvable: true,
      quote: "Their words.", note: "..." },
  ],

  // Who / what could address each pain.
  solvers: [
    { pain_ids: ["P1", "P3"], who: "Capability or person", builds: "What they'd build or do.", proof: "Evidence they can deliver." },
    { pain_ids: ["P2"], who: "Another solver", builds: "...", proof: "..." },
  ],

  // Everyone in and around the room. side = a short camp label used for grouping + color.
  people: [
    { id: "them", name: "Full Name", role: "Title", side: "them", lead: true,
      note: "One-liner on who they are and why they matter.",
      research: "Public professional background from web research (role history, notable facts).",
      quote: "A characteristic line." },
    { id: "bridge", name: "Connector", role: "Mentor / intro", side: "bridge", note: "..." },
    { id: "us", name: "You", role: "Your role", side: "us", note: "..." },
  ],

  agreements: [
    { text: "What was agreed or decided.", quote: "The line that seals it." },
  ],

  actions: [
    { text: "Concrete next step.", owner: "Who", when: "By when", done: false },
    { text: "Already handled.", owner: "You", when: "", done: true },
  ],

  // Optional background timeline.
  background: [
    { year: "YYYY", title: "Milestone", detail: "..." },
  ],
};
