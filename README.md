# NBA Fantasy Data

Free ESPN NBA scoreboard and box-score collector for 2026–27. Runs on GitHub Actions without an API key.

Outputs are uploaded as workflow artifacts: `player_game_logs.csv`, `games.csv`, `coverage.json`. The collector fails if any completed game's box score cannot be parsed, rather than publishing a misleading complete dataset.

Run manually: Actions → NBA ESPN Collector → Run workflow. Scheduled times are 05:30, 13:00 and 20:30 Philippine time (21:30, 05:00 and 12:30 UTC respectively). Schedules may be delayed.

ESPN endpoints are unofficial. Validate coverage before using these records for fantasy decisions. Yahoo league information is collected separately through Flaim.

## Phase 2: Flaim/Yahoo bridge (read-only)

`bridge.py` combines the ESPN CSV with a separately supplied JSON snapshot of Yahoo rosters obtained through Flaim. It does **not** upload ESPN data into Flaim, refresh Flaim automatically, or modify Yahoo rosters.

Example `rosters.json`:
```json
{"leagues":[
  {"league_id":"478.l.31010","team_id":"12","players":[{"playerId":"5352","name":"Nikola Jokić","team":"DEN","selectedPosition":"Util"}]},
  {"league_id":"478.l.33011","team_id":"4","players":[{"playerId":"6707","name":"Tari Eason","team":"HOU","selectedPosition":"G"}]}
]}
```
Run `python bridge.py --stats output/player_game_logs.csv --rosters rosters.json --out analysis`.
Review `analysis/bridge_validation.json`. Player matching is deliberately conservative: exact normalized name plus current team, with a single ESPN athlete ID. Players without a game this season, injured players, team changes, and spelling discrepancies can be unmatched. **Do not assume Yahoo player IDs equal ESPN athlete IDs.**

For now, workflow artifacts expire after 30 days and aren't directly readable by Flaim. To automate the bridge fully, an authorized integration must retrieve a fresh Flaim roster snapshot and the current GitHub artifact on each run. Do not put private league roster snapshots into a public repository without consent.
