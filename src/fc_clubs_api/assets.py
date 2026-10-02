"""URLs for club crests, division badges and reputation tier icons.

These images are served by EA's content CDNs, not by the Pro Clubs API, and need
no special headers. All URLs below were checked to return a PNG on 2026-10-02.

Crest rule (from https://github.com/Interactive-63/eafc-pro-clubs-api-research):
a club in ``clubs/matches`` has a ``TEAM`` field that is normally the crest id to
use. It equals ``teamId`` when the club uses a real-world badge and
``customKit.crestAssetId`` when it uses a custom one. In rare cases neither
matches and the ``TEAM`` URL 404s; fall back to ``crestAssetId`` or the
not-found crest. Outside ``clubs/matches`` (e.g. ``clubs/info``) there is no
``TEAM`` field; there ``customKit.selectedKitType == "1"`` was observed to mean
a custom crest and ``"0"`` a real badge.
"""

from __future__ import annotations

from typing import List, Optional, Union

IdLike = Union[int, str]

CREST_URL_TEMPLATE = (
    "https://eafc24.content.easports.com/fifa/fltOnlineAssets/"
    "24B23FDE-7835-41C2-87A2-F453DFDB2E82/2024/fcweb/crests/256x256/l{id}.png"
)
NOT_FOUND_CREST_URL = (
    "https://media.contentapi.ea.com/content/dam/eacom/fc/pro-clubs/notfound-crest.png"
)
DIVISION_CREST_URL_TEMPLATE = (
    "https://media.contentapi.ea.com/content/dam/eacom/fc/pro-clubs/divisioncrest{division}.png"
)
REPUTATION_TIER_URL_TEMPLATE = (
    "https://media.contentapi.ea.com/content/dam/eacom/fc/pro-clubs/reputation-tier{tier}.png"
)


def _valid_id(value: Optional[IdLike]) -> Optional[int]:
    """``int(value)`` if it is a usable (positive) id, else None."""
    if value is None or value == "":
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def crest_url(asset_id: IdLike) -> str:
    """256x256 crest PNG for a ``TEAM``, ``teamId`` or ``crestAssetId`` value."""
    number = _valid_id(asset_id)
    if number is None:
        raise ValueError(f"asset_id must be a positive id, not {asset_id!r}")
    return CREST_URL_TEMPLATE.format(id=number)


def crest_url_candidates(
    *,
    team: Optional[IdLike] = None,
    team_id: Optional[IdLike] = None,
    crest_asset_id: Optional[IdLike] = None,
    selected_kit_type: Optional[IdLike] = None,
) -> List[str]:
    """Crest URLs to try in order, ending with the not-found crest.

    Useful for front ends: show the first URL and fall back to the next one when
    an image fails to load.

    Args:
        team: ``clubs[id].TEAM`` from ``clubs/matches`` (best source).
        team_id: ``teamId`` from the club details.
        crest_asset_id: ``customKit.crestAssetId`` from the club details.
        selected_kit_type: ``customKit.selectedKitType``; ``1`` puts the custom
            crest before the real badge when ``team`` is unknown.
    """
    order = [team]
    if str(selected_kit_type) == "0":
        order += [team_id, crest_asset_id]
    else:
        order += [crest_asset_id, team_id]

    urls: List[str] = []
    for value in order:
        number = _valid_id(value)
        if number is not None:
            url = CREST_URL_TEMPLATE.format(id=number)
            if url not in urls:
                urls.append(url)
    urls.append(NOT_FOUND_CREST_URL)
    return urls


def club_crest_url(
    *,
    team: Optional[IdLike] = None,
    team_id: Optional[IdLike] = None,
    crest_asset_id: Optional[IdLike] = None,
    selected_kit_type: Optional[IdLike] = None,
) -> str:
    """The single best crest URL for a club (the first of :func:`crest_url_candidates`)."""
    return crest_url_candidates(
        team=team,
        team_id=team_id,
        crest_asset_id=crest_asset_id,
        selected_kit_type=selected_kit_type,
    )[0]


def division_crest_url(division: IdLike) -> str:
    """Division badge PNG. ``division`` is 1 (top) to 6."""
    number = _valid_id(division)
    if number is None or number > 6:
        raise ValueError(f"division must be 1-6, not {division!r}")
    return DIVISION_CREST_URL_TEMPLATE.format(division=number)


def reputation_tier_url(tier: IdLike) -> str:
    """Reputation tier icon PNG. ``tier`` is 0 to 3 (``reputationtier`` in EA's data)."""
    try:
        number = int(tier)
    except (TypeError, ValueError):
        number = -1
    if not 0 <= number <= 3:
        raise ValueError(f"tier must be 0-3, not {tier!r}")
    return REPUTATION_TIER_URL_TEMPLATE.format(tier=number)


def kit_color_hex(value: IdLike) -> str:
    """Convert EA's decimal RGB kit/crest colour to hex: ``"16777215"`` -> ``"#ffffff"``."""
    number = int(value)
    if not 0 <= number <= 0xFFFFFF:
        raise ValueError(f"colour must be 0-16777215, not {value!r}")
    return f"#{number:06x}"
