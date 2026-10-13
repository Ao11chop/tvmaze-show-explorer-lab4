from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from explorer import main, run
from tvmaze_api import APIError

SHOWS = [{"id": 526, "name": "The Office", "premiered": "2005-03-24"},
         {"id": 1292, "name": "The Office", "premiered": "2001-07-09"}]
EPISODES = [{"name": "Pilot", "season": 1, "number": 1, "airdate": "2005-03-24", "runtime": 30},
            {"name": "Next", "season": 2, "number": 1}]


class CLITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "favorites.json"
        self.client = Mock()
        self.client.search.return_value = SHOWS
        self.client.episodes.return_value = EPISODES
        self.lines = []

    def play(self, commands):
        run(self.client, self.path, Mock(side_effect=commands), self.lines.append)

    def test_blank_invalid_selection_filters_and_favorites_use_no_extra_calls(self):
        self.play([" ", " The Office ", "0", "bad", "3", "1", "1", "99", "A", "F", "F", "L", "Q"])
        self.client.search.assert_called_once_with("The Office")
        self.client.episodes.assert_called_once_with(526)
        self.assertTrue(self.path.exists())
        output = "\n".join(self.lines)
        self.assertIn("already in favorites", output)
        self.assertIn("Season 1 (1)", output)
        self.assertIn("No episodes were returned for that season", output)

    def test_reselection_uses_existing_search_results(self):
        self.play(["The Office", "1", "B", "2", "Q"])
        self.client.search.assert_called_once()
        self.assertEqual([call.args[0] for call in self.client.episodes.call_args_list], [526, 1292])

    def test_no_matches_and_back_then_new_search(self):
        self.client.search.side_effect = [[], SHOWS, SHOWS]
        self.play(["zzzzunlikely", "The Office", "B", "Girls", "Q"])
        self.assertEqual(self.client.search.call_count, 3)
        self.client.episodes.assert_not_called()
        self.assertIn("No matching shows", "\n".join(self.lines))

    def test_404_reselects_without_searching_again(self):
        self.client.episodes.side_effect = [APIError("missing", 404), []]
        self.play(["The Office", "1", "2", "Q"])
        self.client.search.assert_called_once()
        self.assertEqual(self.client.episodes.call_count, 2)
        self.assertIn("HTTP 404", "\n".join(self.lines))

    def test_final_episode_failure_returns_to_search(self):
        self.client.episodes.side_effect = APIError("offline")
        self.play(["The Office", "1", "Q"])
        self.assertIn("Returning to search", "\n".join(self.lines))

    def test_failed_search_returns_to_prompt(self):
        self.client.search.side_effect = APIError("offline")
        self.play(["The Office", "Q"])
        self.client.episodes.assert_not_called()
        self.assertIn("Search failed", "\n".join(self.lines))

    def test_damaged_favorites_still_allow_browsing(self):
        self.path.write_text("broken", encoding="utf-8")
        self.play(["The Office", "1", "F", "Q"])
        self.assertEqual(self.path.read_text(encoding="utf-8"), "broken")
        self.assertIn("saving is disabled", "\n".join(self.lines))

    def test_main_closes_session_when_input_ends(self):
        with patch("explorer.requests.Session") as session, \
             patch("explorer.run", side_effect=EOFError), \
             patch("sys.argv", ["explorer.py"]), patch("builtins.print"):
            main()
        session.return_value.__exit__.assert_called_once()


if __name__ == "__main__":
    unittest.main()
