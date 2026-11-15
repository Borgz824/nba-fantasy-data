import unittest
from historical_lineup_pipeline import run
class HistoricalPipelineTests(unittest.TestCase):
 def setUp(self):
  self.date="2026-11-12";self.lid="478.l.31010"
  self.roster={"snapshot":{"type":"date","date":self.date},"players":[{"playerId":"101","name":"A","selectedPosition":"PG"}]}
  self.fixture={"coverage_verified":True,"games":[{"game_id":"1","start_utc":"2026-11-13T00:30:00Z","home":"NYK","away":"BOS","status":"scheduled"}]}
  self.stats=[{"athlete_id":"55","player":"A","team":"NY","game_id":"1","game_date_utc":"2026-11-13T00:30:00Z"}]
 def test_cross_midnight_utc_join(self):
  r=run(self.lid,self.roster,self.stats,self.fixture,self.date)
  self.assertTrue(r["ready"])
  self.assertTrue(r["lineup_audit"]["players"][0]["historical_active_game_assignment"])
  self.assertFalse(r["future_starts_verified"])
 def test_missing_log_blocks(self):
  r=run(self.lid,self.roster,[],self.fixture,self.date)
  self.assertFalse(r["ready"])
  self.assertIsNone(r["lineup_audit"]["players"][0]["historical_active_game_assignment"])
 def test_unverified_fixture_rejected(self):
  del self.fixture["coverage_verified"]
  with self.assertRaises(ValueError):run(self.lid,self.roster,self.stats,self.fixture,self.date)
 def test_snapshot_date_mismatch(self):
  self.roster["snapshot"]["date"]="2026-11-11"
  with self.assertRaises(ValueError):run(self.lid,self.roster,self.stats,self.fixture,self.date)
 def test_inactive_bench_not_start(self):
  self.roster["players"][0]["selectedPosition"]="BN"
  r=run(self.lid,self.roster,self.stats,self.fixture,self.date)
  self.assertFalse(r["lineup_audit"]["players"][0]["historical_active_game_assignment"])
if __name__=="__main__":unittest.main()
