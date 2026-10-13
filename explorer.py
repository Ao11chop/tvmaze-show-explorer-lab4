"""Run with: python explorer.py (Python 3.12 or newer)."""

import argparse
from pathlib import Path

import requests

from display import show_episodes, show_matches, show_profile
from favorites import load_favorites, save_favorite, show_favorites
from tvmaze_api import APIError, TVMazeClient

DEFAULT_FAVORITES = Path(__file__).resolve().with_name("favorites.json")


def choose_show(shows, input_fn=input, output=print):
    while True:
        selection = input_fn("Choose a result number, B to search again, or Q to quit: ").strip()
        if selection.upper() in ("B", "Q"):
            return selection.upper()
        try:
            number = int(selection)
        except ValueError:
            number = 0
        if 1 <= number <= len(shows):
            return shows[number - 1]
        output(f"Enter a number from 1 to {len(shows)}, B, or Q.")


def browse_show(show, episodes, favorites, path, writable, input_fn=input, output=print):
    """Everything here uses local data; no client is available to make a request."""
    show_episodes(episodes, output=output)
    while True:
        output("\nSeason number = filter | A = all episodes | F = save favorite | L = list favorites")
        output("B = choose another result | N = new search | Q = quit")
        command = input_fn("Action: ").strip().upper()
        if command in ("B", "N", "Q"):
            return command
        if command == "A":
            show_episodes(episodes, output=output)
        elif command == "F":
            save_favorite(show, favorites, path, writable=writable, output=output)
        elif command == "L":
            show_favorites(favorites, output)
        else:
            try:
                season = int(command)
            except ValueError:
                season = 0
            if season > 0:
                show_episodes(episodes, season, output)
            else:
                output("Enter a positive season number or one of the listed letters.")


def run(client, favorites_path=DEFAULT_FAVORITES, input_fn=input, output=print):
    favorites, writable = load_favorites(favorites_path, output)
    output("TV Show Explorer — TVmaze")
    output(f"Loaded {len(favorites)} favorite(s). Local file: {favorites_path}")
    while True:
        title = input_fn("\nShow title (Q to quit): ").strip()
        if title.upper() == "Q":
            return
        if not title:
            output("Enter a show title; blank input does not send a request.")
            continue
        try:
            shows = client.search(title)
        except APIError as exc:
            output(f"Search failed: {exc} Please try another title.")
            continue
        if not shows:
            output("No matching shows. Please try another title.")
            continue

        while True:
            show_matches(shows, output)
            show = choose_show(shows, input_fn, output)
            if show == "Q":
                return
            if show == "B":
                break
            # The search result already contains the profile. No detail request.
            show_profile(show, output)
            try:
                episodes = client.episodes(show["id"])
            except APIError as exc:
                if exc.status == 404:
                    output("The episode guide was not found (HTTP 404). Choose another result or go back.")
                    continue
                output(f"Episode request failed: {exc} Returning to search.")
                break
            action = browse_show(show, episodes, favorites, favorites_path, writable, input_fn, output)
            if action == "Q":
                return
            if action == "N":
                break
            # B returns to the same downloaded matches without repeating A1.


def main():
    parser = argparse.ArgumentParser(description="Search TVmaze and browse episode guides.")
    parser.add_argument("--favorites", type=Path, default=DEFAULT_FAVORITES,
                        help="local favorites JSON file (default: beside explorer.py)")
    args = parser.parse_args()
    try:
        with requests.Session() as session:
            run(TVMazeClient(session), args.favorites)
    except (EOFError, KeyboardInterrupt):
        print("\nInput ended.")
    print("Goodbye.")


if __name__ == "__main__":
    main()
