# Recipes

All examples assume:

```python
from fc_clubs_api import FC27API

api = FC27API(timezone="Europe/London")
club_id = api.find_club_id("Your Club Name")
```

## With pandas

```python
api = FC27API(output="dataframe", timezone="Europe/London")

# Top 5 scorers this season
members = api.get_member_stats(club_id)
members.sort_values("goals", ascending=False).head(5)[["name", "goals", "assists"]]

# Last 5 league results
matches = api.get_club_matches(club_id)
matches.head(5)[["timestamp", "opponentName", "goals", "goalsAgainst", "result"]]

# Win rate over the last 10 league matches
wins = (matches["result"] == "win").sum()
print(f"Won {wins} of {len(matches)}")

# One player's recent matches
players = api.get_match_players(club_id)
players[players["name"] == "YourGamertag"][["timestamp", "rating", "goals", "assists"]]

# Average match rating per player, best first
players.groupby("name")["rating"].mean().sort_values(ascending=False)

# Save to CSV / Excel
members.to_csv("members.csv", index=False)
members.to_excel("members.xlsx", index=False)   # needs: pip install openpyxl
```

## Without pandas

Records are the default, so the `api` from the top of the page works as is.

```python
members = api.get_member_stats(club_id)
top = sorted(members, key=lambda m: m["goals"], reverse=True)[:5]
for m in top:
    print(f'{m["name"]:<20} {m["goals"]:>3} goals {m["assists"]:>3} assists')

form = "".join(m["result"][0].upper() for m in api.get_club_matches(club_id))
print(form)   # e.g. "WWDLW..."
```

## Match events

```python
api = FC27API(output="dataframe")
players = api.get_match_players(club_id, include_events=True)

# Who progresses the ball? Share of completed passes played forward
p = players.groupby("name")[["passesCompletedForward", "passesCompleted"]].sum()
(p["passesCompletedForward"] / p["passesCompleted"]).sort_values(ascending=False)

# Where does each player win the ball back?
players.groupby("name")[[
    "possessionWonDefensiveThird", "possessionWonMiddleThird", "possessionWonAttackingThird",
]].sum()

# Positioning: times out of position per 90 minutes
per90 = players.groupby("name")[["outOfPosition", "secondsPlayed"]].sum()
per90["outOfPosition"] / per90["secondsPlayed"] * 5400
```

## Raw JSON for your own storage

```python
import json
from datetime import datetime, timezone

raw = api.get_club_matches(club_id, output="raw")
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
with open(f"matches-{club_id}-{stamp}.json", "w", encoding="utf-8") as f:
    json.dump(raw, f, ensure_ascii=False)
```

EA only keeps the last 10 matches per type. Saving raw responses on a schedule is
the only way to build a longer history; de-duplicate on `matchId`.

## Crests in a web page or bot

```python
from fc_clubs_api import assets

club = api.get_club_details(club_id, output="records")[0]
overall = api.get_club_overall_stats(club_id, output="records")[0]

html = f'<img src="{club["crestUrl"]}" alt="{club["clubName"]}">'
badge = assets.division_crest_url(overall["bestDivision"] or 6)
```

## Many clubs politely

```python
import time

for club_id in club_ids:
    stats = api.get_club_overall_stats(club_id, output="records")
    ...
    time.sleep(1)   # no built-in rate limiting; don't get blocked
```

## Fields this package doesn't map

```python
api.get_json("clubs/overallStats", {"clubIds": club_id})  # any endpoint, raw
api.get_member_stats(club_id, all_columns=True)           # every EA field, EA names
```
