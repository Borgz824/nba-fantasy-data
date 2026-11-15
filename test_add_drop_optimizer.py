import unittest
from add_drop_optimizer import optimize,category_delta
from bridge import METRICS

def row(name,team,athlete,game,pts):
    vals={"fgm":"4","fga":"10","ftm":"2","fta":"3","3pm":"1","3pa":"4","oreb":"1","dreb":"4","reb":"5","ast":"3","stl":"1","blk":"1","to":"2","pts":str(pts)}
    return dict(player=name,team=team,athlete_id=athlete,game_id=game,game_date_utc="2026-11-13T00:00Z",**vals)

def sample(league="478.l.31010"):
    return {"league_id":league,"rostered":[{"name":"Alpha","team":"NY","playerId":"1","slot":"BN","status":""}],"free_agents":[{"name":"Beta","team":"LA","playerId":"2","status":"","acquisitionState":"free_agent"}],"remaining_starts":{"Alpha":1,"Beta":2},"starts_verified":True,"lineup_eligibility_verified":True,"moves_remaining":2,"current_team_totals":{k:100 for k in METRICS}}

class OptimizerTests(unittest.TestCase):
    def setUp(self):
        self.stats=[row(name,team,aid,str(i),pts) for name,team,aid,pts in [("Alpha","NY","a",10),("Beta","LA","b",20)] for i in range(1,7)]
    def test_unverified_blocks(self):
        s=sample();s["starts_verified"]=False
        r=optimize(self.stats,s)
        self.assertFalse(r["ready"])
        self.assertEqual(r["comparisons"],[])
    def test_scenario_delta(self):
        r=optimize(self.stats,sample())
        self.assertTrue(r["ready"])
        self.assertEqual(len(r["comparisons"]),1)
        self.assertEqual(r["comparisons"][0]["all_deltas"]["pts"],30)
        self.assertEqual(r["comparisons"][0]["all_deltas"]["to"],-2)
    def test_pwt_categories(self):
        r=optimize(self.stats,sample("478.l.33011"))
        self.assertIn("ftm",r["comparisons"][0]["all_deltas"])
        self.assertIn("three_pct",r["comparisons"][0]["all_deltas"])
    def test_percentage_weighted_by_attempts(self):
        base={k:100 for k in METRICS};base.update({"fgm":50,"fga":100})
        delta={k:0 for k in METRICS};delta.update({"fgm":10,"fga":10})
        self.assertAlmostEqual(category_delta(delta,base,("fg_pct",))["fg_pct"],round(60/110-0.5,6))

if __name__=="__main__":unittest.main()
