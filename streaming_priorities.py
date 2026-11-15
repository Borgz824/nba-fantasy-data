#!/usr/bin/env python3
"""Read-only category gap and streaming priority analysis from validated Yahoo snapshots.

This is NOT a future-games projection. No player moves are recommended from gaps alone.
"""
import argparse,json
from pathlib import Path
from flaim_matchup_adapter import adapt
from matchup_engine import score,NETMON,PWT

def assess(matchup_payload,league_id,team_id):
    snapshot=adapt(matchup_payload.get("data",matchup_payload),league_id,team_id)
    if not snapshot["validation"]["current_totals_complete"]:
        raise ValueError("Yahoo category totals incomplete")
    cats=NETMON if league_id.endswith("31010") else PWT
    gaps=score(snapshot["ours"]["current_totals"],snapshot["opponent"]["current_totals"],cats)
    behind=[g for g in gaps if g["leader"]=="opponent"]
    ahead=[g for g in gaps if g["leader"]=="ours"]
    unknown=[g for g in gaps if g["leader"] in ("unknown","tie")]
    return {"league_id":league_id,"week":snapshot["week"],"opponent":snapshot["opponent"]["team_name"],"ahead":ahead,"behind":behind,"unknown_or_tied":unknown,"verified_source":"Flaim Yahoo current matchup totals","recommendation":"HOLD pending remaining-games, injuries, lineup eligibility and free-agent ESPN comparison","projection_ready":False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--flaim",required=True);ap.add_argument("--league-id",required=True)
    ap.add_argument("--team-id",required=True);ap.add_argument("--out",required=True)
    a=ap.parse_args()
    result=assess(json.loads(Path(a.flaim).read_text()),a.league_id,a.team_id)
    Path(a.out).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"ahead":len(result["ahead"]),"behind":len(result["behind"]),"unknown":len(result["unknown_or_tied"])},indent=2))

if __name__=="__main__":main()
