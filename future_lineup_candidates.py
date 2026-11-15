#!/usr/bin/env python3
"""Current Yahoo roster + upcoming NBA schedule: bounded candidates, never verified starts."""
from yahoo_lineup_validation import inspect_roster
from nba_schedule_validation import validate_games,team
def audit_future_candidates(league_id,roster,fixture_payload,start_date,end_date):
    lineup=inspect_roster(league_id,roster)
    games=validate_games(fixture_payload,start_date,end_date)
    players=[]
    for p in roster["players"]:
        pid=str(p["playerId"])
        nba=team(p.get("team") or p.get("proTeam"))
        matches=[g for g in games if nba and nba in (g["home"],g["away"])]
        players.append({"playerId":pid,"name":p.get("name"),"nba_team":nba or None,
            "assigned_slot":p.get("selectedPosition"),
            "eligible_positions":p.get("eligiblePositions") if isinstance(p.get("eligiblePositions"),list) else None,
            "editable_now":p.get("isEditable") if type(p.get("isEditable")) is bool else None,
            "is_undroppable":p.get("isUndroppable") if type(p.get("isUndroppable")) is bool else None,
            "scheduled_games":len(matches),"scheduled_yahoo_dates":[g["yahoo_date"] for g in matches],
            "verified_eligible_starts":None,"future_lineup_verified":False,
            "future_lock_time_verified":False})
    scheduled=[p for p in players if p["scheduled_games"]>0]
    active_scheduled=[p for p in scheduled if p["assigned_slot"] in {"PG","SG","G","SF","PF","F","C","Util"}]
    return {"league_id":league_id,"current_assignment_validated":lineup["current_assignment_validated"],
        "scheduled_rostered_player_count":len(scheduled),
        "scheduled_current_active_slot_count":len(active_scheduled),
        "scheduled_bench_or_il_count":len(scheduled)-len(active_scheduled),
        "nba_schedule_provider_response_validated":True,
        "nba_schedule_independent_completeness_verified":False,
        "future_starts_verified":False,"future_locks_verified":False,
        "players":players,"recommendation":"HOLD — current roster metadata and scheduled games are not future Yahoo starts"}
