"""The two planned TVmaze calls and their shared retry policy."""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import math
import time

import requests

BASE_URL = "https://api.tvmaze.com"
TIMEOUT = 10


class APIError(Exception):
    """An error that the command line interface can explain without a traceback."""

    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def retry_delay(header):
    """Honor Retry-After seconds or an HTTP date, with a three second minimum."""
    if header:
        try:
            seconds = float(header)
            if math.isfinite(seconds):
                return max(3.0, seconds)
        except (ValueError, TypeError):
            pass
        try:
            date = parsedate_to_datetime(header)
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            return max(3.0, (date - datetime.now(timezone.utc)).total_seconds())
        except (ValueError, TypeError, OverflowError):
            pass
    return 3.0


def fetch_json(session, path, params=None, *, pause=time.sleep, output=print):
    """GET one endpoint, retry once for network errors, 429, or 5xx.

    Redirects are disabled to avoid silently making an unplanned request.
    Other HTTP errors, invalid JSON, and invalid data shapes are not retried.
    """
    for attempt in range(2):
        try:
            response = session.get(
                BASE_URL + path, params=params, timeout=TIMEOUT,
                allow_redirects=False,
            )
        except (requests.Timeout, requests.ConnectionError) as exc:
            if attempt == 0:
                output("Connection failed or timed out; retrying once in 1 second.")
                pause(1)
                continue
            raise APIError("TVmaze could not be reached after two attempts.") from exc
        except requests.RequestException as exc:
            raise APIError("The request failed. Please try another search.") from exc

        try:
            status = response.status_code
            if status == 429 or 500 <= status <= 599:
                if attempt == 0:
                    delay = retry_delay(response.headers.get("Retry-After")) if status == 429 else 1
                    output(f"TVmaze returned HTTP {status}; retrying once in {delay:g} seconds.")
                else:
                    raise APIError(f"TVmaze returned HTTP {status} after two attempts.", status)
            elif not 200 <= status <= 299:
                raise APIError(f"TVmaze returned HTTP {status}.", status)
            else:
                try:
                    data = response.json()
                except ValueError as exc:
                    raise APIError("TVmaze returned invalid JSON.") from exc
                if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
                    raise APIError("TVmaze returned an unexpected response format.")
                return data
        finally:
            response.close()
        pause(delay)


class TVMazeClient:
    def __init__(self, session, *, pause=time.sleep, output=print):
        self.session = session
        self.pause = pause
        self.output = output
        session.headers.update({"User-Agent": "CSCI2910-TVShowExplorer/1.0"})

    def _fetch(self, path, params=None):
        return fetch_json(self.session, path, params, pause=self.pause, output=self.output)

    def search(self, title):
        title = title.strip()
        if not title:
            return []
        # A1: requests encodes the user's title as the q query parameter.
        rows = self._fetch("/search/shows", {"q": title})
        shows = [row.get("show") for row in rows]
        if not all(isinstance(show, dict) and type(show.get("id")) is int
                   and show["id"] > 0 for show in shows):
            raise APIError("TVmaze returned a search result without a valid show ID.")
        return shows

    def episodes(self, show_id):
        if type(show_id) is not int or show_id <= 0:
            raise APIError("A valid numeric show ID is required.")
        # A2: the default episode list excludes specials; no extra calls follow links.
        return self._fetch(f"/shows/{show_id}/episodes")
