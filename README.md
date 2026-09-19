# FC 27 Clubs API

An unofficial Python client for the **EA Sports FC 27 Pro Clubs API**, the same
endpoints `proclubs.ea.com` calls from the browser. You can find clubs and get
their stats, members, matches and per-player match ratings as tables (pandas
DataFrames).

Not affiliated with or endorsed by EA. The endpoints are undocumented and can
change without notice.

- **New to Python, or want to know how it works?** Read [docs/how-it-works.md](docs/how-it-works.md).
  It walks through the code and explains every import and decision.
- **Want EA's raw responses?** See [docs/endpoints.md](docs/endpoints.md).

## Install

You need Python 3.9 or newer.

```bash
git clone https://github.com/1erkandogan/fc26-clubs-api.git
cd fc26-clubs-api
pip install -r requirements.txt   # installs pandas, the only dependency
```

No API key needed. The whole client is one file, [`fc27_api.py`](fc27_api.py).
Put your own script **in the same folder** (or copy `fc27_api.py` next to your
script) so that `from fc27_api import FC27API` can find it.

## Quick start

```python
from fc27_api import FC27API

api = FC27API(timezone="Europe/Istanbul")      # match times in your timezone

club_id = api.find_club_id("Your Club Name")   # -> the id, e.g. 1001

print(api.get_club_matches(club_id))           # last 10 league matches
print(api.get_member_stats(club_id))           # squad stats this season
```

Or run the example: `python examples/quickstart.py "Your Club Name"`

## Methods

| Method | Gives you (one row per ...) |
|---|---|
| `find_club_id(name)` | the club's id as a number. If several clubs match, the error lists them. |
| `search_club_by_name(name)` | club matching the name: division, wins, goals, points |
| `get_club_details(club_id)` | club (1 row): name, ids, stadium |
| `get_club_overall_stats(club_id)` | club (1 row): record, goals, streaks, skill rating |
| `get_member_stats(club_id)` | member: games, goals, assists, average rating, pass/tackle rates |
| `get_member_career_stats(club_id)` | member: career totals at the club |
| `get_club_matches(club_id, match_type="leagueMatch", count=10)` | match, from your side: opponent, score, `result` (win/draw/loss), `dnf` |
| `get_match_players(club_id, match_type="leagueMatch", count=10, both_teams=False)` | player per match: rating, goals, assists, shots, passes, tackles |
| `get_playoff_achievements(club_id)` | achievement (EA has only returned an empty list so far) |
| `get_json(endpoint, params)` | EA's raw response as dicts/lists, e.g. `api.get_json("clubs/info", {"clubIds": 1001})` |

- `match_type` is `"leagueMatch"`, `"friendlyMatch"` or `"playoffMatch"`.
- By default, tables have a short set of readable columns. Add `all_columns=True` to
  `search_club_by_name`, `get_club_details`, `get_club_overall_stats`,
  `get_member_stats` or `get_match_players` to get every field EA sends, with EA's names.
- `FC27API(platform="common-gen5", timeout=10, timezone="UTC")`: all settings are optional.
- If there is no data, you get an empty table (`df.empty` is `True`).

## Recipes

```python
from fc27_api import FC27API

api = FC27API(timezone="Europe/Istanbul")
club_id = api.find_club_id("Your Club Name")

# Top 5 scorers this season
members = api.get_member_stats(club_id)
print(members.sort_values("goals", ascending=False).head(5)[["name", "goals", "assists"]])

# Last 5 league results
matches = api.get_club_matches(club_id)
print(matches.head(5)[["timestamp", "opponentName", "goals", "goalsAgainst", "result"]])

# Win rate over the last 10 league matches
wins = (matches["result"] == "win").sum()
print(f"Won {wins} of {len(matches)}")

# One player's recent matches
players = api.get_match_players(club_id)
print(players[players["name"] == "YourGamertag"][["timestamp", "rating", "goals", "assists"]])

# Average match rating per player, best first
print(players.groupby("name")["rating"].mean().sort_values(ascending=False))

# Save any table to open in Excel
members.to_csv("members.csv", index=False)
# members.to_excel("members.xlsx", index=False)   # needs: pip install openpyxl
```

## Errors

- **`FC27APIError`**: EA couldn't be reached, refused the request, or didn't send JSON.
- **`ValueError`**: you passed something invalid, such as an unknown `match_type`, or a
  club name that `find_club_id` couldn't match to one club.

```python
from fc27_api import FC27API, FC27APIError

try:
    df = FC27API().get_club_details(1001)
except FC27APIError as error:
    print("EA problem:", error)
```

## Good to know

- **EA blocks non-browser requests.** Every request sends browser-like headers
  (`HEADERS` in `fc27_api.py`). Without them EA answers 403 or doesn't answer at all.
  Plain `curl` is blocked even with the headers, while Python works.
- **No caching or rate limiting.** Every call goes straight to EA. If you loop over
  many clubs, add a pause between requests (`time.sleep(1)`) so you don't get blocked.

## Changes from the FC 26 version

The EA URLs are unchanged: EA's `/api/fc` path has no game year in it. The code changed:

- `fc26_api.py` and `fc26_api_class.py` have become one file, `fc27_api.py` (`FC27API`).
- Four endpoints are new: member stats, member career stats, overall stats and playoff achievements.
- `find_club_id` is new. `search_club_by_name` now returns **all** matching clubs,
  where FC26 kept only the first.
- `get_club_matches` gives one clean row per match with the result. The old
  `get_club_matches_normalized` produced sparse `clubs<ID>.*` columns.
- `get_match_players` is new: per-player ratings and stats for each match.
- Match times are real dates in your chosen timezone, not a hard-coded +1h/+2h shift.
- Friendly results are worked out from the score, because EA doesn't fill in win/loss for friendlies.
- Errors raise `FC27APIError` instead of silently returning `None`.
- `requests` was replaced with Python's built-in `urllib`, so pandas is the only dependency.

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests run offline, using EA responses saved in `tests/fixtures/`. They keep the real structure,
but every club and player name, id and date is a placeholder.

## License

MIT, see [LICENSE.md](LICENSE.md).
