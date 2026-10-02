"""The HTTP layer: the only module that talks to EA.

It uses ``urllib`` from the standard library on purpose, so the base install has
no third-party dependencies.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Mapping, Optional

from .exceptions import FC27ConnectionError, FC27HTTPError, FC27ResponseError

BASE_URL = "https://proclubs.ea.com/api/fc"

# EA's servers sit behind Akamai, which blocks requests that don't look like
# they come from the proclubs.ea.com website itself: without these headers EA
# answers 403 or never answers. "sec-fetch-site: same-origin" is the key one.
HEADERS = {
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
    "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    "sec-fetch-site": "same-origin",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    ),
}


def build_url(endpoint: str, params: Mapping[str, Any]) -> str:
    """Return the full URL for ``endpoint`` with ``params`` as the query string."""
    return f"{BASE_URL}/{endpoint.strip('/')}?{urllib.parse.urlencode(params)}"


def request_json(
    endpoint: str,
    params: Mapping[str, Any],
    *,
    timeout: float,
    headers: Optional[Mapping[str, str]] = None,
) -> Any:
    """GET ``endpoint`` and return the decoded JSON body.

    JSON ``null`` (which EA sometimes sends instead of ``[]``) is returned as ``[]``.

    Raises:
        FC27HTTPError: EA answered with an error status.
        FC27ConnectionError: EA could not be reached or timed out.
        FC27ResponseError: The body was not JSON.
    """
    url = build_url(endpoint, params)
    request = urllib.request.Request(url, headers=dict(headers or HEADERS))

    # `from None` keeps tracebacks short: the message already says what failed.
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        raise FC27HTTPError(error.code, url) from None
    except OSError as error:  # no network, timeout, DNS failure, ...
        raise FC27ConnectionError(f"Could not reach EA ({error}) for {url}", url) from None
    except json.JSONDecodeError:
        raise FC27ResponseError(f"EA did not send JSON for {url}", url) from None

    if data is None:
        return []
    return data
