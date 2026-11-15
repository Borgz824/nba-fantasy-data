#!/usr/bin/env python3
"""Retrieve NBA fixtures from ESPN scoreboard, fail closed on missing daily responses.

US Eastern dates are the Yahoo calendar-date basis. Private Yahoo data is not
sent to ESPN. ESPN is an unofficial source; coverage_verified means all
requested date endpoints responded with a structurally valid event list, NOT
that ESPN independently guarantees every NBA fixture is present.
"""
import argparse,json,time
from datetime import date,datetime,timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from nba_schedule_validation import parse_utc,validate_games
BASE="https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
def dates_between(start,end):
    a,b=date.fromisoformat(start),date.fromisoformat(end)
    if b<a or (b-a).days>31:raise ValueError("Invalid or excessively long date window")
    return [a+timedelta(days=i) for i in range((b-a).days+1)]
def extract_day(payload,requested):
    if not isinstance(payload,dict) or not isinstance(payload.get("events"),list):
        raise ValueError("ESPN day missing events array: "+requested.isoformat())
    out=[]
    for event in payload["events"]:
        comps=event.get("competitions")
        if not isinstance(comps,list) or len(comps)!=1:raise ValueError("Missing competition")
        competitors=comps[0].get("competitors")
        if not isinstance(competitors,list) or len(competitors)!=2:raise ValueError("Missing competitors")
        sides={c.get("homeAway"):c.get("team",{}).get("abbreviation") for c in competitors}
        if set(sides)!={"home","away"} or not all(sides.values()):raise ValueError("Missing teams")
        state=event.get("status",{}).get("type",{}).get("state")
        if state not in ("pre","in","post"):raise ValueError("Unknown game state")
        if state!="pre":continue
        start=event.get("date")
        parse_utc(start)
        out.append({"game_id":str(event["id"]),"start_utc":start,
                    "home":sides["home"],"away":sides["away"],"status":"scheduled"})
    return out
def fetch(start,end,fetch_json):
    days=dates_between(start,end)
    games={}
    for day in days:
        data=fetch_json(day)
        for g in extract_day(data,day):
            if g["game_id"] in games and games[g["game_id"]]!=g:
                raise ValueError("Conflicting ESPN fixture "+g["game_id"])
            games[g["game_id"]]=g
    raw={"coverage_verified":True,"games":list(games.values())}
    verified=validate_games(raw,start,end)
    # Date-scoped ESPN queries may include games falling on adjacent US dates;
    # require every returned fixture in target window to have been parsed.
    return {"coverage_verified":True,"source":"ESPN unofficial scoreboard",
            "requested_yahoo_dates":[d.isoformat() for d in days],
            "coverage_basis":"Every requested ESPN daily endpoint returned a valid events array; provider completeness not independently guaranteed",
            "games":[g for g in raw["games"] if g["game_id"] in {v["game_id"] for v in verified}]}
def espn_day(day):
    url=BASE+"?"+urlencode({"dates":day.strftime("%Y%m%d"),"limit":"1000"})
    req=Request(url,headers={"User-Agent":"nba-fantasy-data/1.0","Accept":"application/json"})
    with urlopen(req,timeout=20) as response:
        return json.load(response)
def main():
    p=argparse.ArgumentParser()
    for k in ("start-date","end-date","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    result=fetch(a.start_date,a.end_date,espn_day)
    path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"days":len(result["requested_yahoo_dates"]),"fixtures":len(result["games"]),"provider_completeness_guaranteed":False}))
if __name__=="__main__":main()
