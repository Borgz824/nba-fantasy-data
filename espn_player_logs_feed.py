#!/usr/bin/env python3
"""Fetch public ESPN NBA boxscore player logs; fail on missing final-game boxscores."""
import argparse,csv,json,time
from datetime import date,timedelta
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlencode
from espn_fixture_feed import espn_day,dates_between
from completed_fixture_feed import extract_completed_day
from nba_schedule_validation import team as normalize_team

FIELDS=["game_id","game_date_utc","athlete_id","player","team","position","opponent","minutes","fgm","fga","ftm","fta","3pm","3pa","oreb","dreb","reb","ast","stl","blk","to","pts","fg_pct","ft_pct","three_pct"]
BASE="https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?"
def pair(v):
    a,b=str(v).split("-");return float(a),float(b)
def fetch_summary(gid):
    req=Request(BASE+urlencode({"event":gid}),headers={"User-Agent":"nba-fantasy-data/1.0","Accept":"application/json"})
    with urlopen(req,timeout=25) as response:return json.load(response)
def parse_game(game,payload):
    teams=payload.get("boxscore",{}).get("players",[])
    if len(teams)!=2:raise ValueError("Missing two boxscore teams: "+game["game_id"])
    result=[]
    for entry in teams:
        team=normalize_team(entry.get("team",{}).get("abbreviation"))
        if team not in (normalize_team(game["home"]),normalize_team(game["away"])):raise ValueError("Boxscore team mismatch")
        opponent=normalize_team(game["away"]) if team==normalize_team(game["home"]) else normalize_team(game["home"])
        for group in entry.get("statistics",[]):
            labels=group.get("labels",[])
            for athlete in group.get("athletes",[]):
                if athlete.get("didNotPlay") or athlete.get("ejected") and not athlete.get("stats"):continue
                vals=athlete.get("stats",[])
                if not vals or len(vals)!=len(labels):continue
                d=dict(zip(labels,vals))
                if "MIN" not in d or str(d["MIN"]).strip() in ("--",""):continue
                if not all(k in d for k in ("FG","3PT","FT","REB","AST","STL","BLK","TO","PTS")):raise ValueError("Unexpected boxscore columns")
                fgm,fga=pair(d["FG"]);tpm,tpa=pair(d["3PT"]);ftm,fta=pair(d["FT"])
                aid=str(athlete.get("athlete",{}).get("id") or "")
                if not aid:raise ValueError("Missing athlete ID")
                def val(k):return float(d.get(k,0))
                row={"game_id":game["game_id"],"game_date_utc":game["start_utc"],"athlete_id":aid,
                     "player":athlete["athlete"]["displayName"],"team":team,"position":(athlete["athlete"].get("position") or {}).get("abbreviation",""),"opponent":opponent,
                     "minutes":float(d["MIN"].split(":")[0])+float(d["MIN"].split(":")[1])/60 if ":" in str(d["MIN"]) else float(d["MIN"]),
                     "fgm":fgm,"fga":fga,"ftm":ftm,"fta":fta,"3pm":tpm,"3pa":tpa,
                     "oreb":val("OREB"),"dreb":val("DREB"),"reb":val("REB"),
                     "ast":val("AST"),"stl":val("STL"),"blk":val("BLK"),"to":val("TO"),"pts":val("PTS"),
                     "fg_pct":fgm/fga if fga else 0,"ft_pct":ftm/fta if fta else 0,"three_pct":tpm/tpa if tpa else 0}
                result.append(row)
    if len(result)<10:raise ValueError("Too few players in completed boxscore: "+game["game_id"])
    return result
def collect(start,end,fetch_day=espn_day,fetch_box=fetch_summary):
    games={}
    for day in dates_between(start,end):
        for game in extract_completed_day(fetch_day(day)):
            games[game["game_id"]]=game
    rows=[];failures=[]
    for idx,game in enumerate(games.values()):
        try:rows.extend(parse_game(game,fetch_box(game["game_id"])))
        except Exception as exc:failures.append({"game_id":game["game_id"],"error":str(exc)})
        if idx and idx%20==0:time.sleep(0.5)
    return rows,{"source":"ESPN unofficial scoreboard/summary","requested_dates":[start,end],
                 "completed_games":len(games),"parsed_games":len(games)-len(failures),
                 "player_game_rows":len(rows),"failures":failures,
                 "coverage_verified":not failures and len(games)>0,
                 "provider_completeness_independently_verified":False}
def main():
    p=argparse.ArgumentParser()
    for k in ("start-date","end-date","out","report"):p.add_argument("--"+k,required=True)
    a=p.parse_args();rows,report=collect(a.start_date,a.end_date)
    for path in (a.out,a.report):Path(path).parent.mkdir(parents=True,exist_ok=True)
    with open(a.out,"w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(rows)
    Path(a.report).write_text(json.dumps(report,indent=2))
    print(json.dumps(report))
    if not report["coverage_verified"]:raise SystemExit("Incomplete NBA game-log coverage")
if __name__=="__main__":main()
