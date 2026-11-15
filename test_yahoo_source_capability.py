import unittest
from yahoo_source_capability import assess_yahoo_sources
class YahooSourceCapabilityTests(unittest.TestCase):
 def test_category_totals_not_daily_scoring(self):
  r=assess_yahoo_sources({"matchups":[{"home":{"categories":[]},"away":{}}]},
    {"players":[{"playerId":"1"}]})
  self.assertTrue(r["matchup_category_totals_available"])
  self.assertFalse(r["player_daily_fantasy_scoring_verified"])
  self.assertFalse(r["add_drop_ready"])
 def test_missing_roster_ids(self):
  r=assess_yahoo_sources({"matchups":[]},{"players":[{}]})
  self.assertFalse(r["roster_player_ids_available"])
 def test_malformed_payload_rejected(self):
  with self.assertRaises(ValueError):assess_yahoo_sources({}, {})
if __name__=="__main__":unittest.main()
