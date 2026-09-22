# Contributing

Thanks for taking a look. This is a small, deliberately simple project, and the
bar for changes is higher than the size of the diff might suggest. Please read
this before opening a pull request.

**Open an issue first.** Describe the problem and how to reproduce it, and wait
for a reply before writing code. Pull requests that arrive with no issue behind
them are usually closed, even when the code is fine. This isn't about the code:
it's that an unwanted change still costs a review, and a merge is permanent.

## Design decisions that are not up for change

These look like oversights. They aren't, and pull requests changing them will be
closed:

- **The client is one file.** `fc27_api.py` stays a single module. No `src/`
  layout, no splitting into `client.py` / `models.py` / `parsers.py`.
- **pandas is the only dependency.** No `requests`, no `httpx`, no `pydantic`.
  The HTTP layer uses `urllib` from the standard library on purpose, so that
  `pip install -r requirements.txt` pulls in exactly one thing.
- **`requirements.txt` is correct as it is.** Don't pin, unpin, re-sort, add
  hashes, or "clean it up". Change it only if you are adding a dependency that
  was agreed in an issue first.
- **The code is written to be read by beginners.** `docs/how-it-works.md` walks
  through this file line by line and explains every import. Comprehensions,
  clever one-liners, and abstraction layers that make the walkthrough wrong are
  a cost, not an improvement.
- **No tooling config.** No linters, formatters, pre-commit hooks, CI workflows,
  type annotations, `pyproject.toml`, or packaging. If the project needs these
  later, that's a decision for the maintainer.
- **Python 3.9+.** Don't use syntax that requires anything newer.

## Changes that are welcome

- **EA changed something and the client broke.** This is the most valuable kind
  of contribution. Endpoints, headers and response shapes are undocumented and
  move without warning.
- **A method returns wrong data.** Bad column mapping in `COLUMNS`, a timestamp
  converted to the wrong timezone, a win counted as a draw.
- **A new endpoint** that `proclubs.ea.com` actually calls, with a fixture
  showing its real response shape.
- **A crash or unhandled error** on input that should work.
- **Documentation that is factually wrong** — a method signature that doesn't
  match the code, a recipe that errors when you run it.

## Changes that will be closed without review

- Reformatting, re-indenting, reordering imports, or changing quote style.
- Renaming variables, methods or parameters for taste.
- Single-typo README edits. Open an issue instead; it's less work for both of us.
- Adding badges, a code of conduct, issue templates, or funding files.
- Rewriting working code to a different style with no behaviour change.
- Generated changes where you haven't run the tests or the library yourself.

## If you are writing code

1. **One change per pull request.** Don't bundle a bug fix with a rename.
2. **Keep the diff minimal.** Don't touch lines your change doesn't need. A
   whitespace change buried in a real fix makes it hard to review.
3. **Add a test.** Tests run offline against saved EA responses in
   `tests/fixtures/`. If you're fixing a parsing bug, add or extend a fixture so
   the bug would have been caught.
4. **Fixture data must be fake.** Every club name, player name, id and date in
   `tests/fixtures/` is a placeholder. Keep the real structure, but never commit
   a real gamertag, club or account id — yours or anyone else's.
5. **Run the tests before pushing:**

   ```bash
   python -m unittest discover -s tests -v
   ```

6. **Check the change against the live API too**, where it makes sense. The
   fixtures can't tell you that EA started rejecting your headers.

## Reporting a bug without writing code

That is a genuinely useful contribution, and often more useful than a patch.
Open an issue with:

- What you called, with the arguments (a real club id is fine, it's public).
- What you got: the full traceback, or the table that came back wrong.
- What you expected instead.
- Your Python version and OS.

If EA's response itself looks odd, include the raw JSON from
`api.get_json(...)` — that's usually the fastest way to identify the problem.

## Licence

This project is MIT licensed. By contributing you agree your changes are
released under the same licence.
