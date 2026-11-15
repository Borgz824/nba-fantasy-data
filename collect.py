#!/usr/bin/env python3
"""Collect ESPN NBA regular-season player box scores, failing closed on missing games."""
import csv
import json
import os
import time
from datetime import date, timedelta, datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
START = date(2026, 10, 1)  # includes preseason for schedule discovery; filter by season type
END = min(date.today(), date(2027, 6, 30))
OUT = Path("output")
OUT.mkdir(exist_ok=True)
COLUMNS = ["game_id", "game_date_utc", "athlete_id", "player", "team", "opponent", "minutes",
           "fgm", "fga", "ftm", "fta", "3pm", "3pa", "oreb", "dreb", "reb",
           "ast", "stl", "blk", "to", "pts", "fg_pct", "ft_pct", "three_pct"]

def fetch(path, params):
    url = BASE + "/" + path + "?" + urlencode(params)
    for attempt in range(5):
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; fantasy-data-collector/1.0)", "Accept": "application/json"})
            with urlopen(req, timeout=30) as response:
                return json.load(response)
        except Exception as exc:
            if attempt == 4:
                raise RuntimeError(f"Failed {url}: {exc}") from exc
            time.sleep(min(20, 2 ** attempt))
    raise AssertionError("unreachable")

def as_num(s):
    if s in ("", "--", None):
        return None
    try:
        return float(s) if "." in str(s) else int(s)
    except (ValueError, TypeError):
        return None

def pair(s):
    a, sep, b = str(s or "").partition("-")
    return (as_num(a), as_num(b)) if sep else (None, None)

def rows_from_summary(game, summary):
    box = summary.get("boxscore", {})
    teams = box.get("players", [])
    if len(teams) != 2:
        raise ValueError("missing two team player blocks")
    rows = []
    for block in teams:
        team = block.get("team", {}).get("abbreviation", "")
        other = [t.get("team", {}).get("abbreviation", "") for t in teams if t is not block]
        opponent = other[0] if other else ""
        for group in block.get("statistics", []):
            labels = [str(x).upper() for x in group.get("labels", [])]
            for athlete in group.get("athletes", []):
                if athlete.get("didNotPlay") or athlete.get("didNotDress"):
                    continue
                stats = athlete.get("stats", [])
                if not stats or len(stats) != len(labels):
                    continue
                d = dict(zip(labels, stats))
                person = athlete.get("athlete", {})
                if not person.get("id"):
                    raise ValueError("player without ID")
                fgm, fga = pair(d.get("FG"))
                threem, threea = pair(d.get("3PT"))
                ftm, fta = pair(d.get("FT"))
                row = {
                    "game_id": game["id"], "game_date_utc": game.get("date", ""),
                    "athlete_id": person["id"], "player": person.get("displayName", ""),
                    "team": team, "opponent": opponent, "minutes": d.get("MIN"),
                    "fgm": fgm, "fga": fga, "ftm": ftm, "fta": fta,
                    "3pm": threem, "3pa": threea,
                    "oreb": as_num(d.get("OREB")), "dreb": as_num(d.get("DREB")),
                    "reb": as_num(d.get("REB")), "ast": as_num(d.get("AST")),
                    "stl": as_num(d.get("STL")), "blk": as_num(d.get("BLK")),
                    "to": as_num(d.get("TO")), "pts": as_num(d.get("PTS")),
                    "fg_pct": round(fgm / fga, 6) if fga and fgm is not None else None,
                    "ft_pct": round(ftm / fta, 6) if fta and ftm is not None else None,
                    "three_pct": round(threem / threea, 6) if threea and threem is not None else None,
                }
                rows.append(row)
    if not rows:
        raise ValueError("no player rows")
    return rows

def write_csv(path, records, columns):
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

def main():
    games = {}
    day = START
    while day <= END:
        payload = fetch("scoreboard", {"dates": day.strftime("%Y%m%d"), "limit": 100})
        for event in payload.get("events", []):
            # ESPN season type 2 = regular season
            if str(event.get("season", {}).get("type", "")) != "2":
                continue
            games[str(event["id"])] = event
        day += timedelta(days=1)
        time.sleep(0.15)
    if not games:
        raise RuntimeError("No regular-season games found; check ESPN schedule schema")
    complete = [g for g in games.values() if g.get("status", {}).get("type", {}).get("completed") is True]
    records, failed = [], {}
    for game in sorted(complete, key=lambda g: g.get("date", "")):
        try:
            summary = fetch("summary", {"event": game["id"]})
            records.extend(rows_from_summary(game, summary))
        except Exception as exc:
            failed[str(game["id"])] = str(exc)
        time.sleep(0.2)
    keys = [(r["game_id"], r["athlete_id"]) for r in records]
    duplicates = len(keys) - len(set(keys))
    required = ["fgm", "fga", "ftm", "fta", "3pm", "3pa", "reb", "ast", "stl", "blk", "to", "pts"]
    missing_fields = sum(any(r[k] is None for k in required) for r in records)
    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "schedule_games": len(games), "completed_games": len(complete),
        "parsed_games": len(set(r["game_id"] for r in records)),
        "player_game_rows": len(records), "duplicate_player_game_rows": duplicates,
        "rows_missing_required_stats": missing_fields,
        "failed_games": failed, "source": "ESPN unofficial API",
        "complete": not failed and not duplicates and not missing_fields and len(set(r["game_id"] for r in records)) == len(complete),
    }
    write_csv(OUT / "player_game_logs.csv", records, COLUMNS)
    write_csv(OUT / "games.csv", [
        {"game_id": g["id"], "date_utc": g.get("date", ""), "name": g.get("name", ""),
         "completed": g.get("status", {}).get("type", {}).get("completed", False)}
        for g in games.values()
    ], ["game_id", "date_utc", "name", "completed"])
    (OUT / "coverage.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    if not manifest["complete"]:
        raise SystemExit("Validation failed: dataset is NOT certified complete")

if __name__ == "__main__":
    main()
