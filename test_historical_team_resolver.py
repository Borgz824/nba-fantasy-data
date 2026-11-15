import unittest
from historical_team_resolver import resolve_historical_teams
class HistoricalTeamTests(unittest.TestCase):
 def setUp(self):
  self.roster={"snapshot":{"type":"date","date":"2026-11-12"},"players":[{"playerId":"101","name":"Test Player","selectedPosition":"PG"}]}
  self.row={"athlete_id":"999","player":"Test Player","team":"NY","game_id":"1","game_date_utc":"2026-11-12T23:00:00Z"}
 def run_resolve(self,rows=None):
  return resolve_historical_teams(self.roster,[self.row] if rows is None else rows,"2026-11-12")
 def test_same_day_unique_identity(self):
  r=self.run_resolve();self.assertTrue(r["all_teams_verified"])
  self.assertEqual(r["players"][0]["team"],"NY")
 def test_missing_game_not_assumed_no_game(self):
  r=self.run_resolve([]);self.assertFalse(r["all_teams_verified"])
  self.assertIsNone(r["players"][0]["team"])
 def test_two_espn_ids_ambiguous(self):
  r=self.run_resolve([self.row,{**self.row,"athlete_id":"888"}])
  self.assertFalse(r["all_teams_verified"])
 def test_two_teams_ambiguous(self):
  r=self.run_resolve([self.row,{**self.row,"team":"BOS"}])
  self.assertFalse(r["all_teams_verified"])
 def test_other_utc_date_not_matched(self):
  r=self.run_resolve([{**self.row,"game_date_utc":"2026-11-13T00:00:00Z"}])
  self.assertFalse(r["all_teams_verified"])
 def test_mismatched_roster_date_rejected(self):
  self.roster["snapshot"]["date"]="2026-11-11"
  with self.assertRaises(ValueError):self.run_resolve()
 def test_timezone_naive_rejected(self):
  with self.assertRaises(ValueError):self.run_resolve([{**self.row,"game_date_utc":"2026-11-12T23:00:00"}])
if __name__=="__main__":unittest.main()
