"""Find a club and print its recent matches and top scorers (needs pandas).

pip install "fc-clubs-api[pandas]"
python examples/quickstart.py "Your Club Name"
"""

import sys

from fc_clubs_api import FC27API, AmbiguousClubError, ClubNotFoundError

club_name = sys.argv[1] if len(sys.argv) > 1 else input("Club name: ")
api = FC27API(output="dataframe", timezone="Europe/London")

try:
    club_id = api.find_club_id(club_name)
except (ClubNotFoundError, AmbiguousClubError) as error:
    sys.exit(str(error))

print(f"Club id: {club_id}\n")

matches = api.get_club_matches(club_id)
print("Last league matches:")
print(matches[["timestamp", "opponentName", "goals", "goalsAgainst", "result"]], "\n")

members = api.get_member_stats(club_id)
top = members.sort_values("goals", ascending=False).head(5)
print("Top scorers this season:")
print(top[["name", "goals", "assists", "averageRating"]])
