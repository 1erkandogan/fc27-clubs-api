"""A plain-Python club summary: no pandas required.

pip install fc-clubs-api
python examples/records_no_pandas.py 1001
"""

import sys

from fc_clubs_api import FC27API

club_id = int(sys.argv[1]) if len(sys.argv) > 1 else int(input("Club id: "))
api = FC27API(output="records")

club = api.get_club_details(club_id)[0]
stats = api.get_club_overall_stats(club_id)[0]
matches = api.get_club_matches(club_id)

print(f"{club['clubName']} ({club['stadium']})")
print(f"Record: {stats['wins']}W {stats['ties']}D {stats['losses']}L, skill {stats['skillRating']}")
print("Form:  ", " ".join(match["result"][0].upper() for match in matches))

for match in matches:
    when = match["timestamp"].strftime("%d %b %H:%M")
    score = f"{match['goals']}-{match['goalsAgainst']}"
    print(f"  {when}  {score:>5}  {match['opponentName']}")
