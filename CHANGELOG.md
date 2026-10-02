# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/). While the version is 0.x, minor
releases may contain breaking changes; they are always listed under **Changed**.

## [0.2.0] - Unreleased

The client is now a proper package with three output formats, decoded match events
and full documentation.

### Added

- **Output formats.** Every data method takes `output="raw" | "records" | "dataframe"`
  (or `OutputFormat.RAW` / `RECORDS` / `DATAFRAME`), with a client-wide default via
  `FC27API(output=...)`. `raw` returns EA's JSON untouched; `records` returns typed,
  flat dicts without needing pandas; `dataframe` is the 0.1 behaviour and the default.
- **Current-season leaderboard.** `search_club_by_name(scope="current_season")` uses
  `currentSeasonLeaderboard/search`. `max_result_count=` passes EA's `maxResultCount`.
- **Match events.** `get_match_players(include_events=True)` adds 85 stats decoded from
  `match_event_aggregate_*` (pass direction/length, possession won by third,
  positioning, feedback, ...). `fc_clubs_api.events` exposes `parse_event_aggregates`,
  `decode_events` and the `EVENT_STATS` table. Mappings from the
  [EA FC Pro Clubs API research](https://github.com/Interactive-63/eafc-pro-clubs-api-research) project.
- **Crests and images.** `crestUrl` in search, club details and matches
  (`opponentCrestUrl` too). `fc_clubs_api.assets` builds crest, division badge and
  reputation tier URLs and converts kit colours to hex.
- New columns: `reputationTier`, `promotions`, `relegations` (search),
  `reputationTier` (overall stats), `crestAssetId` (details), `playerId` (match players).
- `get_member_career_stats(all_columns=...)`, `get_playoff_achievements(output=...)`.
- Specific exceptions: `FC27HTTPError` (`.status_code`), `FC27ConnectionError`,
  `FC27ResponseError` (all subclass `FC27APIError`), `ClubNotFoundError` and
  `AmbiguousClubError` (`.candidates`, both subclass `ValueError`).
- Enums `MatchType`, `LeaderboardScope`, `Platform` (all `str` subclasses).
- `FC27API(headers=...)` to add or override HTTP headers.
- `fc-clubs` command line tool (`python -m fc_clubs_api`).
- Type hints throughout and a `py.typed` marker.
- Documentation site (MkDocs), CI on Python 3.9–3.14 with and without pandas,
  ruff, release workflow.

### Changed

- **Breaking: pandas is now optional.** `pip install fc-clubs-api` no longer installs
  pandas. Install `fc-clubs-api[pandas]` to keep DataFrame output (still the default);
  without it, DataFrame calls raise `ImportError` with the install command.
- **Breaking:** `get_member_career_stats` now returns curated, renamed columns by
  default (`ratingAve` → `averageRating`, `favoritePosition` → `position`). Pass
  `all_columns=True` for the previous output.
- **Breaking:** `MATCH_TYPES`, `COLUMNS`, `to_dataframe` and `pick_columns` are no
  longer importable from `fc_clubs_api`; use `MatchType` and `all_columns=True`.
- The package moved to a `src/` layout. `from fc_clubs_api import FC27API` is unchanged.
- Minimum pandas version is 2.0.
- On Windows, `tzdata` is installed for timezone support.

### Removed

- `requirements.txt` (dependencies live in `pyproject.toml`).

## [0.1.1] - 2026-10-02

### Changed

- README links are absolute so they work on PyPI.

## [0.1.0] - 2026-10-02

First release: `FC27API` with club search, details, overall stats, member and career
stats, matches and per-player match stats as pandas DataFrames.

[0.2.0]: https://github.com/1erkandogan/fc27-clubs-api/compare/8001299...HEAD
[0.1.1]: https://github.com/1erkandogan/fc27-clubs-api/commit/8001299
[0.1.0]: https://github.com/1erkandogan/fc27-clubs-api/commit/5cb18c8
