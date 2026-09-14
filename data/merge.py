import json, glob
from collections import Counter
master=json.load(open('data/pubs.json'))
notes=json.load(open('verify/new_notes.json'))
new=[]
for f in ['north','east','south','west','central']:
    new+=json.load(open(f'data/new_{f}.json'))
def apply(p, v):
    for k,val in v.get('patch',{}).items():
        if k=='occ+':
            for o in val:
                if o not in p['occ']: p['occ'].append(o)
            continue
        parts=k.split('.'); tgt=p
        ok=True
        for part in parts[:-1]:
            if tgt.get(part) is None:
                ok=False; break
            tgt=tgt[part]
        if ok: tgt[parts[-1]]=val
    # keep occ in sync with roast
    if p.get('food') and p['food'].get('roast') and 'roast' not in p['occ']: p['occ'].append('roast')
    if p.get('food') and not p['food'].get('roast') and 'roast' in p['occ'] and v.get('patch',{}).get('food.roast') is False: p['occ'].remove('roast')
    p['verify']={'status':v['status'],'checked':'2026-09','source':v.get('source'),'notes':v.get('notes')}
out=list(master); ids={p['id'] for p in master}
dropped=[]
for p in new:
    assert p['id'] not in ids, p['id']
    v=notes.get(p['id'])
    if v:
        if v['status']=='closed': dropped.append(p['id']); continue
        apply(p,v)
    out.append(p); ids.add(p['id'])
json.dump(out, open('data/pubs_all.json','w',encoding='utf-8'), indent=1, ensure_ascii=False)
c=Counter(p['verify']['status'] for p in out)
fb=sum(1 for p in out if p['fb'])
unv_fb=[p['id'] for p in out if p['verify']['status']=='unverified' and p['fb']]
print(len(out),'pubs total;',dict(c),'; with football:',fb,'; dropped closed:',dropped)
print('unverified football pubs:',len(unv_fb)); print(' '.join(unv_fb))
