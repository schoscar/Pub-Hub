import json, datetime, hashlib, re
pubs=json.load(open('data/pubs_plus.json'))
cur=sum(1 for p in pubs if p.get('tier')=='curated')
base=len(pubs)-cur
checked=sum(1 for p in pubs if p.get('tier')=='curated' and (p.get('verify') or {}).get('status') in ('verified','partial'))
d=datetime.date.today().isoformat()
meta={"count":len(pubs),"curated":cur,"base":base,"checked":checked,"generated":d}
lines=[]
lines.append(f"// Generated on {d}. {len(pubs)} pubs: {cur} curated ({checked} checked) + {base} OpenStreetMap listings. Map data (c) OpenStreetMap contributors, ODbL.")
lines.append("window.PUBS_META="+json.dumps(meta)+";")
body=",\n".join(json.dumps(p, separators=(',',':')) for p in pubs)
lines.append("window.PUBS=["+body+"];")
open('pubs.js','w',encoding='utf-8').write("\n".join(lines)+"\n")
print(meta)

# Version the data URLs so a rebuild always reaches browsers and the service
# worker, instead of a stale pubs.js sitting in an HTTP cache.
def stamp(f): return hashlib.sha1(open(f,'rb').read()).hexdigest()[:8]
vers = {'pubs.js': stamp('pubs.js'), 'london.js': stamp('london.js')}
for f in ('index.html', 'sw.js'):
    t = open(f, encoding='utf-8').read()
    for name, v in vers.items():
        t = re.sub(re.escape(name) + r'(\?v=[0-9a-f]+)?', name + '?v=' + v, t)
    open(f, 'w', encoding='utf-8').write(t)
print('data urls stamped', vers)
