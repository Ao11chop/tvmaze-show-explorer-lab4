"""Offline tests; no real API calls or real retry sleeps."""

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
import unittest
from unittest.mock import Mock

import requests

from tvmaze_api import APIError, TVMazeClient, fetch_json, retry_delay


def response(status=200, data=None, headers=None):
    result = Mock(status_code=status, headers=headers or {})
    result.json.return_value = [] if data is None else data
    return result


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.session = Mock(headers={})
        self.pause = Mock()
        self.output = Mock()

    def fetch(self):
        return fetch_json(self.session, "/search/shows", {"q": "the office"},
                          pause=self.pause, output=self.output)

    def test_success_and_request_contract(self):
        result = response(data=[{"show": {"id": 526}}])
        self.session.get.return_value = result
        self.assertEqual(self.fetch(), [{"show": {"id": 526}}])
        self.session.get.assert_called_once_with(
            "https://api.tvmaze.com/search/shows", params={"q": "the office"},
            timeout=10, allow_redirects=False)
        result.close.assert_called_once()
        self.pause.assert_not_called()

    def test_network_failure_then_success(self):
        for error in (requests.Timeout, requests.ConnectionError):
            with self.subTest(error=error):
                self.session.get.reset_mock()
                self.session.get.side_effect = [error(), response()]
                self.assertEqual(self.fetch(), [])
                self.assertEqual(self.session.get.call_count, 2)

    def test_network_failure_stops_after_two(self):
        self.session.get.side_effect = requests.Timeout()
        with self.assertRaises(APIError):
            self.fetch()
        self.assertEqual(self.session.get.call_count, 2)
        self.pause.assert_called_once_with(1)

    def test_server_errors_and_rate_limit_retry_once(self):
        for status in (429, 500, 503, 599):
            with self.subTest(status=status):
                self.session.get.reset_mock()
                self.pause.reset_mock()
                self.session.get.side_effect = [response(status, headers={"Retry-After": "8"}), response()]
                self.assertEqual(self.fetch(), [])
                self.assertEqual(self.session.get.call_count, 2)
                self.pause.assert_called_once_with(8 if status == 429 else 1)

    def test_persistent_server_error_stops(self):
        self.session.get.side_effect = [response(503), response(503)]
        with self.assertRaises(APIError) as error:
            self.fetch()
        self.assertEqual(error.exception.status, 503)
        self.assertEqual(self.session.get.call_count, 2)

    def test_other_statuses_never_retry(self):
        for status in (301, 400, 404, 403):
            with self.subTest(status=status):
                self.session.get.reset_mock()
                self.session.get.return_value = response(status)
                with self.assertRaises(APIError) as error:
                    self.fetch()
                self.assertEqual(error.exception.status, status)
                self.assertEqual(self.session.get.call_count, 1)

    def test_bad_json_and_shape_do_not_retry(self):
        for data in ({"error": "bad"}, ["bad"], [None]):
            with self.subTest(data=data):
                self.session.get.reset_mock()
                self.session.get.return_value = response(data=data)
                with self.assertRaises(APIError):
                    self.fetch()
                self.assertEqual(self.session.get.call_count, 1)
        self.session.get.reset_mock()
        self.session.get.return_value.json.side_effect = ValueError("bad JSON")
        with self.assertRaisesRegex(APIError, "invalid JSON"):
            self.fetch()
        self.assertEqual(self.session.get.call_count, 1)

    def test_retry_after_parsing(self):
        for value in (None, "garbage", "1", "-10", "inf", "nan"):
            self.assertEqual(retry_delay(value), 3)
        self.assertEqual(retry_delay("7"), 7)
        future = datetime.now(timezone.utc) + timedelta(seconds=90)
        self.assertGreater(retry_delay(format_datetime(future)), 80)

    def test_client_uses_only_planned_endpoints(self):
        client = TVMazeClient(self.session, pause=self.pause, output=self.output)
        self.assertEqual(client.search("  "), [])
        self.session.get.assert_not_called()
        self.session.get.return_value = response(data=[{"show": {"id": 526}}])
        self.assertEqual(client.search("  The Office  "), [{"id": 526}])
        client.episodes(526)
        self.assertEqual(self.session.get.call_count, 2)
        self.assertEqual(self.session.get.call_args.args[0], "https://api.tvmaze.com/shows/526/episodes")

    def test_invalid_show_id_cannot_become_a_path(self):
        client = TVMazeClient(self.session)
        for invalid in (None, True, -1, "526/episodes"):
            with self.assertRaises(APIError):
                client.episodes(invalid)
        self.session.get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
