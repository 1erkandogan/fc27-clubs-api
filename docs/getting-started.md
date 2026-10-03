# Getting started

## Install

Python 3.9 or newer.

=== "With pandas (analysis)"

    ```bash
    pip install "fc-clubs-api[pandas]"
    ```

    Pass `output="dataframe"` (on the client or per call) to get pandas DataFrames.

=== "Without pandas (apps, bots)"

    ```bash
    pip install fc-clubs-api
    ```

    No third-party dependencies. Methods return lists of dicts (`records`) by default.

No API key or account is needed; the data is public.

## First calls

```python
from fc_clubs_api import FC27API

api = FC27API(timezone="Europe/London")   # match times in your timezone

club_id = api.find_club_id("Your Club Name")   # -> 1001

api.get_club_details(club_id)             # name, stadium, crest
api.get_club_overall_stats(club_id)       # record, streaks, skill rating
api.get_member_stats(club_id)             # squad stats this season
api.get_club_matches(club_id)             # last 10 league matches
api.get_match_players(club_id)            # every player's rating per match
```

`find_club_id` picks the club whose name matches exactly (ignoring case), or the only
search result. If several clubs match, it raises
[`AmbiguousClubError`](errors.md) listing them; pass the id directly instead.

## Client settings

```python
FC27API(
    platform="common-gen5",   # PS5 / Xbox Series / PC; the only one verified for FC 27
    timeout=10,               # seconds before FC27ConnectionError
    timezone="UTC",           # IANA name or tzinfo for match timestamps
    output="records",         # default format: "records", "dataframe" or "raw"
    headers=None,             # extra HTTP headers, merged over the defaults
)
```

## Methods

| Method | One row per | Notes |
|---|---|---|
| `find_club_id(name)` | — | Returns an `int` |
| `search_club_by_name(name)` | matching club | `scope="current_season"` for this season's table |
| `get_club_details(club_id)` | club (1 row) | Name, ids, stadium, `crestUrl` |
| `get_club_overall_stats(club_id)` | club (1 row) | Record, goals, streaks, skill rating |
| `get_member_stats(club_id)` | member | This season: games, goals, assists, rating, pass/tackle rates |
| `get_member_career_stats(club_id)` | member | Career totals at this club |
| `get_club_matches(club_id, match_type, count)` | match | Opponent, score, `result`, `dnf`, crests |
| `get_match_players(club_id, match_type, count)` | player per match | `both_teams=True`, `include_events=True` |
| `get_playoff_achievements(club_id)` | achievement | EA has only returned `[]` so far |
| `get_json(endpoint, params)` | — | Any endpoint, raw JSON |

All data methods accept `output=`. `match_type` is `"leagueMatch"` (default),
`"friendlyMatch"` or `"playoffMatch"`, or `MatchType.LEAGUE` etc. `count` can't
exceed 10: EA never sends more than the last 10 matches, and there is no paging.

Full signatures: [API reference](reference.md).

## Command line

```bash
fc-clubs "Your Club Name"                    # tables (with pandas) or JSON
fc-clubs 1001 --match-type friendlyMatch --timezone Europe/Paris
fc-clubs "Your Club Name" --json > club.json
python -m fc_clubs_api --help
```

A purely numeric argument is treated as a club id.

## Next

- [Output formats](output-formats.md): raw vs records vs DataFrame.
- [Recipes](recipes.md): top scorers, form, per-player trends, exports.
- [Endpoints](endpoints.md): what EA actually sends.
