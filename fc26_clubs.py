from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import fc26_api_class as fc26class


def _pick(row: Dict[str, Any], *keys: str) -> Optional[Any]:
    """Return the first truthy value from the provided keys."""
    for key in keys:
        if key in row and row[key] not in (None, "", []):
            return row[key]
    return None


def _to_datetime(value: Any) -> Optional[datetime]:
    """Normalize pandas timestamp or datetime-like values into datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    to_python = getattr(value, "to_pydatetime", None)
    if callable(to_python):
        return to_python()
    return None


def _to_int(value: Any) -> Optional[int]:
    """Safely convert a numeric-like value into an int."""
    if value in (None, "", []):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@dataclass
class Club:
    """
    Lightweight representation of a Pro Clubs team with metadata fetched
    via the FC26 API client.
    """

    name: str
    api: fc26class.FC26_API = field(default_factory=fc26class.FC26_API)
    club_id: str = field(init=False)
    club_name: Optional[str] = field(init=False, default=None)
    abbreviation: Optional[str] = field(init=False, default=None)
    region_id: Optional[int] = field(init=False, default=None)
    skill_rating: Optional[int] = field(init=False, default=None)
    total_members: Optional[int] = field(init=False, default=None)
    wins: Optional[int] = field(init=False, default=None)
    losses: Optional[int] = field(init=False, default=None)
    draws: Optional[int] = field(init=False, default=None)
    overall_record: Optional[str] = field(init=False, default=None)

    def __post_init__(self) -> None:
        self._hydrate_from_search()
        self._hydrate_from_details()

    def _hydrate_from_search(self) -> None:
        """Populate base information using the search endpoint."""
        search_df = self.api.search_club_by_name(self.name)
        if search_df is None or search_df.empty:
            raise ValueError(f"Club '{self.name}' was not found in the FC26 API.")

        search_row = search_df.iloc[0].to_dict()
        self.club_id = str(_pick(search_row, "clubId", "clubID"))
        if not self.club_id:
            raise ValueError(f"Club '{self.name}' search response missing clubId.")

        self.club_name = _pick(search_row, "clubInfoclubName", "clubName", "name")
        self.abbreviation = _pick(search_row, "clubInfoabbrevName", "abbrevName")
        self.region_id = _to_int(_pick(search_row, "clubInforegionId", "regionId"))
        self.skill_rating = _to_int(_pick(search_row, "clubInfskillRating", "skillRating"))
        self.total_members = _to_int(_pick(search_row, "clubInfomemberCount", "memberCount"))

    def _hydrate_from_details(self) -> None:
        """Populate season/record data using the club details endpoint."""
        details_df = self.api.get_club_details(self.club_id)
        if details_df is None or details_df.empty:
            return

        detail_row = details_df.iloc[0].to_dict()
        self.wins = _to_int(_pick(detail_row, "wins", "seasonWins", "allWins"))
        self.losses = _to_int(_pick(detail_row, "losses", "seasonLosses", "allLosses"))
        self.draws = _to_int(_pick(detail_row, "ties", "seasonDraws", "seasonTies"))
        self.overall_record = detail_row.get("record") or self._format_record()

    def _format_record(self) -> Optional[str]:
        if None in (self.wins, self.losses, self.draws):
            return None
        return f"{self.wins}-{self.losses}-{self.draws}"


@dataclass
class ClubMatch:
    """Simple DTO holding metadata about a single match."""

    match_id: Optional[str]
    timestamp: Optional[datetime]
    match_type: Optional[str]
    result: Optional[str]
    goals_for: Optional[int]
    goals_against: Optional[int]
    opponent_id: Optional[str]
    opponent_name: Optional[str]
    raw: Dict[str, Any] = field(repr=False, default_factory=dict)


@dataclass
class Matches:
    """
    Convenience wrapper for fetching recent matches for a club and exposing
    a list of typed match summaries.
    """

    club: Club
    match_type: str = "friendlyMatch"
    api: Optional[fc26class.FC26_API] = None
    fixtures: List[ClubMatch] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        if self.api is None:
            self.api = self.club.api
        self._hydrate_matches()

    def _hydrate_matches(self) -> None:
        matches_df = self.api.get_club_matches(self.club.club_id, match_type=self.match_type)
        if matches_df is None or matches_df.empty:
            return
        for _, row in matches_df.iterrows():
            row_dict = row.to_dict()
            opponent_id, opponent_payload = self._find_opponent(row_dict.get("clubs", {}))
            our_payload = self._extract_club_payload(row_dict.get("clubs", {}))
            self.fixtures.append(
                ClubMatch(
                    match_id=str(row_dict.get("matchId") or row_dict.get("id") or ""),
                    timestamp=_to_datetime(row_dict.get("timestamp")),
                    match_type=row_dict.get("matchType", self.match_type),
                    result=our_payload.get("result") or row_dict.get("winner"),
                    goals_for=_to_int(our_payload.get("goals")),
                    goals_against=_to_int(opponent_payload.get("goals") if opponent_payload else None),
                    opponent_id=opponent_id,
                    opponent_name=(opponent_payload or {}).get("name"),
                    raw=row_dict,
                )
            )

    def _extract_club_payload(self, clubs_payload: Any) -> Dict[str, Any]:
        """Return the payload that corresponds to our club."""
        if not isinstance(clubs_payload, dict):
            return {}
        return clubs_payload.get(self.club.club_id, {})

    def _find_opponent(self, clubs_payload: Any) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Return (opponent_id, opponent_payload) for the first non-club entry."""
        if not isinstance(clubs_payload, dict):
            return (None, None)
        for club_id, payload in clubs_payload.items():
            if club_id != self.club.club_id:
                return (club_id, payload or {})
        return (None, None)
