import unittest
from flaim_matchup_adapter import adapt,totals

class FlaimAdapterTests(unittest.TestCase):
    def test_netmon_matchup_extraction(self):
        def side(id,name):
            cats=[("9004003","10/20"),("9007006","8/10"),("10","4"),("12","30"),("15","10"),("16","8"),("17","2"),("18","1"),("19","3")]
            return {"teamId":id,"teamName":name,"categories":[{"statId":k,"value":v} for k,v in cats]}
        p={"leagueKey":"478.l.31010","matchups":[{"week":4,"home":side("12","SuperBorgz"),"away":side("10","Opponent")}]}
        result=adapt(p,"478.l.31010","12")
        self.assertTrue(result["validation"]["current_totals_complete"])
        self.assertEqual(result["ours"]["current_totals"]["fgm"],10)
        self.assertFalse(result["validation"]["future_starts_verified"])
        self.assertEqual(result["ours"]["remaining_games"],{})
    def test_missing_fgm_detected(self):
        totals_,errors,missing=totals({"categories":[]},"478.l.33011")
        self.assertIn("fgm",missing)
        self.assertEqual(totals_,{})
    def test_wrong_league_fails(self):
        with self.assertRaises(ValueError):
            adapt({"leagueKey":"wrong"},"478.l.31010","12")

if __name__=="__main__":unittest.main()
