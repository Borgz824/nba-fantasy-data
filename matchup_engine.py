#!/usr/bin/env python3
"""Phase 4.2: transparent matchup scenario calculations; never infer games remaining."""
import argparse,csv,json
from pathlib import Path
from bridge import build,load_stats,METRICS

NETMON=("fg_pct","ft_pct","3pm","pts","reb","ast","stl","blk","to")
PWT=("fg_pct","ftm","ft_pct","3pm","three_pct","pts","oreb","dreb","reb","ast","stl","blk","to")
RATIOS={"fg_pct":("fgm","fga"),"ft_pct":("ftm","fta"),"three_pct":("3pm","3pa")}
LOWER={"to"}

def score(a,b,categories):
    out=[]
    for cat in categories:
        if cat in RATIOS:
            made,attempt=RATIOS[cat]
            av=a.get(made,0)/a[attempt] if a.get(attempt,0) else None
            bv=b.get(made,0)/b[attempt] if b.get(attempt,0) else None
        else: av=a.get(cat);bv=b.get(cat)
        leader="unknown" if av is None or bv is None else ("tie" if abs(av-bv)<1e-10 else ("ours" if (av<bv if cat in LOWER else av>bv) else "opponent"))
        out.append({"category":cat,"ours":av,"opponent":bv,"leader":leader,"gap":None if av is None or bv is None else av-bv})
    return out

def forecast(base,players,remaining,min_games=5):
    result=dict(base)
    missing=[]
    for p in players:
        name=p["name"]
        count=remaining.get(name)
        if not isinstance(count,int) or isinstance(count,bool) or count<0:
            missing.append({"name":name,"reason":"missing valid confirmed remaining-game count"});continue
        if count==0:continue
        if p["match_status"]!="matched" or p["games"]<min_games:
            missing.append({"name":name,"reason":"unmatched or insufficient historical sample"});continue
        if p.get("status"):
            missing.append({"name":name,"reason":"injury designation requires availability review"});continue
        for metric in METRICS:result[metric]=result.get(metric,0)+p[metric+"_total"]/p["games"]*count
    return result,missing

def project(stats,league,snapshot,min_games=5):
    lid=league["league_id"]
    if lid not in ("478.l.31010","478.l.33011"):raise ValueError("Unsupported league")
    cats=NETMON if lid.endswith("31010") else PWT
    joined,issues=build(stats,[league])
    indexed={p["yahoo_player_id"]:p for p in joined[lid]}
    def side(side_name):
        s=snapshot[side_name]
        ids=s.get("player_ids",[])
        roster=[]
        for pid in ids:
            if pid not in indexed:raise ValueError("Unknown player id "+str(pid))
            player=dict(indexed[pid])
            player["name"]=player["player"]
            player["status"]=next((p.get("status","") for p in league["players"] if p.get("playerId")==pid),"")
            roster.append(player)
        return forecast(s["current_totals"],roster,s.get("remaining_games",{}),min_games)
    ours,ours_missing=side("ours");theirs,theirs_missing=side("opponent")
    return {"league_id":lid,"week":snapshot.get("week"),"scenario":"historical rates multiplied by explicitly supplied remaining games","categories":score(ours,theirs,cats),"blocked_players":{"ours":ours_missing,"opponent":theirs_missing},"identity_issues":issues,"complete":not(ours_missing or theirs_missing or issues),"warning":"Not a probability or guaranteed final score; requires verified Yahoo totals, eligible lineup starts, game counts and injury review"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--stats",required=True);ap.add_argument("--rosters",required=True)
    ap.add_argument("--matchups",required=True);ap.add_argument("--out",default="analysis")
    args=ap.parse_args()
    stats=load_stats(args.stats)
    leagues={l["league_id"]:l for l in json.loads(Path(args.rosters).read_text())["leagues"]}
    scenarios=json.loads(Path(args.matchups).read_text())["leagues"]
    dest=Path(args.out);dest.mkdir(parents=True,exist_ok=True)
    results=[]
    for scenario in scenarios:
        lid=scenario["league_id"]
        results.append(project(stats,leagues[lid],scenario))
    (dest/"matchup_scenarios.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
    print(json.dumps({"leagues":len(results),"complete":sum(x["complete"] for x in results)},indent=2))
    if not all(x["complete"] for x in results):raise SystemExit("Projection blocked: see matchup_scenarios.json")

if __name__=="__main__":main()
