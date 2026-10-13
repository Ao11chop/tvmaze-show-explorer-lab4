# TV Show Explorer

CSCI 2910 — Lab 4: Using Web APIs — Implementation

This Python command line program implements the TVmaze show explorer planned
in Lab 3. It will search for a title, let the user choose the intended show,
display a profile and episode guide, filter episodes by season, and save
favorites locally.

## Development plan

1. Add the shared HTTP handler with a ten second timeout and one retry.
2. Implement show search, profiles, episode ordering, and season filtering.
3. Add local favorites and command line navigation.
4. Verify the planned success and failure cases and document how to run it.

Only two API call locations are planned:

| Label | Request | Trigger |
| --- | --- | --- |
| A1 | `GET https://api.tvmaze.com/search/shows?q={title}` | A new nonblank title |
| A2 | `GET https://api.tvmaze.com/shows/{id}/episodes` | Selecting a show |

Profile display, season filtering, and favorites will reuse the downloaded data.
No API key is required.

## Issues

- **Open — transient failures:** implement at most two attempts, including
  HTTP 429 with `Retry-After`, while avoiding retries for other client errors.
- **Open — incomplete metadata:** dates, ratings, and episode numbers can be
  missing. Display `Unknown` and sort without comparing `None` with integers.
- **Open — favorite persistence:** a damaged or unwritable favorites file must
  leave browsing available and must not silently overwrite existing data.
- **Open — request reuse:** navigation and season filters must not trigger
  undocumented endpoints or redundant profile requests.

## Data source

Television information comes from [TVmaze](https://www.tvmaze.com/) through its
[public API](https://www.tvmaze.com/api). TVmaze data is available under
[CC BY-SA](https://creativecommons.org/licenses/by-sa/4.0/). The application
will display each show's source URL. This attribution concerns TVmaze data;
it does not apply a license to the application's source code.
