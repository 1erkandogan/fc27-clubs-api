"""Crest, division and reputation tier URLs."""

import pytest

from fc_clubs_api import assets


def crest(asset_id):
    return assets.CREST_URL_TEMPLATE.format(id=asset_id)


def test_team_field_wins():
    assert assets.club_crest_url(team="99090304", team_id=243, crest_asset_id="99090304") == crest(
        99090304
    )


def test_selected_kit_type_orders_fallbacks():
    custom = assets.crest_url_candidates(team_id=243, crest_asset_id="991", selected_kit_type="1")
    real = assets.crest_url_candidates(team_id=1824, crest_asset_id="992", selected_kit_type="0")
    assert custom == [crest(991), crest(243), assets.NOT_FOUND_CREST_URL]
    assert real == [crest(1824), crest(992), assets.NOT_FOUND_CREST_URL]


def test_zero_ids_fall_through_to_not_found():
    assert (
        assets.club_crest_url(team="0", team_id=0, crest_asset_id="0") == assets.NOT_FOUND_CREST_URL
    )


def test_candidates_are_deduplicated():
    urls = assets.crest_url_candidates(team=5, crest_asset_id="5")
    assert urls == [crest(5), assets.NOT_FOUND_CREST_URL]


def test_division_and_reputation():
    assert assets.division_crest_url("1").endswith("divisioncrest1.png")
    assert assets.reputation_tier_url(0).endswith("reputation-tier0.png")
    for bad in (0, 7, "x"):
        with pytest.raises(ValueError):
            assets.division_crest_url(bad)
    for bad in (-1, 4, None):
        with pytest.raises(ValueError):
            assets.reputation_tier_url(bad)


def test_kit_color_hex():
    assert assets.kit_color_hex("16777215") == "#ffffff"
    assert assets.kit_color_hex(0) == "#000000"
    with pytest.raises(ValueError):
        assets.kit_color_hex(16777216)


def test_crest_url_rejects_zero():
    with pytest.raises(ValueError):
        assets.crest_url(0)
