"""Unofficial Python client for the EA Sports FC 27 Pro Clubs API.

Quick start::

    from fc_clubs_api import FC27API

    api = FC27API()                          # list of dicts by default
    club_id = api.find_club_id("Example FC")
    api.get_club_matches(club_id)            # list of dicts
    api.get_club_matches(club_id, output="dataframe")  # pandas DataFrame
    api.get_club_matches(club_id, output="raw")        # EA's JSON

Documentation: https://1erkandogan.github.io/fc27-clubs-api/
"""

from . import assets, events
from ._http import BASE_URL, HEADERS
from ._output import OutputFormat
from ._version import __version__
from .client import FC27API
from .enums import LeaderboardScope, MatchType, Platform
from .exceptions import (
    AmbiguousClubError,
    ClubNotFoundError,
    FC27APIError,
    FC27ConnectionError,
    FC27HTTPError,
    FC27ResponseError,
)

__all__ = [
    "BASE_URL",
    "HEADERS",
    "AmbiguousClubError",
    "ClubNotFoundError",
    "FC27API",
    "FC27APIError",
    "FC27ConnectionError",
    "FC27HTTPError",
    "FC27ResponseError",
    "LeaderboardScope",
    "MatchType",
    "OutputFormat",
    "Platform",
    "__version__",
    "assets",
    "events",
]
