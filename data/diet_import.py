# Adds dietary information to data/pubs_plus.json from OpenStreetMap diet:* tags.
# Refetch the source with the Overpass query in data/osm_diet_query.txt.
import json
from collections import Counter

els = json.load(open('data/osm_diet.json'))['elements']
YES = {'yes', 'only'}
NO = {'no'}
# "limited" is a real answer but not a promise, so it is not a yes.
FIELDS = [('veg', 'diet:vegetarian'), ('vegan', 'diet:vegan'), ('gf', 'diet:gluten_free'), ('halal', 'diet:halal')]

by_osm = {}
for e in els:
    t = e.get('tags', {})
    d = {}
    for key, tag in FIELDS:
        v = t.get(tag)
        d[key] = True if v in YES else (False if v in NO else None)
    if any(v is not None for v in d.values()):
        by_osm[f"{e['type']}/{e['id']}"] = d

pubs = json.load(open('data/pubs_plus.json'))
hit = 0
for p in pubs:
    oid = (p.get('osm') or {}).get('id')
    d = by_osm.get(oid)
    if d:
        p['diet'] = d; hit += 1
    else:
        p.setdefault('diet', {k: None for k, _ in FIELDS})
json.dump(pubs, open('data/pubs_plus.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('diet records from OSM:', len(by_osm), '; matched to pubs:', hit)
print(Counter({k: sum(1 for p in pubs if p['diet'][k] is True) for k, _ in FIELDS}))
