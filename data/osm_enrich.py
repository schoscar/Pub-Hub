# Pulls the OpenStreetMap tags we had not been using into data/pubs_plus.json:
# live_sport, closing times parsed out of opening_hours, the brewery tie behind
# brand/operator, and a handful of feature tags. Refetch the source with the
# Overpass query in data/osm_tags_query.txt.
import json, re
from collections import Counter

els = json.load(open('data/osm_tags.json'))['elements']
T = {f"{e['type']}/{e['id']}": e.get('tags', {}) for e in els}

# A British pub's brewery tie tells you most of what will be on the bar, so the
# pub company is a far better guide to the beer than OSM's sparse brewery tag.
# pours: what you can count on. guest: whether anything else gets a line.
TIE = {
    "Samuel Smith":  ("Samuel Smith",  ["Old Brewery Bitter", "Alpine Lager", "Taddy Lager", "Nut Brown Ale"], False),
    "Fuller's":      ("Fuller's",      ["London Pride", "ESB", "Oliver's Island", "Frontier"], False),
    "Young's":       ("Young's",       ["Young's Original", "Young's Special", "Camden Hells"], True),
    "Greene King":   ("Greene King",   ["Greene King IPA", "Abbot Ale", "Old Speckled Hen"], True),
    "Shepherd Neame":("Shepherd Neame",["Master Brew", "Spitfire", "Bishops Finger", "Whitstable Bay"], False),
    "Nicholson's":   ("Nicholson's",   ["Nicholson's Pale Ale", "a rotating cask range"], True),
    "Wetherspoon":   ("Wetherspoon",   ["Abbot Ale", "Doom Bar", "a large rotating guest range"], True),
    "Hall & Woodhouse": ("Badger", ["Badger First Call", "Tanglefoot", "Fursty Ferret"], False),
    "Charles Wells": ("Charles Wells", ["Bombardier", "Young's Original"], True),
    "BrewDog":       ("BrewDog",       ["Punk IPA", "Hazy Jane", "Lost Lager"], True),
    "The Craft Beer Co.": ("Free house", ["a large rotating cask and keg range"], True),
    "Stonegate":     ("Stonegate",     ["a managed range, mostly national brands"], True),
    "Mitchells & Butlers": ("Mitchells & Butlers", ["a managed range, mostly national brands"], True),
    "Taylor Walker": ("Taylor Walker", ["a rotating cask range"], True),
    "Ember Inns":    ("Ember Inns",    ["a rotating cask range"], True),
    "O'Neill's":     ("O'Neill's",     ["Guinness", "a rotating cask range"], True),
    "Geronimo Inns": ("Geronimo Inns", ["Young's Original", "a rotating guest range"], True),
    "Free House":    ("Free house",    [], True),
}
# OSM spells the same company several ways.
ALIAS = {
    "young & co": "Young's", "youngs": "Young's", "young's": "Young's", "young & co's brewery": "Young's",
    "fullers": "Fuller's", "fuller's": "Fuller's", "fuller, smith & turner": "Fuller's",
    "sam_smiths": "Samuel Smith", "samuel smith": "Samuel Smith", "samuel smiths": "Samuel Smith",
    "sam smith": "Samuel Smith", "samuel smith old brewery": "Samuel Smith",
    "jd weatherspoon": "Wetherspoon", "j d wetherspoon": "Wetherspoon", "wetherspoons": "Wetherspoon",
    "jd wetherspoon": "Wetherspoon", "wetherspoon": "Wetherspoon",
    "mitchells & butlers plc": "Mitchells & Butlers", "spirit pub company": "Stonegate",
    "greene king": "Greene King", "shepherd neame": "Shepherd Neame", "nicholson's": "Nicholson's",
    "nicholsons": "Nicholson's", "stonegate": "Stonegate", "stonegate pub company": "Stonegate",
    "brewdog": "BrewDog", "hall & woodhouse": "Hall & Woodhouse", "charles wells": "Charles Wells",
    "the craft beer co.": "The Craft Beer Co.", "free house": "Free House", "freehouse": "Free House",
    "taylor walker": "Taylor Walker", "ember inns": "Ember Inns", "o'neill's": "O'Neill's",
    "geronimo inns": "Geronimo Inns",
}
def tie_for(tags):
    for key in ('brand', 'operator'):
        v = tags.get(key)
        if not v: continue
        name = ALIAS.get(v.strip().lower())
        if name in TIE: return TIE[name]
    return None

def closing_hour(oh):
    """Latest closing time in opening_hours, as an hour number where 1am is 25."""
    if not oh: return None
    best = None
    for _, _, h, m in re.findall(r'\b(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})', oh):
        h, m = int(h), int(m)
        if h > 28: continue
        v = (h + 24 if h < 12 else h) + m / 60
        best = v if best is None else max(best, v)
    return best

pubs = json.load(open('data/pubs_plus.json'))
n = Counter()
for p in pubs:
    tags = T.get((p.get('osm') or {}).get('id'))
    if not tags: continue
    base = p.get('tier') != 'curated'

    # --- the football ------------------------------------------------------
    # live_sport says only that a pub shows sport, so map pubs get a stub that
    # every detailed football filter rejects. It is never treated as a write-up.
    if base and tags.get('live_sport') == 'yes' and not p['fb']:
        p['fb'] = {"screens": 0, "big": 0, "proj": False, "pos": [], "sound": "",
                   "sky": False, "tnt": False, "all": False, "book": False,
                   "teams": [], "atmos": "", "crowd": "", "stub": True}
        n['live_sport'] += 1

    # --- closing time ------------------------------------------------------
    if base and not p.get('late'):
        c = closing_hour(tags.get('opening_hours'))
        if c:
            h = int(c) % 24
            p['late'] = f"{h:02d}:{int(round((c % 1) * 60)):02d}"
            n['late'] += 1

    # --- what you will be drinking ----------------------------------------
    t = tie_for(tags)
    beer = {
        "tie": t[0] if t else None,
        "pours": list(t[1]) if t else [],
        "guest": t[2] if t else None,
        "ale": tags.get('real_ale') == 'yes' or 'ale' in p['feat'],
        "craft": tags.get('microbrewery') == 'yes' or 'craft' in p['feat'],
        "micro": tags.get('microbrewery') == 'yes',
    }
    if any(v for v in beer.values()):
        p['beer'] = beer; n['beer'] += 1
        if t: n['tie'] += 1

    # --- feature tags ------------------------------------------------------
    for tag, val, feat in [('real_ale', 'yes', 'ale'), ('real_fire', 'yes', 'fire'),
                           ('dog', 'yes', 'dogs'), ('microbrewery', 'yes', 'craft'),
                           ('cocktails', 'yes', 'cocktails'), ('live_music', 'yes', 'music')]:
        if tags.get(tag) == val and feat not in p['feat']:
            p['feat'].append(feat); n['feat:' + feat] += 1
    sport = tags.get('sport') or ''
    if ('billiards' in sport or 'darts' in sport) and 'games' not in p['feat']:
        p['feat'].append('games'); n['feat:games'] += 1

for p in pubs:
    p.setdefault('beer', {"tie": None, "pours": [], "guest": None, "ale": 'ale' in p['feat'], "craft": 'craft' in p['feat'], "micro": False})

json.dump(pubs, open('data/pubs_plus.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(dict(n))
print('pubs with a named brewery tie:', sum(1 for p in pubs if p['beer']['tie']))
print('map pubs now showing football  :', sum(1 for p in pubs if p.get('tier') != 'curated' and p['fb']))
print('map pubs with a closing time   :', sum(1 for p in pubs if p.get('tier') != 'curated' and p['late']))
