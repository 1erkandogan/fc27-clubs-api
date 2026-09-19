"""Find a club and print its recent matches and top scorers.

Run from the repo root:  python examples/quickstart.py "Your Club Name"
"""

import sys
from pathlib import Path

# This script lives in examples/, but fc27_api.py is one folder up. Adding that
# folder to sys.path (the list of places Python looks for imports) lets
# `from fc27_api import ...` find it. Your own scripts don't need this if
# they sit next to fc27_api.py.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fc27_api import FC27API  # noqa: E402  (import after the sys.path line)

# The club name comes from the command line; if it's missing, ask for it.
if len(sys.argv) > 1:
    club_name = sys.argv[1]
else:
    club_name = input("Club name: ")

api = FC27API(timezone="Europe/Istanbul")

# find_club_id raises ValueError with a list of options if the name is ambiguous.
try:
    club_id = api.find_club_id(club_name)
except ValueError as error:
    sys.exit(str(error))

print(f"Club id: {club_id}\n")

matches = api.get_club_matches(club_id)
print("Last league matches:")
print(matches[["timestamp", "opponentName", "goals", "goalsAgainst", "result"]], "\n")

members = api.get_member_stats(club_id)
print("Top scorers this season:")
print(members.sort_values("goals", ascending=False).head(5)[["name", "goals", "assists", "averageRating"]])
