"""The three output formats: raw, records and dataframe."""

import pytest
from conftest import fake_ea, fixture

from fc_clubs_api import FC27API, OutputFormat


def test_raw_is_untouched():
    with fake_ea(fixture("info")):
        assert FC27API(output="raw").get_club_details(1001) == fixture("info")
    with fake_ea(fixture("matches")):
        raw = FC27API().get_match_players(1001, output=OutputFormat.RAW, include_events=True)
    assert raw == fixture("matches")


def test_raw_null_becomes_empty_list():
    with fake_ea(None):
        assert FC27API(output="raw").get_club_matches(1001) == []


def test_records_are_rectangular():
    with fake_ea(fixture("matches")):
        rows = FC27API(output="records").get_match_players(1001, both_teams=True, all_columns=True)
    keys = set(rows[0])
    assert all(set(row) == keys for row in rows)


def test_per_call_override_beats_client_default():
    api = FC27API(output="raw")
    with fake_ea(fixture("overall")):
        assert isinstance(api.get_club_overall_stats(1001, output="records")[0], dict)
        assert api.get_club_overall_stats(1001) == fixture("overall")


def test_invalid_output_name():
    with pytest.raises(ValueError, match="output must be one of"):
        FC27API(output="json")
    with pytest.raises(ValueError, match="output must be one of"):
        FC27API().get_club_details(1001, output="csv")


def test_output_format_is_a_string():
    assert OutputFormat.RECORDS == "records"
    assert str(OutputFormat.DATAFRAME) == "dataframe"


@pytest.mark.parametrize(
    "method, fixture_name, kwargs",
    [
        ("search_club_by_name", "search", {}),
        ("get_club_details", "info", {}),
        ("get_club_overall_stats", "overall", {}),
        ("get_member_stats", "members", {}),
        ("get_member_career_stats", "career", {}),
        ("get_club_matches", "matches", {}),
        ("get_match_players", "matches", {"include_events": True}),
    ],
)
def test_dataframe_matches_records(method, fixture_name, kwargs):
    pd = pytest.importorskip("pandas")
    api = FC27API(timezone="Europe/Istanbul")
    arg = "example" if method == "search_club_by_name" else 1001
    with fake_ea(fixture(fixture_name)):
        records = getattr(api, method)(arg, output="records", **kwargs)
        df = getattr(api, method)(arg, output="dataframe", **kwargs)

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == list(records[0])
    assert len(df) == len(records)
    for column in df.columns:
        expected = records[0][column]
        actual = df[column].iat[0]
        if expected is None:
            assert pd.isna(actual)
        else:
            assert actual == expected, column


def test_dataframe_types_and_timezone():
    pytest.importorskip("pandas")
    with fake_ea(fixture("matches")):
        df = FC27API(output="dataframe").get_club_matches(1001)
    assert str(df["timestamp"].dt.tz) == "UTC"
    assert df["goals"].dtype.kind == "i"


def test_empty_dataframe():
    pd = pytest.importorskip("pandas")
    with fake_ea([]):
        df = FC27API(output="dataframe").get_club_matches(1001, "playoffMatch")
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_missing_pandas_fails_before_any_request(no_pandas):
    message = r"fc-clubs-api\[pandas\]"
    with fake_ea(fixture("info")) as fake, pytest.raises(ImportError, match=message):
        FC27API(output="dataframe").get_club_details(1001)
    fake.assert_not_called()


def test_default_output_is_records_without_pandas(no_pandas):
    api = FC27API()
    assert api.output is OutputFormat.RECORDS
    with fake_ea(fixture("info")):
        rows = api.get_club_details(1001)
    assert isinstance(rows, list)
    assert rows[0]["clubId"] == 1001


def test_records_and_raw_work_without_pandas(no_pandas):
    with fake_ea(fixture("info")):
        assert FC27API(output="records").get_club_details(1001)[0]["clubId"] == 1001
        assert FC27API(output="raw").get_club_details(1001) == fixture("info")
