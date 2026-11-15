import unittest
from yahoo_lineup_validation import inspect_roster
class LineupTests(unittest.TestCase):
 def setUp(self):
  self.lid="478.l.31010"
  self.roster={"snapshot":{"type":"current"},"players":[{"playerId":"1","name":"A","selectedPosition":"PG","eligiblePositions":["PG","G","Util"],"isEditable":True}]}
 def test_compatible(self):
  r=inspect_roster(self.lid,self.roster)
  self.assertTrue(r["current_assignment_validated"])
  self.assertFalse(r["future_starts_verified"])
 def test_incompatible(self):
  self.roster["players"][0]["eligiblePositions"]=["C"]
  self.assertFalse(inspect_roster(self.lid,self.roster)["current_assignment_validated"])
 def test_unknown_not_assumed(self):
  del self.roster["players"][0]["eligiblePositions"]
  self.assertEqual(inspect_roster(self.lid,self.roster)["unknown_eligibility"],["A"])
 def test_duplicate_id(self):
  self.roster["players"]*=2
  with self.assertRaises(ValueError):inspect_roster(self.lid,self.roster)
 def test_overfilled(self):
  self.roster["players"].append({"playerId":"2","name":"B","selectedPosition":"PG","eligiblePositions":["PG"]})
  self.assertFalse(inspect_roster(self.lid,self.roster)["current_assignment_validated"])
 def test_historical_rejected(self):
  self.roster["snapshot"]["type"]="date"
  with self.assertRaises(ValueError):inspect_roster(self.lid,self.roster)
 def test_bench_is_not_future_start(self):
  self.roster["players"][0]["selectedPosition"]="BN"
  self.assertIsNone(inspect_roster(self.lid,self.roster)["players"][0]["future_eligible_starts"])
 def test_pwt_il_and_three_util_slots(self):
  players=[{"playerId":str(i),"name":str(i),"selectedPosition":slot,"eligiblePositions":[slot] if slot not in ("BN","IL") else []}
    for i,slot in enumerate(["PG","SG","G","SF","PF","F","C","Util","Util","Util","BN","BN","IL","IL"],1)]
  report=inspect_roster("478.l.33011",{"snapshot":{"type":"current"},"players":players})
  self.assertTrue(report["current_assignment_validated"])
  self.assertEqual(report["slot_counts"]["IL"],2)
  self.assertFalse(report["future_starts_verified"])
 def test_pwt_excess_il_rejected(self):
  players=[{"playerId":str(i),"name":str(i),"selectedPosition":"IL","eligiblePositions":[]} for i in range(3)]
  report=inspect_roster("478.l.33011",{"snapshot":{"type":"current"},"players":players})
  self.assertFalse(report["current_assignment_validated"])
  self.assertEqual(report["overfilled_slots"]["IL"],3)
 def test_noneditable_not_treated_as_future_lock(self):
  self.roster["players"][0]["isEditable"]=False
  p=inspect_roster(self.lid,self.roster)["players"][0]
  self.assertIs(p["is_editable_now"],False)
  self.assertIs(p["future_lineup_verified"],False)
if __name__=="__main__":unittest.main()
