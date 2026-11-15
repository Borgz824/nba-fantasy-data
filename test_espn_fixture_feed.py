import unittest
from datetime import date
from espn_fixture_feed import extract_day,fetch
def event(gid="123",when="2026-11-16T00:30:00Z",state="pre"):
    return {"id":gid,"date":when,"status":{"type":{"state":state}},
            "competitions":[{"competitors":[{"homeAway":"home","team":{"abbreviation":"NYK"}},
                                        {"homeAway":"away","team":{"abbreviation":"DEN"}}]}]}
class FeedTests(unittest.TestCase):
    def test_one_day(self):
        result=fetch("2026-11-15","2026-11-15",lambda day:{"events":[event()]})
        self.assertEqual(len(result["games"]),1)
        self.assertTrue(result["coverage_verified"])
    def test_invalid_daily_response(self):
        with self.assertRaises(ValueError):fetch("2026-11-15","2026-11-15",lambda day:{})
    def test_missing_team(self):
        x=event();x["competitions"][0]["competitors"][0]["team"]={}
        with self.assertRaises(ValueError):extract_day({"events":[x]},date(2026,11,15))
    def test_nonfuture_excluded(self):
        self.assertEqual(extract_day({"events":[event(state="post")]},date(2026,11,15)),[])
    def test_date_window_guard(self):
        with self.assertRaises(ValueError):fetch("2026-11-15","2027-01-01",lambda day:{"events":[]})
    def test_deduplicate(self):
        result=fetch("2026-11-15","2026-11-16",lambda day:{"events":[event()]})
        self.assertEqual(len(result["games"]),1)
if __name__=="__main__":unittest.main()
