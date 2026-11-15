#!/usr/bin/env python3
"""Convert a manually supplied Flaim matchup response to auditable current totals.

No schedule, future starts, or roster membership is inferred.
Input is a JSON export of the get_matchups data object; do not commit private exports.
"""
import argparse,json
from pathlib import Path

METRIC_IDS={"9004003":("fgm","fga"),"9007006":("ftm","fta"),"6":("fta",),"7":("ftm",),"9":("3pa",),"10":("3pm",),"12":("pts",),"13":("oreb",),"14":("dreb",),"15":("reb",),"16":("ast",),"17":("stl",),"18":("blk",),"19":("to",)}
CATS={"478.l.31010":("fgm","fga","ftm","fta","3pm","pts","reb","ast","stl","blk","to"),"478.l.33011":("fgm","fga","ftm","fta","3pm","3pa","pts","oreb","dreb","reb","ast","stl","blk","to")}

def totals(side,league_id):
    values={};errors=[]
    for item in side.get("categories",[]):
        stat=str(item.get("statId",""))
        if stat not in METRIC_IDS:continue
        keys=METRIC_IDS[stat]
        try:
            raw=str(item["value"])
            chunks=raw.split("/")
            if len(chunks)!=len(keys):raise ValueError("wrong component count")
            for k,v in zip(keys,chunks):
                number=float(v)
                if number<0:raise ValueError("negative total")
                values[k]=number
        except (KeyError,TypeError,ValueError):
            errors.append({"statId":stat,"reason":"missing or invalid Yahoo value"})
    missing=sorted(set(CATS[league_id])-set(values))
    return values,errors,missing

def adapt(payload,league_id,team_id):
    if league_id not in CATS:raise ValueError("Unsupported league")
    if payload.get("leagueKey")!=league_id:raise ValueError("League key mismatch")
    matches=[m for m in payload.get("matchups",[]) if team_id in (str(m.get("home",{}).get("teamId")),str(m.get("away",{}).get("teamId")))]
    if len(matches)!=1:raise ValueError("Expected exactly one matchup for team")
    match=matches[0]
    ours=match["home"] if str(match["home"]["teamId"])==team_id else match["away"]
    opponent=match["away"] if ours is match["home"] else match["home"]
    our_totals,our_errors,our_missing=totals(ours,league_id)
    opp_totals,opp_errors,opp_missing=totals(opponent,league_id)
    return {"league_id":league_id,"week":match.get("week"),"status":match.get("status"),"ours":{"team_id":team_id,"team_name":ours.get("teamName"),"current_totals":our_totals,"player_ids":[],"remaining_games":{}},"opponent":{"team_id":str(opponent["teamId"]),"team_name":opponent.get("teamName"),"current_totals":opp_totals,"player_ids":[],"remaining_games":{}},"validation":{"current_totals_complete":not(our_errors or opp_errors or our_missing or opp_missing),"ours_missing":our_missing,"opponent_missing":opp_missing,"ours_errors":our_errors,"opponent_errors":opp_errors,"future_starts_verified":False,"note":"player_ids and remaining_games intentionally empty; fill only from verified lineup and schedule"}}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--flaim",required=True);ap.add_argument("--league-id",required=True);ap.add_argument("--team-id",required=True);ap.add_argument("--out",required=True)
    a=ap.parse_args()
    payload=json.loads(Path(a.flaim).read_text(encoding="utf-8"))
    result=adapt(payload.get("data",payload),a.league_id,a.team_id)
    Path(a.out).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result["validation"],indent=2))
    if not result["validation"]["current_totals_complete"]:raise SystemExit("Missing current Yahoo totals")

if __name__=="__main__":main()
