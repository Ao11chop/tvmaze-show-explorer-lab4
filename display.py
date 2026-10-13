"""Format TVmaze data for a terminal; these functions make no API calls."""

from html.parser import HTMLParser
import textwrap


class SummaryText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in ("p", "br", "div", "li"):
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in ("p", "div", "li"):
            self.parts.append(" ")


def text(value):
    """Keep terminal control characters out of remote text."""
    if value is None or value == "":
        return "Unknown"
    value = str(value)
    return " ".join("".join(c if c.isprintable() else " " for c in value).split()) or "Unknown"


def plain_summary(value):
    if not value:
        return "Unknown"
    parser = SummaryText()
    parser.feed(str(value))
    return text("".join(parser.parts))


def source_url(show):
    url = show.get("url")
    if isinstance(url, str) and url.startswith("https://www.tvmaze.com/"):
        return url
    return f"https://www.tvmaze.com/shows/{show['id']}"


def show_matches(shows, output=print):
    output("\nSearch results:")
    for index, show in enumerate(shows, 1):
        premiered = show.get("premiered")
        year = premiered[:4] if isinstance(premiered, str) and premiered else "Unknown"
        output(f"{index:>2}. {text(show.get('name'))} ({year}) | ID {show['id']}")


def show_profile(show, output=print):
    output(f"\n{text(show.get('name'))} | ID {show['id']}")
    output("-" * 72)
    genres = show.get("genres")
    rating = show.get("rating")
    output(f"Language: {text(show.get('language'))}")
    output(f"Genres: {', '.join(text(g) for g in genres) if genres else 'Unknown'}")
    output(f"Status: {text(show.get('status'))} | Premiered: {text(show.get('premiered'))}")
    output(f"Rating: {text(rating.get('average') if isinstance(rating, dict) else None)}")
    output(textwrap.fill(plain_summary(show.get("summary")), width=88))
    output(f"Source: TVmaze — {source_url(show)}")
    output("TVmaze data: CC BY-SA — https://creativecommons.org/licenses/by-sa/4.0/")


def episode_order(episode):
    return tuple(value if type(value) is int and value >= 0 else float("inf")
                 for value in (episode.get("season"), episode.get("number")))


def filter_episodes(episodes, season=None):
    selected = episodes if season is None else [e for e in episodes if e.get("season") == season]
    return sorted(selected, key=episode_order)


def show_episodes(episodes, season=None, output=print):
    selected = filter_episodes(episodes, season)
    heading = "All episodes" if season is None else f"Season {season}"
    output(f"\n{heading} ({len(selected)}):")
    if not selected:
        output("Episode information is unavailable." if season is None
               else "No episodes were returned for that season.")
        return
    output(f"{'Season':<8} {'Episode':<8} {'Air date':<12} {'Runtime':<12} Title")
    output("-" * 88)
    for episode in selected:
        runtime = episode.get("runtime")
        runtime_text = "Unknown" if runtime is None else f"{text(runtime)} min"
        output(f"{text(episode.get('season')):<8} {text(episode.get('number')):<8} "
               f"{text(episode.get('airdate')):<12} {runtime_text:<12} {text(episode.get('name'))}")
