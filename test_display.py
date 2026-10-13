import unittest

from display import filter_episodes, plain_summary, show_episodes, show_matches, show_profile


class DisplayTests(unittest.TestCase):
    def test_html_summary_and_entities(self):
        self.assertEqual(plain_summary("<p>A <b>show</b> &amp; more.</p><p>Next.</p>"),
                         "A show & more. Next.")

    def test_missing_metadata_is_unknown(self):
        lines = []
        show_profile({"id": 526}, lines.append)
        result = "\n".join(lines)
        self.assertIn("Premiered: Unknown", result)
        self.assertIn("Rating: Unknown", result)
        self.assertIn("https://www.tvmaze.com/shows/526", result)
        self.assertIn("CC BY-SA", result)
        show_matches([{"id": 526, "name": "The Office"}], lines.append)
        self.assertIn("(Unknown) | ID 526", lines[-1])

    def test_sorting_and_filtering_with_missing_numbers(self):
        data = [{"season": 2, "number": 1}, {"season": None, "number": None},
                {"season": 1, "number": None}, {"season": 1, "number": 2},
                {"season": 1, "number": 1}]
        self.assertEqual(filter_episodes(data), [data[4], data[3], data[2], data[0], data[1]])
        self.assertEqual(len(filter_episodes(data, 1)), 3)
        self.assertEqual(data[0]["season"], 2)  # Original download is unchanged.

    def test_empty_episode_guide_and_missing_fields(self):
        lines = []
        show_episodes([], output=lines.append)
        self.assertIn("Episode information is unavailable.", lines)
        show_episodes([{}], output=lines.append)
        self.assertGreaterEqual(lines[-1].count("Unknown"), 5)
        show_episodes([{"season": 1}], 9, lines.append)
        self.assertIn("No episodes were returned for that season.", lines)


if __name__ == "__main__":
    unittest.main()
