// Pub Hub "Ask": turns one sentence about a night out into Pub Hub's own filters.
//
// It runs on Cloudflare Workers AI's free daily allowance. When that runs out
// the free plan returns an error rather than a bill, and the page falls back to
// keyword matching. The model never names pubs: it only fills in filters, and
// the page applies them to its own checked data, so it cannot invent a pub or a
// screen that is not there. Every field it returns is checked against the list
// below before it leaves this Worker.
//
// Deploy: paste this whole file into a Worker and add a Workers AI binding
// called AI. See worker/README.md. Regenerate the vocabulary block with
// `python3 worker/build.py` after the app's teams or cuisines change.

/*VOCAB-START*/
const VOCAB = {"teams": {"ARS": "Arsenal", "BRE": "Brentford", "CHA": "Charlton Athletic", "CHE": "Chelsea", "CRY": "Crystal Palace", "FUL": "Fulham", "LEY": "Leyton Orient", "MIL": "Millwall", "QPR": "Queens Park Rangers", "TOT": "Tottenham Hotspur", "WHU": "West Ham United", "WIM": "AFC Wimbledon", "AVL": "Aston Villa", "CEL": "Celtic", "EVE": "Everton", "LEE": "Leeds United", "LIV": "Liverpool", "MCI": "Manchester City", "MUN": "Manchester United", "NEW": "Newcastle United", "NOR": "Norwich City", "RAN": "Rangers", "ENG": "England", "IRL": "Ireland", "SCO": "Scotland", "WAL": "Wales"}, "features": ["ale", "craft", "cocktails", "fire", "heritage", "music", "dj", "karaoke", "comedy", "quiz", "games", "theatre", "dogs", "family", "rooftop", "riverside", "hire", "hidden", "quirky", "outdoor"], "cuisines": ["American", "BBQ", "Barbecue", "Breakfast", "British", "Burgers", "Caribbean", "Fish and chips", "French", "Gastropub", "Grill", "Indian", "Irish", "Italian", "Mediterranean", "Mexican", "Pie", "Pies", "Pizza", "Pub classics", "Sandwich", "Seafood", "Street food", "Tapas", "Thai"]};
/*VOCAB-END*/

const MODEL = "@cf/meta/llama-3.3-70b-instruct-fp8-fast";
const ALLOWED_ORIGINS = ["https://schoscar.github.io", "http://localhost:8766", "http://127.0.0.1:8766"];
const MAX_CHARS = 300;
const TABS = ["match", "rugby", "eat", "party", "quiet", "outside", "explore"];
const REGIONS = ["", "N", "E", "S", "W", "C"];
const LATE = [0, 24, 25, 26];
const DIETS = ["veg", "vegan", "gf"];

const SCHEMA = {
  type: "object",
  properties: {
    tab: { type: "string", enum: TABS },
    place: { type: "string" },
    region: { type: "string", enum: REGIONS },
    team: { type: "string" },
    rugby_fans: { type: "array", items: { type: "string" } },
    twickenham: { type: "boolean" },
    open_until: { type: "integer", enum: LATE },
    features: { type: "array", items: { type: "string" } },
    group_size: { type: "integer" },
    cuisine: { type: "array", items: { type: "string" } },
    diet: { type: "array", items: { type: "string", enum: DIETS } },
    roast: { type: "boolean" },
    no_screens: { type: "boolean" },
    cant_filter: { type: "array", items: { type: "string" } },
    summary: { type: "string" },
  },
  required: ["tab", "summary"],
};

function systemPrompt() {
  const teams = Object.entries(VOCAB.teams || {}).map(([k, v]) => `${k}=${v}`).join(", ");
  return `You turn a request for a London pub into search filters for the Pub Hub app. Reply with JSON only, matching the schema.

tab: the one that fits the main purpose.
- match: watching football. rugby: watching rugby, the Six Nations, Twickenham.
- eat: the food is the point. party: birthday, leaving drinks, big night, dancing, late session.
- quiet: a quiet drink, a catch-up, a date, no screens. outside: garden, terrace, sun, riverside.
- explore: anything else.
place: a London neighbourhood, high street or station they name, copied exactly as written. Empty if none. Never a pub name or a region.
region: N, E, S, W or C when they name a broad area. South east, south west, south of the river are S. North west is N. The City and the West End are C. Empty otherwise.
team: a football team code from this list, only for football: ${teams}. Empty if none.
rugby_fans: national rugby sides they support, codes ENG, IRL, SCO, WAL. Only for rugby.
twickenham: true only for a match day at Twickenham.
open_until: 24, 25 or 26 for open until midnight, 1am or 2am. Set it only if they ask for late, a late licence, past midnight, dancing, or name a time after 11pm. Wanting a few more drinks after a game is not a reason to set it.
features: any of ${(VOCAB.features || []).join(", ")}. outdoor means any outside space. music means live music. Only what they ask for.
group_size: how many people, if they say. Otherwise 0.
cuisine: any of ${(VOCAB.cuisines || []).join(", ")}. Only if named.
diet: veg, vegan or gf for vegetarian, vegan or gluten-free.
roast: true for a Sunday roast. no_screens: true if they want to avoid screens or the football.
cant_filter: short phrases for anything they asked for that these fields cannot express, such as a kick-off time, a fixture, a budget or a vibe. Empty if none.
summary: one short sentence in plain British English saying what you will search for. Do not mention JSON or filters.`;
}

function clean(r) {
  r = r && typeof r === "object" ? r : {};
  const pick = (v, list, d) => (list.includes(v) ? v : d);
  const arr = (v, list) => (Array.isArray(v) ? [...new Set(v.filter(x => list.includes(x)))] : []);
  const str = (v, n) => (typeof v === "string" ? v.trim().slice(0, n) : "");
  const tab = pick(r.tab, TABS, "explore");
  return {
    tab,
    place: str(r.place, 40),
    region: pick(r.region, REGIONS, ""),
    team: tab === "match" ? pick(r.team, Object.keys(VOCAB.teams || {}), "") : "",
    rugby_fans: tab === "rugby" ? arr(r.rugby_fans, ["ENG", "IRL", "SCO", "WAL"]) : [],
    twickenham: tab === "rugby" && r.twickenham === true,
    open_until: pick(Number(r.open_until), LATE, 0),
    features: arr(r.features, VOCAB.features || []),
    group_size: Math.max(0, Math.min(200, parseInt(r.group_size, 10) || 0)),
    cuisine: arr(r.cuisine, VOCAB.cuisines || []),
    diet: arr(r.diet, DIETS),
    roast: r.roast === true,
    no_screens: r.no_screens === true,
    cant_filter: Array.isArray(r.cant_filter) ? r.cant_filter.filter(x => typeof x === "string" && x.trim()).map(x => x.trim().slice(0, 80)).slice(0, 4) : [],
    summary: str(r.summary, 200),
  };
}

const reply = (body, status, headers) => new Response(JSON.stringify(body), { status, headers: { ...headers, "Content-Type": "application/json" } });

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const ok = ALLOWED_ORIGINS.includes(origin);
    const cors = {
      "Access-Control-Allow-Origin": ok ? origin : ALLOWED_ORIGINS[0],
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Access-Control-Max-Age": "86400",
      Vary: "Origin",
    };
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    if (request.method !== "POST") return reply({ error: 'Send a POST with {"q": "your request"}.' }, 405, cors);
    // Not security, just keeps other sites from spending the daily allowance.
    if (!ok) return reply({ error: "This endpoint only answers Pub Hub." }, 403, cors);

    let q;
    try { q = String((await request.json()).q || "").trim().slice(0, MAX_CHARS); }
    catch { return reply({ error: "The body must be JSON." }, 400, cors); }
    if (!q) return reply({ error: "Type what you are after first." }, 400, cors);
    if (!env.AI) return reply({ error: "Workers AI is not connected. Add a Workers AI binding named AI." }, 500, cors);

    try {
      const out = await env.AI.run(MODEL, {
        messages: [{ role: "system", content: systemPrompt() }, { role: "user", content: q }],
        response_format: { type: "json_schema", json_schema: SCHEMA },
        max_tokens: 400,
        temperature: 0,
      });
      const raw = typeof out?.response === "string" ? JSON.parse(out.response) : out?.response;
      return reply({ filters: clean(raw), model: MODEL }, 200, cors);
    } catch (e) {
      // Covers the daily allowance running out and the model missing the schema.
      return reply({ error: "The model could not answer.", detail: String(e?.message || e).slice(0, 200) }, 502, cors);
    }
  },
};
