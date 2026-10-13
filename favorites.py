"""Small local JSON store. A failed save leaves the previous file intact."""

import json
import os
from pathlib import Path
import tempfile

from display import source_url, text


def load_favorites(path, output=print):
    """Return (favorites, safe_to_write); refuse to replace unreadable data."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [], True
    except (OSError, UnicodeError, ValueError) as exc:
        output(f"Warning: cannot read favorites ({exc}). Browsing is available; saving is disabled.")
        return [], False
    if not isinstance(data, list) or not all(
        isinstance(row, dict) and type(row.get("id")) is int and row["id"] > 0
        and isinstance(row.get("name"), str) and isinstance(row.get("url"), str)
        for row in data
    ):
        output("Warning: favorites have an invalid format. Browsing is available; saving is disabled.")
        return [], False
    return data, True


def save_favorite(show, favorites, path, *, writable=True, output=print):
    if not writable:
        output("Favorites were not saved: fix or move the unreadable file, then restart.")
        return False
    if any(row["id"] == show["id"] for row in favorites):
        output("This show is already in favorites.")
        return False
    favorite = {"id": show["id"], "name": text(show.get("name")), "url": source_url(show)}
    updated = favorites + [favorite]
    path = Path(path)
    temporary = None
    try:
        # Write beside the destination so replacement stays on the same filesystem.
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=path.name + ".", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(updated, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(temporary, path)
    except (OSError, UnicodeError) as exc:
        output(f"Warning: favorite could not be saved ({exc}). Browsing is still available.")
        return False
    finally:
        if temporary is not None and temporary.exists():
            try:
                temporary.unlink()
            except OSError:
                pass
    favorites.append(favorite)
    output(f"Saved {favorite['name']} to {path}.")
    return True


def show_favorites(favorites, output=print):
    output(f"\nSaved favorites ({len(favorites)}):")
    if not favorites:
        output("No favorites saved yet.")
    for favorite in favorites:
        output(f"{text(favorite['name'])} | ID {favorite['id']} | {text(favorite['url'])}")
