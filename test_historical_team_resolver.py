import unittest
from historical_team_resolver import resolve_historical_teams
class HistoricalTeamTests(unittest.TestCase):
 def setUp(self):
  self.day="2026-11-12"
  self.roster={"snapshot":{"type":"date","date":self.day},"players":[{"playerId":"101","name":"Test Player","selectedPosition":"PG"}]}
  self.row={"athlete_id":"999","player":"Test Player","team":"NY","game_id":"1","game_date_utc":"2026-11-13T01:00:00Z"}
  self.fixtures=[{"game_id":"1","yahoo_date":self.day,"home":"NYK","away":"BOS"}]
 def run_resolve(self,rows=None,fixtures=None):
  return resolve_historical_teams(self.roster,[self.row] if rows is None else rows,self.day,self.fixtures if fixtures is None else fixtures)
 def test_game_id_matches_even_when_utc_next_day(self):
  r=self.run_resolve();self.assertTrue(r["all_teams_verified"])
  self.assertEqual(r["players"][0]["team"],"NYK")
 def test_missing_log_not_assumed_no_game(self):
  r=self.run_resolve([]);self.assertFalse(r["all_teams_verified"])
  self.assertIsNone(r["players"][0]["team"])
 def test_two_espn_ids_ambiguous(self):
  self.assertFalse(self.run_resolve([self.row,{**self.row,"athlete_id":"888"}])["all_teams_verified"])
 def test_two_valid_teams_ambiguous(self):
  self.assertFalse(self.run_resolve([self.row,{**self.row,"team":"BOS"}])["all_teams_verified"])
 def test_team_outside_fixture_rejected(self):
  self.assertFalse(self.run_resolve([{**self.row,"team":"LAL"}])["all_teams_verified"])
 def test_other_game_id_not_matched(self):
  self.assertFalse(self.run_resolve([{**self.row,"game_id":"2"}])["all_teams_verified"])
 def test_mismatched_roster_date_rejected(self):
  self.roster["snapshot"]["date"]="2026-11-11"
  with self.assertRaises(ValueError):self.run_resolve()
 def test_missing_fixtures_rejected(self):
  with self.assertRaises(ValueError):resolve_historical_teams(self.roster,[self.row],self.day)
 def test_duplicate_fixture_id_rejected(self):
  with self.assertRaises(ValueError):self.run_resolve(fixtures=self.fixtures*2)
 def test_duplicate_yahoo_player_rejected(self):
  self.roster["players"]*=2
  with self.assertRaises(ValueError):self.run_resolve()
if __name__=="__main__":unittest.main()
