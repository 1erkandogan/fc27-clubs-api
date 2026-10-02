# fc-clubs-api

**An unofficial Python client for the EA Sports FC 27 Pro Clubs API**, the same
endpoints [proclubs.ea.com](https://proclubs.ea.com) calls from the browser. Find
clubs, then get their stats, members, match history and per-player match ratings.

```python
from fc_clubs_api import FC27API

api = FC27API()
club_id = api.find_club_id("Example FC")
api.get_club_matches(club_id)        # last 10 league matches, as a DataFrame
```

<div class="grid cards" markdown>

-   **Three output formats**

    EA's raw JSON, clean typed records, or pandas DataFrames, chosen per client or
    per call. → [Output formats](output-formats.md)

-   **Zero required dependencies**

    The core is standard library only. pandas is an optional extra.
    → [Getting started](getting-started.md)

-   **Decoded match events**

    80+ stats EA doesn't name: pass direction and length, possession won by third,
    positioning. → [Match events](match-events.md)

-   **Documented API**

    Every endpoint's raw response, its quirks, and dated observations.
    → [Endpoints](endpoints.md)

</div>

## Features

- All 8 known club endpoints: search (all-time and current season), details,
  overall stats, member and career stats, matches, per-player match stats, playoff
  achievements.
- Match rows seen from your club's side, with `result` (win/draw/loss) and `dnf`
  worked out for league matches *and* friendlies.
- Crest, division and reputation image URLs, with the crest fallback rule.
- Timezone-aware timestamps, consistent camelCase columns, `all_columns=True` for
  everything EA sends.
- Fully typed (`py.typed`), tested offline on Python 3.9–3.14, with and without pandas.
- `fc-clubs` command line tool.

!!! warning "Unofficial"
    Not affiliated with or endorsed by EA. The endpoints are undocumented and can
    change without notice. Open an [issue](https://github.com/1erkandogan/fc27-clubs-api/issues)
    when something breaks.

## Acknowledgements

Endpoint, crest and event-ID findings from the community
[EA FC Pro Clubs API research](https://github.com/Interactive-63/eafc-pro-clubs-api-research)
project.
