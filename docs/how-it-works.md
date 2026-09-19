# How it works: a beginner's guide to `fc27_api.py`

This guide walks through [`fc27_api.py`](../fc27_api.py) from top to bottom. It covers
what each part does, why it is there, and where plain Python was enough and where
it wasn't. You only need basic Python: variables, lists, dicts, `for` loops, `if`
and functions.

Keep `fc27_api.py` open next to this page while you read.

---

## 1. The big picture

When you open a club page on proclubs.ea.com, your browser quietly asks EA's server
for the data behind it by visiting URLs like this one:

```
https://proclubs.ea.com/api/fc/clubs/info?platform=common-gen5&clubIds=1001
```

EA answers with **JSON**, which is text that looks almost exactly like Python dicts and lists:

```json
{"1001": {"name": "Example FC", "clubId": 1001, "regionId": 1000000, "teamId": 100}}
```

That URL is an **API endpoint**: a web address that returns data instead of a web page.
`fc27_api.py` does what the browser does:

1. build the URL,
2. send the request,
3. turn the JSON answer into Python objects,
4. clean them up and turn them into a table (a pandas `DataFrame`).

All of EA's endpoints and their answers are listed in [endpoints.md](endpoints.md).

---

## 2. The imports, and why each one is there

```python
import json
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd
```

The first four come **with Python**, so you don't need to install anything:

| Import | What we use it for |
|---|---|
| `json` | Turning EA's JSON text into Python dicts and lists (`json.load`). |
| `urllib.parse` | Building the `?platform=common-gen5&clubIds=1001` part of the URL. `urlencode` also escapes spaces and special characters, so a club name like `FC Köln & Co` still works. |
| `urllib.request` | Sending the request to EA (`Request`, `urlopen`). |
| `urllib.error` | The error urllib raises when EA answers with an error code such as 403 (`HTTPError`). |

`pandas` is the **only** thing you have to install (`pip install pandas`). Section 2.2 explains why.

### 2.1 Why not `requests`?

Most tutorials use the popular [`requests`](https://requests.readthedocs.io) library,
and it is a fine choice. With `requests` the call looks like this:

```python
response = requests.get(url, params=params, headers=HEADERS, timeout=10)
data = response.json()
```

With the built-in `urllib`, it looks like this:

```python
url = BASE_URL + "/" + endpoint + "?" + urllib.parse.urlencode(params)
request = urllib.request.Request(url, headers=HEADERS)
with urllib.request.urlopen(request, timeout=10) as response:
    data = json.load(response)
```

That is two more lines. `requests` becomes worth it when you need things like
connection re-use, automatic retries, cookies or file uploads. We send a handful of
simple GET requests, so the built-in version is enough, and it is one less thing to install.

### 2.2 Why pandas? Wasn't plain Python enough?

Plain Python *can* do everything pandas does. It just takes much more code for the
things people want to do with football stats. Say we have the member list from EA,
a list of dicts:

```python
members = api.get_json("members/stats", {"clubId": 1001})["members"]
# [{"name": "Player1", "goals": "2", "ratingAve": "7.4", ...}, ...]
```

**Plain Python:**

```python
# Top scorer. Note int(...): EA sends "2", which is text, not a number.
best = None
for member in members:
    if best is None or int(member["goals"]) > int(best["goals"]):
        best = member
print(best["name"])

# Average rating
total = 0
for member in members:
    total += float(member["ratingAve"])
print(total / len(members))

# Save to a CSV file you can open in Excel
import csv
with open("members.csv", "w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=members[0].keys())
    writer.writeheader()
    writer.writerows(members)
```

**pandas:**

```python
df = api.get_member_stats(1001)

print(df.sort_values("goals", ascending=False).head(1))   # top scorer
print(df["averageRating"].mean())                        # average rating
df.to_csv("members.csv", index=False)                    # save to CSV
```

A `DataFrame` is a table with named columns, like a spreadsheet inside Python.
Sorting, filtering, averaging, grouping and saving are each one line, and
`print(df)` shows a readable table. That is why every method returns one.

### 2.3 Things we deliberately left out

- **`typing` / type hints.** You often see code like `def get(club_id: int) -> pd.DataFrame:`.
  Those `: int` and `-> ...` parts are optional notes for code editors, and Python
  ignores them when the code runs. To keep the code plain, each function says in its
  docstring (the `"""text"""` under the `def`) what it takes and returns.
- **Extra layers** such as a separate file per endpoint, or a model class per response.
  One file you can read top to bottom is easier to follow.

---

## 3. Settings at the top of the file

```python
BASE_URL = "https://proclubs.ea.com/api/fc"
MATCH_TYPES = ("leagueMatch", "friendlyMatch", "playoffMatch")
HEADERS = {...}
COLUMNS = {...}
```

Names in `CAPITALS` are **constants**, values that never change while the program runs.
Putting them at the top means that if EA changes something, you fix it in one place.

### HEADERS: why we pretend to be a browser

Every request carries **headers**, small notes about who is asking. EA's servers sit
behind a protection service (Akamai) that blocks requests that don't look like they
come from the proclubs.ea.com website. Without our headers, EA either answers
**403 Forbidden** or doesn't answer at all, and the request just hangs until the timeout.

The important header is `"sec-fetch-site": "same-origin"`, which means "this request
comes from EA's own site". The `user-agent` and `sec-ch-ua` say "I am Chrome on Windows".

### COLUMNS: short, friendly tables

EA returns lots of columns, 43 per player per match, with inconsistent names:
`passesmade`, `ratingAve`, `mom` (man of the match). `COLUMNS` lists, for each method,
which columns to keep and what to call them:

```python
"players": {
    "playername": "name",          # EA's name  ->  our name
    "passesmade": "passesMade",
    "mom": "manOfTheMatch",
    ...
}
```

If you want everything EA sends, with its original names, pass `all_columns=True`.

---

## 4. `FC27APIError`: our own error type

```python
class FC27APIError(Exception):
    """Raised when EA can't be reached, refuses the request, or doesn't send JSON."""
```

This is a new kind of error, built on Python's `Exception`. It has no code inside
(only the docstring), because it doesn't need any: its only job is to have its own name.
Many different things can go wrong on the network. We turn all of them into this one
error, so your code only has to catch one thing:

```python
try:
    df = api.get_club_details(1001)
except FC27APIError as error:
    print("EA problem:", error)
```

---

## 5. The two helper functions

### `to_dataframe(records)`: from EA's data to a clean table

It does two fixes.

**Fix 1: nested dicts become columns** with `pd.json_normalize`. EA often puts dicts inside dicts:

```python
{"clubId": "1001", "wins": "20", "clubInfo": {"name": "Example FC", "teamId": 100}}
```

`pd.DataFrame(...)` would leave the whole `clubInfo` dict in a single cell.
`pd.json_normalize(...)` spreads it out:

| clubId | wins | clubInfo.name | clubInfo.teamId |
|---|---|---|---|
| 1001 | 20 | Example FC | 100 |

**Fix 2: text numbers become real numbers** with `pd.to_numeric`. EA sends almost
every number as text: `"25"`, `"7.4"`. Text can't be added up, and it sorts wrongly
(`"9"` comes after `"25"` because `"9"` > `"2"`). So for each column we *try* to convert it:

```python
for column in df.columns:
    try:
        df[column] = pd.to_numeric(df[column])
    except (ValueError, TypeError):
        pass  # a text column such as a name: leave it as text
```

`try` / `except` means "attempt this; if it fails with one of these errors, do the
`except` part instead of crashing". For a column of names, `to_numeric` fails,
and `pass` means "do nothing", so the column stays text.

### `pick_columns(df, columns, all_columns)`

```python
keep = []
for ea_name in columns:
    if ea_name in df.columns:
        keep.append(ea_name)
return df[keep].rename(columns=columns)
```

It collects the columns from `COLUMNS` that really exist in the table (EA sometimes
leaves one out), keeps only those (`df[keep]`) and renames them (`.rename`).

---

## 6. The `FC27API` class

```python
class FC27API:
    def __init__(self, platform="common-gen5", timeout=10, timezone="UTC"):
        self.platform = platform
        self.timeout = timeout
        self.timezone = timezone
```

**Why a class and not just functions?** Every request needs the same settings:
platform, timeout and timezone. A class lets you choose them **once**:

```python
api = FC27API(timezone="Europe/Istanbul")
api.get_club_matches(1001)     # uses Istanbul time
api.get_member_stats(1001)     # same settings, no need to repeat them
```

- `__init__` runs when you write `FC27API(...)` and stores the settings.
- `self` is the object itself. `self.timezone` means "this object's timezone".
  Every method gets `self` first, which is how it can read the settings.
- `platform="common-gen5"` is a **default argument**. You can leave it out,
  and then the default is used.

### `get_json`: the one place that talks to EA

Every other method calls this one. Step by step:

```python
query = {"platform": self.platform}
query.update(params)
```

EA needs `platform` on every request, so we start with it and add the method's own
parameters, for example `{"clubIds": 1001}`.

```python
url = BASE_URL + "/" + endpoint + "?" + urllib.parse.urlencode(query)
# https://proclubs.ea.com/api/fc/clubs/info?platform=common-gen5&clubIds=1001
request = urllib.request.Request(url, headers=HEADERS)
```

This builds the full URL and attaches our browser-like headers.

```python
try:
    with urllib.request.urlopen(request, timeout=self.timeout) as response:
        data = json.load(response)
```

`urlopen` sends the request. `timeout` means "give up after 10 seconds instead of
waiting forever". The `with` block makes sure the connection is closed afterwards,
even if something goes wrong. `json.load` reads the answer and turns the JSON text
into dicts and lists.

```python
except urllib.error.HTTPError as error:
    raise FC27APIError(f"EA answered with error {error.code} for {url}") from None
except OSError as error:  # no internet, timeout, DNS problem, ...
    raise FC27APIError(f"Could not reach EA ({error}) for {url}") from None
except json.JSONDecodeError:
    raise FC27APIError(f"EA did not send JSON for {url}") from None
```

Three things can go wrong:

- EA answers with an error code, for example 403 when it blocks us.
- The network fails: no internet, or the timeout ran out.
- EA sends something that isn't JSON, for example an HTML "blocked" page.

Each one becomes an `FC27APIError` with a clear message.

`from None` hides Python's internal error chain, so you see one short message
instead of two long tracebacks.

The order matters. `HTTPError` is a special kind of `OSError`, so it has to be checked
first, or the `OSError` line would catch it with the less helpful message.

```python
if data is None:
    return []
return data
```

Sometimes EA answers `null` (Python `None`) instead of an empty list. Turning that into
`[]` means the rest of the code never has to check for `None`.

### `_convert_times`: readable dates

EA gives match times as **Unix timestamps**, the number of seconds since
1 January 1970 UTC. For example, `1767297600` is 1 January 2026, 20:00:00 UTC.

```python
utc_times = pd.to_datetime(df["timestamp"], unit="s", utc=True)
df["timestamp"] = utc_times.dt.tz_convert(self.timezone)
```

The first line turns the seconds into dates in UTC. The second converts them to your
timezone, so `"Europe/Istanbul"` shows 23:00.

The leading underscore in `_convert_times` is a Python convention that means
"helper used inside the class, you don't need to call it yourself".

---

## 7. The methods, one by one

Most methods follow the same three steps: **ask EA → make a table → keep the useful columns**.

```python
def get_club_overall_stats(self, club_id, all_columns=False):
    data = self.get_json("clubs/overallStats", {"clubIds": club_id})
    return pick_columns(to_dataframe(data), COLUMNS["overall"], all_columns)
```

The differences come from the different shapes EA sends back:

| Method | What EA sends | Extra step |
|---|---|---|
| `search_club_by_name` | a list of clubs | none |
| `get_club_details` | `{"1001": {...club...}}`, a dict keyed by id | `list(data.values())` keeps only the `{...club...}` part |
| `get_club_overall_stats` | a list with one club | none |
| `get_member_stats` / `get_member_career_stats` | `{"members": [...], "positionCount": {...}}` | `data.get("members", [])` takes the list |
| `get_playoff_achievements` | `[]` so far | none |

`data.get("members", [])` means "give me `data["members"]`, or `[]` if it isn't there",
so a missing key doesn't crash the program.

### `find_club_id`

Most methods need a club **id** (like `1001`), but you usually know the **name**.
`find_club_id` searches and picks the right result:

1. no results → `ValueError("No club found ...")`
2. a club whose name matches exactly (`.lower()` ignores upper/lower case) → its id
3. only one result → its id
4. otherwise → a `ValueError` listing every option, e.g.
   `2 clubs match 'example': Example FC (id 1001), Example United (id 1002). ...`

It returns `int(club["clubId"])` because EA sends the id as text (`"1001"`).

### `get_club_matches`: the longest method

A match from EA looks like this (trimmed). The keys of `clubs` are **club ids as text**:

```python
{
  "matchId": "1000000000001",
  "timestamp": 1767297600,
  "clubs": {
    "1001": {"goals": "4", "goalsAgainst": "0", "wins": "1", "ties": "0", "losses": "0",
             "winnerByDnf": "1", "details": {"name": "Example FC"}},
    "2001": {"goals": "0", "goalsAgainst": "4", "wins": "0", "ties": "0", "losses": "1",
             "winnerByDnf": "0", "details": {"name": "Opponent A"}}
  },
  "players": {...}
}
```

We want **one simple row per match, from our club's point of view**. Step by step:

```python
club_id = str(club_id)
```

The dict keys are text (`"1001"`). If you passed the number `1001`, then `clubs.get(1001)`
would find nothing, because `1001` and `"1001"` are different keys. So we convert to text first.

```python
us = clubs.get(club_id, {})
opponent_id = None
them = {}
for other_id in clubs:
    if other_id != club_id:
        opponent_id = other_id
        them = clubs[other_id]
```

`us` is our club's data. The loop finds the other key in `clubs`: that is the opponent.

```python
goals = int(us.get("goals", 0))
goals_against = int(us.get("goalsAgainst", 0))

if us.get("wins") == "1":
    result = "win"
elif us.get("losses") == "1":
    result = "loss"
elif us.get("ties") == "1":
    result = "draw"
elif goals > goals_against:
    result = "win"
...
```

In **league** matches, EA fills in `wins` / `losses` / `ties`, so we use them.
In **friendlies**, EA leaves all three at `"0"`, which we found by checking real data,
so we fall back to comparing the goals.

```python
"clubName": us.get("details", {}).get("name"),
```

This is two `.get`s in a row: first the `details` dict (or `{}` if missing), then the
`name` inside it. If anything is missing you get `None` instead of a crash.

```python
"dnf": us.get("winnerByDnf") == "1" or them.get("winnerByDnf") == "1",
```

DNF means "did not finish": a team quit, and the other team was given the win.
This column is `True` for those matches.

Each finished `row` dict is added to `rows`. At the end, `to_dataframe(rows)` turns the
list of dicts into a table, and `_convert_times` fixes the dates.

### `get_match_players`

EA stores player stats two levels deep: `players → club id → player id → stats`.
So there are two loops:

```python
for player_club, players in match.get("players", {}).items():
    if player_club != club_id and not both_teams:
        continue  # skip the opponent's players
    for player_id, stats in players.items():
        row = {"matchId": ..., "timestamp": ..., "clubId": player_club, "playerId": player_id}
        row.update(stats)
        rows.append(row)
```

`.items()` gives you each key together with its value. `continue` jumps straight to
the next loop round. `row.update(stats)` copies all of EA's stat fields into our row.

---

## 8. `if __name__ == "__main__":`

```python
if __name__ == "__main__":
    api = FC27API()
    ...
```

The code under this line runs only when you start the file directly
(`python fc27_api.py`), as a quick demo. It does **not** run when your own script
imports the file with `from fc27_api import FC27API`.

---

## 9. The tests (`tests/test_fc27_api.py`)

The tests check that every method still produces the right table. They **never contact EA**:

- EA's live data changes all the time, and tests need fixed answers.
- EA might be down, or might block you for sending too many requests.

Instead, `unittest.mock.patch` temporarily **replaces** `urllib.request.urlopen` with a
fake. The fake returns a saved response from `tests/fixtures/`. Those files have the exact
shape of real EA responses, but every club and player name, id and date is a placeholder:

```python
with fake_ea(fixture("matches")):
    df = FC27API().get_club_matches(1001)
self.assertEqual(list(df["result"]), ["win", "draw", "loss"])
```

Run them with:

```bash
python -m unittest discover -s tests -v
```
