#!/usr/bin/env python3
"""Read-only, category-aware fantasy roster optimizer. No Yahoo transaction execution.

Input: ESPN per-game logs (bridge.load_stats schema), private Flaim snapshot:
{"leagues":[{"league_id":"478.l.31010","roster":{"players":[...]},
"free_agents":{"freeAgents":[...]}}]}
Returns evidence-based historical comparisons; does not assert future starts/locks.
"""
import argparse, json, math
from pathlib import Path
from bridge import load_stats, build, METRICS
from matchup_engine import NETMON, PWT, RATIOS, LOWER

LEAGUES={"478.l.31010":NETMON,"478.l.33011":PWT}
def _people(payload,key):
    v=payload.get(key,{})
    if isinstance(v,dict):return v.get("players" if key=="roster" else "freeAgents",[])
    return v if isinstance(v,list) else []

def _rate(p,k):
    return float(p[k+"_total"])/p["games"]

def evaluate(stats,snapshot,min_games=5,limit=30):
    outputs={}
    for league in snapshot.get("leagues",[]):
        lid=league.get("league_id")
        if lid not in LEAGUES or lid in outputs:raise ValueError("Unknown/duplicate league")
        roster=_people(league,"roster")
        agents=_people(league,"free_agents")
        people=roster+agents
        if not roster or not agents:
            outputs[lid]={"ready":False,"reason":"Missing roster or free agents","recommendations":[]}
            continue
        joined,issues=build(stats,[{"league_id":lid,"players":people}])
        indexed={str(p["yahoo_player_id"]):p for p in joined[lid] if p["yahoo_player_id"] is not None}
        valid={pid:p for pid,p in indexed.items() if p["match_status"]=="matched" and p["games"]>=min_games}
        cats=LEAGUES[lid]
        # Derive per-game league-specific values from *all matched* players in the sample.
        pool=list(valid.values())
        if len(pool)<3:
            outputs[lid]={"ready":False,"reason":"Insufficient matched player sample","issues":issues,"recommendations":[]}
            continue
        values={}
        for p in pool:
            v={}
            for cat in cats:
                if cat in RATIOS:
                    made,attempt=RATIOS[cat]
                    v[cat]=_rate(p,made) - (_rate(p,attempt)*(
                        sum(_rate(x,made) for x in pool)/max(sum(_rate(x,attempt) for x in pool),1e-9)))
                else:v[cat]=_rate(p,cat)*(-1 if cat in LOWER else 1)
            values[str(p["yahoo_player_id"])]=v
        means={c:sum(v[c] for v in values.values())/len(values) for c in cats}
        stds={c:max(math.sqrt(sum((v[c]-means[c])**2 for v in values.values())/len(values)),1e-9) for c in cats}
        scores={pid:{c:(v[c]-means[c])/stds[c] for c in cats} for pid,v in values.items()}
        total={pid:sum(v.values()) for pid,v in scores.items()}
        choices=[]
        for drop in roster:
            dp=str(drop.get("playerId"))
            if dp not in total:continue
            for add in agents:
                ap=str(add.get("playerId"))
                if ap not in total or ap==dp:continue
                changes={c:round(scores[ap][c]-scores[dp][c],3) for c in cats}
                gain=round(total[ap]-total[dp],3)
                choices.append({"add":add.get("name"),"drop":drop.get("name"),
                  "add_player_id":ap,"drop_player_id":dp,"score_delta":gain,
                  "category_z_deltas":changes,
                  "positive_categories":[c for c in cats if changes[c]>0],
                  "negative_categories":[c for c in cats if changes[c]<0],
                  "acquisition_state":add.get("acquisitionState","unknown"),
                  "short_term_schedule_unverified":True,"transaction_not_executed":True,
                  "sample_games":{"add":valid[ap]["games"],"drop":valid[dp]["games"]}})
        choices.sort(key=lambda x:x["score_delta"],reverse=True)
        outputs[lid]={"ready":True,"roster_count":len(roster),"free_agent_count":len(agents),
          "matched_players":len(valid),"unmatched":issues,
          "eligible_comparisons":len(choices),
          "recommendations":choices[:limit],
          "roster_rankings":sorted([{"name":p.get("name"),"score":round(total[str(p.get("playerId"))],3)}
                for p in roster if str(p.get("playerId")) in total],key=lambda x:x["score"],reverse=True),
          "caveats":["Historical category-z comparison, not matchup win probability",
            "Percentage categories use make/attempt volume-adjusted contribution",
            "Unmatched or under-five-game players excluded, not presumed weak",
            "Yahoo eligibility, future games, injury, lineup locks and weekly move limits not verified",
            "Positive score does not automatically justify sacrificing long-term roster value"]}
    if set(outputs)!=set(LEAGUES):raise ValueError("Both leagues required")
    return {"leagues":outputs,"recommendation_status":"statistical candidates only"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--stats",required=True);p.add_argument("--snapshot",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    report=evaluate(load_stats(a.stats),json.loads(Path(a.snapshot).read_text()))
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2))
    print(json.dumps({k:{"ready":v["ready"],"comparisons":v.get("eligible_comparisons",0)}
       for k,v in report["leagues"].items()},indent=2))
if __name__=="__main__":main()
