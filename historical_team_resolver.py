#!/usr/bin/env python3
"""Resolve historical NBA teams from ESPN game IDs matched to Yahoo-date fixtures.

Never equate Yahoo IDs with ESPN IDs. Historical ESPN logs are evidence of
participation only, not proof that an absent player had no scheduled game.
"""
import argparse,json
from collections import defaultdict
from datetime import date
from pathlib import Path
from bridge import normalize,load_stats
from nba_schedule_validation import team
def resolve_historical_teams(roster,stats,as_of_date,fixtures=None):
    date.fromisoformat(as_of_date)
    if roster.get("snapshot",{}).get("type")!="date" or roster["snapshot"].get("date")!=as_of_date:
        raise ValueError("Dated Yahoo roster snapshot mismatch")
    if not isinstance(fixtures,list):raise ValueError("Verified game-ID fixtures required")
    game_ids=set()
    for g in fixtures:
        if g.get("yahoo_date")==as_of_date:
            gid=str(g.get("game_id") or "")
            if not gid or gid in game_ids:raise ValueError("Missing/duplicate fixture ID")
            game_ids.add(gid)
    index=defaultdict(list)
    for r in stats:
        if str(r.get("game_id") or "") in game_ids:
            index[normalize(r.get("player"))].append(r)
    out=[];unresolved=[];seen=set()
    for p in roster.get("players",[]):
        pid=str(p.get("playerId") or "")
        if not pid or pid in seen:raise ValueError("Missing/duplicate Yahoo player ID")
        seen.add(pid)
        matches=index.get(normalize(p.get("name")),[])
        ids={str(r.get("athlete_id") or "") for r in matches}
        teams={str(r.get("team") or "").upper() for r in matches}
        if len(ids)==1 and "" not in ids and len(teams)==1 and "" not in teams:
            t=next(iter(teams))
            out.append({**p,"team":team(t),
                        "team_resolution":"espn_fixture_game_id",
                        "espn_athlete_id":next(iter(ids))})
        else:
            reason="no ESPN log for Yahoo-date fixture" if not matches else "ambiguous ESPN identity/team"
            unresolved.append({"playerId":pid,"name":p.get("name"),"reason":reason})
            out.append({**p,"team":None,"team_resolution":"unverified"})
    return {"snapshot":roster["snapshot"],"players":out,
            "resolved_count":len(out)-len(unresolved),"unresolved":unresolved,
            "all_teams_verified":bool(out) and not unresolved,
            "limitation":"ESPN game-ID join is not Yahoo identity verification; absent logs do not imply no scheduled game"}
def main():
    p=argparse.ArgumentParser()
    for k in ("roster","stats","date","fixtures","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    raw=json.loads(Path(a.roster).read_text())
    fixture_data=json.loads(Path(a.fixtures).read_text())
    if fixture_data.get("coverage_verified") is not True:raise ValueError("Fixture coverage unverified")
    from nba_schedule_validation import validate_games
    fixtures=validate_games(fixture_data,a.date,a.date)
    result=resolve_historical_teams(raw.get("data",raw),load_stats(a.stats),a.date,fixtures)
    Path(a.out).write_text(json.dumps(result,indent=2))
    print(json.dumps({"resolved":result["resolved_count"],"unresolved":len(result["unresolved"])}))
if __name__=="__main__":main()
