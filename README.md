# FC 26 Clubs API

An unofficial, unauthenticated Python client for the **EA Sports FC 26 Pro Clubs API**.
Search for clubs by name, pull club details, and fetch recent matches — everything comes
back as a pandas `DataFrame`.

This is an experiment built for the EA Sports FC 26. It is not affiliated with, endorsed by, or supported by EA. The endpoints it uses are the ones `proclubs.ea.com` calls from the browser and can change or disappear without notice.

## Requirements

* Python 3.9+
* Dependencies pinned in [`requirements.txt`](requirements.txt)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/1erkandogan/fc26-clubs-api.git
   cd fc26-clubs-api
   ```
2. (Recommended) Create a virtual environment:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS / Linux
   source .venv/bin/activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

No API key, token, or `.env` file is needed — the Pro Clubs endpoints are public.

## Quick start

```python
from fc26_api_class import FC26_API

api = FC26_API()

# Search returns the single best match as a one-row DataFrame
club = api.search_club_by_name("Real Madrid")
if club is None:
    raise SystemExit("search failed")
if club.empty:
    raise SystemExit("no club with that name")

club_id = club["clubId"].iat[0]   # e.g. 240

details = api.get_club_details(club_id)                       # transposed DataFrame
matches = api.get_club_matches_normalized(club_id, "leagueMatch")

print(details)
print(matches.head())
```

Both modules also run standalone (`python fc26_api_class.py`), but the `__main__` block is
a placeholder demo using the fake id `"123456"` and club name `"MyClub"` — replace those
before expecting output.

## API reference

### `FC26_API(session=None, timeout=10)`

| Argument  | Default | Notes |
|-----------|---------|-------|
| `session` | `None`  | Pass a `requests.Session` to reuse connections or inject a mock in tests. A new session is created when omitted. |
| `timeout` | `10`    | Per-request timeout in seconds. |

### Methods

All methods return `Optional[pd.DataFrame]` — a `DataFrame` on success, `None` when the
request or the post-processing fails. A successful call that simply found nothing returns
an **empty** `DataFrame`, not `None`, so check both (`if df is None or df.empty`).

| Method | Endpoint | Returns |
|---|---|---|
| `search_club_by_name(club_name)` | `allTimeLeaderboard/search` | `clubInfo`-normalized DataFrame, **first row only** |
| `get_club_details(club_id)` | `clubs/info` | **Transposed** DataFrame (fields as rows) |
| `get_club_matches(club_id, match_type="friendlyMatch")` | `clubs/matches` | Raw match DataFrame with `timestamp` converted to datetime (+1h) |
| `get_club_matches_normalized(club_id, match_type="friendlyMatch", gmt=2)` | `clubs/matches` | As above with the nested `clubs` column flattened, `timestamp` shifted by `gmt` hours |

Valid `match_type` values: `friendlyMatch`, `leagueMatch`, `playoffMatch`.
`maxResultCount` is hard-coded to `10`, so the match calls return at most the 10 most
recent games.

### Error handling

Internally the client raises `FC26APIError` (network failure, non-2xx status, undecodable
JSON, a missing expected column). The public methods catch it, store it on
`self._last_error`, and return `None`, so a normal call site just guards on `None`:

```python
from fc26_api_class import FC26_API, FC26APIError

api = FC26_API()
matches = api.get_club_matches(club_id, "leagueMatch")

if matches is None:
    print("request failed:", api._last_error)   # private for now, see Known issues
```

If you want the exception instead of `None`, call the private `_request_builder` directly
and catch `FC26APIError` yourself.

## How it talks to EA

Two details matter more than anything else in this repo:

**1. `platform=common-gen5` is sent on every call.** It is hard-coded and not currently
parameterizable. Requests without it are rejected.

**2. The requests must look like the site's own XHR calls.** EA sits behind Akamai, which
blocks anything that does not resemble browser traffic from `proclubs.ea.com`. The client
always sends this header set (`fc26_api_class.py:25-34`):

```python
{
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
    "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
}
```

`sec-fetch-site: same-origin` together with a realistic `user-agent` / `sec-ch-ua` is what
gets through. Drop them and the edge returns an error page instead of JSON.

Base URL: `https://proclubs.ea.com/api/fc`

**No caching, no retries, no backoff, no rate limiting.** Every call goes straight to EA.
If you loop over many clubs, add your own throttling — it is a free public endpoint and
hammering it is a good way to get blocked.

## Legacy module: `fc26_api.py`

`fc26_api.py` exposes the same four calls as plain module-level functions
(`search_club_by_name`, `get_club_details`, `get_club_matches`,
`get_club_matches_normalized`). Differences from the class client:

* Errors are printed and `None` is returned; there is no `FC26APIError`.
* No `requests.Session`, so no connection reuse; the timeout is fixed at 10s.
* `search_club_by_name` returns **all** matching rows, not just the first.
* Timestamps are always shifted by +2 hours.

Prefer `fc26_api_class.py` for new work. The functional module is kept because older
notebooks import it.

## Known issues

* `get_club_details` still contains a stray debug `print()` (`fc26_api_class.py:155`).
* Timezone handling is inconsistent: `+1h` in `get_club_matches`, `gmt=2` by default in
  `get_club_matches_normalized`, `+2h` in `fc26_api.py`. All datetimes are tz-naive.
* `FC26_API.search_club_by_name` silently truncates the result to one row.
* `_last_error` has no public accessor yet.
* `platform` and `maxResultCount` cannot be overridden.
* There are no automated tests.
* The `Club` / `Matches` dataclasses that briefly existed in git history were removed and
  are **not** part of the current API.

## Built With

* [Python](https://www.python.org/)
* [pandas](https://pandas.pydata.org/) — response handling and normalization
* [requests](https://requests.readthedocs.io/en/latest/) — HTTP

## Contributing

Contributions are welcome. Feel free to open an issue or submit a pull request.

## License

MIT — see [LICENSE.md](LICENSE.md).
