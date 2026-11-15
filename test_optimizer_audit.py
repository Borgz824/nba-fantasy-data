import unittest
from unittest.mock import patch
from add_drop_optimizer import optimize
class OptimizerAuditTests(unittest.TestCase):
 def setUp(self):
  self.lid="478.l.31010"
  self.snapshot={"league_id":self.lid,"rostered":[{"name":"A","team":"LAL","playerId":"1","slot":"PG"}],
    "free_agents":[{"name":"B","team":"NYK","playerId":"2","acquisitionState":"free_agent"}],
    "remaining_starts":{"A":2,"B":2},"starts_verified":True,
    "lineup_eligibility_verified":True,"moves_remaining":2}
 def check(self):
  with patch("add_drop_optimizer.build",return_value=({self.lid:[]},[])):
   return optimize([],self.snapshot)
 def test_flags_alone_cannot_unlock(self):
  result=self.check()
  self.assertFalse(result["ready"])
  self.assertEqual(result["recommendation"],"HOLD — insufficient verified inputs")
  self.assertTrue(any("independent Yahoo lineup" in x.get("reason","") for x in result["blockers"]))
 def test_future_audit_absent_blocks(self):
  self.snapshot["lineup_validation"]={"league_id":self.lid,"current_assignment_validated":True,"future_starts_verified":False,"players":[]}
  self.snapshot["schedule_validation"]={"league_id":self.lid,"future_starts_verified":True,"players":[]}
  self.assertFalse(self.check()["ready"])
 def test_scheduled_games_not_eligible_starts(self):
  self.snapshot["lineup_validation"]={"league_id":self.lid,"current_assignment_validated":True,"future_starts_verified":True,
     "players":[{"playerId":i,"future_lineup_verified":True,"future_eligible_starts":2} for i in ("1","2")]}
  self.snapshot["schedule_validation"]={"league_id":self.lid,"future_starts_verified":True,
     "players":[{"playerId":i,"verified_eligible_starts":2,"scheduled_games":1} for i in ("1","2")]}
  self.assertTrue(any("fixture bounds" in x.get("reason","") for x in self.check()["blockers"]))
 def test_missing_id_rejected(self):
  self.snapshot["lineup_validation"]={"league_id":self.lid,"current_assignment_validated":True,"future_starts_verified":True,"players":[]}
  self.snapshot["schedule_validation"]={"league_id":self.lid,"future_starts_verified":True,"players":[]}
  self.assertTrue(any("player ID absent" in x.get("reason","") for x in self.check()["blockers"]))
if __name__=="__main__":unittest.main()
