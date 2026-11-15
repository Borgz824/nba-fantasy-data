import unittest
from nba_injury_identity import merge,candidate_name

class InjuryIdentityTests(unittest.TestCase):
    def test_surname_first(self):
        self.assertEqual(candidate_name("Reaves, Austin"),"Austin Reaves")
        self.assertIsNone(candidate_name("Austin"))
    def test_match_and_unmatched_are_distinct(self):
        data={"players":[{"athlete_id":"1","name":"Austin Reaves"},{"athlete_id":"2","name":"Other Player"}],"coverage":{}}
        report={"source_url":"https://example.org/report.pdf","retrieved_at_utc":"2026-11-15T00:00:00Z",
                "entries":[{"name_candidate":"Reaves, Austin","status":"Questionable","page":1,"raw_line":"Reaves, Austin Questionable"},
                           {"name_candidate":"Unknown, Person","status":"Out","page":1,"raw_line":"Unknown, Person Out"}]}
        result,audit=merge(data,report)
        self.assertEqual(audit["matched_rows"],1)
        self.assertEqual(audit["unmatched_rows"],1)
        self.assertFalse(audit["all_report_rows_matched"])
        self.assertEqual(result["players"][0]["injury_status"],"Questionable")
        self.assertIsNone(result["players"][1]["injury_status"])
        self.assertFalse(result["players"][1]["injury_verified"])
if __name__=="__main__":unittest.main()
