#!/usr/bin/env python3
"""Resolve historical NBA club from ESPN game logs using Yahoo name and game date.

Yahoo IDs are never equated to ESPN athlete IDs. Name-only matches require
one ESPN athlete identity, and same-date multiple teams are rejected.
"""
import argparse,json
from collections import defaultdict
from datetime import date,datetime,timezone
from pathlib import Path
from bridge import normalize,TEAM_ALIASES,load_stats
def row_date(value):
    if not isinstance(value,str) or not value:raise ValueError("Missing ESPN game date")
    raw=value.replace("Z","+00:00")
    dt=datetime.fromisoformat(raw)
    if dt.tzinfo is None:raise ValueError("ESPN game date must include timezone")
    return dt.astimezone(timezone.utc).date()
def resolve_historical_teams(roster,stats,as_of_date):
    day=date.fromisoformat(as_of_date)
    if roster.get("snapshot",{}).get("type")!="date" or roster["snapshot"].get("date")!=as_of_date:
        raise ValueError("Dated Yahoo roster snapshot mismatch")
    index=defaultdict(list)
    for r in stats:
        if row_date(r.get("game_date_utc"))==day:
            index[normalize(r.get("player"))].append(r)
    out=[];unresolved=[]
    for p in roster.get("players",[]):
        pid=str(p.get("playerId") or "")
        if not pid:raise ValueError("Yahoo player ID missing")
        matches=index.get(normalize(p.get("name")),[])
        ids={str(r.get("athlete_id") or "") for r in matches}
        teams={str(r.get("team") or "").upper() for r in matches}
        if len(ids)==1 and "" not in ids and len(teams)==1 and "" not in teams:
            t=next(iter(teams))
            resolved=TEAM_ALIASES.get(t,t)
            out.append({**p,"team":resolved,"team_resolution":"espn_same_utc_date",
                        "espn_athlete_id":next(iter(ids))})
        else:
            reason="no same-date ESPN game log" if not matches else "ambiguous ESPN identity/team"
            unresolved.append({"playerId":pid,"name":p.get("name"),"reason":reason})
            out.append({**p,"team":None,"team_resolution":"unverified"})
    return {"snapshot":roster["snapshot"],"players":out,
            "resolved_count":len(out)-len(unresolved),"unresolved":unresolved,
            "all_teams_verified":bool(out) and not unresolved,
            "limitation":"No game log is not proof of no scheduled game; UTC dates can differ from Yahoo Eastern dates"}
def main():
    p=argparse.ArgumentParser()
    for k in ("roster","stats","date","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    raw=json.loads(Path(a.roster).read_text())
    result=resolve_historical_teams(raw.get("data",raw),load_stats(a.stats),a.date)
    Path(a.out).write_text(json.dumps(result,indent=2))
    print(json.dumps({"resolved":result["resolved_count"],"unresolved":len(result["unresolved"])}))
if __name__=="__main__":main()
