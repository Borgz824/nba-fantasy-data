import unittest
from nba_player_intelligence import calculate

def row(day,game,pts,fgm,fga):
    return {"athlete_id":"42","player":"Sample Player","team":"NYK","game_id":game,
            "game_date_utc":day+"T23:00:00Z","minutes":"30","fgm":str(fgm),"fga":str(fga),
            "ftm":"2","fta":"2","3pm":"1","3pa":"3","oreb":"1","dreb":"3",
            "reb":"4","ast":"5","stl":"1","blk":"0","to":"2","pts":str(pts)}
class IntelligenceTests(unittest.TestCase):
    def test_rolling_and_weighted_shooting(self):
        rows=[row("2026-11-01","1",10,1,2),row("2026-11-14","2",30,8,20)]
        fixtures={"coverage_verified":True,"requested_yahoo_dates":["2026-11-16"],
                  "games":[{"game_id":"3","status":"scheduled","home":"NYK","away":"BOS","start_utc":"2026-11-16T23:00:00Z"}]}
        result=calculate(rows,fixtures,"2026-11-15")
        p=result["players"][0]
        self.assertEqual(p["windows"]["season"]["games"],2)
        self.assertEqual(p["windows"]["last_7_days"]["games"],1)
        self.assertAlmostEqual(p["windows"]["season"]["fg_pct"],round(9/22,4))
        self.assertEqual(p["scheduled_game_count"],1)
        self.assertFalse(p["eligible_starts_verified"])
        self.assertAlmostEqual(p["usage_rate"],0.2)
    def test_six_espn_team_aliases_have_future_games(self):
        aliases={"NY":"NYK","SA":"SAS","NO":"NOP","GS":"GSW","WSH":"WAS","UTAH":"UTA"}
        items=list(aliases.items())
        fixtures={"coverage_verified":True,"requested_yahoo_dates":["2026-11-16"],
                  "games":[{"game_id":"f"+str(i),"status":"scheduled",
                            "home":items[2*i][0],"away":items[2*i+1][0],
                            "start_utc":"2026-11-16T23:00:00Z"} for i in range(3)]}
        rows=[]
        for i,(alias,roster_team) in enumerate(items):
            r=row("2026-11-14","hist"+str(i),10,4,9)
            r.update({"athlete_id":str(i+1),"player":"Test Player "+str(i),"team":roster_team})
            rows.append(r)
        result=calculate(rows,fixtures,"2026-11-15")
        self.assertEqual(result["player_count"],6)
        self.assertTrue(all(p["scheduled_game_count"]==1 for p in result["players"]))

    def test_reject_duplicate(self):
        r=row("2026-11-14","2",30,8,20)
        with self.assertRaises(ValueError):calculate([r,r],{"coverage_verified":True,"games":[]},"2026-11-15")
    def test_reject_unverified_fixture(self):
        with self.assertRaises(ValueError):calculate([row("2026-11-14","2",30,8,20)],{"coverage_verified":False,"games":[]},"2026-11-15")
if __name__=="__main__":unittest.main()
