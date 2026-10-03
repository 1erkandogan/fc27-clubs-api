"""Decoded match events: how each player passes and wins the ball (needs pandas).

python examples/match_events.py 1001
"""

import sys

from fc_clubs_api import FC27API

club_id = int(sys.argv[1]) if len(sys.argv) > 1 else int(input("Club id: "))
api = FC27API(output="dataframe")

players = api.get_match_players(club_id, include_events=True)
totals = players.groupby("name")[
    [
        "passesCompleted",
        "passesCompletedForward",
        "passesCompletedLong",
        "possessionWonDefensiveThird",
        "possessionWonMiddleThird",
        "possessionWonAttackingThird",
        "outOfPosition",
    ]
].sum()
totals["forwardShare"] = (totals["passesCompletedForward"] / totals["passesCompleted"]).round(2)

print(totals.sort_values("passesCompleted", ascending=False).to_string())
