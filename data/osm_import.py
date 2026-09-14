import json, re, math, unicodedata
from collections import Counter
cur=json.load(open('data/pubs_all.json'))
osm=json.load(open('data/osm_pubs.json'))['elements']
sta=json.load(open('data/osm_stations.json'))['elements']

PC={ # postcode district -> area
'N1':'Islington','N2':'East Finchley','N3':'Finchley','N4':'Finsbury Park','N5':'Highbury','N6':'Highgate','N7':'Holloway','N8':'Hornsey','N9':'Edmonton','N10':'Muswell Hill','N11':'New Southgate','N12':'North Finchley','N13':'Palmers Green','N14':'Southgate','N15':'South Tottenham','N16':'Stoke Newington','N17':'Tottenham','N18':'Upper Edmonton','N19':'Archway','N20':'Whetstone','N21':'Winchmore Hill','N22':'Wood Green',
'NW1':'Camden','NW2':'Cricklewood','NW3':'Hampstead','NW4':'Hendon','NW5':'Kentish Town','NW6':'Kilburn','NW7':'Mill Hill','NW8':'St John\'s Wood','NW9':'Kingsbury','NW10':'Willesden','NW11':'Golders Green',
'E1':'Whitechapel','E2':'Bethnal Green','E3':'Bow','E4':'Chingford','E5':'Clapton','E6':'East Ham','E7':'Forest Gate','E8':'Hackney','E9':'Homerton','E10':'Leyton','E11':'Leytonstone','E12':'Manor Park','E13':'Plaistow','E14':'Isle of Dogs','E15':'Stratford','E16':'Canning Town','E17':'Walthamstow','E18':'South Woodford','E20':'Stratford',
'SE1':'Southwark','SE2':'Abbey Wood','SE3':'Blackheath','SE4':'Brockley','SE5':'Camberwell','SE6':'Catford','SE7':'Charlton','SE8':'Deptford','SE9':'Eltham','SE10':'Greenwich','SE11':'Kennington','SE12':'Lee','SE13':'Lewisham','SE14':'New Cross','SE15':'Peckham','SE16':'Rotherhithe','SE17':'Walworth','SE18':'Woolwich','SE19':'Crystal Palace','SE20':'Penge','SE21':'Dulwich','SE22':'East Dulwich','SE23':'Forest Hill','SE24':'Herne Hill','SE25':'South Norwood','SE26':'Sydenham','SE27':'West Norwood','SE28':'Thamesmead',
'SW1':'Westminster','SW2':'Brixton Hill','SW3':'Chelsea','SW4':'Clapham','SW5':'Earl\'s Court','SW6':'Fulham','SW7':'South Kensington','SW8':'South Lambeth','SW9':'Brixton','SW10':'West Brompton','SW11':'Battersea','SW12':'Balham','SW13':'Barnes','SW14':'Mortlake','SW15':'Putney','SW16':'Streatham','SW17':'Tooting','SW18':'Wandsworth','SW19':'Wimbledon','SW20':'Raynes Park',
'W1':'West End','W2':'Paddington','W3':'Acton','W4':'Chiswick','W5':'Ealing','W6':'Hammersmith','W7':'Hanwell','W8':'Kensington','W9':'Maida Vale','W10':'North Kensington','W11':'Notting Hill','W12':'Shepherd\'s Bush','W13':'West Ealing','W14':'West Kensington',
'WC1':'Bloomsbury','WC2':'Covent Garden','EC1':'Clerkenwell','EC2':'City of London','EC3':'City of London','EC4':'City of London',
'BR1':'Bromley','BR2':'Bromley','BR3':'Beckenham','BR4':'West Wickham','BR5':'Orpington','BR6':'Orpington','BR7':'Chislehurst','CR0':'Croydon','CR2':'South Croydon','CR4':'Mitcham','CR7':'Thornton Heath','CR8':'Purley','DA5':'Bexley','DA6':'Bexleyheath','DA7':'Bexleyheath','DA8':'Erith','DA14':'Sidcup','DA15':'Sidcup','DA16':'Welling','DA17':'Belvedere','EN1':'Enfield','EN2':'Enfield','EN3':'Enfield','EN4':'Cockfosters','EN5':'Barnet','HA0':'Wembley','HA1':'Harrow','HA2':'Harrow','HA3':'Harrow','HA4':'Ruislip','HA5':'Pinner','HA6':'Northwood','HA7':'Stanmore','HA8':'Edgware','HA9':'Wembley','IG1':'Ilford','IG2':'Gants Hill','IG3':'Seven Kings','IG4':'Redbridge','IG5':'Clayhall','IG6':'Barkingside','IG8':'Woodford','IG11':'Barking','KT1':'Kingston','KT2':'Kingston','KT3':'New Malden','KT4':'Worcester Park','KT5':'Surbiton','KT6':'Surbiton','KT9':'Chessington','RM1':'Romford','RM2':'Romford','RM3':'Harold Wood','RM5':'Collier Row','RM6':'Chadwell Heath','RM7':'Romford','RM8':'Dagenham','RM9':'Dagenham','RM10':'Dagenham','RM11':'Hornchurch','RM12':'Hornchurch','RM13':'Rainham','RM14':'Upminster','SM1':'Sutton','SM2':'Sutton','SM3':'Cheam','SM4':'Morden','SM5':'Carshalton','SM6':'Wallington','TW1':'Twickenham','TW2':'Twickenham','TW3':'Hounslow','TW4':'Hounslow','TW5':'Heston','TW7':'Isleworth','TW8':'Brentford','TW9':'Richmond','TW10':'Richmond','TW11':'Teddington','TW12':'Hampton','TW13':'Feltham','TW14':'Feltham','UB1':'Southall','UB2':'Southall','UB3':'Hayes','UB4':'Hayes','UB5':'Northolt','UB6':'Greenford','UB7':'West Drayton','UB8':'Uxbridge','UB10':'Hillingdon',
}
def region_from_pc(d):
    if not d: return None
    m=re.match(r'([A-Z]{1,2})(\d+)', d); 
    if not m: return None
    a,n=m.group(1),int(m.group(2))
    if a in ('WC','EC'): return 'C'
    if a=='W' and n==1: return 'C'
    if a=='SW' and n==1: return 'C'
    if a in ('N','NW','EN','HA','IG') and a!='IG': return 'N' if a in ('N','NW','EN','HA') else None
    if a in ('IG','RM'): return 'E'
    if a=='E': return 'E'
    if a in ('SE','SW','BR','CR','DA','KT','SM'): return 'S'
    if a in ('W','TW','UB'): return 'W'
    return None
def norm(s):
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    s=re.sub(r'\(.*?\)','',s); s=s.replace('&',' and ').replace("'",'')
    s=re.sub(r'\b(the|ye|olde|old|pub|public house|tavern|inn|arms|bar|hotel)\b',' ',s)
    return re.sub(r'[^a-z0-9]+',' ',s).strip()
def dist(a,b,c,d):
    R=6371000; dl=math.radians(c-a); dg=math.radians(d-b)
    x=math.sin(dl/2)**2+math.cos(math.radians(a))*math.cos(math.radians(c))*math.sin(dg/2)**2
    return 2*R*math.asin(math.sqrt(x))
def coords(e):
    if 'lat' in e: return e['lat'],e['lon']
    c=e.get('center'); return (c['lat'],c['lon']) if c else (None,None)

stations=[(s['tags']['name'],s['lat'],s['lon']) for s in sta if s.get('tags',{}).get('name') and 'lat' in s]
def nearest_station(lat,lng):
    best=min(stations,key=lambda s:dist(lat,lng,s[1],s[2])); d=dist(lat,lng,best[1],best[2])
    return best[0].replace(' Underground Station','').replace(' Station','').replace(' Railway','').strip(), max(1,round(d/80))
def nearest_curated(lat,lng):
    best=min(cur,key=lambda p:dist(lat,lng,p['lat'],p['lng'])); return best, dist(lat,lng,best['lat'],best['lng'])

matched={}; base=[]; skipped=0
for e in osm:
    t=e.get('tags',{}); name=t.get('name')
    if not name: skipped+=1; continue
    lat,lng=coords(e)
    if lat is None: skipped+=1; continue
    n=norm(name)
    hit=None
    for p in cur:
        if p['id'] in matched: continue
        d=dist(lat,lng,p['lat'],p['lng'])
        if d>450: continue
        pn=norm(p['name'])
        if n==pn or (len(n)>4 and (n in pn or pn in n)):
            if hit is None or d<hit[1]: hit=(p,d)
    osm_info={'id':f"{e['type']}/{e['id']}",'website':t.get('website') or t.get('contact:website'),'phone':t.get('phone') or t.get('contact:phone'),'hours':t.get('opening_hours'),'postcode':t.get('addr:postcode'),'street':t.get('addr:street'),'housenumber':t.get('addr:housenumber'),'brewery':t.get('brewery') or t.get('operator'),'real_ale':t.get('real_ale'),'outdoor':t.get('outdoor_seating'),'wheelchair':t.get('wheelchair'),'cuisine':t.get('cuisine'),'food':t.get('food'),'dog':t.get('dog'),'music':t.get('live_music'),'beer_garden':t.get('beer_garden')}
    osm_info={k:v for k,v in osm_info.items() if v}
    if hit:
        p,d=hit; matched[p['id']]=d
        p['lat'],p['lng']=lat,lng; p['osm']=osm_info
        continue
    pc=(t.get('addr:postcode') or '').upper().strip(); district=None
    m=re.match(r'([A-Z]{1,2}\d{1,2})',pc); 
    if m: district=m.group(1)
    area=PC.get(district); region=region_from_pc(district)
    near,nd=nearest_curated(lat,lng)
    if not area: area=t.get('addr:suburb') or (near['area'] if nd<2500 else (t.get('addr:city') or 'London'))
    if not region:
        region=near['region'] if nd<4000 else ('N' if lat>51.53 else 'S') if abs(lng+0.12)<0.12 else ('E' if lng>-0.05 else 'W')
    st,walk=nearest_station(lat,lng)
    cuis=[c.strip().replace('_',' ').title() for c in (t.get('cuisine') or '').split(';') if c.strip()][:3]
    cuis=[{'Pub':'Pub classics','British':'British','Fish And Chips':'Fish and chips','Burger':'Burgers','Pizza':'Pizza','Thai':'Thai','Indian':'Indian','Italian':'Italian','Steak House':'Grill','Regional':'British','International':'International'}.get(c,c) for c in cuis]
    food_yes=bool(cuis) or (t.get('food') in ('yes','served'))
    out_yes=t.get('outdoor_seating')=='yes' or t.get('beer_garden')=='yes'
    feat=[]
    if t.get('real_ale')=='yes': feat.append('ale')
    if t.get('dog')=='yes': feat.append('dogs')
    if t.get('live_music')=='yes': feat.append('music')
    if t.get('fireplace')=='yes': feat.append('fire')
    base.append({'id':f"osm-{e['type']}-{e['id']}",'name':name,'area':area,'region':region,'station':st,'walk':walk,'lat':lat,'lng':lng,'tier':'base',
        'fb':None,'occ':(['outdoor'] if out_yes else []),'group':0,'out':{'kind':'terrace' if t.get('outdoor_seating')=='yes' else ('garden' if t.get('beer_garden')=='yes' else 'none'),'benches':False,'river':False,'big':False},
        'late':'','price':0,'food':{'cuisine':cuis,'sitDown':food_yes,'where':None,'rating':1 if food_yes else 0,'roast':False,'note':'Food listed on OpenStreetMap' if food_yes else 'Not known'},
        'feat':feat,'rep':0,'tip':'','osm':osm_info,'verify':{'status':'map','checked':'2026-09','source':f"https://www.openstreetmap.org/{e['type']}/{e['id']}",'notes':'Listed as a pub on OpenStreetMap. Name and position come from the map; everything else is unknown until checked.'}})
for p in cur: p.setdefault('tier','curated')
allp=cur+base
# station for curated pubs missing station text is kept; add osm-derived nearest station as 'station2' not needed
json.dump(allp, open('data/pubs_plus.json','w',encoding='utf-8'), ensure_ascii=False, indent=0)
print('curated',len(cur),'matched to OSM',len(matched),'; base added',len(base),'; skipped',skipped,'; total',len(allp))
print('unmatched curated:', [p['name'] for p in cur if p['id'] not in matched][:60])
print('base by region', Counter(p['region'] for p in base))
print('base with food',sum(1 for p in base if p['food']['rating']),'outdoor',sum(1 for p in base if p['out']['kind']!='none'),'ale',sum(1 for p in base if 'ale' in p['feat']))

# ---- second pass: looser matching for curated pubs still unmatched
GENERIC={'prince george','rose and crown','royal oak','black lion','victoria','lamb','anchor and hope','woodman','prince albert','crown and anchor','red lion','george','kings','queens','white hart','castle'}
def toks(s): return {t for t in norm(s).split() if len(t)>=4}
removed=set(); second=0
for p in cur:
    if p['id'] in matched: continue
    pt=toks(p['name']); pn=norm(p['name']); best=None
    for b in base:
        if b['id'] in removed: continue
        d=dist(p['lat'],p['lng'],b['lat'],b['lng'])
        lim=700 if pn in GENERIC else 1500
        if d>lim: continue
        bt=toks(b['name']); bn=norm(b['name'])
        ok = pn==bn or (pt and bt and len(pt&bt)/max(1,min(len(pt),len(bt)))>=0.5) or (len(pn)>4 and (pn in bn or bn in pn))
        if ok and (best is None or d<best[1]): best=(b,d)
    if best:
        b,d=best; matched[p['id']]=d; second+=1
        p['lat'],p['lng']=b['lat'],b['lng']; p['osm']=b['osm']; removed.add(b['id'])
base=[b for b in base if b['id'] not in removed]
allp=cur+base
json.dump(allp, open('data/pubs_plus.json','w',encoding='utf-8'), ensure_ascii=False, indent=0)
print('second pass matched',second,'; still unmatched:', [p['name']+' ('+p['area']+')' for p in cur if p['id'] not in matched])
print('total now',len(allp))
