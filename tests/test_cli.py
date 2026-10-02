"""The fc-clubs command line."""

import json

import pytest
from conftest import fixture

from fc_clubs_api import __main__ as cli


@pytest.fixture
def fake_api(monkeypatch):
    responses = {
        "allTimeLeaderboard/search": fixture("search"),
        "clubs/matches": fixture("matches"),
        "members/stats": fixture("members"),
    }
    monkeypatch.setattr(
        cli.FC27API, "get_json", lambda self, endpoint, params=None: responses[endpoint]
    )


def test_json_output(fake_api, capsys):
    assert cli.main(["Example FC", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["clubId"] == 1001
    assert payload["matches"][0]["result"] == "win"
    assert payload["members"][0]["name"] == "Player1"


def test_table_output(fake_api, capsys):
    pytest.importorskip("pandas")
    assert cli.main(["1001"]) == 0
    out = capsys.readouterr().out
    assert "Opponent A" in out and "Player1" in out


def test_ambiguous_name_exits_with_error(fake_api, capsys):
    assert cli.main(["example", "--json"]) == 1
    assert "2 clubs match" in capsys.readouterr().err
