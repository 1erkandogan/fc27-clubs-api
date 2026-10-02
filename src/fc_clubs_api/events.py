"""Decode the per-player match event counters into named stats.

Every player in a ``clubs/matches`` response carries ``match_event_aggregate_0``
to ``match_event_aggregate_3``: comma-separated ``event_id:count`` pairs such as
``"215:21,216:5,30:8"``. EA does not document the event ids.

The mapping below comes from the community research at
https://github.com/Interactive-63/eafc-pro-clubs-api-research (FC 27, validated
against ~51,000 player-match rows). Only mappings that research rates as
**confirmed / high confidence** are decoded here. Partial and exploratory
mappings are listed in ``docs/match-events.md`` but deliberately not decoded.

Example:
    >>> from fc_clubs_api.events import parse_event_aggregates, decode_events
    >>> player = {"match_event_aggregate_0": "215:21,216:5,30:8", "match_event_aggregate_1": ""}
    >>> parse_event_aggregates(player)
    {215: 21, 216: 5, 30: 8}
    >>> decode_events(player)["passesCompletedForward"]
    8
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Tuple

AGGREGATE_PREFIX = "match_event_aggregate_"

SOURCE_URL = "https://github.com/Interactive-63/eafc-pro-clubs-api-research"


@dataclass(frozen=True)
class EventStat:
    """A named stat computed from event counters.

    The value is ``sum(add) - sum(subtract)``, floored at 0 when ``subtract`` is
    used (derived "remainder" stats can't go negative).

    Attributes:
        name: Output column name (camelCase).
        description: What the stat counts, with any caveat from the research.
        add: Event ids whose counts are added.
        subtract: Event ids whose counts are subtracted.
    """

    name: str
    description: str
    add: Tuple[int, ...]
    subtract: Tuple[int, ...] = ()

    def compute(self, counts: Mapping[int, int]) -> int:
        """Evaluate the stat for one player's parsed event counts."""
        value = sum(counts.get(event, 0) for event in self.add)
        if self.subtract:
            value -= sum(counts.get(event, 0) for event in self.subtract)
            value = max(0, value)
        return value

    @property
    def formula(self) -> str:
        """Human-readable formula, e.g. ``event_215 - (event_30 + event_32)``."""

        def terms(events: Tuple[int, ...]) -> str:
            joined = " + ".join(f"event_{event}" for event in events)
            return f"({joined})" if len(events) > 1 else joined

        text = " + ".join(f"event_{event}" for event in self.add)
        if self.subtract:
            text = f"max(0, {text} - {terms(self.subtract)})"
        return text


def _stat(name: str, description: str, *add: int, minus: Tuple[int, ...] = ()) -> EventStat:
    return EventStat(name=name, description=description, add=add, subtract=minus)


#: Confirmed / high-confidence stats, in documentation order.
EVENT_STATS: Tuple[EventStat, ...] = (
    # Passing: totals, direction and length
    _stat("passesCompleted", "Passes completed (excludes offside passes)", 215),
    _stat("passesFailed", "Passes failed", 216),
    _stat("passesCompletedForward", "Completed passes played forward", 30),
    _stat("passesCompletedBackward", "Completed passes played backward", 32),
    _stat("passesCompletedSideways", "Completed passes played sideways", 34),
    _stat(
        "passesCompletedDirectionUnknown",
        "Completed passes with no direction event",
        215,
        minus=(30, 32, 34),
    ),
    _stat("passesCompletedShort", "Completed short passes", 24),
    _stat("passesCompletedMedium", "Completed medium passes", 26),
    _stat("passesCompletedLong", "Completed long passes", 28),
    _stat("passesCompletedCross", "Completed crosses (includes set pieces)", 36),
    _stat(
        "passesCompletedLengthUnknown",
        "Completed passes with no length event",
        215,
        minus=(24, 26, 28, 36),
    ),
    _stat("passesFailedForward", "Failed passes played forward", 31),
    _stat("passesFailedBackward", "Failed passes played backward", 33),
    _stat("passesFailedSideways", "Failed passes played sideways", 35),
    _stat(
        "passesFailedDirectionUnknown",
        "Failed passes with no direction event",
        216,
        minus=(31, 33, 35),
    ),
    _stat("passesFailedShort", "Failed short passes", 25),
    _stat("passesFailedMedium", "Failed medium passes", 27),
    _stat("passesFailedLong", "Failed long passes", 29),
    _stat("passesFailedCross", "Failed crosses (open play only)", 37),
    _stat(
        "passesFailedLengthUnknown",
        "Failed passes with no length event",
        216,
        minus=(25, 27, 29, 37),
    ),
    _stat("firstTimePasses", "First-time passes", 143),
    _stat("switchesOfPlay", "Switch-of-play passes", 144),
    _stat("flairPasses", "Fancy / flair passes", 147),
    _stat("throughPasses", "Successful through balls", 152),
    _stat("offsidePasses", "Passes caught offside", 153),
    # Shooting and goals
    _stat("shots", "Shots (on + off target)", 217, 218),
    _stat("shotsOnTarget", "Shots on target (blocked shots can fold in)", 217),
    _stat("shotsOnTargetInsideBox", "Shots on target from inside the box", 13),
    _stat("shotsOnTargetOutsideBox", "Shots on target from outside the box", 18),
    _stat("shotsOffTarget", "Shots off target", 218),
    _stat("shotsOffTargetInsideBox", "Shots off target from inside the box", 14),
    _stat("shotsOffTargetOutsideBox", "Shots off target from outside the box", 19),
    _stat("shotsSaved", "Shots saved", 202),
    _stat("goals", "Goals", 214),
    _stat("goalsFirstTime", "Goals from first-time shots (a tag, not a partition)", 128),
    _stat("goalsWeakFoot", "Goals with the weak foot (a tag, not a partition)", 131),
    _stat("goalsOffPost", "Goals in off the post (a tag, not a partition)", 136),
    _stat("assists", "Assists", 11),
    _stat("secondAssists", "Second assists", 115),
    _stat("throughBallAssists", "Assists from through balls (a tag, not a partition)", 118),
    # Dribbling
    _stat("dribblesCompleted", "Dribbles completed", 174),
    _stat("dribblesCarried", "Dribbles carried", 97),
    _stat("dribblesBeat", "Players beaten without a skill move", 112, minus=(38,)),
    _stat("dribblesSkillMoveBeat", "Players beaten with a skill move", 38),
    # Defending
    _stat("tacklesWon", "Tackles won", 0),
    _stat("tacklesLost", "Tackles lost", 1),
    _stat("standingTacklesWon", "Standing tackles won", 229),
    _stat("slidingTacklesWon", "Sliding tackles won", 230),
    _stat("cleanTackles", "Successful tackles on the ball", 164),
    _stat("dangerousTackles", "Dangerous tackles", 163),
    _stat("interceptions", "Interceptions", 6),
    _stat("opponentsDispossessed", "Opponents dispossessed", 158),
    _stat("crossesBlocked", "Crosses blocked", 156),
    _stat("aerialDuelsWonAttacking", "Aerial duels won when attacking", 265),
    _stat("aerialDuelsWonDefending", "Aerial duels won when defending", 266),
    _stat("goodDirectionSaves", "Saves diving the right way", 267),
    # Possession
    _stat("possessionLostDefensiveThird", "Possession lost in the defensive third", 105),
    _stat("possessionLostMiddleThird", "Possession lost in the middle third", 106),
    _stat("possessionLostAttackingThird", "Possession lost in the attacking third", 107),
    _stat("possessionWonDefensiveThird", "Possession won in the defensive third", 108),
    _stat("possessionWonMiddleThird", "Possession won in the middle third", 109),
    _stat("possessionWonAttackingThird", "Possession won in the attacking third", 110),
    # Discipline and set pieces
    _stat("foulsConceded", "Fouls conceded, all areas", 2, 3),
    _stat("foulsConcededDefensiveThird", "Fouls conceded around the defensive third", 3),
    _stat("foulsWon", "Times this player was fouled", 4),
    _stat("yellowCards", "Yellow cards (immediate + delayed)", 95, 213),
    _stat("yellowCardsImmediate", "Yellow cards shown as play stopped", 95),
    _stat("yellowCardsDelayed", "Yellow cards shown after advantage was played", 213),
    _stat("penaltiesConceded", "Penalties conceded", 94),
    _stat("cornersConceded", "Corners conceded", 10),
    _stat("cornersTaken", "Corners taken", 145),
    # Positioning and in-game feedback
    _stat("inPosition", "Times the feedback praised this player's positioning", 111),
    _stat("outOfPosition", "Times out of position, any severity", 219),
    _stat("outOfPositionSeverity1", "Out of position, severity 1 of 5", 99),
    _stat("outOfPositionSeverity2", "Out of position, severity 2 of 5", 100),
    _stat("outOfPositionSeverity3", "Out of position, severity 3 of 5", 101),
    _stat("outOfPositionSeverity4", "Out of position, severity 4 of 5", 102),
    _stat("outOfPositionSeverity5", "Out of position, severity 5 of 5", 103),
    _stat("feedbackUseTheBall", "Feedback: 'Use the ball'", 212),
    _stat("feedbackPickYourPass", "Feedback: 'Pick your pass'", 207),
    _stat("feedbackNoGoodOption", "Feedback: 'No good option'", 175),
    _stat("feedbackGoodOptionTaken", "Feedback: 'Good option taken'", 176),
    _stat("feedbackBestOptionTaken", "Feedback: 'Best option taken'", 177),
    _stat("feedbackShouldHavePassedElsewhere", "Feedback: 'Should have passed elsewhere'", 182),
    _stat("feedbackChoseToPass", "Feedback: 'Chose to pass'", 183),
)


def parse_event_aggregates(player: Mapping[str, Any]) -> Dict[int, int]:
    """Merge a player's ``match_event_aggregate_*`` strings into ``{event_id: count}``.

    Works on a raw player dict from ``clubs/matches`` (or any dict that has the
    aggregate fields). Empty buckets are skipped, ids appearing in several
    buckets are summed, and malformed pairs are ignored. An id that is absent
    means a count of 0.
    """
    counts: Dict[int, int] = {}
    for key, value in player.items():
        if not key.startswith(AGGREGATE_PREFIX) or not isinstance(value, str):
            continue
        for pair in value.split(","):
            event, sep, count = pair.partition(":")
            if not sep:
                continue
            try:
                event_id, number = int(event), int(count)
            except ValueError:
                continue
            counts[event_id] = counts.get(event_id, 0) + number
    return counts


def decode_events(player: Mapping[str, Any]) -> Dict[str, int]:
    """Return every stat in :data:`EVENT_STATS` for one player, by name.

    Args:
        player: A raw player dict from ``clubs/matches`` (with the
            ``match_event_aggregate_*`` fields), or an already parsed
            ``{event_id: count}`` mapping from :func:`parse_event_aggregates`.
    """
    if any(isinstance(key, int) for key in player):
        counts: Mapping[int, int] = player  # type: ignore[assignment]
    else:
        counts = parse_event_aggregates(player)
    return {stat.name: stat.compute(counts) for stat in EVENT_STATS}
