"""Offline integration smoke test: ESPN player stats + Yahoo roster snapshot."""
import unittest
from bridge import build, normalize

class BridgeTest(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(normalize("Nikola Jokić"), "nikola jokic")
    def test_two_leagues_and_team_aliases(self):
        def record(name, team, athlete, game, pts):
            return dict(player=name, team=team, athlete_id=athlete, game_id=game,
                game_date_utc="2026-11-13T00:00Z", **{
                    "fgm":"4","fga":"10","ftm":"2","fta":"2","3pm":"1","3pa":"3",
                    "oreb":"1","dreb":"4","reb":"5","ast":"3","stl":"1","blk":"1","to":"2","pts":str(pts)})
        stats=[
            record("Herbert Jones","NO","111","game1",11),
            record("Herbert Jones","NO","111","game2",15),
            record("OG Anunoby","NY","222","game1",18),
            record("Devin Vassell","SA","333","game2",21),
            record("Anthony Davis","WSH","444","game2",24),
        ]
        leagues=[
            {"league_id":"478.l.31010","players":[
                {"name":"Herbert Jones","team":"NOP","playerId":"10","selectedPosition":"G"},
                {"name":"OG Anunoby","team":"NYK","playerId":"20","selectedPosition":"SF"},
                {"name":"Devin Vassell","team":"SAS","playerId":"30","selectedPosition":"F"}]},
            {"league_id":"478.l.33011","players":[
                {"name":"Herbert Jones","team":"NOP","playerId":"10","selectedPosition":"F"},
                {"name":"Anthony Davis","team":"WAS","playerId":"40","selectedPosition":"BN"}]},
        ]
        result,issues=build(stats,leagues)
        self.assertEqual(issues,[])
        self.assertEqual(len(result["478.l.31010"]),3)
        self.assertEqual(len(result["478.l.33011"]),2)
        h=result["478.l.31010"][0]
        self.assertEqual(h["games"],2)
        self.assertEqual(h["pts_total"],26.0)
        self.assertEqual(h["pts_per_game"],13.0)
        self.assertEqual(h["espn_athlete_id"],"111")
        self.assertEqual(h["yahoo_player_id"],"10")
    def test_ambiguous_identity_fails_closed(self):
        base={"player":"Test Player","team":"NY","game_id":"1"}
        stats=[dict(base,athlete_id="1"),dict(base,athlete_id="2")]
        leagues=[{"league_id":"478.l.31010","players":[{"name":"Test Player","team":"NYK"}]}]
        result,issues=build(stats,leagues)
        self.assertEqual(issues[0]["reason"],"ambiguous")
        self.assertEqual(result["478.l.31010"][0]["match_status"],"ambiguous")

if __name__=="__main__":
    unittest.main()
