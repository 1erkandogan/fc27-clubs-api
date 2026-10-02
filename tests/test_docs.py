"""Keep the documentation in step with the code."""

from pathlib import Path

from fc_clubs_api.events import EVENT_STATS

DOCS = Path(__file__).resolve().parent.parent / "docs"


def test_every_decoded_event_stat_is_documented():
    text = (DOCS / "match-events.md").read_text(encoding="utf-8")
    for stat in EVENT_STATS:
        assert f"| `{stat.name}` | `{stat.formula}` |" in text, stat.name
