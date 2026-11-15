import unittest
from nba_schedule_validation import validate_games,audit_players
class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.payload={"coverage_verified":True,"games":[{"game_id":"1","start_utc":"2026-11-16T00:30:00Z","home":"NYK","away":"DEN","status":"scheduled"}]}
    def test_eastern_vs_ph_date(self):
        g=validate_games(self.payload,"2026-11-15","2026-11-15")[0]
        self.assertEqual((g["yahoo_date"],g["philippines_date"]),("2026-11-15","2026-11-16"))
    def test_missing_coverage_rejected(self):
        with self.assertRaises(ValueError):validate_games({"games":self.payload["games"]},"2026-11-15","2026-11-15")
    def test_duplicate_rejected(self):
        self.payload["games"]*=2
        with self.assertRaises(ValueError):validate_games(self.payload,"2026-11-15","2026-11-15")
    def test_no_guessed_starts(self):
        g=validate_games(self.payload,"2026-11-15","2026-11-15")
        p=audit_players([{"name":"Test","team":"NYK","selectedPosition":"BN","status":"O"}],g)[0]
        self.assertEqual(p["scheduled_games"],1)
        self.assertIsNone(p["verified_eligible_starts"])
        self.assertFalse(p["active_slot_now"])
    def test_naive_timestamp_rejected(self):
        self.payload["games"][0]["start_utc"]="2026-11-16T00:30:00"
        with self.assertRaises(ValueError):validate_games(self.payload,"2026-11-15","2026-11-15")
    def test_team_alias(self):
        g=validate_games(self.payload,"2026-11-15","2026-11-15")
        self.assertEqual(audit_players([{"name":"Test","team":"NY","selectedPosition":"PG"}],g)[0]["scheduled_games"],1)
if __name__=="__main__":unittest.main()
