import unittest
from bridge import build

def game(name,team,athlete):
    return dict(player=name,team=team,athlete_id=athlete,game_id=team,
      game_date_utc="2026-11-15T00:00:00Z",**{
        "fgm":2,"fga":4,"ftm":1,"fta":2,"3pm":1,"3pa":2,
        "oreb":1,"dreb":2,"reb":3,"ast":2,"stl":1,"blk":0,"to":1,"pts":6})

class BridgeIdentityTest(unittest.TestCase):
    def test_traded_player_single_athlete(self):
        rows=[game("Example Player","BOS","123"),game("Example Player","NY","123")]
        result,issues=build(rows,[{"league_id":"478.l.31010","players":[{"name":"Example Player","team":"LAL","playerId":"y"}]}])
        self.assertEqual(issues,[])
        p=result["478.l.31010"][0]
        self.assertEqual(p["games"],2)
        self.assertEqual(p["match_method"],"unique_name_fallback")
    def test_ambiguous_identity_rejected(self):
        rows=[game("Example Player","BOS","123"),game("Example Player","NY","456")]
        result,issues=build(rows,[{"league_id":"478.l.31010","players":[{"name":"Example Player","team":"LAL","playerId":"y"}]}])
        self.assertEqual(result["478.l.31010"][0]["match_status"],"unmatched")
        self.assertTrue(issues)
if __name__=="__main__":unittest.main()
