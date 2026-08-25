# -*- coding: utf-8 -*-
import json, sys
from collections import Counter, defaultdict
sys.path.insert(0,'.')
import nodes, mapping, mary, elsie, maggies, lyns
from mapping import M, ISSUES, NR

def mary_paths():
    """Convert Mary's id->own_amount weeks into path->own_amount."""
    def path(i):
        parts=[]; cur=i
        while cur is not None:
            nm,par = nodes.NODES[cur]; parts.append(nm); cur=par
        return ">".join(reversed(parts))
    out=[]
    for w in mary.W:
        d={}
        for i,v in w.items():
            if v: d[path(i)] = d.get(path(i),0)+v
        out.append(d)
    return out

STORES=[
 ("Simply Elsie",7356,"UTC",elsie.W,elsie.DAILY_CREATED,elsie.DAILY_CLOSED,elsie.TOTALS),
 ("Maggie's Tanks",6576,"UTC",maggies.W,maggies.DAILY_CREATED,maggies.DAILY_CLOSED,maggies.TOTALS),
 ("Mary's Tanks",6377,"UTC+10",mary_paths(),mary.DAILY_CREATED,mary.DAILY_CLOSED,mary.TOTALS),
 ("Lyn's Tanks",6527,"UTC",lyns.W,lyns.DAILY_CREATED,lyns.DAILY_CLOSED,lyns.TOTALS),
]

unmapped=Counter()
def expand(week):
    """path->own_amount  =>  {issue:{reason:count}} applying the multi-issue mapping."""
    out=defaultdict(Counter)
    for p,v in week.items():
        if not v: continue
        pairs = M.get(p)
        if pairs is None:
            seg=p.split(">")
            # Commslayer nests reasons arbitrarily deep; resolve on top-level ancestor + leaf,
            # then on parent + leaf, then on the leaf alone.
            for cand in (seg[0]+">"+seg[-1] if len(seg)>2 else None,
                         ">".join(seg[-2:]) if len(seg)>2 else None,
                         seg[-1] if len(seg)>1 else None):
                if cand and cand in M: pairs=M[cand]; break
        if pairs is None:
            unmapped[p]+=v
            pairs=[("Other",NR)]
        for iss,rsn in pairs:
            out[iss][rsn]+=v
    return {k:dict(vv) for k,vv in out.items()}

DAYS=[]
import datetime as dt
d0=dt.date(2026,7,1)
for k in range(56): DAYS.append((d0+dt.timedelta(days=k)).isoformat())
WEEKS=[]
for s,e in zip(nodes.WEEKS,nodes.WEEK_END):
    a=dt.date.fromisoformat(s); b=dt.date.fromisoformat(e)
    WEEKS.append({"s":s,"e":e,"i0":(a-d0).days,"i1":(b-d0).days,
                  "label":f"{a.day}–{b.day} {b.strftime('%b')}" if a.month==b.month
                          else f"{a.day} {a.strftime('%b')}–{b.day} {b.strftime('%b')}"})

out={"generated":"2026-08-25","from":"2026-07-01","to":"2026-08-25",
     "days":DAYS,"weeks":WEEKS,"issues":ISSUES,"stores":[]}
for name,sid,tz,W,dc,dl,tot in STORES:
    assert len(dc)==56 and len(dl)==56, name
    wk=[expand(w) for w in W]
    dayDelta = tot["created"] - sum(dc)
    if dayDelta: print(f"NOTE {name}: daily series {sum(dc):,} vs period total {tot['created']:,} (delta {dayDelta}, {dayDelta/tot['created']*100:.2f}% - tz boundary)")
    out["stores"].append({"name":name,"id":sid,"tz":tz,"created":dc,"closed":dl,
                          "totCreated":tot["created"],"totClosed":tot["closed"],
                          "dayDelta":dayDelta,"wk":wk})

# reasons per issue, ordered by total volume
agg=defaultdict(Counter)
for st in out["stores"]:
    for w in st["wk"]:
        for iss,rs in w.items():
            for r,v in rs.items(): agg[iss][r]+=v
out["reasons"]={i:[r for r,_ in agg[i].most_common()] for i in ISSUES if i in agg}

json.dump(out,open("dashboard_data.json","w"),separators=(",",":"))

print("UNMAPPED paths:",len(unmapped),"tickets:",sum(unmapped.values()))
for p,v in unmapped.most_common(15): print("   ",p,v)
tickets=sum(st["totCreated"] for st in out["stores"])
issues=sum(v for i in agg for v in agg[i].values())
classified=sum(sum(w.values()) for st in out["stores"] for wk in st["wk"] for w in [Counter()] ) # placeholder
print("\nTOTAL tickets:",tickets)
print("TOTAL issues :",issues)
print("issues/ticket:",round(issues/tickets,3))
print("\nIssue totals (all stores, full period):")
for i in ISSUES:
    if i in agg: print(f"   {i:<22}{sum(agg[i].values()):>7,}   reasons={len(agg[i])}")
print("\nfile bytes:",len(open("dashboard_data.json").read()))
