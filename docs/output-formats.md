# Output formats

Every data method can return the same data in three formats. Pick the one that fits
what you are building.

| Format | Returns | Best for | Needs |
|---|---|---|---|
| `"raw"` | EA's JSON exactly as received (`dict` / `list`) | Storing responses, proxies, fields this package doesn't map, debugging EA changes | nothing |
| `"records"` | `list[dict]`, one flat, typed dict per row | Web backends, bots, JSON APIs, ORMs, anything without pandas | nothing |
| `"dataframe"` | `pandas.DataFrame` | Analysis, notebooks, CSV/Excel export | `pip install "fc-clubs-api[pandas]"` |

`"dataframe"` is the default, so code written for 0.1 keeps working.

## Choosing a format

Set a default on the client, override it on any call:

```python
from fc_clubs_api import FC27API, OutputFormat

api = FC27API(output="records")                    # default for every call

api.get_member_stats(1001)                         # -> list[dict]
api.get_member_stats(1001, output="raw")           # -> EA's JSON
api.get_member_stats(1001, output="dataframe")     # -> DataFrame

api.get_member_stats(1001, output=OutputFormat.RAW)  # the enum works too
```

An unknown name raises `ValueError`. Asking for a DataFrame without pandas installed
raises `ImportError` with the install command, *before* any request is sent.

## The same call, three ways

`api.get_club_matches(1001, count=1)`:

=== "raw"

    ```python
    [{
      "matchId": "1000000000001",
      "timestamp": 1767297600,
      "timeAgo": {"number": 4, "unit": "hours"},
      "clubs": {
        "1001": {"goals": "4", "goalsAgainst": "0", "wins": "1", "winnerByDnf": "1",
                 "TEAM": "100", "details": {"name": "Example FC", ...}, ...},
        "2001": {...}
      },
      "players": {"1001": {"<playerId>": {...}}, "2001": {...}},
      "aggregate": {...}
    }]
    ```

=== "records"

    ```python
    [{
      "matchId": 1000000000001,
      "timestamp": datetime(2026, 1, 1, 20, 0, tzinfo=timezone.utc),
      "matchType": "leagueMatch",
      "clubId": 1001,
      "clubName": "Example FC",
      "opponentId": 2001,
      "opponentName": "Opponent A",
      "goals": 4,
      "goalsAgainst": 0,
      "result": "win",
      "dnf": True,
      "crestUrl": "https://eafc24.content.easports.com/.../l100.png",
      "opponentCrestUrl": "https://eafc24.content.easports.com/.../l100.png",
    }]
    ```

=== "dataframe"

    ```text
             matchId                 timestamp    matchType  clubId    clubName  opponentId opponentName  goals  goalsAgainst result   dnf  ...
    0  1000000000001 2026-01-01 20:00:00+00:00  leagueMatch    1001  Example FC        2001   Opponent A      4             0    win  True  ...
    ```

## What `records` and `dataframe` do to EA's data

Both formats are built by the same code, so they always have identical columns and
values. Compared with `raw`:

1. **Rows.** The list of rows is pulled out of EA's wrapper (`{"members": [...]}`,
   `{"1001": {...}}`, `players → club → player`).
2. **Flattened.** Nested objects become dotted keys: `clubInfo.name`,
   `customKit.stadName`.
3. **Typed.** Numeric text becomes `int` / `float`. A field is converted only if every
   value in it is numeric, so names and empty strings stay text.
4. **Timestamps.** Unix seconds become timezone-aware `datetime`s in the client's
   `timezone` (default UTC).
5. **Curated columns.** A short, consistently named (camelCase) set of columns,
   e.g. `ratingAve` → `averageRating`, `mom` → `manOfTheMatch`.
   `all_columns=True` keeps every field under EA's own name instead.
6. **Derived fields.** `result` and `dnf` per match, `crestUrl`, and (opt-in) decoded
   [match events](match-events.md).
7. **Rectangular.** Every dict has the same keys; missing values are `None`
   (`NaN` in the DataFrame).

`raw` changes only one thing: a JSON `null` from EA becomes `[]`.

## Which parameters apply

| Parameter | raw | records / dataframe |
|---|---|---|
| `all_columns` | ignored | keeps every EA field |
| `include_events` | ignored | adds decoded event columns |
| `FC27API(timezone=...)` | ignored (Unix seconds) | converts timestamps |
| `both_teams` (`get_match_players`) | ignored (EA always sends both teams) | filters rows |

For `get_club_matches` and `get_match_players`, `raw` returns the same thing: the
list of match objects from `clubs/matches`. `find_club_id` always returns an `int`.

## Going between formats

```python
import json
import pandas as pd

rows = api.get_member_stats(1001, output="records")
df = pd.DataFrame(rows)                              # same as output="dataframe"

json.dumps(rows, default=str)                        # datetimes -> ISO strings
df.to_json(orient="records", date_format="iso")      # DataFrame -> JSON
```
