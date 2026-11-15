#!/usr/bin/env python3
"""Fail-closed readiness audit for two Yahoo fantasy leagues.

Consumes PRIVATE local Flaim exports and GitHub ESPN outputs. Never commits roster data.
Usage: python gm_readiness.py --stats output/player_game_logs.csv --input private_snapshot.json --out analysis/readiness.json

Snapshot format: {"leagues":[{"league_id":"478.l.31010","team_id":"12",
 "matchups":{...Flaim get_matchups data...},"roster":{...get_roster data...},
 "free_agents":{...get_free_agents data...},"transactions":{...get_transactions data...},
 "verified_starts":{"Player Name":1},"lineup_eligibility_verified":false,
 "moves_remaining":null}]}
"""
import argparse, csv, json
from pathlib import Path
from bridge import build, load_stats
from flaim_matchup_adapter import adapt

LEAGUES={"478.l.31010":"12","478.l.33011":"4"}
def inspect(stats, snapshot):
    results={}
    seen=set()
    schedule_payload=snapshot.get("schedule_validation") or {}
    schedule_by_league={x["league_id"]:x for x in schedule_payload.get("leagues",[])}
    lineup_by_league=snapshot.get("lineup_validation",{})
    for league in snapshot.get("leagues",[]):
        lid=league.get("league_id")
        if lid not in LEAGUES or lid in seen or str(league.get("team_id"))!=LEAGUES.get(lid):
            raise ValueError("Unexpected/duplicate league or team identity")
        seen.add(lid)
        checks={}
        def mark(name, ok, reason=""):
            checks[name]={"passed":bool(ok),"reason":"" if ok else reason}
        matchup=adapt(league["matchups"].get("data",league["matchups"]),lid,LEAGUES[lid])
        mark("matchup_totals",matchup["validation"]["current_totals_complete"],"Missing/invalid Yahoo shooting or category totals")
        roster=league.get("roster",{}).get("players",[])
        agents=league.get("free_agents",{}).get("freeAgents",[])
        mark("roster_present",bool(roster),"Missing Yahoo roster")
        mark("free_agents_present",bool(agents),"Missing Yahoo free-agent inventory")
        players=[{"name":p.get("name"),"team":p.get("team"),"playerId":p.get("playerId"),
                  "selectedPosition":p.get("selectedPosition")} for p in roster]
        joined,issues=build(stats,[{"league_id":lid,"players":players}]) if players else ({lid:[]},[])
        mark("roster_identity",bool(players) and not issues,"Unmatched/ambiguous Yahoo-to-ESPN players")
        mark("historical_sample",bool(players) and all(p["games"]>=5 for p in joined[lid]),"Some rostered players have fewer than five game logs")
        mark("injury_review",bool(players) and not any(p.get("status") for p in roster),"Roster has injury designations needing review")
        starts=league.get("verified_starts",{})
        schedule=schedule_by_league.get(lid,{})
        schedule_players={p.get("name"):p for p in schedule.get("players",[])}
        starts_valid=bool(players) and all(type(starts.get(p["name"])) is int and starts[p["name"]]>=0 for p in roster)
        eligible_valid=schedule.get("future_starts_verified") is True and all(type(schedule_players.get(p["name"],{}).get("verified_eligible_starts")) is int for p in roster)
        mark("remaining_starts",starts_valid and eligible_valid,"Future eligible starts not verified; scheduled games alone are insufficient")
        lineup=lineup_by_league.get(lid,{})
        mark("lineup_eligibility",lineup.get("current_assignment_validated") is True and lineup.get("future_starts_verified") is True and league.get("lineup_eligibility_verified") is True,"Current Yahoo position eligibility or future lineup locks unverified")
        moves=league.get("moves_remaining")
        mark("moves_verified",type(moves) is int and 0<=moves<=4,"Weekly adds not reconciled against complete Yahoo transactions")
        mark("free_agent_states",bool(agents) and all(a.get("acquisitionState") in ("free_agent","waivers") for a in agents),"Missing/unknown acquisition state")
        tx=league.get("transactions",{})
        limits=tx.get("limitations",{})
        mark("transaction_completeness",bool(tx) and not any(limits.get(k) for k in ("possibly_truncated","upstream_bound_reached","upstream_completeness_unverified","omitted_unrecognized_rows")),"Transaction provider coverage unverified")
        mark("opponent_starts",league.get("opponent_starts_verified") is True,"Opponent eligible future starts not confirmed")
        schedule_verified=schedule_payload.get("nba_schedule_verified") is True and bool(schedule_by_league.get(lid,{}).get("players"))
        mark("nba_schedule",schedule_verified,"Verified fixture feed and schedule audit missing")
        mark("timezone",league.get("yahoo_lineup_date_verified") is True and schedule_verified,"Yahoo US lineup date / PH game date not verified")
        mark("independent_injury",league.get("injury_news_verified") is True,"Independent injury and availability review absent")
        mark("opponent_roster",league.get("opponent_roster_verified") is True,"Opponent roster snapshot not verified")
        mark("all_league_rosters",league.get("all_league_rosters_verified") is True,"All 16 team rosters not verified in snapshot")
        mark("standings",league.get("standings_verified") is True,"Standings not verified in snapshot")
        mark("projection",league.get("projection_validated") is True,"Matchup forecast has not passed scenario validation")
        mark("optimizer",league.get("optimizer_validated") is True,"ADD/DROP optimizer has not passed all preconditions")
        results[lid]={"checks":checks,"passed":sum(v["passed"] for v in checks.values()),"total":len(checks),"ready":all(v["passed"] for v in checks.values())}
    if seen!=set(LEAGUES):raise ValueError("Both target leagues are required")
    return {"ready":all(v["ready"] for v in results.values()),"leagues":results,"note":"20 prerequisite checks per league (40 total). Readiness is not a claim of 40 independent GM analytic conclusions."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--stats",required=True);p.add_argument("--input",required=True);p.add_argument("--out",required=True)
    a=p.parse_args()
    report=inspect(load_stats(a.stats),json.loads(Path(a.input).read_text(encoding="utf-8")))
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"ready":report["ready"],"leagues":{k:{"passed":v["passed"],"total":v["total"]} for k,v in report["leagues"].items()}},indent=2))
    if not report["ready"]:raise SystemExit("GM readiness blocked; see report for exact missing inputs")
if __name__=="__main__":main()
