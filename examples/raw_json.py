"""Save EA's raw responses to JSON files, e.g. to build a match archive.

EA only keeps a club's last 10 matches per type, so running this on a schedule
and de-duplicating on matchId is the only way to keep a longer history.

    python examples/raw_json.py 1001 archive/
"""

import json
import sys
from pathlib import Path

from fc_clubs_api import FC27API, MatchType

club_id = int(sys.argv[1])
folder = Path(sys.argv[2] if len(sys.argv) > 2 else "archive")
folder.mkdir(parents=True, exist_ok=True)

api = FC27API(output="raw")

for match_type in MatchType:
    for match in api.get_club_matches(club_id, match_type):
        path = folder / f"{match['matchId']}.json"
        if not path.exists():
            path.write_text(json.dumps(match, ensure_ascii=False), encoding="utf-8")
            print("saved", path)
