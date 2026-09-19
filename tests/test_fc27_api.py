"""Offline tests: run with  python -m unittest discover -s tests -v

These tests never contact EA. `unittest.mock.patch` temporarily replaces
urllib.request.urlopen (the function that sends the request) with a fake that
returns a saved response from tests/fixtures/. This keeps the tests fast and
repeatable, and they don't break when EA's live data changes.

The fixtures have the exact shape of real EA responses, but every club, player,
id, date and kit value is a placeholder: Example FC = 1001, Opponent A = 2001,
Player1, Player2, ...
"""

import io
import json
import unittest
import urllib.error
import urllib.parse
from pathlib import Path
from unittest.mock import patch

from fc27_api import FC27API, FC27APIError

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name):
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def fake_ea(payload):
    """Pretend EA answers every request with `payload` (as JSON text)."""
    body = json.dumps(payload).encode("utf-8")
    # side_effect builds a fresh response for every call, like a real server.
    return patch("urllib.request.urlopen", side_effect=lambda *args, **kwargs: io.BytesIO(body))


def sent_params(fake):
    """The query parameters of the last request our code sent."""
    request = fake.call_args[0][0]
    query = urllib.parse.urlparse(request.full_url).query
    return dict(urllib.parse.parse_qsl(query))


class ClubTests(unittest.TestCase):
    def test_search_returns_all_results_with_short_columns(self):
        with fake_ea(fixture("search")) as fake:
            df = FC27API().search_club_by_name("example")

        self.assertEqual(len(df), 2)
        self.assertEqual(df["clubName"].iat[0], "Example FC")
        self.assertEqual(df["wins"].iat[0], 20)  # "20" (text) became 20 (number)
        self.assertNotIn("clubInfo.customKit.kitId", df.columns)
        self.assertEqual(sent_params(fake), {"platform": "common-gen5", "clubName": "example"})

    def test_all_columns_keeps_ea_names(self):
        with fake_ea(fixture("search")):
            df = FC27API().search_club_by_name("example", all_columns=True)
        self.assertIn("clubInfo.customKit.kitId", df.columns)

    def test_club_details_is_one_row(self):
        with fake_ea(fixture("info")):
            df = FC27API().get_club_details(1001)

        self.assertEqual(len(df), 1)
        self.assertEqual(df["clubName"].iat[0], "Example FC")
        self.assertEqual(df["stadium"].iat[0], "Example Stadium")

    def test_overall_stats_keeps_nulls(self):
        with fake_ea(fixture("overall")):
            df = FC27API().get_club_overall_stats(1001)

        self.assertEqual(df["skillRating"].iat[0], 1500)
        self.assertEqual(df["winStreak"].iat[0], 3)
        self.assertTrue(df["bestDivision"].isna().iat[0])

    def test_members(self):
        with fake_ea(fixture("members")):
            df = FC27API().get_member_stats(1001)
        self.assertEqual(len(df), 2)
        self.assertEqual(df["averageRating"].iat[0], 7.4)

        with fake_ea(fixture("career")):
            self.assertEqual(len(FC27API().get_member_career_stats(1001)), 2)


class FindClubIdTests(unittest.TestCase):
    def test_exact_name_ignoring_case(self):
        with fake_ea(fixture("search")):
            self.assertEqual(FC27API().find_club_id("example fc"), 1001)

    def test_single_result(self):
        with fake_ea(fixture("search")[1:]):
            self.assertEqual(FC27API().find_club_id("example"), 1002)

    def test_ambiguous_lists_options(self):
        with fake_ea(fixture("search")):
            with self.assertRaises(ValueError) as caught:
                FC27API().find_club_id("example")
        self.assertIn("Example FC (id 1001)", str(caught.exception))

    def test_no_result(self):
        with fake_ea([]):
            with self.assertRaises(ValueError):
                FC27API().find_club_id("nothing")


class MatchTests(unittest.TestCase):
    def test_matches_from_club_side(self):
        with fake_ea(fixture("matches")) as fake:
            df = FC27API().get_club_matches(1001)

        # 1: league win (opponent quit), 2: league draw, 3: friendly lost 0-3
        self.assertEqual(list(df["result"]), ["win", "draw", "loss"])
        self.assertEqual(list(df["dnf"]), [True, False, False])
        self.assertEqual(df["opponentId"].iat[0], 2001)
        self.assertEqual(df["goalsAgainst"].iat[2], 3)
        self.assertEqual(str(df["timestamp"].dt.tz), "UTC")
        self.assertEqual(sent_params(fake)["maxResultCount"], "10")

    def test_timezone(self):
        with fake_ea(fixture("matches")):
            df = FC27API(timezone="Europe/Istanbul").get_club_matches(1001)
        # 20:00 UTC is 23:00 in Istanbul (UTC+3)
        self.assertEqual(df["timestamp"].iat[0].hour, 23)

    def test_match_players_own_team_by_default(self):
        with fake_ea(fixture("matches")):
            df = FC27API().get_match_players(1001)
        self.assertEqual(len(df), 3 * 2)  # 3 matches x 2 players (fixtures are trimmed)
        self.assertEqual(set(df["clubId"]), {1001})
        self.assertIn("passesMade", df.columns)

    def test_match_players_both_teams(self):
        with fake_ea(fixture("matches")):
            df = FC27API().get_match_players(1001, both_teams=True)
        self.assertEqual(len(df), 3 * 2 * 2)

    def test_empty_and_null_matches(self):
        for payload in ([], None):
            with fake_ea(payload):
                self.assertTrue(FC27API().get_club_matches(1001, "playoffMatch").empty)
                self.assertTrue(FC27API().get_match_players(1001, "playoffMatch").empty)

    def test_bad_match_type(self):
        with self.assertRaises(ValueError):
            FC27API().get_club_matches(1001, "cupMatch")


class ErrorTests(unittest.TestCase):
    def test_http_error(self):
        error = urllib.error.HTTPError("url", 403, "Forbidden", {}, None)
        with patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(FC27APIError):
                FC27API().get_club_details(1001)

    def test_timeout(self):
        with patch("urllib.request.urlopen", side_effect=TimeoutError("timed out")):
            with self.assertRaises(FC27APIError):
                FC27API().get_club_details(1001)

    def test_not_json(self):
        with patch("urllib.request.urlopen", return_value=io.BytesIO(b"<html>blocked</html>")):
            with self.assertRaises(FC27APIError):
                FC27API().get_club_details(1001)


if __name__ == "__main__":
    unittest.main()
