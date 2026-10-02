# fc-clubs-api

[![PyPI](https://img.shields.io/pypi/v/fc-clubs-api)](https://pypi.org/project/fc-clubs-api/)
[![Python](https://img.shields.io/pypi/pyversions/fc-clubs-api)](https://pypi.org/project/fc-clubs-api/)
[![CI](https://github.com/1erkandogan/fc27-clubs-api/actions/workflows/ci.yml/badge.svg)](https://github.com/1erkandogan/fc27-clubs-api/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-online-blue)](https://1erkandogan.github.io/fc27-clubs-api/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/1erkandogan/fc27-clubs-api/blob/main/LICENSE.md)

An unofficial Python client for the **EA Sports FC 27 Pro Clubs API**, the same
endpoints [proclubs.ea.com](https://proclubs.ea.com) calls from the browser. Find
clubs and get their stats, members, match history and per-player match ratings as
EA's raw JSON, clean Python records or pandas DataFrames.

```python
from fc_clubs_api import FC27API

api = FC27API()
club_id = api.find_club_id("Your Club Name")
api.get_club_matches(club_id)    # last 10 league matches
```

**[Documentation](https://1erkandogan.github.io/fc27-clubs-api/)** ·
[Getting started](https://1erkandogan.github.io/fc27-clubs-api/getting-started/) ·
[API reference](https://1erkandogan.github.io/fc27-clubs-api/reference/) ·
[EA endpoints](https://1erkandogan.github.io/fc27-clubs-api/endpoints/) ·
[Changelog](https://github.com/1erkandogan/fc27-clubs-api/blob/main/CHANGELOG.md)

## Features

- **Three output formats**: `raw` JSON, typed `records`, or a pandas `dataframe`,
  set per client or per call.
- **No required dependencies.** The core is standard library only; pandas is an extra.
- **Every known club endpoint**: search (all-time and current season), details,
  overall stats, member and career stats, matches, per-player match stats.
- **Matches from your side**: opponent, score, `result` (win/draw/loss) and `dnf`,
  correct for league matches *and* friendlies.
- **80+ decoded match events** EA doesn't name: pass direction and length,
  possession won by pitch third, positioning, in-game feedback.
- **Crest, division and reputation images**, with the crest fallback rule.
- Timezone-aware timestamps, consistent camelCase columns, fully typed,
  a `fc-clubs` CLI.

## Install

Python 3.9 or newer.

```bash
pip install "fc-clubs-api[pandas]"   # with DataFrame output (analysis, notebooks)
pip install fc-clubs-api             # no dependencies (apps, bots, APIs)
```

No API key needed; the data is public.

## Output formats

The same data, three ways. `dataframe` is the default.

| Format | Returns | For |
|---|---|---|
| `"raw"` | EA's JSON exactly as received | storage, proxies, fields not mapped here |
| `"records"` | `list[dict]`: flat, typed, renamed, timestamps as `datetime` | backends, bots, JSON APIs |
| `"dataframe"` | `pandas.DataFrame` with the same columns as `records` | analysis, CSV/Excel |

```python
from fc_clubs_api import FC27API

api = FC27API(output="records", timezone="Europe/London")   # client default

api.get_member_stats(1001)                       # list of dicts
api.get_member_stats(1001, output="raw")         # {"members": [...], "positionCount": {...}}
api.get_member_stats(1001, output="dataframe")   # DataFrame
```

[More on output formats →](https://1erkandogan.github.io/fc27-clubs-api/output-formats/)

## Methods

| Method | One row per |
|---|---|
| `find_club_id(name)` | returns the club id (`int`) |
| `search_club_by_name(name, scope="all_time")` | matching club; `scope="current_season"` for this season |
| `get_club_details(club_id)` | club: name, ids, stadium, crest |
| `get_club_overall_stats(club_id)` | club: record, goals, streaks, skill rating |
| `get_member_stats(club_id)` | member: this season's games, goals, assists, rating, pass/tackle rates |
| `get_member_career_stats(club_id)` | member: career totals at the club |
| `get_club_matches(club_id, match_type, count)` | match: opponent, score, `result`, `dnf` |
| `get_match_players(club_id, match_type, count)` | player per match: rating, goals, passes, tackles, ... |
| `get_playoff_achievements(club_id)` | achievement (EA has only returned `[]` so far) |
| `get_json(endpoint, params)` | any endpoint, raw |

- Every data method takes `output=`. Most take `all_columns=True` for every field EA
  sends, with EA's names.
- `match_type`: `"leagueMatch"` (default), `"friendlyMatch"`, `"playoffMatch"`, or
  `MatchType.LEAGUE` etc. `count` is capped at 10 by EA, with no paging.
- `get_match_players(..., both_teams=True, include_events=True)` adds the opponents
  and the decoded event stats.

## Examples

```python
from fc_clubs_api import FC27API

api = FC27API(timezone="Europe/London")
club_id = api.find_club_id("Your Club Name")

# Top 5 scorers this season
members = api.get_member_stats(club_id)
members.sort_values("goals", ascending=False).head(5)[["name", "goals", "assists"]]

# Average match rating per player, best first
players = api.get_match_players(club_id)
players.groupby("name")["rating"].mean().sort_values(ascending=False)

# Where does each player win the ball back? (decoded match events)
events = api.get_match_players(club_id, include_events=True)
events.groupby("name")[["possessionWonDefensiveThird", "possessionWonMiddleThird",
                        "possessionWonAttackingThird"]].sum()
```

More in the [recipes](https://1erkandogan.github.io/fc27-clubs-api/recipes/) and
[`examples/`](https://github.com/1erkandogan/fc27-clubs-api/tree/main/examples).
From the terminal:

```bash
fc-clubs "Your Club Name"            # recent matches and squad, or --json
```

## Errors

All network and response problems raise `FC27APIError` (subclasses
`FC27HTTPError` with `.status_code`, `FC27ConnectionError`, `FC27ResponseError`).
`find_club_id` raises `ClubNotFoundError` or `AmbiguousClubError` (with
`.candidates`), both `ValueError`s. [Details →](https://1erkandogan.github.io/fc27-clubs-api/errors/)

## Good to know

- **EA blocks non-browser requests.** Every request sends browser-like headers
  (`fc_clubs_api.HEADERS`); without them EA answers 403 or not at all.
- **No caching or rate limiting.** Every call goes straight to EA. Pause between
  requests (`time.sleep(1)`) when looping over many clubs.
- **Unofficial.** Not affiliated with or endorsed by EA. The endpoints are
  undocumented and can change without notice.

## Contributing

Bug reports are especially welcome when EA changes something and the client breaks.
Please open an issue before writing code. See
[CONTRIBUTING.md](https://github.com/1erkandogan/fc27-clubs-api/blob/main/CONTRIBUTING.md).

## Acknowledgements

The current-season endpoint, crest rules and match event mappings build on the
community [EA FC Pro Clubs API research](https://github.com/Interactive-63/eafc-pro-clubs-api-research)
project.

## License

MIT, see [LICENSE.md](https://github.com/1erkandogan/fc27-clubs-api/blob/main/LICENSE.md).
