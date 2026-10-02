"""Command line: ``fc-clubs "Club Name"`` or ``python -m fc_clubs_api "Club Name"``.

Prints the club's recent matches and current-season member stats, as tables
when pandas is installed, otherwise (or with ``--json``) as JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from . import FC27API, MatchType, __version__
from .exceptions import FC27APIError


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="fc-clubs",
        description="Show a Pro Clubs club's recent matches and member stats.",
    )
    parser.add_argument("club", help="club name (exact) or numeric club id")
    parser.add_argument(
        "--match-type",
        default=MatchType.LEAGUE.value,
        choices=[member.value for member in MatchType],
        help="which matches to show (default: leagueMatch)",
    )
    parser.add_argument("--timezone", default="UTC", help="IANA timezone, e.g. Europe/London")
    parser.add_argument("--json", action="store_true", help="print JSON instead of tables")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    as_json = args.json
    if not as_json:
        try:
            import pandas  # noqa: F401
        except ImportError:
            as_json = True

    api = FC27API(timezone=args.timezone, output="records" if as_json else "dataframe")
    try:
        club_id = int(args.club) if args.club.isdigit() else api.find_club_id(args.club)
        matches = api.get_club_matches(club_id, args.match_type)
        members = api.get_member_stats(club_id)
    except (FC27APIError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if as_json:
        payload = {"clubId": club_id, "matches": matches, "members": members}
        print(json.dumps(payload, indent=2, default=str, ensure_ascii=False))
        return 0

    print(f"Club id: {club_id}\n")
    print("Recent matches:")
    if matches.empty:
        print("  (none)")
    else:
        columns = ["timestamp", "opponentName", "goals", "goalsAgainst", "result"]
        print(matches[columns].to_string(index=False))
    print("\nMembers (this season):")
    if members.empty:
        print("  (none)")
    else:
        columns = ["name", "gamesPlayed", "goals", "assists", "averageRating"]
        top = members.sort_values("goals", ascending=False)
        print(top[columns].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
