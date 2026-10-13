import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from favorites import load_favorites, save_favorite


class FavoritesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "favorites.json"
        self.output = Mock()
        self.show = {"id": 526, "name": "The Office", "url": "https://www.tvmaze.com/shows/526/the-office"}

    def test_missing_file_then_save_reload_and_duplicate(self):
        favorites, writable = load_favorites(self.path, self.output)
        self.assertEqual(favorites, [])
        self.assertTrue(writable)
        self.assertTrue(save_favorite(self.show, favorites, self.path, output=self.output))
        original = self.path.read_bytes()
        self.assertEqual(load_favorites(self.path)[0], favorites)
        self.assertFalse(save_favorite(self.show, favorites, self.path, output=self.output))
        self.assertEqual(len(favorites), 1)
        self.assertEqual(self.path.read_bytes(), original)

    def test_corrupt_file_is_not_overwritten(self):
        for bad in ("{", '{"id": 526}', '[{"id": true}]', '[null]'):
            with self.subTest(bad=bad):
                self.path.write_text(bad, encoding="utf-8")
                favorites, writable = load_favorites(self.path, self.output)
                self.assertFalse(writable)
                self.assertFalse(save_favorite(self.show, favorites, self.path,
                                               writable=writable, output=self.output))
                self.assertEqual(self.path.read_text(encoding="utf-8"), bad)

    def test_write_failure_keeps_file_and_memory(self):
        self.path.write_text("[]", encoding="utf-8")
        favorites = []
        with patch("favorites.os.replace", side_effect=PermissionError("read-only")):
            self.assertFalse(save_favorite(self.show, favorites, self.path, output=self.output))
        self.assertEqual(favorites, [])
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), [])
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])

    def test_read_failure_disables_saving(self):
        with patch.object(Path, "read_text", side_effect=PermissionError("read-only")):
            self.assertEqual(load_favorites(self.path, self.output), ([], False))


if __name__ == "__main__":
    unittest.main()
