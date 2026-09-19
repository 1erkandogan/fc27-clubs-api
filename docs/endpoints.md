# Endpoint reference

All endpoints are `GET https://proclubs.ea.com/api/fc/<endpoint>` and need
`platform=common-gen5` plus the browser-style headers in `fc27_api.py`
(`HEADERS`). Without them EA's edge (Akamai) answers **403** or never answers
(the request hangs until it times out). Plain `curl` is blocked even with the
headers, while Python (`urllib` or `requests`) gets through.

Observed on **2026-09-19** against a real club. The structure is real, but all names,
ids, dates, kit values and club totals below are **placeholders** ("Example FC" = `1001`,
"Opponent A" = `2001`, "Player1", ...). The same anonymized responses are in
[`tests/fixtures/`](../tests/fixtures/).

General quirks:

- Almost every value is a **string**, including numbers (`"25"`, `"7.4"`). The
  client converts numeric columns for you.
- Some parameters are singular (`clubId`) and some plural (`clubIds`). Only single
  ids have been tested.
- Empty results are `[]`. JSON `null` has also been reported for matches.

| Endpoint | Club parameter | Python method |
|---|---|---|
| [`allTimeLeaderboard/search`](#alltimeleaderboardsearch) | `clubName` | `search_club_by_name` |
| [`clubs/info`](#clubsinfo) | `clubIds` | `get_club_details` |
| [`clubs/overallStats`](#clubsoverallstats) | `clubIds` | `get_club_overall_stats` |
| [`members/stats`](#membersstats) | `clubId` | `get_member_stats` |
| [`members/career/stats`](#memberscareerstats) | `clubId` | `get_member_career_stats` |
| [`clubs/matches`](#clubsmatches) | `clubIds` | `get_club_matches`, `get_match_players` |
| [`club/playoffAchievements`](#clubplayoffachievements) | `clubId` | `get_playoff_achievements` |

---

## allTimeLeaderboard/search

`?platform=common-gen5&clubName=example`

Returns a **list** of every club whose name contains the text. Each item has all-time
league totals plus a nested `clubInfo`, which is the same object `clubs/info` returns.

```json
[
  {
    "clubId": "1001",
    "wins": "20", "losses": "3", "ties": "2",
    "gamesPlayed": "25", "gamesPlayedPlayoff": "0",
    "goals": "60", "goalsAgainst": "25", "cleanSheets": "10",
    "points": "62", "reputationtier": "1",
    "promotions": "3", "relegations": "0", "bestDivision": "2",
    "clubInfo": {
      "name": "Example FC", "clubId": 1001, "regionId": 1000000, "teamId": 100,
      "customKit": { "stadName": "Example Stadium", "kitId": "0", "...": "..." }
    },
    "platform": "common-gen5",
    "clubName": "Example FC",
    "currentDivision": "2"
  }
]
```

## clubs/info

`?platform=common-gen5&clubIds=1001`

Returns a **dict keyed by club id (string)**.

```json
{
  "1001": {
    "name": "Example FC",
    "clubId": 1001,
    "regionId": 1000000,
    "teamId": 100,
    "customKit": {
      "stadName": "Example Stadium",
      "kitId": "0", "seasonalTeamId": "0", "seasonalKitId": "0",
      "selectedKitType": "0", "customKitId": "0",
      "kitColor1": "16777215", "kitColor2": "0", "kitColor3": "0", "kitColor4": "0",
      "customAwayKitId": "0",
      "kitAColor1": "16777215", "kitAColor2": "0", "kitAColor3": "0", "kitAColor4": "0",
      "customThirdKitId": "0",
      "kitThrdColor1": "16777215", "kitThrdColor2": "0", "kitThrdColor3": "0", "kitThrdColor4": "0",
      "dCustomKit": "0", "customKeeperKitId": "0",
      "crestColor": "0", "crestAssetId": "0"
    }
  }
}
```

Kit colours are decimal RGB: `16777215` = `0xFFFFFF` (white), so `f"#{int(c):06x}"`.

## clubs/overallStats

`?platform=common-gen5&clubIds=1001`

Returns a **list with one item**.

```json
[
  {
    "clubId": "1001",
    "bestDivision": null,
    "bestFinishGroup": null,
    "finishesInDivision1Group1": "0", "...": "... up to finishesInDivision6Group1",
    "gamesPlayed": "25", "gamesPlayedPlayoff": "0",
    "goals": "60", "goalsAgainst": "25",
    "promotions": "3", "relegations": "0",
    "wins": "20", "losses": "3", "ties": "2",
    "lastMatch0": "1", "...": "... up to lastMatch9",
    "lastOpponent0": "2001", "...": "... up to lastOpponent9",
    "wstreak": "3",
    "unbeatenstreak": "8",
    "skillRating": "1500",
    "reputationtier": "1",
    "leagueAppearances": "25"
  }
]
```

- `bestDivision` / `bestFinishGroup` can be `null`.
- `lastOpponent0`–`9` are the club ids of the last 10 opponents, newest first.
  `lastMatch0`–`9` held `1` or `-1`; what `-1` means is unconfirmed.

## members/stats

`?platform=common-gen5&clubId=1001`

Current-season stats. Returns `{members: [...], positionCount: {...}}`.

```json
{
  "members": [
    {
      "name": "Player1",
      "gamesPlayed": "18", "winRate": "94",
      "goals": "2", "assists": "0",
      "cleanSheetsDef": "7", "cleanSheetsGK": "0",
      "shotSuccessRate": "50", "passesMade": "138", "passSuccessRate": "84",
      "ratingAve": "7.4",
      "tacklesMade": "24", "tackleSuccessRate": "26",
      "proName": "Pro 1", "proPos": "5", "proStyle": "0", "proHeight": "187",
      "proNationality": "165", "proOverall": "78", "proOverallStr": "78",
      "manOfTheMatch": "1", "redCards": "0",
      "prevGoals": "0", "prevGoals1": "0", "...": "... up to prevGoals10",
      "favoritePosition": "defender"
    }
  ],
  "positionCount": { "midfielder": 4, "goalkeeper": 1, "forward": 6, "defender": 3 }
}
```

- `name` is the platform gamertag. `proName` is the in-game player name and can be `""`.
- `proPos`, `proStyle` and `proNationality` are numeric EA ids. No lookup table has been published.
- `positionCount` counts `favoritePosition`. The client drops it; use
  `df["favoritePosition"].value_counts()` instead.

## members/career/stats

`?platform=common-gen5&clubId=1001`

Career totals at this club. The wrapper is the same as `members/stats`, with fewer fields:

```json
{
  "members": [
    {
      "name": "Player1",
      "proPos": "25",
      "gamesPlayed": "29", "goals": "5", "assists": "3",
      "manOfTheMatch": "1", "ratingAve": "7.3", "prevGoals": "0",
      "favoritePosition": "forward"
    }
  ],
  "positionCount": { "midfielder": 4, "goalkeeper": 1, "forward": 7, "defender": 2 }
}
```

## clubs/matches

`?platform=common-gen5&clubIds=1001&matchType=leagueMatch&maxResultCount=10`

`matchType` is `leagueMatch`, `friendlyMatch` or `playoffMatch`. Returns a **list of
matches**, newest first. `playoffMatch` returned `[]`.

```json
[
  {
    "matchId": "1000000000001",
    "timestamp": 1767297600,
    "timeAgo": { "number": 4, "unit": "hours" },
    "clubs": {
      "1001": {
        "date": "1767297600", "gameNumber": "0", "season_id": "0",
        "matchType": "1",
        "goals": "4", "goalsAgainst": "0", "score": "4",
        "wins": "1", "ties": "0", "losses": "0",
        "result": "16385", "winnerByDnf": "1",
        "TEAM": "100",
        "details": { "name": "Example FC", "clubId": 1001, "...": "same as clubs/info" }
      },
      "2001": { "...": "opponent, same shape" }
    },
    "players": {
      "1001": {
        "<playerId>": {
          "playername": "...", "pos": "midfielder", "rating": "6.10",
          "goals": "0", "assists": "0", "shots": "0",
          "passattempts": "0", "passesmade": "0",
          "tackleattempts": "0", "tacklesmade": "0",
          "saves": "0", "goalsconceded": "0",
          "cleansheetsany": "0", "cleansheetsdef": "0", "cleansheetsgk": "0",
          "mom": "0", "redcards": "0",
          "secondsPlayed": "635", "gameTime": "635",
          "wins": "0", "losses": "1", "userResult": "6",
          "archetypeid": "11", "vproattr": "NH", "vprohackreason": "0",
          "ballDiveSaves": "0", "crossSaves": "0", "goodDirectionSaves": "0",
          "parrySaves": "0", "punchSaves": "0", "reflexSaves": "0",
          "SCORE": "0", "namespace": "2", "realtimegame": "104", "realtimeidle": "1",
          "match_event_aggregate_0": "0:1,1:1,100:1,106:2,...",
          "match_event_aggregate_1": "", "match_event_aggregate_2": "", "match_event_aggregate_3": ""
        }
      },
      "2001": { "...": "..." }
    },
    "aggregate": {
      "1001": { "...": "same fields as a player, summed over the club (no playername)" },
      "2001": { "...": "..." }
    }
  }
]
```

- `clubs`, `players` and `aggregate` are keyed by **club id**. `players[clubId]` is keyed by **player id**.
- `timestamp` is Unix seconds, UTC.
- `result` codes seen in league matches: `1` = win, `2` = loss, `4` = draw,
  `16385` = win by opponent DNF (quit), `10` = loss by DNF. `winnerByDnf` is `"1"` for the club that was awarded the win.
- **Friendlies** set `wins`/`ties`/`losses`/`result` to `"0"` for both clubs, so
  work out the result from `goals` vs `goalsAgainst`. `get_club_matches` does this.
- `clubs[id].matchType` was `"1"` for league matches and `"5"` for friendlies.
- `match_event_aggregate_*` are `eventId:count` lists. The event ids are undocumented.

## club/playoffAchievements

`?platform=common-gen5&clubId=1001`

Returned `[]`. The shape of a populated item is unknown.
