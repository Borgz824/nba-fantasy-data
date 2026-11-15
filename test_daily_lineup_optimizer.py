import unittest
from daily_lineup_optimizer import optimal_lineup

class DailyLineupTest(unittest.TestCase):
    def test_exact_assignment_beats_greedy(self):
        players=[
          {"playerId":"a","name":"Flexible","eligiblePositions":["PG","SG"]},
          {"playerId":"b","name":"Point","eligiblePositions":["PG"]},
          {"playerId":"c","name":"Bench","eligiblePositions":["SG"]}]
        out=optimal_lineup(players,{"a":10,"b":9,"c":1},["PG","SG"])
        self.assertEqual([x["playerId"] for x in out["lineup"]],["b","a"])
        self.assertEqual(out["score"],19)
    def test_no_inferred_eligibility_or_il(self):
        players=[{"playerId":"a","eligiblePositions":["PG"],"name":"A"},
                 {"playerId":"b","eligiblePositions":["Util"],"selectedPosition":"IL","name":"B"}]
        out=optimal_lineup(players,{"a":5,"b":20},["Util"])
        self.assertIsNone(out["lineup"][0]["playerId"])
    def test_verified_schedule_restriction(self):
        players=[{"playerId":"a","eligiblePositions":["C"],"name":"A"},
                 {"playerId":"b","eligiblePositions":["C"],"name":"B"}]
        out=optimal_lineup(players,{"a":20,"b":10},["C"],{"b"})
        self.assertEqual(out["lineup"][0]["playerId"],"b")
        self.assertTrue(out["date_specific_verified"])
if __name__=="__main__":unittest.main()
