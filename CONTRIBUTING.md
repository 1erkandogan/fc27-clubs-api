# Contributing

Thanks for taking a look. Bug reports are the most useful contribution to this
project, because EA changes its undocumented API without warning. Code is welcome
too; please read this first.

**Open an issue before writing code** for anything beyond a small bug fix. Describe
the problem and wait for a reply. Pull requests for features nobody agreed on are
usually closed, even when the code is fine: an unwanted change still costs a review,
and a merge is permanent.

## Development setup

```bash
git clone https://github.com/1erkandogan/fc27-clubs-api.git
cd fc27-clubs-api
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev,docs]"
```

| Task | Command |
|---|---|
| Run the tests | `pytest` |
| Lint | `ruff check .` |
| Format | `ruff format .` |
| Preview the docs | `mkdocs serve` |
| Build the docs like CI | `mkdocs build --strict` |
| Build the package | `python -m build && twine check dist/*` |

CI runs all of these on every pull request, on Python 3.9 to 3.14, plus the test
suite once without pandas installed.

## Principles

These are deliberate. Pull requests that change them will be closed unless an issue
agreed on it first.

- **No runtime dependencies beyond the standard library.** HTTP uses `urllib`. pandas
  is an optional extra and must only be imported lazily, inside `_output.py`.
- **Raw means raw.** `output="raw"` returns EA's JSON exactly as received. All cleaning
  happens in `_normalize.py` / `client.py`, so the `records` and `dataframe` formats
  share one code path.
- **Public vs internal.** Anything importable from `fc_clubs_api` (see `__all__`) is
  public and follows semantic versioning. Modules starting with `_` are internal.
  Breaking a public name needs a CHANGELOG entry under **Changed**.
- **Python 3.9+.** No syntax or standard library features from newer versions.
- **Observed, not assumed.** Documentation of EA's behaviour states when it was
  checked. Guesses are labelled as guesses.

## Changes that are welcome

- **EA changed something and the client broke.** The most valuable kind of fix.
- **A method returns wrong data:** a bad column mapping, a wrong timezone, a win
  counted as a draw.
- **A new endpoint** that `proclubs.ea.com` actually calls, with an anonymized
  fixture showing its real response.
- **A crash or unhandled error** on input that should work.
- **Documentation that is wrong:** a signature that doesn't match the code, a recipe
  that errors when run.

## Changes that will be closed without review

- Reformatting or restyling working code with no behaviour change.
- Renaming public methods or parameters for taste.
- New dependencies, or a different HTTP library.
- Generated changes you haven't run yourself.

## Match event mappings

Event-ID findings come from the community
[EA FC Pro Clubs API research](https://github.com/Interactive-63/eafc-pro-clubs-api-research)
project. Submit new or corrected mappings **there**, with evidence. This package only
decodes mappings that project rates as confirmed / high confidence; open an issue
here when one is promoted, and update `EVENT_STATS` in `events.py` and the table in
`docs/match-events.md` together (a test checks they match).

## Pull request checklist

1. **One change per pull request.** Don't bundle a fix with a rename.
2. **Keep the diff minimal.** Don't touch lines your change doesn't need.
3. **Add a test.** Tests run offline against saved responses in `tests/fixtures/`.
   When fixing a parsing bug, add or extend a fixture so the bug would have been caught.
4. **Fixture data must be fake.** Keep EA's real structure, but replace every club
   name, player name, id and date with a placeholder (Example FC = `1001`, Opponent A
   = `2001`, Player1, ...). Never commit a real gamertag or account id.
5. **Check against the live API** when the change concerns EA's behaviour. Fixtures
   can't tell you EA started rejecting the headers.
6. **Update the docs and CHANGELOG** for anything a user would notice.

## Reporting a bug

Open an issue with:

- What you called, with the arguments (a club id is fine, it's public).
- What you got: the full traceback, or the output that came back wrong.
- What you expected.
- Your Python version, OS and `fc_clubs_api.__version__`.
- If EA's response looks odd, the raw JSON from `output="raw"` or `api.get_json(...)`.

## Licence

This project is MIT licensed. By contributing you agree your changes are released
under the same licence.
