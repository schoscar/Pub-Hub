import json, math
BBOX={'w':-0.335,'e':0.085,'n':51.625,'s':51.355}
def proj(lng,lat): return ((lng-BBOX['w'])/(BBOX['e']-BBOX['w']))*440+10, ((BBOX['n']-lat)/(BBOX['n']-BBOX['s']))*420+10
def dp(points, tol):
    # Douglas-Peucker on projected points
    if len(points)<3: return points
    def perp(p,a,b):
        (x,y),(x1,y1),(x2,y2)=p,a,b
        dx,dy=x2-x1,y2-y1
        if dx==dy==0: return math.hypot(x-x1,y-y1)
        t=max(0,min(1,((x-x1)*dx+(y-y1)*dy)/(dx*dx+dy*dy)))
        return math.hypot(x-(x1+t*dx), y-(y1+t*dy))
    stack=[(0,len(points)-1)]; keep=[False]*len(points); keep[0]=keep[-1]=True
    while stack:
        i,j=stack.pop()
        if j<=i+1: continue
        idx,dm=-1,0
        for k in range(i+1,j):
            d=perp(points[k],points[i],points[j])
            if d>dm: idx,dm=k,d
        if dm>tol: keep[idx]=True; stack.append((i,idx)); stack.append((idx,j))
    return [p for p,k in zip(points,keep) if k]
def path(points, close=False, prec=1):
    f=lambda v: ('%.*f'%(prec,v)).rstrip('0').rstrip('.')
    s='M'+' L'.join(f'{f(x)} {f(y)}' for x,y in points)
    return s+('Z' if close else '')
def geom_pts(way):
    return [proj(g['lon'],g['lat']) for g in way.get('geometry',[]) if g]
