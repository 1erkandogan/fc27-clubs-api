"""Decoding match_event_aggregate_* into named stats."""

import pytest

from fc_clubs_api.events import EVENT_STATS, EventStat, decode_events, parse_event_aggregates


def test_parse_merges_buckets_and_skips_empty():
    player = {
        "match_event_aggregate_0": "215:7,30:2,6:1",
        "match_event_aggregate_1": "97:14,6:2",
        "match_event_aggregate_2": "",
        "match_event_aggregate_3": "",
        "goals": "1",
    }
    assert parse_event_aggregates(player) == {215: 7, 30: 2, 6: 3, 97: 14}


def test_parse_ignores_malformed_pairs():
    assert parse_event_aggregates({"match_event_aggregate_0": "1:2,oops,3:x,,4:5"}) == {1: 2, 4: 5}


def test_decode_derived_stats():
    counts = {215: 10, 30: 4, 32: 1, 34: 2, 112: 3, 38: 1, 217: 2, 218: 3, 95: 1, 213: 1}
    stats = decode_events(counts)
    assert stats["passesCompletedDirectionUnknown"] == 3  # 10 - (4 + 1 + 2)
    assert stats["dribblesBeat"] == 2  # 112 - 38
    assert stats["shots"] == 5
    assert stats["yellowCards"] == 2
    assert stats["interceptions"] == 0  # absent id = 0


def test_remainders_never_negative():
    assert decode_events({215: 1, 30: 5})["passesCompletedDirectionUnknown"] == 0


def test_decode_accepts_raw_player_dict():
    assert decode_events({"match_event_aggregate_0": "214:2"})["goals"] == 2


def test_every_stat_is_named_once():
    names = [stat.name for stat in EVENT_STATS]
    assert len(names) == len(set(names))
    assert all(isinstance(stat, EventStat) and stat.description for stat in EVENT_STATS)


@pytest.mark.parametrize(
    "name, formula",
    [
        ("passesCompleted", "event_215"),
        ("shots", "event_217 + event_218"),
        ("dribblesBeat", "max(0, event_112 - event_38)"),
        ("passesCompletedDirectionUnknown", "max(0, event_215 - (event_30 + event_32 + event_34))"),
    ],
)
def test_formula_text(name, formula):
    stat = next(stat for stat in EVENT_STATS if stat.name == name)
    assert stat.formula == formula
