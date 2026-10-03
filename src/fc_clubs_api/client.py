"""The :class:`FC27API` client."""

from __future__ import annotations

import datetime as _dt
from typing import Any, Callable, Dict, List, Mapping, Optional, Union
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from . import _columns
from ._http import HEADERS, request_json
from ._normalize import Record, coerce_numbers, convert_timestamps, flatten, select_columns
from ._output import OutputFormat, OutputLike, import_pandas, resolve_output, to_dataframe
from .assets import club_crest_url
from .enums import LeaderboardScope, MatchType, Platform
from .events import EVENT_STATS, decode_events
from .exceptions import AmbiguousClubError, ClubNotFoundError

ClubId = Union[int, str]
TimezoneLike = Union[str, _dt.tzinfo]

_SEARCH_ENDPOINTS = {
    LeaderboardScope.ALL_TIME: "allTimeLeaderboard/search",
    LeaderboardScope.CURRENT_SEASON: "currentSeasonLeaderboard/search",
}


def _to_tzinfo(timezone: TimezoneLike) -> _dt.tzinfo:
    if isinstance(timezone, _dt.tzinfo):
        return timezone
    if timezone.upper() == "UTC":
        return _dt.timezone.utc
    try:
        return ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError(f"Unknown timezone {timezone!r}, e.g. use 'Europe/London'") from None


def _crest_for(info: Mapping[str, Any], team: Any = None) -> str:
    """Best crest URL for a club info object (``clubs/info`` shape)."""
    kit = info.get("customKit") or {}
    return club_crest_url(
        team=team,
        team_id=info.get("teamId"),
        crest_asset_id=kit.get("crestAssetId"),
        selected_kit_type=kit.get("selectedKitType"),
    )


class FC27API:
    """Client for EA Sports FC 27's Pro Clubs API.

    Every data method can return three formats, chosen with ``output`` on the
    client (the default for all calls) or on any single call:

    * ``"raw"``: EA's JSON exactly as received.
    * ``"records"``: a list of clean, typed, flat dicts (no pandas needed).
    * ``"dataframe"``: a pandas DataFrame with the same columns as ``records``.

    Args:
        platform: EA platform id. ``"common-gen5"`` (PS5 / Xbox Series / PC) is
            the only one verified for FC 27.
        timeout: Seconds to wait for EA before raising
            :class:`~fc_clubs_api.FC27ConnectionError`.
        timezone: IANA name (``"Europe/Istanbul"``) or ``tzinfo`` used for match
            timestamps in ``records``/``dataframe`` output. Default UTC.
        output: Default output format: ``"records"`` (default), ``"dataframe"``
            or ``"raw"``, or an :class:`~fc_clubs_api.OutputFormat`.
        headers: Extra or replacement HTTP headers, merged over the built-in
            browser-like headers EA requires.

    Example:
        ```python
        api = FC27API(output="records", timezone="Europe/London")
        club_id = api.find_club_id("Example FC")
        latest = api.get_club_matches(club_id)[0]
        print(latest["opponentName"], latest["result"])
        ```
    """

    def __init__(
        self,
        platform: Union[Platform, str] = Platform.GEN5,
        timeout: float = 10,
        timezone: TimezoneLike = "UTC",
        output: OutputLike = OutputFormat.RECORDS,
        headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        self.platform = str(platform)
        self.timeout = timeout
        self.timezone = timezone
        self.output = resolve_output(output, OutputFormat.RECORDS)
        self.headers: Dict[str, str] = {**HEADERS, **(headers or {})}

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(platform={self.platform!r}, timeout={self.timeout!r}, "
            f"timezone={self._timezone!r}, output={self.output.value!r})"
        )

    @property
    def timezone(self) -> TimezoneLike:
        """Timezone for match timestamps (as passed in)."""
        return self._timezone

    @timezone.setter
    def timezone(self, value: TimezoneLike) -> None:
        self._tzinfo = _to_tzinfo(value)
        self._timezone = value

    # ------------------------------------------------------------------ core

    def get_json(self, endpoint: str, params: Optional[Mapping[str, Any]] = None) -> Any:
        """GET any endpoint and return EA's JSON untouched.

        The escape hatch for endpoints or parameters this client doesn't wrap.
        ``platform`` is added automatically.

        Example:
            ```python
            api.get_json("clubs/info", {"clubIds": 1001})
            # {"1001": {"name": "Example FC", "clubId": 1001, ...}}
            ```

        Raises:
            FC27APIError: EA could not be reached, refused, or sent non-JSON.
        """
        query: Dict[str, Any] = {"platform": self.platform}
        query.update(params or {})
        return request_json(endpoint, query, timeout=self.timeout, headers=self.headers)

    def _format(self, output: Optional[OutputLike]) -> OutputFormat:
        """Resolve the output format; fail before any request if pandas is missing."""
        fmt = resolve_output(output, self.output)
        if fmt is OutputFormat.DATAFRAME:
            import_pandas()
        return fmt

    def _deliver(
        self,
        fmt: OutputFormat,
        raw: Any,
        rows: Callable[[Any], List[Record]],
        columns: Optional[Mapping[str, str]] = None,
        all_columns: bool = False,
        timestamps: bool = False,
    ) -> Any:
        """Shape ``raw`` into the requested output format."""
        if fmt is OutputFormat.RAW:
            return raw
        records = coerce_numbers(rows(raw))
        if timestamps:
            records = convert_timestamps(records, "timestamp", self._tzinfo)
        if columns is not None:
            records = select_columns(records, columns, all_columns)
        if fmt is OutputFormat.RECORDS:
            return records
        return to_dataframe(records)

    # ----------------------------------------------------------------- clubs

    def search_club_by_name(
        self,
        club_name: str,
        all_columns: bool = False,
        *,
        scope: Union[LeaderboardScope, str] = LeaderboardScope.ALL_TIME,
        max_result_count: Optional[int] = None,
        output: Optional[OutputLike] = None,
    ) -> Any:
        """Clubs whose name contains ``club_name``, one row per club.

        Args:
            club_name: Text to search for (case-insensitive, partial match).
            all_columns: Keep every field EA sends, with EA's names.
            scope: ``"all_time"`` (``allTimeLeaderboard/search``) or
                ``"current_season"`` (``currentSeasonLeaderboard/search``).
            max_result_count: Sent as EA's ``maxResultCount``. It is **not** an
                exact limit: EA returned roughly half as many clubs as asked
                (1 -> 0, 10 -> ~4, 50 -> 11-18). Omitted, EA behaves like ~10.
            output: Override the client's output format.

        Returns:
            League record, divisions, points and ``crestUrl`` per club.
        """
        fmt = self._format(output)
        try:
            scope = LeaderboardScope(scope)
        except ValueError:
            raise ValueError(
                f"scope must be 'all_time' or 'current_season', not {scope!r}"
            ) from None
        params: Dict[str, Any] = {"clubName": club_name}
        if max_result_count is not None:
            params["maxResultCount"] = max_result_count
        raw = self.get_json(_SEARCH_ENDPOINTS[scope], params)

        def rows(data: List[Dict[str, Any]]) -> List[Record]:
            out = []
            for club in data:
                row = flatten(club)
                row["crestUrl"] = _crest_for(club.get("clubInfo") or {})
                out.append(row)
            return out

        columns = {**_columns.SEARCH, "crestUrl": "crestUrl"}
        return self._deliver(fmt, raw, rows, columns, all_columns)

    def find_club_id(self, club_name: str) -> int:
        """Return the id of the club called ``club_name``.

        Picks the club whose name matches exactly (ignoring case), or the only
        search result.

        Raises:
            ClubNotFoundError: No club matched (a ``ValueError``).
            AmbiguousClubError: Several clubs matched and none exactly; the
                error's ``candidates`` lists ``(id, name)`` pairs (a ``ValueError``).
        """
        results = self.get_json("allTimeLeaderboard/search", {"clubName": club_name})
        if not results:
            raise ClubNotFoundError(f"No club found for {club_name!r}")

        for club in results:
            if club["clubName"].lower() == club_name.lower():
                return int(club["clubId"])

        if len(results) == 1:
            return int(results[0]["clubId"])

        candidates = [(int(club["clubId"]), club["clubName"]) for club in results]
        options = ", ".join(f"{name} (id {club_id})" for club_id, name in candidates)
        raise AmbiguousClubError(
            f"{len(results)} clubs match {club_name!r}: {options}. "
            "Use the exact club name, or use the id directly.",
            candidates,
        )

    def get_club_details(
        self, club_id: ClubId, all_columns: bool = False, *, output: Optional[OutputLike] = None
    ) -> Any:
        """One row: club name, ids, stadium and ``crestUrl``.

        ``all_columns=True`` adds every kit field (``customKit.*``). Raw output
        is EA's ``{"<clubId>": {...}}`` dict.
        """
        fmt = self._format(output)
        raw = self.get_json("clubs/info", {"clubIds": club_id})

        def rows(data: Dict[str, Any]) -> List[Record]:
            out = []
            for info in data.values():
                row = flatten(info)
                row["crestUrl"] = _crest_for(info)
                out.append(row)
            return out

        return self._deliver(fmt, raw, rows, _columns.DETAILS, all_columns)

    def get_club_overall_stats(
        self, club_id: ClubId, all_columns: bool = False, *, output: Optional[OutputLike] = None
    ) -> Any:
        """One row: record, goals, streaks, skill rating, promotions.

        ``all_columns=True`` adds ``lastMatch0-9`` / ``lastOpponent0-9`` and
        division finishes; see the endpoint reference for their meaning.
        """
        fmt = self._format(output)
        raw = self.get_json("clubs/overallStats", {"clubIds": club_id})
        return self._deliver(fmt, raw, _flat_rows, _columns.OVERALL, all_columns)

    def get_playoff_achievements(
        self, club_id: ClubId, *, output: Optional[OutputLike] = None
    ) -> Any:
        """Playoff achievements. EA has only returned an empty list so far."""
        fmt = self._format(output)
        raw = self.get_json("club/playoffAchievements", {"clubId": club_id})
        return self._deliver(fmt, raw, _flat_rows)

    # --------------------------------------------------------------- members

    def get_member_stats(
        self, club_id: ClubId, all_columns: bool = False, *, output: Optional[OutputLike] = None
    ) -> Any:
        """One row per club member with their current-season stats.

        Raw output is EA's ``{"members": [...], "positionCount": {...}}``.
        """
        fmt = self._format(output)
        raw = self.get_json("members/stats", {"clubId": club_id})
        return self._deliver(fmt, raw, _member_rows, _columns.MEMBERS, all_columns)

    def get_member_career_stats(
        self, club_id: ClubId, all_columns: bool = False, *, output: Optional[OutputLike] = None
    ) -> Any:
        """One row per club member with their career totals at this club."""
        fmt = self._format(output)
        raw = self.get_json("members/career/stats", {"clubId": club_id})
        return self._deliver(fmt, raw, _member_rows, _columns.CAREER, all_columns)

    # --------------------------------------------------------------- matches

    def _fetch_matches(self, club_id: ClubId, match_type: Union[MatchType, str], count: int) -> Any:
        try:
            match_type = MatchType(match_type)
        except ValueError:
            choices = tuple(member.value for member in MatchType)
            raise ValueError(f"match_type must be one of {choices}, not {match_type!r}") from None
        params = {"clubIds": club_id, "matchType": match_type.value, "maxResultCount": count}
        return self.get_json("clubs/matches", params)

    def get_club_matches(
        self,
        club_id: ClubId,
        match_type: Union[MatchType, str] = MatchType.LEAGUE,
        count: int = 10,
        *,
        output: Optional[OutputLike] = None,
    ) -> Any:
        """One row per match seen from ``club_id``'s side, newest first.

        Args:
            club_id: The club whose matches to fetch.
            match_type: ``"leagueMatch"``, ``"friendlyMatch"`` or ``"playoffMatch"``
                (or a :class:`~fc_clubs_api.MatchType`).
            count: How many recent matches to ask for. EA never sends more than 10.
            output: Override the client's output format.

        Returns:
            Opponent, score, ``result`` (``win``/``draw``/``loss``), ``dnf`` and
            both crests. Raw output is EA's list of match objects.
        """
        fmt = self._format(output)
        raw = self._fetch_matches(club_id, match_type, count)
        match_type_value = MatchType(match_type).value
        our_id = str(club_id)  # EA keys clubs by id as text

        def rows(matches: List[Dict[str, Any]]) -> List[Record]:
            return [_match_row(match, our_id, match_type_value) for match in matches]

        return self._deliver(fmt, raw, rows, timestamps=True)

    def get_match_players(
        self,
        club_id: ClubId,
        match_type: Union[MatchType, str] = MatchType.LEAGUE,
        count: int = 10,
        both_teams: bool = False,
        all_columns: bool = False,
        *,
        include_events: bool = False,
        output: Optional[OutputLike] = None,
    ) -> Any:
        """One row per player per match: rating, goals, passes, tackles, ...

        Args:
            club_id: The club whose matches to fetch.
            match_type: As in :meth:`get_club_matches`.
            count: As in :meth:`get_club_matches`.
            both_teams: Include the opponents' players (tell them apart by ``clubId``).
            all_columns: Keep every field EA sends, with EA's names.
            include_events: Add the decoded event stats from
                :data:`fc_clubs_api.events.EVENT_STATS` (``passesCompletedForward``,
                ``possessionWonAttackingThird``, ...). Where EA already sends a
                field of the same name (``goals``, ``assists``, ``shots``), EA's
                value is kept.
            output: Override the client's output format.

        Returns:
            Player rows. Raw output is EA's list of match objects (the same as
            :meth:`get_club_matches` with ``output="raw"``).
        """
        fmt = self._format(output)
        raw = self._fetch_matches(club_id, match_type, count)
        our_id = str(club_id)

        def rows(matches: List[Dict[str, Any]]) -> List[Record]:
            out = []
            for match in matches:
                # match["players"] is {"<clubId>": {"<playerId>": {...stats...}}}
                for player_club, players in (match.get("players") or {}).items():
                    if player_club != our_id and not both_teams:
                        continue
                    for player_id, stats in players.items():
                        row: Record = {
                            "matchId": match.get("matchId"),
                            "timestamp": match.get("timestamp"),
                            "clubId": player_club,
                            "playerId": player_id,
                        }
                        row.update(stats)
                        if include_events:
                            for name, value in decode_events(stats).items():
                                row.setdefault(name, value)
                        out.append(row)
            return out

        columns = dict(_columns.PLAYERS)
        if include_events:
            for stat in EVENT_STATS:
                columns.setdefault(stat.name, stat.name)
        return self._deliver(fmt, raw, rows, columns, all_columns, timestamps=True)


# --------------------------------------------------------------------- helpers


def _flat_rows(data: Any) -> List[Record]:
    return [flatten(item) for item in data or []]


def _member_rows(data: Any) -> List[Record]:
    members = data.get("members", []) if isinstance(data, dict) else []
    return [flatten(member) for member in members]


def _match_row(match: Mapping[str, Any], our_id: str, match_type: str) -> Record:
    clubs = match.get("clubs") or {}
    us = clubs.get(our_id, {})

    # The other key in `clubs` is the opponent.
    opponent_id: Optional[str] = None
    them: Mapping[str, Any] = {}
    for other_id, other in clubs.items():
        if other_id != our_id:
            opponent_id, them = other_id, other

    goals = int(us.get("goals", 0))
    goals_against = int(us.get("goalsAgainst", 0))

    # League matches say who won in wins/ties/losses. Friendlies leave those at
    # "0" for both clubs, so there the score decides.
    if us.get("wins") == "1":
        result = "win"
    elif us.get("losses") == "1":
        result = "loss"
    elif us.get("ties") == "1":
        result = "draw"
    elif goals > goals_against:
        result = "win"
    elif goals < goals_against:
        result = "loss"
    else:
        result = "draw"

    us_info = us.get("details") or {}
    them_info = them.get("details") or {}
    return {
        "matchId": match.get("matchId"),
        "timestamp": match.get("timestamp"),
        "matchType": match_type,
        "clubId": our_id,
        "clubName": us_info.get("name"),
        "opponentId": opponent_id,
        "opponentName": them_info.get("name"),
        "goals": goals,
        "goalsAgainst": goals_against,
        "result": result,
        # DNF = "did not finish": someone quit and the other club got the win.
        "dnf": us.get("winnerByDnf") == "1" or them.get("winnerByDnf") == "1",
        "crestUrl": _crest_for(us_info, us.get("TEAM")),
        "opponentCrestUrl": _crest_for(them_info, them.get("TEAM")),
    }
