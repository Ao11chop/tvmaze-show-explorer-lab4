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
