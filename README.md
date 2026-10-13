# TV Show Explorer

CSCI 2910 — Lab 4: Using Web APIs — Implementation

This Python command line program implements the TVmaze show explorer planned
in Lab 3. Search for a title, choose the intended show, display its profile and
episode guide, filter episodes by season, and save favorites locally.

## Run the application

Install Python 3.12 or newer. In VS Code, open this repository's folder and use
its terminal. On Windows:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe explorer.py
```

On macOS or Linux, create a virtual environment with `python3 -m venv .venv`
and use `.venv/bin/python` in place of `.\.venv\Scripts\python.exe`.
An internet connection is required for searches and episode requests.
No account, API key, or `.env` file is needed for TVmaze's public endpoints.

At the title prompt, enter a show name or Q to quit. Blank titles make no
request. Choose a numbered match; B returns to search and Q exits.

| Episode menu input | Behavior |
| --- | --- |
| A positive season number, such as `1` | Filter the downloaded episode guide |
| `A` | Show all downloaded episodes |
| `F` | Save the selected show's ID, name, and source URL |
| `L` | List locally saved favorites |
| `B` | Choose another show from the existing search results |
| `N` | Enter a new search title |
| `Q` | Exit and close the HTTP session |

Commands are case insensitive. Dates, runtimes, ratings, and episode numbers
that are unavailable display as `Unknown`. A missing episode guide still
allows viewing the profile and saving the show.

Favorites are loaded from `favorites.json` beside `explorer.py` and are excluded
from Git. To use a different file:

```powershell
.\.venv\Scripts\python.exe explorer.py --favorites my-favorites.json
```

The file's parent directory must already exist. A damaged favorites file is
left intact and saves are disabled with a warning until it is fixed or moved
and the app is restarted. Browsing continues after a file error.

## API design

There are exactly two API call locations:

| Label | Request | Trigger |
| --- | --- | --- |
| A1 | `GET https://api.tvmaze.com/search/shows?q={title}` | A new nonblank title |
| A2 | `GET https://api.tvmaze.com/shows/{id}/episodes` | Selecting a show |

Profile display, season filtering, and favorites reuse downloaded data. A1
uses `requests.Session.get(..., params={"q": title})` to encode the title.
A2 uses the chosen result's numeric ID and the default list without specials.
The program never fetches posters, follows episode links, or makes a separate
show-detail request. Returning to results reuses A1; selecting a show sends A2.

Each request has a ten second timeout. Timeouts, connection failures, and HTTP
5xx retry once after one second. HTTP 429 retries once after at least three
seconds, honoring a longer valid `Retry-After`. Other HTTP errors and invalid
JSON do not retry. A2 HTTP 404 returns to the existing selection list; other
final failures return to search. All successful bodies must be lists of objects.

| File | Responsibility |
| --- | --- |
| `explorer.py` | Prompts, navigation, and session lifetime |
| `tvmaze_api.py` | A1, A2, response validation, and retry policy |
| `display.py` | Plain text profiles, episode sorting, and local filtering |
| `favorites.py` | JSON loading, duplicate checks, and atomic saves |
| `test_*.py` | Offline HTTP, display, persistence, and interaction tests |

## Verification

Run the offline checks with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

All 26 tests passed on October 12, 2026 with Python 3.12 and requests 2.34.2.
They cover ambiguous and empty searches, invalid selection, null metadata,
empty episode lists, retry limits, rate limiting, malformed responses,
favorites errors, session closure, and navigation without extra API calls.

`LIVE_CHECK.txt` records a live run on October 12, 2026. The no-match search,
The Office search, and selected episode request each returned HTTP 200.
Repeated season filters, favorite saves, and favorite listing made zero extra
requests. The selected US show was ID 526. Catalog data can change.

For a class demonstration, search `The Office`, distinguish the premiere
years in the results, choose a version, enter `1`, then `F`, `F`, and `L`.
The second save should report that the show is already in favorites.
Use B to choose another version or N to start a new search.

## Issues

- **Resolved — transient failures:** the shared HTTP handler uses at most two
  attempts. HTTP 429 waits at least three seconds and honors a longer numeric
  or HTTP date `Retry-After`. Network failures and 5xx wait one second. Other
  errors, invalid JSON, and invalid data shapes do not retry. Offline tests
  check the request count and delay without sleeping or contacting TVmaze.
- **Resolved — incomplete metadata:** display functions use `Unknown` for
  missing fields, strip summary HTML, and sort unknown episode numbers after
  known numbers. Tests cover null metadata, HTML entities, empty guides,
  ordering, and filters without modifying the original download.
- **Resolved — favorite persistence:** loading a damaged or unreadable file
  disables saves with a warning. Saves write a temporary file and replace the
  destination only after writing succeeds. IDs prevent duplicates. Tests
  verify reloads, corruption, permission errors, and preservation of the
  previous file and in-memory list after a failed save.
- **Resolved — request reuse:** the browsing menu receives downloaded data
  rather than an HTTP client. Filters, favorite saves, and favorite listing
  cannot make API calls. Integration tests verify one search and one episode
  request across repeated filters and saves; B reuses matches for reselection.

## Data source

Television information comes from [TVmaze](https://www.tvmaze.com/) through its
[public API](https://www.tvmaze.com/api). TVmaze data is available under
[CC BY-SA](https://creativecommons.org/licenses/by-sa/4.0/). The application
will display each show's source URL. This attribution concerns TVmaze data;
it does not apply a license to the application's source code.
