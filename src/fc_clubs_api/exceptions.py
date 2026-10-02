"""Exceptions raised by fc_clubs_api.

Everything that goes wrong while talking to EA is an :class:`FC27APIError`, so a
single ``except FC27APIError`` catches all network and response problems. Bad
input from the caller (an unknown match type, a club name that doesn't match
exactly one club) raises a :class:`ValueError` subclass instead.
"""

from __future__ import annotations

from typing import List, Optional, Tuple


class FC27APIError(Exception):
    """Base class: EA could not be reached, refused the request, or sent bad data.

    Attributes:
        url: The full request URL, when known.
    """

    def __init__(self, message: str, url: Optional[str] = None) -> None:
        super().__init__(message)
        self.url = url


class FC27HTTPError(FC27APIError):
    """EA answered with an HTTP error status (403 from Akamai is the common one).

    Attributes:
        status_code: The HTTP status code EA returned.
    """

    def __init__(self, status_code: int, url: str) -> None:
        super().__init__(f"EA answered with HTTP {status_code} for {url}", url)
        self.status_code = status_code


class FC27ConnectionError(FC27APIError):
    """EA could not be reached: no network, DNS failure or timeout."""


class FC27ResponseError(FC27APIError):
    """EA answered, but the body was not valid JSON (often an HTML block page)."""


class ClubNotFoundError(ValueError):
    """No club matched the name passed to :meth:`FC27API.find_club_id`."""


class AmbiguousClubError(ValueError):
    """Several clubs matched and none had exactly the requested name.

    Attributes:
        candidates: ``(club_id, club_name)`` pairs for every match, in EA's order.
    """

    def __init__(self, message: str, candidates: List[Tuple[int, str]]) -> None:
        super().__init__(message)
        self.candidates = candidates
