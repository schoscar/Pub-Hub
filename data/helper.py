import json
# fb tuple: (screens, big, proj, pos, sound, sky, tnt, all, book, teams, atmos, crowd)
def FB(screens, big, pos, sound, teams=(), atmos="neutral", crowd="lively", proj=False, sky=True, tnt=True, all=False, book=False):
    return {"screens":screens,"big":big,"proj":proj,"pos":list(pos),"sound":sound,"sky":sky,"tnt":tnt,"all":all,"book":book,"teams":list(teams),"atmos":atmos,"crowd":crowd}
# food: (cuisine list, sitDown, where, rating, roast, note)
def FOOD(cuisine=(), sit=False, where=None, rating=0, roast=False, note="Snacks only"):
    return {"cuisine":list(cuisine),"sitDown":sit,"where":where,"rating":rating,"roast":roast,"note":note}
def OUT(kind="none", benches=False, river=False, big=False):
    return {"kind":kind,"benches":benches,"river":river,"big":big}
def P(id, name, area, region, station, walk, lat, lng, fb=None, occ=(), group=10, out=None, late="23:00", price=2, food=None, feat=(), rep=2, tip=""):
    occ=list(occ); food=food or FOOD()
    if food["roast"] and "roast" not in occ: occ.append("roast")
    return {"id":id,"name":name,"area":area,"region":region,"station":station,"walk":walk,"lat":lat,"lng":lng,
            "fb":fb,"occ":occ,"group":group,"out":out or OUT(),"late":late,"price":price,"food":food,"feat":list(feat),"rep":rep,"tip":tip,
            "verify":{"status":"unverified","checked":None,"source":None,"notes":None}}
def save(name, pubs):
    json.dump(pubs, open(f"data/new_{name}.json","w",encoding="utf-8"), indent=1, ensure_ascii=False)
    print(name, len(pubs), "pubs")
