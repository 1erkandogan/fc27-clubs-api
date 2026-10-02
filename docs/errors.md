# Errors

```
Exception
├── FC27APIError                 anything that went wrong talking to EA
│   ├── FC27HTTPError            EA answered 4xx/5xx         .status_code, .url
│   ├── FC27ConnectionError      no network, DNS, timeout    .url
│   └── FC27ResponseError        body was not JSON           .url
└── ValueError
    ├── ClubNotFoundError        find_club_id: no match
    └── AmbiguousClubError       find_club_id: several        .candidates
```

Plain `ValueError` is also raised for invalid arguments (unknown `match_type`,
`output`, `scope` or `timezone`), and `ImportError` when `output="dataframe"` is used
without pandas installed.

## Catching errors

```python
from fc_clubs_api import FC27API, FC27APIError, FC27HTTPError, AmbiguousClubError

api = FC27API()

try:
    club_id = api.find_club_id("Example")
except AmbiguousClubError as error:
    for club_id, name in error.candidates:
        print(club_id, name)
    raise

try:
    df = api.get_member_stats(club_id)
except FC27HTTPError as error:
    if error.status_code == 403:
        print("Blocked by EA's edge. Wait, and check the headers still work.")
    raise
except FC27APIError as error:      # connection or bad response
    print("EA problem:", error)
```

Upgrading from 0.1: every new class subclasses the type 0.1 raised
(`FC27APIError` or `ValueError`), so existing `except` blocks keep working.

## Common causes

| Symptom | Likely cause |
|---|---|
| `FC27HTTPError` 403 | Akamai blocked the request: headers changed on EA's side, or too many requests too fast |
| `FC27ConnectionError` timeout | Akamai silently dropping the request (same causes as 403), or EA is down |
| `FC27ResponseError` | An HTML block or maintenance page instead of JSON |
| Empty result | Wrong club id, no matches of that type (playoffs often return `[]`), or member without games |

There is no built-in retry or rate limiting. When looping over many clubs, pause
between requests (`time.sleep(1)`).
