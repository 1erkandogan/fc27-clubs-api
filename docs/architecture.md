# Architecture

How a call travels through the package, why each module exists, and the
decisions behind them. Read this before changing the code.

## The pipeline

Every data method follows the same four steps:

```
FC27API.get_member_stats(1001, output=...)
   │
   ├─ 1. resolve output format          _output.resolve_output   (fails early if pandas is missing)
   ├─ 2. GET members/stats              _http.request_json       (urllib + browser headers)
   │        └─ output="raw"  ──────────► return EA's JSON untouched
   ├─ 3. normalize                      _normalize               (flatten, numbers, timestamps, columns)
   │        └─ output="records" ───────► return list[dict]
   └─ 4. to_dataframe                   _output.to_dataframe     (pd.DataFrame.from_records)
            └─ output="dataframe" ─────► return DataFrame
```

Because the DataFrame is built *from* the records, the two formats always have the
same columns and values. There is no separate pandas code path to drift out of sync.

## Modules

| Module | Public? | Responsibility |
|---|---|---|
| `client.py` | yes (`FC27API`) | One method per endpoint; shapes EA's response into rows; derives `result`, `dnf`, crest URLs |
| `_http.py` | `BASE_URL`, `HEADERS` | The only code that talks to EA. Builds the URL, sends the request, maps failures to exceptions |
| `_normalize.py` | no | Pure-Python cleaning: `flatten`, `coerce_numbers`, `select_columns`, `convert_timestamps` |
| `_columns.py` | no | The curated column set and camelCase names per method |
| `_output.py` | `OutputFormat` | Output format enum, validation, lazy pandas import |
| `events.py` | yes | `match_event_aggregate_*` parser and the named-stat table |
| `assets.py` | yes | Crest, division and reputation image URLs; kit colours |
| `enums.py` | yes | `MatchType`, `LeaderboardScope`, `Platform` |
| `exceptions.py` | yes | Error hierarchy |
| `__main__.py` | CLI | `fc-clubs` / `python -m fc_clubs_api` |

Modules starting with `_` are internal: they can change in any release. Everything
importable from `fc_clubs_api` directly (see `__all__`) is the public, versioned API.

## Talking to EA (`_http.py`)

### Why the browser headers

EA's servers sit behind Akamai, which blocks requests that don't look like they come
from the proclubs.ea.com website. Without the headers in `HEADERS`, EA answers
**403 Forbidden** or never answers at all (the request hangs until the timeout).
The important one is `"sec-fetch-site": "same-origin"`; `user-agent` and `sec-ch-ua`
identify as Chrome on Windows. Plain `curl` is blocked even with these headers, while
Python's `urllib` gets through.

`FC27API(headers={...})` merges your headers over these defaults, so you can change
the user agent without losing the rest.

### Why `urllib` and not `requests`

The client sends a handful of simple GET requests. `requests` earns its place with
connection pooling, retries, cookies or uploads, none of which are needed here. Using
the standard library keeps the base install dependency-free (only `tzdata` on Windows,
which has no system timezone database).

### Error mapping

```python
try:
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.load(response)
except urllib.error.HTTPError as error:      # EA answered 4xx/5xx
    raise FC27HTTPError(error.code, url) from None
except OSError as error:                     # no network, DNS, timeout
    raise FC27ConnectionError(...) from None
except json.JSONDecodeError:                 # HTML block page, empty body
    raise FC27ResponseError(...) from None
```

The order matters: `HTTPError` is a subclass of `OSError`, so it must be caught
first. `from None` keeps tracebacks to one short message. All three subclass
`FC27APIError`, so `except FC27APIError` still catches everything, as it did in 0.1.

EA sometimes answers JSON `null` instead of `[]`; `request_json` normalizes that to
`[]` so no caller has to check for `None`. This is the only change `raw` output
ever makes.

## Cleaning the data (`_normalize.py`)

EA's JSON has three problems for analysis, each fixed by one function.

**Nested objects** → `flatten`. `{"clubInfo": {"name": "X"}}` becomes
`{"clubInfo.name": "X"}`, the same dotted names `pandas.json_normalize` would produce.

**Numbers sent as text** → `coerce_numbers`. EA sends `"25"` and `"7.4"`. Text
can't be summed and sorts wrongly (`"9"` > `"25"`). A field is converted only if
*every* non-null value in it is numeric, so a column of player names is never
half-converted, and an empty string (`""`, which EA uses for "unknown") keeps the
column as text. Fields containing any decimal become `float`, the rest `int`. The
same function makes the records rectangular: a field missing from one record is
filled with `None`, so every dict has the same keys.

**Unix timestamps** → `convert_timestamps`. `1767297600` becomes a timezone-aware
`datetime` (`2026-01-01 20:00:00+00:00`), converted to the client's `timezone`.

`select_columns` then keeps the curated set from `_columns.py` and renames it
(`passesmade` → `passesMade`, `mom` → `manOfTheMatch`). `all_columns=True` skips
this step and keeps every field under EA's name.

## Shaping each endpoint (`client.py`)

Most methods are three lines: request, pick the list of rows out of EA's shape, deliver.
The shapes differ:

| Method | EA's shape | Rows taken from |
|---|---|---|
| `search_club_by_name` | list of clubs | the list (+ `crestUrl`) |
| `get_club_details` | `{"1001": {...}}` | the dict's values (+ `crestUrl`) |
| `get_club_overall_stats` | list with one item | the list |
| `get_member_stats` / `get_member_career_stats` | `{"members": [...], "positionCount": {...}}` | `members` |
| `get_club_matches` | list of matches | one derived row per match |
| `get_match_players` | list of matches | `players → club id → player id → stats` |

### Match results

`get_club_matches` looks at each match from the requested club's side. EA keys
`clubs` by club id **as text**, so the id is converted with `str()` first; the other
key is the opponent. In league matches EA fills `wins`/`losses`/`ties`; in friendlies
all three are `"0"` for both clubs, so the score decides. `dnf` is true when either
club has `winnerByDnf == "1"` (someone quit and the other club was awarded the win).

### Event stats

With `include_events=True`, each player row gets `events.decode_events(stats)`
merged in with `setdefault`, so EA's own named fields (`goals`, `assists`, `shots`)
are never overwritten by a decoded value. See [Match events](match-events.md).

## Output formats (`_output.py`)

`OutputFormat` is a `str` enum, so `"records"` and `OutputFormat.RECORDS` are
interchangeable. The client stores a default; each method's `output=None` means
"use the default". When the result will be a DataFrame, pandas is imported
**before** the request is sent, so a missing install fails immediately with an
install hint instead of after a network round trip.

## Tests

The tests never contact EA. `tests/conftest.py`'s `fake_ea` patches
`urllib.request.urlopen` to return a saved response from `tests/fixtures/`. The
fixtures have the exact shape of real responses, but every name, id and date is a
placeholder. Client tests run on `records` so the whole suite passes without
pandas; `test_output.py` then checks that the DataFrame matches the records for
every method. CI runs the suite on Python 3.9–3.14, and once more without pandas.

## Decisions worth keeping

- **No runtime dependencies beyond the standard library.** pandas is an extra.
- **Raw means raw.** Never "fix" EA's data in the `raw` path; do it in `_normalize`.
- **One request per call.** No hidden caching, retries or rate limiting: callers
  decide their own policy (and should pause between requests when looping over clubs).
- **Observed, not assumed.** Endpoint behaviour in the docs is dated and checked
  against the live API; guesses are labelled as such.
