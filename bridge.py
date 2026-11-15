#!/usr/bin/env python3
"""Read-only bridge: join ESPN game logs to Flaim Yahoo roster JSON snapshots.
Usage: python bridge.py --stats output/player_game_logs.csv --rosters rosters.json --out analysis
Roster JSON schema: {"leagues":[{"league_id":"478.l.31010","team_id":"12","players":[{"name":"...","team":"...","playerId":"...","selectedPosition":"..."}]}]}
Never assumes ESPN athlete_id == Yahoo playerId. Ambiguous/unmatched players are excluded and reported.
"""
import argparse, csv, json, re, unicodedata
from collections import defaultdict
from pathlib import Path

METRICS=("fgm","fga","ftm","fta","3pm","3pa","oreb","dreb","reb","ast","stl","blk","to","pts")
ALIASES={"nikola jokic":"nikola jokic","og anunoby":"og anunoby"}
def normalize(s):
    s=unicodedata.normalize("NFKD",str(s or "")).encode("ascii","ignore").decode().lower()
    s=re.sub(r"[^a-z0-9 ]+"," ",s)
    return re.sub(r"\\s+"," ",s).strip()

def load_stats(path):
    with open(path,newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    required={"athlete_id","player","team","game_id","game_date_utc",*METRICS}
    if not rows or not required.issubset(rows[0]): raise ValueError("ESPN CSV missing required columns")
    return rows

def build(stats, leagues):
    index=defaultdict(list)
    for r in stats: index[(normalize(r["player"]),r["team"].upper())].append(r)
    results={}; problems=[]
    for league in leagues:
        lid=league["league_id"]
        if lid not in ("478.l.31010","478.l.33011"): raise ValueError("Unexpected league "+lid)
        joined=[]
        for p in league["players"]:
            key=(normalize(p.get("name")),str(p.get("team") or "").upper())
            games=index.get(key,[])
            ids={r["athlete_id"] for r in games}
            status="matched" if games and len(ids)==1 else ("ambiguous" if len(ids)>1 else "unmatched")
            if status!="matched": problems.append({"league_id":lid,"name":p.get("name"),"team":p.get("team"),"reason":status})
            sums={k:sum(float(r[k]) for r in games if r[k] not in ("",None)) for k in METRICS} if status=="matched" else {}
            n=len(games) if status=="matched" else 0
            out={"league_id":lid,"yahoo_player_id":p.get("playerId"),"player":p.get("name"),
                 "team":p.get("team"),"slot":p.get("selectedPosition"),"match_status":status,
                 "espn_athlete_id":next(iter(ids)) if status=="matched" else "",
                 "games":n}
            for k in METRICS:out[k+"_total"]=sums.get(k,"")
            for k in ("pts","reb","ast","stl","blk","to","3pm","oreb","dreb"):
                out[k+"_per_game"]=round(sums[k]/n,3) if n else ""
            out["fg_pct"]=round(sums["fgm"]/sums["fga"],4) if n and sums["fga"] else ""
            out["ft_pct"]=round(sums["ftm"]/sums["fta"],4) if n and sums["fta"] else ""
            out["three_pct"]=round(sums["3pm"]/sums["3pa"],4) if n and sums["3pa"] else ""
            joined.append(out)
        results[lid]=joined
    return results,problems

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--stats",required=True);ap.add_argument("--rosters",required=True);ap.add_argument("--out",default="analysis")
    args=ap.parse_args()
    stats=load_stats(args.stats)
    data=json.loads(Path(args.rosters).read_text(encoding="utf-8"))
    leagues=data["leagues"]
    result,issues=build(stats,leagues)
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    for lid,rows in result.items():
        if rows:
            with (out/(lid.replace(".","_")+"_roster_stats.csv")).open("w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    report={"source_games":len(set(r["game_id"] for r in stats)),"source_rows":len(stats),
            "league_counts":{k:{"roster":len(v),"matched":sum(r["match_status"]=="matched" for r in v)} for k,v in result.items()},
            "issues":issues,"all_roster_players_matched":not issues,
            "limitations":["Name+team join is provisional; ESPN/Yahoo identity crosswalk is not verified",
                           "Current roster snapshot must be refreshed from Flaim separately",
                           "Historical statistics do not establish future schedule or injury availability",
                           "This does not write into Flaim or Yahoo"]}
    (out/"bridge_validation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))
    if issues:raise SystemExit("Unmatched/ambiguous players: inspect bridge_validation.json")
if __name__=="__main__":main()
