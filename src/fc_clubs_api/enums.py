"""Enumerations for the values EA accepts.

Each enum subclasses ``str``, so a member can be passed anywhere the plain string
is accepted and compares equal to it (``MatchType.LEAGUE == "leagueMatch"``).
"""

from __future__ import annotations

from enum import Enum


class MatchType(str, Enum):
    """The ``matchType`` parameter of ``clubs/matches``."""

    LEAGUE = "leagueMatch"
    FRIENDLY = "friendlyMatch"
    PLAYOFF = "playoffMatch"

    def __str__(self) -> str:
        return self.value


class LeaderboardScope(str, Enum):
    """Which leaderboard :meth:`FC27API.search_club_by_name` searches."""

    ALL_TIME = "all_time"
    """``allTimeLeaderboard/search``: totals across every season."""

    CURRENT_SEASON = "current_season"
    """``currentSeasonLeaderboard/search``: totals for the running season only."""

    def __str__(self) -> str:
        return self.value


class Platform(str, Enum):
    """The ``platform`` parameter. Only ``common-gen5`` has been verified for FC 27."""

    GEN5 = "common-gen5"
    """PS5, Xbox Series X|S and PC (cross-play)."""

    def __str__(self) -> str:
        return self.value
