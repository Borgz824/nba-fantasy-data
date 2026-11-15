#!/usr/bin/env python3
"""Exact max-value daily starting lineup assignment using Yahoo eligiblePositions.

This computes a statistical lineup only. The caller must separately confirm
date-specific games, injury availability and lineup locks. Never executes moves.
"""
from functools import lru_cache

DEFAULT_SLOTS={
    "478.l.31010":("PG","SG","G","SF","PF","F","C","Util","Util"),
    "478.l.33011":("PG","SG","G","SF","PF","F","C","Util","Util","Util"),
}
BENCH={"BN","IL","IL+","IR","IR+","NA"}
def can_start(player,slot):
    eligible=set(player.get("eligiblePositions") or [])
    if not eligible:return False
    if slot in eligible:return True
    # Yahoo may explicitly provide flexible eligibility. Do not invent it.
    return False

def optimal_lineup(players,scores,slots,active_player_ids=None):
    """Exact max-weight bipartite assignment, allowing empty slots.

    scores maps Yahoo playerId -> expected category-adjusted value for target day.
    active_player_ids may restrict to independently verified scheduled/available players.
    When omitted, output is historical-value lineup, NOT a game-day recommendation.
    """
    if len(players)>22:raise ValueError("Too many players for exact assignment")
    pool=[]
    for p in players:
        pid=str(p.get("playerId",p.get("id","")))
        if pid not in scores or (active_player_ids is not None and pid not in active_player_ids):
            continue
        if p.get("selectedPosition") in {"IL","IL+","IR","IR+"}:continue
        pool.append((pid,p))
    slots=tuple(slots)
    @lru_cache(None)
    def solve(i,used):
        if i==len(slots):return (0.0,())
        best_score,tail=solve(i+1,used)
        best=(best_score,(None,)+tail)
        for j,(pid,p) in enumerate(pool):
            if used>>j&1 or not can_start(p,slots[i]):continue
            next_score,next_assignment=solve(i+1,used|(1<<j))
            total=float(scores[pid])+next_score
            if total>best[0]:best=(total,(pid,)+next_assignment)
        return best
    score,assignment=solve(0,0)
    names={pid:p.get("name") for pid,p in pool}
    return {"score":round(score,4),
      "lineup":[{"slot":slot,"playerId":pid,"name":names.get(pid) if pid else None}
                for slot,pid in zip(slots,assignment)],
      "unselected":[{"playerId":pid,"name":p.get("name")} for pid,p in pool if pid not in assignment],
      "date_specific_verified":active_player_ids is not None,
      "warning":"Yahoo lineup lock and player health require independent verification"}
