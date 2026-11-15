#!/usr/bin/env python3
"""Conservative, read-only ADD/DROP scenario evaluator.

Input: ESPN player game logs and a PRIVATE candidate JSON snapshot:
{"league_id":"478.l.31010","rostered":[{"name":"...","team":"LAL","playerId":"...","status":"","slot":"BN"}],
 "free_agents":[{"name":"...","team":"NY","playerId":"...","status":"","acquisitionState":"free_agent"}],
 "remaining_starts":{"Player Name":2,...},"starts_verified":true,
 "lineup_eligibility_verified":true,"moves_remaining":1}
No claims of winning probabilities. Historical rates are used only for scenarios.
"""
import argparse,json
from pathlib import Path
from bridge import build,load_stats,METRICS
from matchup_engine import NETMON,PWT,RATIOS,LOWER

def calc_delta(a,b,starts_a,starts_b):
    return {k:b[k+"_total"]/b["games"]*starts_b-a[k+"_total"]/a["games"]*starts_a for k in METRICS}

def category_delta(delta,baseline,cats):
    out={}
    for cat in cats:
        if cat in RATIOS:
            made,attempt=RATIOS[cat]
            old_den=baseline.get(attempt,0)
            new_den=old_den+delta[attempt]
            if old_den<=0 or new_den<=0:out[cat]=None;continue
            old=baseline.get(made,0)/old_den
            new=(baseline.get(made,0)+delta[made])/new_den
            out[cat]=round(new-old,6)
        else:out[cat]=round((-1 if cat in LOWER else 1)*delta[cat],4)
    return out

def optimize(stats,snapshot,min_games=5):
    lid=snapshot["league_id"]
    if lid not in ("478.l.31010","478.l.33011"):raise ValueError("Unknown league")
    cats=NETMON if lid.endswith("31010") else PWT
    roster=snapshot.get("rostered",[])
    agents=snapshot.get("free_agents",[])
    if not roster or not agents:raise ValueError("Roster and free agents required")
    people=roster+agents
    joined,issues=build(stats,[{"league_id":lid,"players":people}])
    indexed={str(x["yahoo_player_id"]):x for x in joined[lid] if x["yahoo_player_id"] is not None}
    validation=[]
    for p in people:
        pid=str(p.get("playerId",""))
        j=indexed.get(pid)
        if not pid or not j or j["match_status"]!="matched" or j["games"]<min_games:
            validation.append({"player":p.get("name"),"reason":"identity or sample not validated"})
    if len(indexed)!=len(people):validation.append({"reason":"duplicate/missing Yahoo player identifiers"})
    starts=snapshot.get("remaining_starts",{})
    for p in people:
        count=starts.get(p.get("name"))
        if not isinstance(count,int) or isinstance(count,bool) or count<0:
            validation.append({"player":p.get("name"),"reason":"remaining eligible starts not verified"})
    # Cross-check independently audited Yahoo lineup and fixture evidence.
    # Flags alone must never authorize scenario generation.
    audit=snapshot.get("lineup_validation") or {}
    schedule=snapshot.get("schedule_validation") or {}
    if audit.get("league_id")!=lid or audit.get("current_assignment_validated") is not True or audit.get("future_starts_verified") is not True:
        validation.append({"reason":"independent Yahoo lineup audit or future locks unverified"})
    if schedule.get("league_id")!=lid or schedule.get("future_starts_verified") is not True:
        validation.append({"reason":"independent future-start schedule audit missing"})
    audited={str(p.get("playerId")):p for p in audit.get("players",[])}
    scheduled={str(p.get("playerId")):p for p in schedule.get("players",[])}
    for p in people:
        pid=str(p.get("playerId"))
        count=starts.get(p.get("name"))
        a=audited.get(pid)
        g=scheduled.get(pid)
        if not a or not g:
            validation.append({"player":p.get("name"),"reason":"Yahoo player ID absent from independent lineup/schedule audit"})
            continue
        verified=g.get("verified_eligible_starts")
        scheduled_count=g.get("scheduled_games")
        if type(verified) is not int or type(scheduled_count) is not int or verified<0 or verified>scheduled_count or type(count) is not int or verified!=count:
            validation.append({"player":p.get("name"),"reason":"eligible starts inconsistent with independently audited fixture bounds"})
        if a.get("future_lineup_verified") is not True or a.get("future_eligible_starts")!=count:
            validation.append({"player":p.get("name"),"reason":"future Yahoo lineup evidence does not corroborate starts"})
    if not snapshot.get("starts_verified"):validation.append({"reason":"remaining starts unverified"})
    if not snapshot.get("lineup_eligibility_verified"):validation.append({"reason":"lineup eligibility unverified"})
    if not isinstance(snapshot.get("moves_remaining"),int) or snapshot["moves_remaining"]<1:
        validation.append({"reason":"no verified remaining acquisition moves"})
    for p in people:
        if p.get("status"):validation.append({"player":p.get("name"),"reason":"injury/status requires review"})
    for p in agents:
        if p.get("acquisitionState")!="free_agent":
            validation.append({"player":p.get("name"),"reason":"not confirmed immediate free agent"})
    base=snapshot.get("current_team_totals",{})
    if not isinstance(base,dict) or any(k not in base or not isinstance(base[k],(float,int)) or base[k]<0 for k in METRICS):
        validation.append({"reason":"complete nonnegative team shooting/count totals required"})
    if validation or issues:
        return {"league_id":lid,"ready":False,"blockers":validation+issues,"comparisons":[],"recommendation":"HOLD — insufficient verified inputs"}
    comparisons=[]
    for a in roster:
        for b in agents:
            if a["playerId"]==b["playerId"]:continue
            pa=indexed[str(a["playerId"])];pb=indexed[str(b["playerId"])]
            delta=calc_delta(pa,pb,starts[a["name"]],starts[b["name"]])
            changes=category_delta(delta,base,cats)
            comparisons.append({"drop":a["name"],"add":b["name"],"category_improvements":{k:v for k,v in changes.items() if v is not None and v>0},"category_regressions":{k:v for k,v in changes.items() if v is not None and v<0},"all_deltas":changes,"scenario_only":True})
    return {"league_id":lid,"ready":True,"comparisons":comparisons,"recommendation":"SCENARIOS ONLY — matchup margins, replacement eligibility, transaction rules and opponent starts still require assessment","warning":"Not win probabilities; projections use historical per-game rates"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--stats",required=True);ap.add_argument("--snapshot",required=True);ap.add_argument("--out",required=True)
    a=ap.parse_args()
    result=optimize(load_stats(a.stats),json.loads(Path(a.snapshot).read_text(encoding="utf-8")))
    Path(a.out).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"ready":result["ready"],"comparisons":len(result["comparisons"]),"blockers":result.get("blockers",[])},indent=2))
    if not result["ready"]:raise SystemExit("ADD/DROP evaluation blocked by missing verification")

if __name__=="__main__":main()
