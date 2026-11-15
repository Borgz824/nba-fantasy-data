import unittest
from yahoo_dated_lineup_audit import audit_dated_roster
class DatedLineupTests(unittest.TestCase):
 def setUp(self):
  self.lid="478.l.31010";self.date="2026-11-12"
  self.roster={"snapshot":{"type":"date"},"players":[
   {"playerId":"1","name":"A","team":"NYK","selectedPosition":"PG"},
   {"playerId":"2","name":"B","team":"DEN","selectedPosition":"BN"}]}
  self.fixtures=[{"game_id":"1","yahoo_date":self.date,"home":"NYK","away":"DEN"}]
 def run_audit(self):
  return audit_dated_roster(self.lid,self.roster,self.fixtures,self.date,self.date)
 def test_active_vs_bench(self):
  r=self.run_audit();self.assertTrue(r["players"][0]["historical_active_game_assignment"])
  self.assertFalse(r["players"][1]["historical_active_game_assignment"])
  self.assertFalse(r["future_starts_verified"])
 def test_mismatched_date(self):
  with self.assertRaises(ValueError):audit_dated_roster(self.lid,self.roster,self.fixtures,self.date,"2026-11-11")
 def test_current_snapshot_rejected(self):
  self.roster["snapshot"]["type"]="current"
  with self.assertRaises(ValueError):self.run_audit()
 def test_no_game_no_assignment(self):
  self.fixtures=[]
  self.assertFalse(self.run_audit()["players"][0]["historical_active_game_assignment"])
 def test_duplicate_player_rejected(self):
  self.roster["players"].append(dict(self.roster["players"][0]))
  with self.assertRaises(ValueError):self.run_audit()
 def test_overfilled_capacity(self):
  self.roster["players"].append({"playerId":"3","name":"C","team":"NYK","selectedPosition":"PG"})
  self.assertFalse(self.run_audit()["historical_snapshot_valid"])
 def test_missing_nba_team_is_unknown(self):
  del self.roster["players"][0]["team"]
  r=self.run_audit()
  self.assertFalse(r["historical_snapshot_valid"])
  self.assertEqual(r["missing_professional_team_player_ids"],["1"])
  self.assertIsNone(r["players"][0]["historical_active_game_assignment"])
  self.assertIsNone(r["players"][0]["scheduled_games_on_date"])
if __name__=="__main__":unittest.main()
