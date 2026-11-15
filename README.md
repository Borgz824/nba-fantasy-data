# NBA Fantasy Data

Free ESPN NBA scoreboard and box-score collector for 2026–27. Runs on GitHub Actions without an API key.

Outputs are uploaded as workflow artifacts: `player_game_logs.csv`, `games.csv`, `coverage.json`. The collector fails if any completed game's box score cannot be parsed, rather than publishing a misleading complete dataset.

Run manually: Actions → NBA ESPN Collector → Run workflow. Scheduled times are 05:30, 13:00 and 20:30 Philippine time (21:30, 05:00 and 12:30 UTC respectively). Schedules may be delayed.

ESPN endpoints are unofficial. Validate coverage before using these records for fantasy decisions. Yahoo league information is collected separately through Flaim.
