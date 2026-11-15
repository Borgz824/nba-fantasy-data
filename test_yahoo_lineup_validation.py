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
if __name__=="__main__":unittest.main()
