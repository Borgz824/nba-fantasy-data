import unittest
from category_gm_optimizer import evaluate

def row(name,pid,pts,team="LAL"):
    return {"athlete_id":pid,"player":name,"team":team,"game_id":pid+"-g",
      "game_date_utc":"2026-11-01T00:00:00Z","fgm":pts/2,"fga":pts,
      "ftm":2,"fta":3,"3pm":1,"3pa":3,"oreb":1,"dreb":2,"reb":3,
      "ast":2,"stl":1,"blk":1,"to":1,"pts":pts}

class CategoryGMTest(unittest.TestCase):
    def test_unlimited_recommendations_and_separate_leagues(self):
        stats=[]
        for i in range(5):
            for n,p,pts in [("Low","1",4),("High","2",24),("Mid","3",12)]:
                r=row(n,p,pts);r["game_id"]=p+"-"+str(i);stats.append(r)
        leagues=[]
        for lid in ("478.l.31010","478.l.33011"):
            leagues.append({"league_id":lid,"roster":{"players":[{"name":"Low","team":"LAL","playerId":"a"}]},
                "free_agents":{"freeAgents":[{"name":"High","team":"LAL","playerId":"b","acquisitionState":"free_agent"},
                  {"name":"Mid","team":"LAL","playerId":"c","acquisitionState":"waivers"}]}})
        report=evaluate(stats,{"leagues":leagues})
        for lid in report["leagues"]:
            x=report["leagues"][lid]
            self.assertTrue(x["ready"])
            self.assertEqual(x["eligible_comparisons"],2)
            self.assertEqual(x["recommendations"][0]["add"],"High")
            self.assertIn("category_z_deltas",x["recommendations"][0])
    def test_missing_data_not_fabricated(self):
        leagues=[{"league_id":lid,"roster":{"players":[]},"free_agents":{"freeAgents":[]}}
          for lid in ("478.l.31010","478.l.33011")]
        report=evaluate([],{"leagues":leagues})
        self.assertTrue(all(not x["ready"] for x in report["leagues"].values()))
if __name__=="__main__":unittest.main()
