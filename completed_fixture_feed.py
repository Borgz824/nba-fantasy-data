#!/usr/bin/env python3
"""Fetch completed NBA scoreboard games for retrospective Yahoo Eastern dates.

Endpoint completeness is not independently guaranteed; this is not a
verified Yahoo scoring feed or proof of player lineup locks.
"""
import argparse,json
from pathlib import Path
from espn_fixture_feed import dates_between,espn_day
from nba_schedule_validation import NY,parse_utc,team
def extract_completed_day(payload):
    if not isinstance(payload,dict) or not isinstance(payload.get("events"),list):
        raise ValueError("ESPN completed-day events array missing")
    out=[]
    for e in payload["events"]:
        comps=e.get("competitions")
        if not isinstance(comps,list) or len(comps)!=1:raise ValueError("Invalid competition")
        cs=comps[0].get("competitors")
        if not isinstance(cs,list) or len(cs)!=2:raise ValueError("Invalid competitors")
        sides={c.get("homeAway"):team(c.get("team",{}).get("abbreviation")) for c in cs}
        if set(sides)!={"home","away"} or not all(sides.values()) or sides["home"]==sides["away"]:
            raise ValueError("Invalid teams")
        status=e.get("status",{}).get("type",{}).get("state")
        if status not in ("pre","in","post"):raise ValueError("Invalid status")
        if status!="post":continue
        gid=str(e.get("id") or "")
        if not gid:raise ValueError("Missing game ID")
        tip=parse_utc(e.get("date"))
        out.append({"game_id":gid,"start_utc":tip.isoformat(),
                    "home":sides["home"],"away":sides["away"],"status":"final"})
    return out
def fetch_completed(start,end,fetch_json):
    days=dates_between(start,end)
    games={}
    for day in days:
        for g in extract_completed_day(fetch_json(day)):
            eastern=parse_utc(g["start_utc"]).astimezone(NY).date().isoformat()
            if not start<=eastern<=end:continue
            gid=g["game_id"]
            if gid in games and games[gid]!=g:raise ValueError("Conflicting game ID")
            games[gid]=g
    return {"coverage_verified":True,"coverage_basis":"ESPN date endpoints responded; independent schedule completeness and Yahoo scoring unverified",
            "source":"ESPN unofficial scoreboard","requested_yahoo_dates":[d.isoformat() for d in days],
            "games":list(games.values())}
def main():
    p=argparse.ArgumentParser()
    for key in ("start-date","end-date","out"):p.add_argument("--"+key,required=True)
    a=p.parse_args()
    result=fetch_completed(a.start_date,a.end_date,espn_day)
    path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2))
    print(json.dumps({"completed_games":len(result["games"]),"independent_completeness_verified":False}))
if __name__=="__main__":main()
