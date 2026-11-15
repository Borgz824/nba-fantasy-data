#!/usr/bin/env python3
"""Collect ESPN current NBA team rosters, including zero-game athletes."""
import argparse,json,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
BASE="https://site.api.espn.com/apis/site/v2/sports/basketball/nba/"
def fetch(path):
    with urlopen(Request(BASE+path,headers={"User-Agent":"nba-fantasy-data/1.0","Accept":"application/json"}),timeout=30) as r:return json.load(r)
def collect(get=fetch):
    teams=get("teams?limit=100")["sports"][0]["leagues"][0]["teams"]
    active=[t["team"] for t in teams if not t["team"].get("isAllStar") and t["team"].get("abbreviation")]
    if len(active)!=30:raise ValueError("Expected 30 NBA teams; received "+str(len(active)))
    roster=[];failures=[]
    for t in active:
        team=t["abbreviation"]
        try:
            athletes=get("teams/"+str(t["id"])+"/roster").get("athletes",[])
            if not athletes:raise ValueError("Empty roster")
            for a in athletes:
                aid=str(a.get("id") or "")
                if not aid:raise ValueError("Missing athlete ID")
                roster.append({"athlete_id":aid,"name":a.get("displayName") or a.get("fullName"),
                               "team":team,"position":(a.get("position") or {}).get("abbreviation"),
                               "roster_status":(a.get("status") or {}).get("name"),
                               "name_variants":list(dict.fromkeys(filter(None,[a.get("displayName"),a.get("fullName"),a.get("shortName")])) )})
        except Exception as e:failures.append({"team":team,"error":str(e)})
        time.sleep(0.2)
    ids=[x["athlete_id"] for x in roster]
    return {"source":"ESPN unofficial NBA current rosters","retrieved_at_utc":datetime.now(timezone.utc).isoformat(),
            "team_count":len(active),"athlete_count":len(roster),"failures":failures,
            "coverage_verified":not failures and len(ids)==len(set(ids)) and len(roster)>350,
            "independently_verified":False,"players":roster}
def main():
    p=argparse.ArgumentParser();p.add_argument("--out",required=True);a=p.parse_args()
    result=collect();Path(a.out).write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!="players"}))
    if not result["coverage_verified"]:raise SystemExit("Incomplete ESPN roster coverage")
if __name__=="__main__":main()
