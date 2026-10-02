"""Error types: specific subclasses stay catchable as the old base types."""

import io
import urllib.error
from unittest.mock import patch

import pytest
from conftest import fake_ea, fixture

from fc_clubs_api import (
    FC27API,
    AmbiguousClubError,
    ClubNotFoundError,
    FC27APIError,
    FC27ConnectionError,
    FC27HTTPError,
    FC27ResponseError,
)


def test_http_error():
    error = urllib.error.HTTPError("url", 403, "Forbidden", {}, None)
    with patch("urllib.request.urlopen", side_effect=error), pytest.raises(FC27HTTPError) as caught:
        FC27API(output="raw").get_club_details(1001)
    assert caught.value.status_code == 403
    assert "clubs/info" in caught.value.url
    assert isinstance(caught.value, FC27APIError)


def test_timeout():
    timeout = patch("urllib.request.urlopen", side_effect=TimeoutError("timed out"))
    with timeout, pytest.raises(FC27ConnectionError):
        FC27API(output="raw").get_club_details(1001)


def test_not_json():
    blocked = patch("urllib.request.urlopen", return_value=io.BytesIO(b"<html>blocked</html>"))
    with blocked, pytest.raises(FC27ResponseError):
        FC27API(output="raw").get_club_details(1001)


def test_club_lookup_errors_are_value_errors():
    with fake_ea([]), pytest.raises(ClubNotFoundError):
        FC27API().find_club_id("nothing")
    with fake_ea(fixture("search")), pytest.raises(AmbiguousClubError) as caught:
        FC27API().find_club_id("example")
    assert caught.value.candidates == [(1001, "Example FC"), (1002, "Example United")]
    assert issubclass(ClubNotFoundError, ValueError)
    assert issubclass(AmbiguousClubError, ValueError)
