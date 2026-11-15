import unittest
from streaming_priorities import assess

def side(team_id,name,fgm,fga,ftm,fta,pts):
    pairs=[("9004003",f"{fgm}/{fga}"),("9007006",f"{ftm}/{fta}"),("10","10"),("12",str(pts)),("15","20"),("16","10"),("17","3"),("18","2"),("19","7")]
    return {"teamId":team_id,"teamName":name,"categories":[{"statId":k,"value":v} for k,v in pairs]}

class PriorityTests(unittest.TestCase):
    def test_current_gap_not_future_projection(self):
        p={"leagueKey":"478.l.31010","matchups":[{"week":4,"home":side("12","SuperBorgz",10,25,9,10,50),"away":side("10","Other",12,24,7,10,60)}]}
        r=assess(p,"478.l.31010","12")
        self.assertEqual(r["week"],4)
        self.assertFalse(r["projection_ready"])
        self.assertEqual(next(x for x in r["behind"] if x["category"]=="pts")["gap"],-10)
        self.assertEqual(next(x for x in r["ahead"] if x["category"]=="ft_pct")["leader"],"ours")
    def test_incomplete_flaim_totals_rejected(self):
        p={"leagueKey":"478.l.31010","matchups":[{"home":{"teamId":"12","categories":[]},"away":{"teamId":"10","categories":[]}}]}
        with self.assertRaises(ValueError):assess(p,"478.l.31010","12")

if __name__=="__main__":unittest.main()
