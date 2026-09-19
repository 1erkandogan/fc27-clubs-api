"""Unofficial client for the EA Sports FC 27 Pro Clubs API.

Every method returns a pandas DataFrame (a table). New to this code? Read
docs/how-it-works.md, which walks through this file step by step.
Raw response formats are in docs/endpoints.md.
"""

# Built into Python, no install needed:
import json             # turns the text EA sends back into Python dicts and lists
import urllib.error     # the errors urllib raises (e.g. EA answering 403)
import urllib.parse     # builds the "?platform=...&clubIds=..." part of a URL
import urllib.request   # sends the request to EA

# The only thing you need to install (pip install pandas). It gives us tables
# (DataFrames) that are easy to sort, filter, average and save to Excel/CSV.
import pandas as pd


BASE_URL = "https://proclubs.ea.com/api/fc"

MATCH_TYPES = ("leagueMatch", "friendlyMatch", "playoffMatch")

# EA's servers sit behind Akamai, which blocks requests that don't look like
# they come from the proclubs.ea.com website itself: without these headers you
# get a 403 error or no answer at all. "sec-fetch-site: same-origin" is the key one.
HEADERS = {
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
    "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    "sec-fetch-site": "same-origin",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    ),
}

# EA returns a lot of columns with inconsistent names (passesmade, ratingAve,
# mom, ...). By default each method keeps only the useful ones and renames them.
# Format: "EA's name": "our name". Pass all_columns=True to get everything as-is.
COLUMNS = {
    "search": {
        "clubId": "clubId",
        "clubName": "clubName",
        "currentDivision": "currentDivision",
        "bestDivision": "bestDivision",
        "gamesPlayed": "gamesPlayed",
        "wins": "wins",
        "ties": "ties",
        "losses": "losses",
        "goals": "goals",
        "goalsAgainst": "goalsAgainst",
        "cleanSheets": "cleanSheets",
        "points": "points",
    },
    "details": {
        "clubId": "clubId",
        "name": "clubName",
        "regionId": "regionId",
        "teamId": "teamId",
        "customKit.stadName": "stadium",
    },
    "overall": {
        "clubId": "clubId",
        "gamesPlayed": "gamesPlayed",
        "wins": "wins",
        "ties": "ties",
        "losses": "losses",
        "goals": "goals",
        "goalsAgainst": "goalsAgainst",
        "skillRating": "skillRating",
        "wstreak": "winStreak",
        "unbeatenstreak": "unbeatenStreak",
        "promotions": "promotions",
        "relegations": "relegations",
        "bestDivision": "bestDivision",
    },
    "members": {
        "name": "name",
        "proName": "playerName",
        "favoritePosition": "position",
        "proOverall": "overall",
        "gamesPlayed": "gamesPlayed",
        "winRate": "winRate",
        "goals": "goals",
        "assists": "assists",
        "ratingAve": "averageRating",
        "manOfTheMatch": "manOfTheMatch",
        "shotSuccessRate": "shotSuccessRate",
        "passesMade": "passesMade",
        "passSuccessRate": "passSuccessRate",
        "tacklesMade": "tacklesMade",
        "tackleSuccessRate": "tackleSuccessRate",
        "cleanSheetsDef": "cleanSheetsDef",
        "cleanSheetsGK": "cleanSheetsGK",
        "redCards": "redCards",
    },
    "players": {
        "matchId": "matchId",
        "timestamp": "timestamp",
        "clubId": "clubId",
        "playername": "name",
        "pos": "position",
        "rating": "rating",
        "goals": "goals",
        "assists": "assists",
        "shots": "shots",
        "passesmade": "passesMade",
        "passattempts": "passAttempts",
        "tacklesmade": "tacklesMade",
        "tackleattempts": "tackleAttempts",
        "saves": "saves",
        "cleansheetsany": "cleanSheet",
        "mom": "manOfTheMatch",
        "redcards": "redCards",
        "secondsPlayed": "secondsPlayed",
    },
}


class FC27APIError(Exception):
    """Raised when EA can't be reached, refuses the request, or doesn't send JSON."""


def to_dataframe(records):
    """Turn a list of dicts from EA into a DataFrame.

    Two fixes happen here:
    1. Nested dicts become their own columns (json_normalize), e.g.
       {"clubInfo": {"name": "X"}} becomes a column called "clubInfo.name".
    2. EA sends numbers as text ("25", "7.4"). Text can't be summed or sorted
       numerically, so every column that is fully numeric is converted.
    """
    if not records:
        return pd.DataFrame()

    df = pd.json_normalize(records)
    for column in df.columns:
        try:
            df[column] = pd.to_numeric(df[column])
        except (ValueError, TypeError):
            pass  # a text column such as a name: leave it as text
    return df


def pick_columns(df, columns, all_columns):
    """Keep only the columns listed in `columns` and give them friendly names."""
    if all_columns:
        return df

    keep = []
    for ea_name in columns:
        if ea_name in df.columns:
            keep.append(ea_name)
    return df[keep].rename(columns=columns)


class FC27API:
    """Talks to EA's Pro Clubs API.

    platform: "common-gen5" (PS5 / Xbox Series / PC). The only one tested.
    timeout:  seconds to wait for EA before giving up.
    timezone: timezone for match times, e.g. "Europe/Istanbul". Default "UTC".
    """

    def __init__(self, platform="common-gen5", timeout=10, timezone="UTC"):
        self.platform = platform
        self.timeout = timeout
        self.timezone = timezone

    # ------------------------------------------------------------------ basics

    def get_json(self, endpoint, params):
        """Ask EA for `endpoint` and return the answer as Python dicts/lists.

        Use this if you want EA's raw, untouched response, for example
        api.get_json("clubs/info", {"clubIds": 1001})
        """
        query = {"platform": self.platform}
        query.update(params)
        url = BASE_URL + "/" + endpoint + "?" + urllib.parse.urlencode(query)
        request = urllib.request.Request(url, headers=HEADERS)

        # `from None` keeps the error message short: our message already says
        # what went wrong, so Python's internal error chain isn't shown.
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.load(response)
        except urllib.error.HTTPError as error:
            raise FC27APIError(f"EA answered with error {error.code} for {url}") from None
        except OSError as error:  # no internet, timeout, DNS problem, ...
            raise FC27APIError(f"Could not reach EA ({error}) for {url}") from None
        except json.JSONDecodeError:
            raise FC27APIError(f"EA did not send JSON for {url}") from None

        # EA sometimes answers "null" instead of an empty list.
        if data is None:
            return []
        return data

    def _convert_times(self, df):
        """EA gives times as Unix seconds (1767297600); make them readable dates."""
        if not df.empty:
            utc_times = pd.to_datetime(df["timestamp"], unit="s", utc=True)
            df["timestamp"] = utc_times.dt.tz_convert(self.timezone)
        return df

    # ------------------------------------------------------------------- clubs

    def search_club_by_name(self, club_name, all_columns=False):
        """All clubs whose name contains `club_name`, one row per club."""
        results = self.get_json("allTimeLeaderboard/search", {"clubName": club_name})
        return pick_columns(to_dataframe(results), COLUMNS["search"], all_columns)

    def find_club_id(self, club_name):
        """Return the id (a number) of the club called `club_name`.

        Uses the club with exactly that name (ignoring upper/lower case), or the
        only search result. If it can't decide, the error lists the options.
        """
        results = self.get_json("allTimeLeaderboard/search", {"clubName": club_name})
        if len(results) == 0:
            raise ValueError(f"No club found for {club_name!r}")

        for club in results:
            if club["clubName"].lower() == club_name.lower():
                return int(club["clubId"])

        if len(results) == 1:
            return int(results[0]["clubId"])

        options = []
        for club in results:
            options.append(f"{club['clubName']} (id {club['clubId']})")
        raise ValueError(
            f"{len(results)} clubs match {club_name!r}: {', '.join(options)}. "
            "Use the exact club name, or use the id directly."
        )

    def get_club_details(self, club_id, all_columns=False):
        """One row: club name, ids and stadium (all_columns adds kit details)."""
        data = self.get_json("clubs/info", {"clubIds": club_id})
        # EA answers {"1001": {...club...}}; we only need the {...club...} part.
        clubs = list(data.values())
        return pick_columns(to_dataframe(clubs), COLUMNS["details"], all_columns)

    def get_club_overall_stats(self, club_id, all_columns=False):
        """One row: wins/draws/losses, goals, streaks, skill rating."""
        data = self.get_json("clubs/overallStats", {"clubIds": club_id})
        return pick_columns(to_dataframe(data), COLUMNS["overall"], all_columns)

    def get_playoff_achievements(self, club_id):
        """Playoff achievements (EA has only returned an empty list so far)."""
        return to_dataframe(self.get_json("club/playoffAchievements", {"clubId": club_id}))

    # ----------------------------------------------------------------- members

    def get_member_stats(self, club_id, all_columns=False):
        """One row per club member with their stats for the current season."""
        data = self.get_json("members/stats", {"clubId": club_id})
        members = data.get("members", [])
        return pick_columns(to_dataframe(members), COLUMNS["members"], all_columns)

    def get_member_career_stats(self, club_id):
        """One row per club member with their career totals at this club."""
        data = self.get_json("members/career/stats", {"clubId": club_id})
        return to_dataframe(data.get("members", []))

    # ----------------------------------------------------------------- matches

    def _get_matches(self, club_id, match_type, count):
        if match_type not in MATCH_TYPES:
            raise ValueError(f"match_type must be one of {MATCH_TYPES}, not {match_type!r}")
        params = {"clubIds": club_id, "matchType": match_type, "maxResultCount": count}
        return self.get_json("clubs/matches", params)

    def get_club_matches(self, club_id, match_type="leagueMatch", count=10):
        """One row per match, seen from `club_id`'s side, newest first.

        match_type: "leagueMatch", "friendlyMatch" or "playoffMatch".
        count:      how many recent matches to ask EA for.
        """
        # EA uses the club id as a text key ("1001"), so compare as text.
        club_id = str(club_id)
        rows = []

        for match in self._get_matches(club_id, match_type, count):
            clubs = match.get("clubs", {})
            us = clubs.get(club_id, {})

            # The other key in `clubs` is the opponent.
            opponent_id = None
            them = {}
            for other_id in clubs:
                if other_id != club_id:
                    opponent_id = other_id
                    them = clubs[other_id]

            goals = int(us.get("goals", 0))
            goals_against = int(us.get("goalsAgainst", 0))

            # League matches say who won in wins/ties/losses. Friendlies leave
            # those at "0", so there we compare the goals instead.
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

            rows.append({
                "matchId": match.get("matchId"),
                "timestamp": match.get("timestamp"),
                "matchType": match_type,
                "clubId": club_id,
                "clubName": us.get("details", {}).get("name"),
                "opponentId": opponent_id,
                "opponentName": them.get("details", {}).get("name"),
                "goals": goals,
                "goalsAgainst": goals_against,
                "result": result,
                # DNF = "did not finish": someone quit and the other team got the win.
                "dnf": us.get("winnerByDnf") == "1" or them.get("winnerByDnf") == "1",
            })

        return self._convert_times(to_dataframe(rows))

    def get_match_players(self, club_id, match_type="leagueMatch", count=10,
                          both_teams=False, all_columns=False):
        """One row per player per match: rating, goals, assists, passes, ...

        By default only `club_id`'s players are included; both_teams=True adds
        the opponents' players too (tell them apart with the clubId column).
        """
        club_id = str(club_id)
        rows = []

        for match in self._get_matches(club_id, match_type, count):
            # match["players"] looks like {"1001": {"<playerId>": {...stats...}}}
            for player_club, players in match.get("players", {}).items():
                if player_club != club_id and not both_teams:
                    continue  # skip the opponent's players
                for player_id, stats in players.items():
                    row = {
                        "matchId": match.get("matchId"),
                        "timestamp": match.get("timestamp"),
                        "clubId": player_club,
                        "playerId": player_id,
                    }
                    row.update(stats)  # add all of EA's stat fields to the row
                    rows.append(row)

        df = self._convert_times(to_dataframe(rows))
        return pick_columns(df, COLUMNS["players"], all_columns)


# This only runs when you start this file directly (python fc27_api.py),
# not when another script does `from fc27_api import FC27API`.
if __name__ == "__main__":
    api = FC27API()
    club_id = api.find_club_id(input("Club name: "))
    print(api.get_club_matches(club_id))
    print(api.get_member_stats(club_id))
