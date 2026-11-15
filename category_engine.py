#!/usr/bin/env python3
"""Phase 4: conservative category-rate rankings. No schedule or win-probability claims."""
import argparse,csv,json,math
from pathlib import Path
from bridge import build,load_stats

COUNT_CATS=("3pm","pts","oreb","dreb","reb","ast","stl","blk","ftm")
ALL_CATS=COUNT_CATS+("to","fg_pct","ft_pct","three_pct")
TEAM_ALIASES={"NOP":"NO","NYK":"NY","SAS":"SA","WAS":"WSH","GSW":"GS","UTA":"UTAH"}

def evaluate(stats,leagues,min_games=5):
    joined,issues=build(stats,leagues)
    outputs={}
    for league in leagues:
        lid=league["league_id"]
        rows=[]
        for p in joined[lid]:
            games=p["games"]
            row={k:p[k] for k in ("league_id","yahoo_player_id","player","team","slot","match_status","games")}
            row["injury_status"]=next((q.get("status","") for q in league["players"] if q.get("playerId")==p["yahoo_player_id"]),"")
            row["sample_quality"]="sufficient" if games>=min_games else ("limited" if games else "unmatched")
            row["eligible_for_ranking"]=p["match_status"]=="matched" and games>=min_games and not row["injury_status"]
            for k in COUNT_CATS+("to",):
                val=p.get(k+"_total")
                row[k+"_pg"]=round(val/games,4) if games and isinstance(val,(float,int)) else ""
            for k in ("fg_pct","ft_pct","three_pct"):
                row[k]=p.get(k,"")
            rows.append(row)
        outputs[lid]=rows
    return outputs,issues

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--stats",required=True)
    parser.add_argument("--rosters",required=True)
    parser.add_argument("--out",default="analysis")
    parser.add_argument("--min-games",type=int,default=5)
    a=parser.parse_args()
    if a.min_games<1:parser.error("--min-games must be positive")
    stats=load_stats(a.stats)
    leagues=json.loads(Path(a.rosters).read_text(encoding="utf-8"))["leagues"]
    outputs,issues=evaluate(stats,leagues,a.min_games)
    dest=Path(a.out);dest.mkdir(parents=True,exist_ok=True)
    for lid,rows in outputs.items():
        if rows:
            with (dest/(lid.replace(".","_")+"_category_rates.csv")).open("w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    report={"input_game_rows":len(stats),"leagues":{lid:{"players":len(rows),"matched":sum(r["match_status"]=="matched" for r in rows),"ranking_eligible":sum(r["eligible_for_ranking"] for r in rows),"limited_or_unmatched":sum(r["sample_quality"]!="sufficient" for r in rows)} for lid,rows in outputs.items()},"issues":issues,"limitations":["Per-game historical rates only, not future-game projections","Injury status is a snapshot, not a medical forecast","No strength-of-schedule or remaining-games information","FG%, FT%, 3PT% are aggregate made/attempted ratios, not averages of percentages","Turnovers are lower-is-better; all other counting stats are higher-is-better","FTM and 3PT% matter only in leagues scoring those categories","No Yahoo moves or automated Flaim synchronization"]}
    (dest/"category_validation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))
    if issues:raise SystemExit("Identity matching incomplete: see category_validation.json")

if __name__=="__main__":main()
