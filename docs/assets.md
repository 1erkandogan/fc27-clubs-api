# Images and crests

Club crests, division badges and reputation tier icons are PNGs served from EA's
content CDNs. They are not part of the Pro Clubs API and need no special headers, so
you can use the URLs directly in an `<img>` tag or a Discord embed.
`fc_clubs_api.assets` builds them. Every URL pattern below was checked to return a PNG
on 2026-10-02.

Source: [EA FC Pro Clubs API research](https://github.com/Interactive-63/eafc-pro-clubs-api-research).

## Club crests

```python
from fc_clubs_api import assets

assets.crest_url(99090304)
# https://eafc24.content.easports.com/fifa/fltOnlineAssets/24B23FDE-7835-41C2-87A2-F453DFDB2E82/2024/fcweb/crests/256x256/l99090304.png
```

A club has two candidate ids: `teamId` (a real-world badge) and
`customKit.crestAssetId` (a custom crest). Which one it shows:

1. **`TEAM` in `clubs/matches`** is the crest id the club played with. Normally it
   equals `teamId` (real badge) or `crestAssetId` (custom crest). This is the best source.
2. Outside matches there is no `TEAM`. In every club checked, `customKit.selectedKitType`
   was `"1"` for custom crests and `"0"` for real badges, so that decides the order.
3. Rarely, `TEAM` matches neither id and its URL returns 404. Fall back to
   `crestAssetId`, then to the not-found crest.

`club_crest_url` applies this rule; `crest_url_candidates` returns the whole fallback
chain for front ends that can retry on a failed image load:

```python
assets.club_crest_url(team="1824", team_id=1824, crest_asset_id="99160407")
assets.crest_url_candidates(team_id=243, crest_asset_id="99090304", selected_kit_type="1")
# [".../l99090304.png", ".../l243.png", ".../notfound-crest.png"]
```

You rarely need to call these yourself: `search_club_by_name`, `get_club_details`
and `get_club_matches` already include `crestUrl` (and `opponentCrestUrl`) in
`records` / `dataframe` output.

## Division badges

```python
assets.division_crest_url(1)   # .../pro-clubs/divisioncrest1.png   (1 = top, 6 = lowest)
```

Use with `currentDivision` / `bestDivision`. Values outside 1–6 raise `ValueError`
(`divisioncrest7.png` does not exist).

## Reputation tiers

```python
assets.reputation_tier_url(3)  # .../pro-clubs/reputation-tier3.png   (0-3)
```

Use with `reputationTier` (`reputationtier` in raw search and overall-stats responses).

## Other images

| Constant | Image |
|---|---|
| `assets.NOT_FOUND_CREST_URL` | Placeholder crest |

## Kit colours

Kit and crest colours (`kitColor1`, `kitAColor1`, `crestColor`, ...) are decimal RGB:

```python
assets.kit_color_hex("16777215")   # "#ffffff"
```
