"""Curated column sets for the ``records`` and ``dataframe`` output formats.

EA returns many fields with inconsistent names (``passesmade``, ``ratingAve``,
``mom``, ...). By default each method keeps only the useful ones and renames them
to consistent camelCase. Format: ``"EA field": "output name"``, in output order.
Pass ``all_columns=True`` to any method to get every field with EA's own names.
"""

from __future__ import annotations

from typing import Dict

SEARCH: Dict[str, str] = {
    "clubId": "clubId",
    "clubName": "clubName",
    "currentDivision": "currentDivision",
    "bestDivision": "bestDivision",
    "gamesPlayed": "gamesPlayed",
    "wins": "wins",
    "ties": "ties",
    "losses": "losses",
    "goals": "goals",
    "goalsAgainst": "goalsAgainst",
    "cleanSheets": "cleanSheets",
    "points": "points",
    "promotions": "promotions",
    "relegations": "relegations",
    "reputationtier": "reputationTier",
}

DETAILS: Dict[str, str] = {
    "clubId": "clubId",
    "name": "clubName",
    "regionId": "regionId",
    "teamId": "teamId",
    "customKit.crestAssetId": "crestAssetId",
    "crestUrl": "crestUrl",
    "customKit.stadName": "stadium",
}

OVERALL: Dict[str, str] = {
    "clubId": "clubId",
    "gamesPlayed": "gamesPlayed",
    "wins": "wins",
    "ties": "ties",
    "losses": "losses",
    "goals": "goals",
    "goalsAgainst": "goalsAgainst",
    "skillRating": "skillRating",
    "wstreak": "winStreak",
    "unbeatenstreak": "unbeatenStreak",
    "promotions": "promotions",
    "relegations": "relegations",
    "bestDivision": "bestDivision",
    "reputationtier": "reputationTier",
}

MEMBERS: Dict[str, str] = {
    "name": "name",
    "proName": "playerName",
    "favoritePosition": "position",
    "proOverall": "overall",
    "gamesPlayed": "gamesPlayed",
    "winRate": "winRate",
    "goals": "goals",
    "assists": "assists",
    "ratingAve": "averageRating",
    "manOfTheMatch": "manOfTheMatch",
    "shotSuccessRate": "shotSuccessRate",
    "passesMade": "passesMade",
    "passSuccessRate": "passSuccessRate",
    "tacklesMade": "tacklesMade",
    "tackleSuccessRate": "tackleSuccessRate",
    "cleanSheetsDef": "cleanSheetsDef",
    "cleanSheetsGK": "cleanSheetsGK",
    "redCards": "redCards",
}

CAREER: Dict[str, str] = {
    "name": "name",
    "favoritePosition": "position",
    "gamesPlayed": "gamesPlayed",
    "goals": "goals",
    "assists": "assists",
    "ratingAve": "averageRating",
    "manOfTheMatch": "manOfTheMatch",
}

PLAYERS: Dict[str, str] = {
    "matchId": "matchId",
    "timestamp": "timestamp",
    "clubId": "clubId",
    "playerId": "playerId",
    "playername": "name",
    "pos": "position",
    "rating": "rating",
    "goals": "goals",
    "assists": "assists",
    "shots": "shots",
    "passesmade": "passesMade",
    "passattempts": "passAttempts",
    "tacklesmade": "tacklesMade",
    "tackleattempts": "tackleAttempts",
    "saves": "saves",
    "cleansheetsany": "cleanSheet",
    "mom": "manOfTheMatch",
    "redcards": "redCards",
    "secondsPlayed": "secondsPlayed",
}
