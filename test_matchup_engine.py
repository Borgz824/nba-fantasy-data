import unittest
from matchup_engine import score,forecast,NETMON,PWT

class MatchupEngineTests(unittest.TestCase):
    def test_scoring_direction_and_weighted_ratios(self):
        a={"fgm":10,"fga":20,"ftm":8,"fta":10,"3pm":4,"3pa":10,"to":7,"pts":40}
        b={"fgm":8,"fga":20,"ftm":9,"fta":12,"3pm":5,"3pa":20,"to":9,"pts":30}
        rows={x["category"]:x for x in score(a,b,("fg_pct","ft_pct","three_pct","to","pts"))}
        self.assertEqual(rows["fg_pct"]["leader"],"ours")
        self.assertEqual(rows["ft_pct"]["leader"],"ours")
        self.assertEqual(rows["three_pct"]["leader"],"ours")
        self.assertEqual(rows["to"]["leader"],"ours")
        self.assertEqual(rows["pts"]["leader"],"ours")
    def test_missing_schedule_blocks_projection(self):
        player={"name":"Example","match_status":"matched","games":6,"status":"","pts_total":60}
        totals,issues=forecast({"pts":100},[player],{})
        self.assertEqual(totals["pts"],100)
        self.assertEqual(len(issues),1)
    def test_injured_player_not_projected(self):
        player={"name":"Example","match_status":"matched","games":6,"status":"O","pts_total":60}
        totals,issues=forecast({"pts":100},[player],{"Example":2})
        self.assertEqual(totals["pts"],100)
        self.assertEqual(len(issues),1)
    def test_league_categories(self):
        self.assertEqual(len(NETMON),9)
        self.assertEqual(len(PWT),13)

if __name__=="__main__":unittest.main()
