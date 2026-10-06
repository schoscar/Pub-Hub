# Writes the researched rugby pubs in data/rugby.json onto data/pubs_plus.json as
# an `rg` record. Each entry carries the source it came from. Re-runnable.
import json
R = {r['id']: r for r in json.load(open('data/rugby.json'))}
pubs = json.load(open('data/pubs_plus.json'))
n = 0
for p in pubs:
    r = R.get(p['id'])
    if r:
        p['rg'] = {k: v for k, v in r.items() if k != 'id'}; n += 1
    else:
        p.pop('rg', None)
json.dump(pubs, open('data/pubs_plus.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('rugby records applied:', n, 'of', len(R))
