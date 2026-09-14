import json, datetime
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
