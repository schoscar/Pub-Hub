# Pub Hub

Every London pub, sorted by what you're after: match day, eating out, a big night, a quiet pint or sitting outside.

A single static web app. No build step, no server: open `index.html` or host the folder anywhere that serves files.

## Files

- `index.html` — the app (HTML, CSS and JavaScript in one file).
- `pubs.js` — the pub dataset: 359 written-up pubs, all checked against a source, plus 3,283 OpenStreetMap listings.
  Written-up pubs and map listings are shown in separate bands, and a map listing drops out of the results the moment you set a filter it cannot answer.
- `london.js` — map layers (roads, parks, water) derived from OpenStreetMap and simplified.
- `manifest.webmanifest`, `sw.js`, `icon*` — lets phones add it to the home screen and open it offline.
- `data/` — source data and the Python scripts that build `pubs.js` and `london.js`.
- `verify/` — notes and sources from checking pubs against their websites and pub directories.

## Rebuilding the data

    python3 data/merge.py        # merges curated pubs + verification notes -> data/pubs_all.json
    python3 data/osm_import.py   # matches OpenStreetMap pubs and adds map listings -> data/pubs_plus.json

    python3 data/osm_enrich.py   # live_sport, closing times, brewery ties, feature tags
    python3 data/diet_import.py  # adds dietary info from OpenStreetMap diet:* tags
    python3 data/build_js.py     # regenerates pubs.js and stamps the data URLs
The raw OpenStreetMap downloads are not committed; fetch them again with the Overpass queries noted in the scripts.

## Hosting

Push to GitHub, then Settings → Pages → Deploy from branch → `main` / root. The site appears at `https://<user>.github.io/pub-hub/`.

## Data

Pub write-ups are original. Map data © OpenStreetMap contributors, ODbL.
