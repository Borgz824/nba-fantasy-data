#!/usr/bin/env python3
"""Public NBA player trends and team fixture counts. No private Flaim data.

Input: existing ESPN player_game_logs.csv and espn_fixture_feed JSON.
Unknown advanced usage/injuries are explicitly unverified, not invented.
"""
import argparse,csv,json
from collections import defaultdict
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
from zoneinfo import ZoneInfo

METRICS=("minutes","fgm","fga","ftm","fta","3pm","3pa","oreb","dreb","reb","ast","stl","blk","to","pts")
EASTERN=ZoneInfo("America/New_York")
def as_day(value):
    return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(EASTERN).date()

def calculate(rows,fixtures,as_of):
    if not rows:raise ValueError("No player game logs")
    required={"athlete_id","player","team","game_id","game_date_utc",*METRICS}
    if not required.issubset(rows[0]):raise ValueError("Missing required player-game columns")
    today=date.fromisoformat(as_of)
    grouped=defaultdict(list);seen=set()
    for row in rows:
        day=as_day(row["game_date_utc"])
        if day>today:continue
        key=(row["athlete_id"],row["game_id"])
        if key in seen:raise ValueError("Duplicate player-game record: "+str(key))
        seen.add(key)
        parsed=dict(row);parsed["_date"]=day
        for metric in METRICS:
            try:parsed[metric]=float(row[metric])
            except (TypeError,ValueError):raise ValueError("Missing/invalid "+metric+" for "+str(key))
        grouped[row["athlete_id"]].append(parsed)
    if not fixtures.get("coverage_verified") or not isinstance(fixtures.get("games"),list):
        raise ValueError("Fixture feed coverage not verified")
    games=fixtures["games"];team_days=defaultdict(list)
    for game in games:
        if game.get("status")!="scheduled":continue
        day=as_day(game["start_utc"])
        if day<today:continue
        for side in ("home","away"):
            team_days[game[side]].append({"game_id":game["game_id"],"yahoo_date":day.isoformat(),"philippines_date":datetime.fromisoformat(game["start_utc"].replace("Z","+00:00")).astimezone(ZoneInfo("Asia/Manila")).date().isoformat()})
    players=[]
    for athlete_id,logs in grouped.items():
        logs.sort(key=lambda r:r["_date"])
        latest=logs[-1]
        windows={}
        for label,cutoff in [("season",None),("last_7_days",7),("last_14_days",14),("last_30_days",30)]:
            sample=[r for r in logs if cutoff is None or r["_date"]>today-timedelta(days=cutoff)]
            totals={k:round(sum(r[k] for r in sample),3) for k in METRICS}
            n=len(sample)
            windows[label]={"games":n,"totals":totals,
                "per_game":{k:round(totals[k]/n,3) if n else None for k in METRICS},
                "fg_pct":round(totals["fgm"]/totals["fga"],4) if totals["fga"] else None,
                "ft_pct":round(totals["ftm"]/totals["fta"],4) if totals["fta"] else None,
                "three_pct":round(totals["3pm"]/totals["3pa"],4) if totals["3pa"] else None}
        players.append({"athlete_id":athlete_id,"name":latest["player"],"team":latest["team"],
                        "last_game_date":latest["_date"].isoformat(),"windows":windows,
                        "scheduled_games":team_days.get(latest["team"],[]),
                        "scheduled_game_count":len(team_days.get(latest["team"],[])),
                        "eligible_starts_verified":False,"injury_verified":False,
                        "usage_rate":None,"usage_rate_verified":False})
    return {"source":"ESPN player-game logs and ESPN unofficial scoreboard",
            "as_of_yahoo_eastern_date":as_of,"player_count":len(players),
            "source_player_games":len(seen),"fixture_games":len(games),
            "fixture_dates":fixtures.get("requested_yahoo_dates",[]),
            "coverage":{"historical_logs_independently_complete":False,
                        "fixture_provider_complete":False,"injury_verified":False,
                        "advanced_usage_available":False,
                        "player_eligible_starts_verified":False},
            "players":sorted(players,key=lambda p:p["name"])}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--logs",required=True);p.add_argument("--fixtures",required=True)
    p.add_argument("--as-of",required=True);p.add_argument("--out",required=True)
    a=p.parse_args()
    with open(a.logs,newline="",encoding="utf-8") as f:rows=list(csv.DictReader(f))
    result=calculate(rows,json.loads(Path(a.fixtures).read_text()),a.as_of)
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"players":result["player_count"],"player_games":result["source_player_games"],"fixtures":result["fixture_games"],"coverage":result["coverage"]}))
if __name__=="__main__":main()
