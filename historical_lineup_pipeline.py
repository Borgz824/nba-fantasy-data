#!/usr/bin/env python3
"""Private retrospective pipeline: Yahoo roster + validated fixtures + ESPN logs.

Never substitutes current NBA teams or infers future eligible starts.
"""
import argparse,json
from pathlib import Path
from nba_schedule_validation import validate_games
from historical_team_resolver import resolve_historical_teams
from yahoo_dated_lineup_audit import audit_dated_roster
from bridge import load_stats
def run(league_id,roster,stats,fixture_payload,yahoo_date):
    if fixture_payload.get("coverage_verified") is not True:
        raise ValueError("Verified fixture response required")
    fixtures=validate_games(fixture_payload,yahoo_date,yahoo_date)
    resolved=resolve_historical_teams(roster,stats,yahoo_date,fixtures)
    audit=audit_dated_roster(league_id,resolved,fixtures,yahoo_date,yahoo_date)
    return {"league_id":league_id,"yahoo_date":yahoo_date,
            "team_resolution":{"resolved_count":resolved["resolved_count"],
                               "unresolved":resolved["unresolved"],
                               "all_teams_verified":resolved["all_teams_verified"]},
            "lineup_audit":audit,"ready":audit["historical_snapshot_valid"],
            "future_starts_verified":False}
def main():
    p=argparse.ArgumentParser()
    for k in ("league-id","roster","stats","fixtures","date","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    raw=json.loads(Path(a.roster).read_text())
    result=run(a.league_id,raw.get("data",raw),load_stats(a.stats),
               json.loads(Path(a.fixtures).read_text()),a.date)
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2))
    print(json.dumps({"ready":result["ready"],"resolved":result["team_resolution"]["resolved_count"],
                      "future_starts_verified":False}))
if __name__=="__main__":main()
