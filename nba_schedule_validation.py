#!/usr/bin/env python3
"""Validate NBA fixtures; distinguish Yahoo (US Eastern) and Philippine dates.

Fixtures: {"coverage_verified":true,"games":[{"game_id":"1",
"start_utc":"2026-11-16T00:30:00Z","home":"NYK","away":"DEN","status":"scheduled"}]}
The caller MUST independently verify complete fixture coverage.
"""
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
NY=ZoneInfo("America/New_York")
PH=ZoneInfo("Asia/Manila")
SUPPORTED={"scheduled","pre","pre_game","not_started"}
ALIASES={"NO":"NOP","NY":"NYK","SA":"SAS","WSH":"WAS","GS":"GSW","UTAH":"UTA"}
ACTIVE={"PG","SG","G","SF","PF","F","C","UTIL"}
def parse_utc(value):
    if not isinstance(value,str):raise ValueError("Missing UTC start")
    dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    if dt.tzinfo is None or dt.utcoffset() is None:raise ValueError("Game start requires timezone")
    return dt.astimezone(timezone.utc)
def team(value):
    value=str(value or "").strip().upper()
    return ALIASES.get(value,value)
def validate_games(payload,start_date,end_date):
    if payload.get("coverage_verified") is not True or not isinstance(payload.get("games"),list):
        raise ValueError("Verified complete fixtures list required")
    start=datetime.fromisoformat(start_date).date()
    end=datetime.fromisoformat(end_date).date()
    if end<start:raise ValueError("Invalid date window")
    seen=set();result=[]
    for g in payload["games"]:
        gid=str(g.get("game_id") or "")
        if not gid or gid in seen:raise ValueError("Missing/duplicate game ID")
        seen.add(gid)
        tip=parse_utc(g.get("start_utc"))
        yahoo=tip.astimezone(NY).date()
        if not start<=yahoo<=end:continue
        home,away=team(g.get("home")),team(g.get("away"))
        if not home or not away or home==away:raise ValueError("Invalid fixture teams")
        if str(g.get("status") or "").lower() not in SUPPORTED:
            raise ValueError("Unverified upcoming fixture "+gid)
        result.append({"game_id":gid,"home":home,"away":away,"start_utc":tip.isoformat(),
                       "yahoo_date":yahoo.isoformat(),
                       "philippines_date":tip.astimezone(PH).date().isoformat()})
    return result
def audit_players(players,fixtures,lineup_date_verified=False):
    output=[]
    for p in players:
        games=[g for g in fixtures if team(p.get("team")) in (g["home"],g["away"])]
        slot=str(p.get("selectedPosition") or "").upper()
        blockers=[]
        if not lineup_date_verified:blockers.append("Yahoo lineup date not independently confirmed")
        if slot not in ACTIVE:blockers.append("Not currently in an active lineup slot")
        if p.get("status"):blockers.append("Injury designation requires review")
        blockers.append("Future roster-slot availability and locks not verified")
        output.append({"name":p.get("name"),"team":team(p.get("team")),"slot":slot,
                       "status":p.get("status"),"scheduled_games":len(games),
                       "yahoo_dates":[g["yahoo_date"] for g in games],
                       "philippines_dates":[g["philippines_date"] for g in games],
                       "active_slot_now":slot in ACTIVE,"verified_eligible_starts":None,
                       "start_verification_blockers":blockers})
    return output
def run(fixtures,rosters,start_date,end_date):
    games=validate_games(fixtures,start_date,end_date)
    leagues=[{"league_id":l.get("league_id"),
              "players":audit_players(l.get("players",[]),games,l.get("yahoo_lineup_date_verified") is True),
              "future_starts_verified":False} for l in rosters.get("leagues",[])]
    return {"fixture_count":len(games),"fixtures":games,"leagues":leagues,
            "nba_schedule_verified":True,"future_starts_verified":False,
            "note":"Scheduled games are not verified eligible player starts"}
def main():
    p=argparse.ArgumentParser()
    for key in ("fixtures","rosters","start-date","end-date","out"):p.add_argument("--"+key,required=True)
    a=p.parse_args()
    result=run(json.loads(Path(a.fixtures).read_text()),json.loads(Path(a.rosters).read_text()),a.start_date,a.end_date)
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2))
    print(json.dumps({"fixtures":result["fixture_count"],"leagues":len(result["leagues"]),
                      "future_starts_verified":False}))
if __name__=="__main__":main()
