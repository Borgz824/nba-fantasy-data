#!/usr/bin/env python3
"""Audit Yahoo dated roster snapshots against NBA fixture dates.

Flaim as_of_date snapshots are historical; never interpret them as future
lineup reservations or verified locks. This module is retrospective only.
"""
from datetime import date
from collections import Counter
from yahoo_lineup_validation import SLOTS,ACTIVE
def audit_dated_roster(league_id, roster, fixtures, yahoo_date, as_of_date):
    if league_id not in SLOTS:raise ValueError("Unknown league")
    try:
        day=date.fromisoformat(yahoo_date)
        snapday=date.fromisoformat(as_of_date)
    except (TypeError,ValueError) as e:raise ValueError("ISO Yahoo dates required") from e
    if snapday!=day:raise ValueError("Snapshot date must match Yahoo fixture date")
    if roster.get("snapshot",{}).get("type")!="date":
        raise ValueError("Historical date snapshot required")
    players=roster.get("players")
    if not isinstance(players,list):raise ValueError("Yahoo players required")
    seen=set();counts=Counter();out=[];unknown_teams=[]
    for p in players:
        pid=str(p.get("playerId") or "")
        slot=p.get("selectedPosition")
        if not pid or pid in seen:raise ValueError("Missing/duplicate Yahoo player ID")
        if slot not in SLOTS[league_id]:raise ValueError("Unknown roster slot")
        seen.add(pid);counts[slot]+=1
        team=str(p.get("team") or "").upper()
        if not team:unknown_teams.append(pid)
        matches=[g for g in fixtures if team and g.get("yahoo_date")==yahoo_date and team in (g.get("home"),g.get("away"))]
        out.append({"playerId":pid,"name":p.get("name"),"assigned_slot":slot,
                    "professional_team_verified":bool(team),
                    "scheduled_games_on_date":len(matches) if team else None,
                    "assigned_active_slot":slot in ACTIVE,
                    "historical_active_game_assignment":(bool(matches) and slot in ACTIVE) if team else None,
                    "future_lineup_verified":False})
    overfilled={s:n for s,n in counts.items() if n>SLOTS[league_id][s]}
    return {"league_id":league_id,"yahoo_date":yahoo_date,
            "historical_snapshot_valid":not overfilled and bool(players) and not unknown_teams,
            "missing_professional_team_player_ids":unknown_teams,
            "overfilled_slots":overfilled,"players":out,
            "future_starts_verified":False,
            "note":"Historical slot and fixture intersection only; does not establish fantasy scoring, lock time, or future lineup eligibility"}
