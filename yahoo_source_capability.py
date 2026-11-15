#!/usr/bin/env python3
"""Conservative source-capability gate for Yahoo basketball GM decisions.

Yahoo category matchup totals do not establish per-player daily scoring,
future lineup locks, or legally available add/drop transactions.
"""
def assess_yahoo_sources(matchup,roster,dated=False):
    matchups=matchup.get("matchups") if isinstance(matchup,dict) else None
    players=roster.get("players") if isinstance(roster,dict) else None
    if not isinstance(matchups,list) or not isinstance(players,list):
        raise ValueError("Yahoo matchup and roster payloads required")
    has_categories=any(isinstance(side.get("categories"),list)
        for m in matchups for side in (m.get("home") or {},m.get("away") or {}))
    has_ids=bool(players) and all(bool(p.get("playerId")) for p in players)
    return {"matchup_category_totals_available":has_categories,
            "roster_player_ids_available":has_ids,
            "historical_roster_snapshot":dated,
            "player_daily_fantasy_scoring_verified":False,
            "future_lineup_lock_times_verified":False,
            "future_eligible_starts_verified":False,
            "add_drop_ready":False,
            "blockers":["No Yahoo player-level daily scoring through Flaim matchup summary",
                        "No verified future Yahoo lineup lock times",
                        "No independently verified future eligible starts"]}
