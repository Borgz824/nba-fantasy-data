import unittest
from completed_fixture_feed import fetch_completed
class CompletedFixtureTests(unittest.TestCase):
 def test_post_game_included_and_utc_eastern_date(self):
  payload={"events":[{"id":"1","date":"2026-11-13T00:30:00Z","status":{"type":{"state":"post"}},"competitions":[{"competitors":[{"homeAway":"home","team":{"abbreviation":"NY"}},{"homeAway":"away","team":{"abbreviation":"BOS"}}]}]}]}
  r=fetch_completed("2026-11-12","2026-11-12",lambda d:payload)
  self.assertEqual(len(r["games"]),1)
  self.assertEqual(r["games"][0]["home"],"NYK")
 def test_future_game_excluded(self):
  payload={"events":[{"id":"1","date":"2026-11-13T00:30:00Z","status":{"type":{"state":"pre"}},"competitions":[{"competitors":[{"homeAway":"home","team":{"abbreviation":"NY"}},{"homeAway":"away","team":{"abbreviation":"BOS"}}]}]}]}
  self.assertEqual(fetch_completed("2026-11-12","2026-11-12",lambda d:payload)["games"],[])
 def test_missing_events_fails(self):
  with self.assertRaises(ValueError):fetch_completed("2026-11-12","2026-11-12",lambda d:{})
 def test_wrong_eastern_date_excluded(self):
  payload={"events":[{"id":"1","date":"2026-11-13T06:30:00Z","status":{"type":{"state":"post"}},"competitions":[{"competitors":[{"homeAway":"home","team":{"abbreviation":"NY"}},{"homeAway":"away","team":{"abbreviation":"BOS"}}]}]}]}
  self.assertEqual(fetch_completed("2026-11-12","2026-11-12",lambda d:payload)["games"],[])
if __name__=="__main__":unittest.main()
