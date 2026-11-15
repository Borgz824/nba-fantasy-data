import unittest
from future_lineup_candidates import audit_future_candidates
class FutureCandidatesTests(unittest.TestCase):
 def setUp(self):
  self.roster={"snapshot":{"type":"current"},"players":[{"playerId":"1","name":"Test","selectedPosition":"PG","eligiblePositions":["PG"],"team":"NY","isEditable":True,"isUndroppable":False}]}
  self.fixtures={"coverage_verified":True,"games":[{"game_id":"123","start_utc":"2026-11-16T00:30:00Z","home":"NYK","away":"BOS","status":"scheduled"}]}
 def test_schedule_and_alias_without_confirmed_start(self):
  r=audit_future_candidates("478.l.31010",self.roster,self.fixtures,"2026-11-15","2026-11-15")
  self.assertEqual(r["players"][0]["scheduled_games"],1)
  self.assertIsNone(r["players"][0]["verified_eligible_starts"])
  self.assertFalse(r["future_starts_verified"])
 def test_scheduled_bench_not_counted_as_active(self):
  self.roster["players"].append({"playerId":"2","name":"Bench","selectedPosition":"BN","eligiblePositions":["PG"],"team":"NY"})
  r=audit_future_candidates("478.l.31010",self.roster,self.fixtures,"2026-11-15","2026-11-15")
  self.assertEqual(r["scheduled_rostered_player_count"],2)
  self.assertEqual(r["scheduled_current_active_slot_count"],1)
  self.assertEqual(r["scheduled_bench_or_il_count"],1)
  self.assertFalse(r["future_starts_verified"])
 def test_invalid_snapshot_rejected(self):
  self.roster["snapshot"]["type"]="date"
  with self.assertRaises(ValueError):audit_future_candidates("478.l.31010",self.roster,self.fixtures,"2026-11-15","2026-11-15")
 def test_unverified_fixture_rejected(self):
  self.fixtures["coverage_verified"]=False
  with self.assertRaises(ValueError):audit_future_candidates("478.l.31010",self.roster,self.fixtures,"2026-11-15","2026-11-15")
if __name__=="__main__":unittest.main()
