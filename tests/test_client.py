"""Endpoint methods, checked in the ``records`` format (runs without pandas)."""

import pytest
from conftest import fake_ea, fixture, sent_request

from fc_clubs_api import FC27API, LeaderboardScope, MatchType
from fc_clubs_api.assets import CREST_URL_TEMPLATE


@pytest.fixture
def api():
    return FC27API(output="records")


# ----------------------------------------------------------------- clubs


def test_search_returns_all_results_with_short_columns(api):
    with fake_ea(fixture("search")) as fake:
        rows = api.search_club_by_name("example")

    assert len(rows) == 2
    assert rows[0]["clubName"] == "Example FC"
    assert rows[0]["wins"] == 20  # "20" (text) became 20 (number)
    assert rows[0]["reputationTier"] == 1
    assert "clubInfo.customKit.kitId" not in rows[0]
    assert sent_request(fake) == (
        "allTimeLeaderboard/search",
        {"platform": "common-gen5", "clubName": "example"},
    )


def test_search_current_season_and_max_result_count(api):
    with fake_ea(fixture("search_current_season")) as fake:
        rows = api.search_club_by_name(
            "example", scope=LeaderboardScope.CURRENT_SEASON, max_result_count=10
        )

    endpoint, params = sent_request(fake)
    assert endpoint == "currentSeasonLeaderboard/search"
    assert params["maxResultCount"] == "10"
    assert rows[0]["points"] == 22
    # selectedKitType "1" means a custom crest, so crestAssetId wins over teamId.
    assert rows[0]["crestUrl"] == CREST_URL_TEMPLATE.format(id=99000001)


def test_search_scope_accepts_plain_string(api):
    with fake_ea([]) as fake:
        assert api.search_club_by_name("x", scope="current_season") == []
    assert sent_request(fake)[0] == "currentSeasonLeaderboard/search"


def test_search_rejects_unknown_scope(api):
    with pytest.raises(ValueError, match="scope"):
        api.search_club_by_name("x", scope="weekly")


def test_all_columns_keeps_ea_names(api):
    with fake_ea(fixture("search")):
        rows = api.search_club_by_name("example", all_columns=True)
    assert "clubInfo.customKit.kitId" in rows[0]
    assert "crestUrl" in rows[0]


def test_club_details_is_one_row(api):
    with fake_ea(fixture("info")) as fake:
        rows = api.get_club_details(1001)

    assert len(rows) == 1
    assert rows[0]["clubName"] == "Example FC"
    assert rows[0]["stadium"] == "Example Stadium"
    assert rows[0]["crestUrl"] == CREST_URL_TEMPLATE.format(id=100)  # real badge: teamId
    assert sent_request(fake) == ("clubs/info", {"platform": "common-gen5", "clubIds": "1001"})


def test_overall_stats_keeps_nulls(api):
    with fake_ea(fixture("overall")):
        row = api.get_club_overall_stats(1001)[0]

    assert row["skillRating"] == 1500
    assert row["winStreak"] == 3
    assert row["bestDivision"] is None


def test_playoff_achievements_empty(api):
    with fake_ea([]):
        assert api.get_playoff_achievements(1001) == []


# --------------------------------------------------------------- members


def test_members(api):
    with fake_ea(fixture("members")) as fake:
        rows = api.get_member_stats(1001)
    assert len(rows) == 2
    assert rows[0]["averageRating"] == 7.4
    assert sent_request(fake)[1]["clubId"] == "1001"


def test_member_career_curated_and_all_columns(api):
    with fake_ea(fixture("career")):
        rows = api.get_member_career_stats(1001)
        full = api.get_member_career_stats(1001, all_columns=True)
    assert len(rows) == 2
    assert rows[0]["averageRating"] == 7.3
    assert "ratingAve" in full[0]
    assert "proPos" not in rows[0]


def test_members_null_response(api):
    with fake_ea(None):
        assert api.get_member_stats(1001) == []


# ------------------------------------------------------------ find_club_id


def test_find_club_id_exact_name_ignoring_case(api):
    with fake_ea(fixture("search")):
        assert api.find_club_id("example fc") == 1001


def test_find_club_id_single_result(api):
    with fake_ea(fixture("search")[1:]):
        assert api.find_club_id("example") == 1002


def test_find_club_id_ambiguous_lists_options(api):
    with fake_ea(fixture("search")), pytest.raises(ValueError) as caught:
        api.find_club_id("example")
    assert "Example FC (id 1001)" in str(caught.value)


def test_find_club_id_no_result(api):
    with fake_ea([]), pytest.raises(ValueError):
        api.find_club_id("nothing")


# --------------------------------------------------------------- matches


def test_matches_from_club_side(api):
    with fake_ea(fixture("matches")) as fake:
        rows = api.get_club_matches(1001)

    # 1: league win (opponent quit), 2: league draw, 3: friendly lost 0-3
    assert [row["result"] for row in rows] == ["win", "draw", "loss"]
    assert [row["dnf"] for row in rows] == [True, False, False]
    assert rows[0]["opponentId"] == 2001
    assert rows[2]["goalsAgainst"] == 3
    assert rows[0]["timestamp"].utcoffset().total_seconds() == 0
    assert rows[0]["crestUrl"] == CREST_URL_TEMPLATE.format(id=100)  # from TEAM
    params = sent_request(fake)[1]
    assert params["maxResultCount"] == "10"
    assert params["matchType"] == "leagueMatch"


def test_match_type_enum(api):
    with fake_ea([]) as fake:
        api.get_club_matches(1001, MatchType.FRIENDLY)
    assert sent_request(fake)[1]["matchType"] == "friendlyMatch"


def test_timezone(api):
    with fake_ea(fixture("matches")):
        rows = FC27API(timezone="Europe/Istanbul", output="records").get_club_matches(1001)
    # 20:00 UTC is 23:00 in Istanbul (UTC+3)
    assert rows[0]["timestamp"].hour == 23


def test_unknown_timezone_is_rejected():
    with pytest.raises(ValueError, match="timezone"):
        FC27API(timezone="Mars/Olympus")


def test_match_players_own_team_by_default(api):
    with fake_ea(fixture("matches")):
        rows = api.get_match_players(1001)
    assert len(rows) == 3 * 2  # 3 matches x 2 players (fixtures are trimmed)
    assert {row["clubId"] for row in rows} == {1001}
    assert "passesMade" in rows[0]
    assert "passesCompletedForward" not in rows[0]


def test_match_players_both_teams(api):
    with fake_ea(fixture("matches")):
        rows = api.get_match_players(1001, both_teams=True)
    assert len(rows) == 3 * 2 * 2


def test_match_players_include_events(api):
    with fake_ea(fixture("matches")):
        rows = api.get_match_players(1001, include_events=True)

    # Player2 in the second match: 215:7, 30:2, 32:2, 34:3, and 97:14 in bucket 1
    row = next(r for r in rows if r["matchId"] == 1000000000002 and r["name"] == "Player2")
    assert row["passesCompleted"] == row["passesMade"] == 7
    assert row["passesCompletedForward"] == 2
    assert row["passesCompletedDirectionUnknown"] == 0
    assert row["dribblesCarried"] == 14
    assert row["yellowCards"] == 1


def test_empty_and_null_matches(api):
    for payload in ([], None):
        with fake_ea(payload):
            assert api.get_club_matches(1001, "playoffMatch") == []
            assert api.get_match_players(1001, "playoffMatch") == []


def test_bad_match_type(api):
    with pytest.raises(ValueError, match="match_type"):
        api.get_club_matches(1001, "cupMatch")


# ----------------------------------------------------------------- misc


def test_get_json_adds_platform_and_custom_headers():
    api = FC27API(headers={"user-agent": "my-bot/1.0"})
    with fake_ea({"ok": True}) as fake:
        assert api.get_json("some/endpoint", {"a": 1}) == {"ok": True}
    request = fake.call_args[0][0]
    assert request.get_header("User-agent") == "my-bot/1.0"
    assert request.get_header("Sec-fetch-site") == "same-origin"  # defaults kept
    assert sent_request(fake) == ("some/endpoint", {"platform": "common-gen5", "a": "1"})


def test_repr():
    assert "output='records'" in repr(FC27API(output="records"))
