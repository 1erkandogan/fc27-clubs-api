"""Shared test helpers.

The tests never contact EA. ``fake_ea`` replaces ``urllib.request.urlopen`` (the
function that sends the request) with a fake that returns a saved response from
``tests/fixtures/``. The fixtures have the exact shape of real EA responses, but
every club, player, id, date and kit value is a placeholder: Example FC = 1001,
Opponent A = 2001, Player1, Player2, ...
"""

from __future__ import annotations

import io
import json
import urllib.parse
from pathlib import Path
from unittest.mock import patch

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name):
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def fake_ea(payload):
    """Pretend EA answers every request with ``payload`` (as JSON text)."""
    body = json.dumps(payload).encode("utf-8")
    # side_effect builds a fresh response for every call, like a real server.
    return patch("urllib.request.urlopen", side_effect=lambda *args, **kwargs: io.BytesIO(body))


def sent_request(fake):
    """(endpoint path, query params) of the last request our code sent."""
    request = fake.call_args[0][0]
    url = urllib.parse.urlparse(request.full_url)
    return url.path.replace("/api/fc/", ""), dict(urllib.parse.parse_qsl(url.query))


@pytest.fixture
def no_pandas():
    """Make ``import pandas`` fail, as on a base install."""
    with patch.dict("sys.modules", {"pandas": None}):
        yield
