#!/usr/bin/env python3
"""Validate Yahoo current roster position eligibility without guessing future starts.

A current roster is NOT a future-date lineup. 'isEditable' is informational,
not a provider-confirmed lock timestamp or a promise of move legality.
"""
import argparse,json
from pathlib import Path
from collections import Counter
SLOTS={
 "478.l.31010":{"PG":1,"SG":1,"G":1,"SF":1,"PF":1,"F":1,"C":1,"Util":2,"BN":3},
 "478.l.33011":{"PG":1,"SG":1,"G":1,"SF":1,"PF":1,"F":1,"C":1,"Util":3,"BN":2,"IL":2},
}
ACTIVE={"PG","SG","G","SF","PF","F","C","Util"}
def inspect_roster(league_id,roster):
    if league_id not in SLOTS:raise ValueError("Unexpected league")
    if not isinstance(roster,dict) or not isinstance(roster.get("players"),list):
        raise ValueError("Yahoo players list required")
    if roster.get("snapshot",{}).get("type")!="current":
        raise ValueError("Current Yahoo roster required for eligiblePositions")
    players=roster["players"]
    seen=set();counts=Counter();checks=[]
    for p in players:
        pid=str(p.get("playerId") or "")
        if not pid or pid in seen:raise ValueError("Missing/duplicate Yahoo player ID")
        seen.add(pid)
        slot=p.get("selectedPosition")
        if slot not in SLOTS[league_id]:raise ValueError("Unknown assigned Yahoo slot")
        counts[slot]+=1
        eligible=p.get("eligiblePositions")
        position_known=isinstance(eligible,list) and bool(eligible) and all(isinstance(v,str) for v in eligible)
        compatible=position_known and slot in eligible if slot in ACTIVE else None
        checks.append({"playerId":pid,"name":p.get("name"),"slot":slot,
                       "eligible_positions":eligible if position_known else None,
                       "assigned_slot_compatible":compatible,
                       "is_editable_now":p.get("isEditable") if isinstance(p.get("isEditable"),bool) else None,
                       "future_lineup_verified":False,"future_eligible_starts":None})
    capacity=SLOTS[league_id]
    overfilled={slot:n for slot,n in counts.items() if n>capacity[slot]}
    invalid=[p["name"] for p in checks if p["assigned_slot_compatible"] is False]
    unknown=[p["name"] for p in checks if p["assigned_slot_compatible"] is None and p["slot"] in ACTIVE]
    return {"league_id":league_id,"player_count":len(players),
            "current_assignment_validated":not overfilled and not invalid and not unknown and bool(players),
            "slot_counts":dict(counts),"overfilled_slots":overfilled,
            "incompatible_players":invalid,"unknown_eligibility":unknown,
            "players":checks,"future_starts_verified":False,
            "note":"Current assignment compatibility only; no future lock or daily-lineup verification"}
def main():
    ap=argparse.ArgumentParser()
    for name in ("league-id","roster","out"):ap.add_argument("--"+name,required=True)
    a=ap.parse_args()
    data=json.loads(Path(a.roster).read_text())
    report=inspect_roster(a.league_id,data.get("data",data))
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2))
    print(json.dumps({"current_assignment_validated":report["current_assignment_validated"],
                      "future_starts_verified":False,"players":report["player_count"]}))
if __name__=="__main__":main()
