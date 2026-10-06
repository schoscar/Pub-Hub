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

// Field order matters: the model writes its reading of the request first, so the
// choices after it follow from what it understood instead of being guessed up
// front. Every field is required, because optional ones tend to be skipped.
function schema() {
  const teams = ["", ...Object.keys(VOCAB.teams || {})];
  return {
    type: "object",
    properties: {
      understanding: { type: "string" },
      tab: { type: "string", enum: TABS },
      team: { type: "string", enum: teams },
      rugby_fans: { type: "array", items: { type: "string", enum: ["ENG", "IRL", "SCO", "WAL"] } },
      twickenham: { type: "boolean" },
      place: { type: "string" },
      region: { type: "string", enum: REGIONS },
      open_until: { type: "integer", enum: LATE },
      features: { type: "array", items: { type: "string", enum: VOCAB.features || [] } },
      group_size: { type: "integer" },
      cuisine: { type: "array", items: { type: "string", enum: VOCAB.cuisines || [] } },
      diet: { type: "array", items: { type: "string", enum: DIETS } },
      roast: { type: "boolean" },
      no_screens: { type: "boolean" },
      cant_filter: { type: "array", items: { type: "string" } },
    },
    required: ["understanding", "tab", "team", "rugby_fans", "twickenham", "place", "region", "open_until", "features", "group_size", "cuisine", "diet", "roast", "no_screens", "cant_filter"],
  };
}

function systemPrompt() {
  const teams = Object.entries(VOCAB.teams || {}).map(([k, v]) => `${k} ${v}`).join("; ");
  return `You read a request for a London pub and fill in search filters for the Pub Hub app. Reply with JSON only.

understanding: one sentence restating what they want. Write this first.
tab: the main purpose.
  match = watching football (any football club, "the game", Premier League). rugby = watching rugby (Six Nations, Twickenham, rugby clubs). Football is never rugby.
  eat = food is the point. party = birthday, leaving drinks, big night, dancing, late session. quiet = quiet drink, catch-up, date, no screens. outside = garden, terrace, sunshine, riverside. explore = anything else.
team: football team code, only when tab is match. ${teams}. Spurs is TOT, the Gunners ARS, the Hammers WHU. Otherwise "".
rugby_fans: national rugby sides they support (ENG, IRL, SCO, WAL), only when tab is rugby.
twickenham: true only for a match day at Twickenham.
place: a neighbourhood, street or station they name, exactly as written. "" if none. Never a region, never a pub name.
region: N, E, S, W or C only if they say north, south, east, west, central, the City or the West End. South east and south west are S. "" if they name no area. Never guess.
open_until: 24, 25 or 26 if they ask to be open until midnight, 1am or 2am, or ask for late, a late licence or dancing. 0 otherwise. A few drinks after a game is 0.
features: from the allowed list only. music = live music or a band. dj = DJs. outdoor = any outside space. dogs = dog friendly. ale = real ale. fire = open fire. games = pool or darts. hire = private room.
group_size: number of people if stated, else 0.
cuisine, diet (veg, vegan, gf), roast, no_screens: only what they ask for.
cant_filter: short phrases for things they asked that the fields above cannot hold, such as a kick-off time, a budget or a mood. [] if none.

Example. Request: "Spurs game in Islington then somewhere late with a band, 8 of us"
{"understanding":"Watch the Tottenham match in Islington, then stay out late somewhere with live music, eight people.","tab":"match","team":"TOT","rugby_fans":[],"twickenham":false,"place":"Islington","region":"","open_until":24,"features":["music"],"group_size":8,"cuisine":[],"diet":[],"roast":false,"no_screens":false,"cant_filter":[]}

Example. Request: "cosy veggie sunday roast near the river, no football on, dog coming"
{"understanding":"A cosy Sunday roast with vegetarian options by the river, away from the football, dog friendly.","tab":"eat","team":"","rugby_fans":[],"twickenham":false,"place":"","region":"","open_until":0,"features":["riverside","dogs"],"group_size":0,"cuisine":[],"diet":["veg"],"roast":true,"no_screens":true,"cant_filter":["cosy"]}`;
}

// The model's answer is checked field by field against the app's vocabulary,
// with common spellings mapped onto the codes, so nothing else can get through.
const FEATURE_WORDS = { "live music": "music", band: "music", bands: "music", djs: "dj", "dog friendly": "dogs", dog: "dogs", garden: "outdoor", outside: "outdoor", terrace: "outdoor", "beer garden": "outdoor", "real ale": "ale", cask: "ale", "craft beer": "craft", "open fire": "fire", fireplace: "fire", historic: "heritage", "roof terrace": "rooftop", river: "riverside", "private room": "hire", pool: "games", darts: "games", kids: "family" };
const DIET_WORDS = { vegetarian: "veg", veggie: "veg", "gluten free": "gf", "gluten-free": "gf" };
function clean(r) {
  r = r && typeof r === "object" ? r : {};
  const pick = (v, list, d) => (list.includes(v) ? v : d);
  const low = v => (typeof v === "string" ? v.trim().toLowerCase() : "");
  const arr = (v, list, words = {}) => Array.isArray(v) ? [...new Set(v.map(x => words[low(x)] || (list.includes(x) ? x : list.find(l => l.toLowerCase() === low(x)))).filter(Boolean))] : [];
  const str = (v, n) => (typeof v === "string" ? v.trim().slice(0, n) : "");
  const teamCode = v => { const t = low(v); if (!t) return ""; const hit = Object.entries(VOCAB.teams || {}).find(([k, n]) => k.toLowerCase() === t || n.toLowerCase() === t); return hit ? hit[0] : { spurs: "TOT", gunners: "ARS", hammers: "WHU" }[t] || ""; };
  const late = v => { if (LATE.includes(Number(v))) return Number(v); const t = low(String(v ?? "")); return /2 ?am|02:00/.test(t) ? 26 : /1 ?am|01:00/.test(t) ? 25 : /midnight|12 ?am|00:00|late/.test(t) ? 24 : 0; };
  const tab = pick(low(r.tab), TABS, "explore");
  return {
    tab,
    understanding: str(r.understanding, 200),
    place: str(r.place, 40),
    region: pick(String(r.region || "").toUpperCase(), REGIONS, ""),
    team: tab === "match" ? teamCode(r.team) : "",
    rugby_fans: tab === "rugby" ? arr(r.rugby_fans, ["ENG", "IRL", "SCO", "WAL"], { england: "ENG", ireland: "IRL", scotland: "SCO", wales: "WAL" }) : [],
    twickenham: tab === "rugby" && r.twickenham === true,
    open_until: late(r.open_until),
    features: arr(r.features, VOCAB.features || [], FEATURE_WORDS),
    group_size: Math.max(0, Math.min(200, parseInt(r.group_size, 10) || 0)),
    cuisine: arr(r.cuisine, VOCAB.cuisines || []),
    diet: arr(r.diet, DIETS, DIET_WORDS),
    roast: r.roast === true,
    no_screens: r.no_screens === true,
    cant_filter: Array.isArray(r.cant_filter) ? r.cant_filter.filter(x => typeof x === "string" && x.trim()).map(x => x.trim().slice(0, 80)).slice(0, 4) : [],
    summary: str(r.understanding || r.summary, 200),
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
        response_format: { type: "json_schema", json_schema: schema() },
        max_tokens: 400,
        temperature: 0,
      });
      const raw = typeof out?.response === "string" ? JSON.parse(out.response) : out?.response;
      return reply({ filters: clean(raw), raw, model: MODEL, version: 2 }, 200, cors);
    } catch (e) {
      // Covers the daily allowance running out and the model missing the schema.
      return reply({ error: "The model could not answer.", detail: String(e?.message || e).slice(0, 200) }, 502, cors);
    }
  },
};
