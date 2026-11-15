import unittest
from category_engine import evaluate

def rec(player,team,athlete,game,pts,fgm,fga,ftm,fta):
    return dict(player=player,team=team,athlete_id=athlete,game_id=str(game),game_date_utc="2026-11-01T00:00Z",
        fgm=str(fgm),fga=str(fga),ftm=str(ftm),fta=str(fta),**{"3pm":"1","3pa":"4","oreb":"2","dreb":"4","reb":"6","ast":"3","stl":"1","blk":"1","to":"2","pts":str(pts)})

class CategoryEngineTests(unittest.TestCase):
    def test_weighted_shooting_and_sample_gate(self):
        stats=[rec("Herbert Jones","NO","123",1,12,1,2,1,2),rec("Herbert Jones","NO","123",2,20,9,10,3,4)]
        leagues=[{"league_id":"478.l.31010","players":[{"name":"Herbert Jones","team":"NOP","playerId":"6577","selectedPosition":"G"}]}]
        result,issues=evaluate(stats,leagues,min_games=2)
        self.assertFalse(issues)
        r=result["478.l.31010"][0]
        self.assertEqual(r["games"],2)
        self.assertEqual(r["pts_pg"],16.0)
        self.assertEqual(r["fg_pct"],round(10/12,4))
        self.assertTrue(r["eligible_for_ranking"])
        limited,_=evaluate(stats,leagues,min_games=5)
        self.assertFalse(limited["478.l.31010"][0]["eligible_for_ranking"])
    def test_out_injury_blocks_ranking(self):
        stats=[rec("Herbert Jones","NO","123",i,12,5,10,2,3) for i in range(6)]
        leagues=[{"league_id":"478.l.33011","players":[{"name":"Herbert Jones","team":"NOP","playerId":"6577","status":"O"}]}]
        result,_=evaluate(stats,leagues)
        self.assertFalse(result["478.l.33011"][0]["eligible_for_ranking"])

if __name__=="__main__":unittest.main()
