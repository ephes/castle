"""
Castle is a little podcast command line utility to show
new episodes and download audio files.
"""

import json
import sys
from datetime import datetime
from operator import attrgetter
from pathlib import Path
from time import mktime

import feedparser
import httpx
import rich.progress
import typer

__version__ = "0.1"
cli = typer.Typer()


def download_with_progress(url, target_path):
    """
    Stolen from: https://www.python-httpx.org/advanced/
    """
    with target_path.open("wb") as download_file:
        with httpx.stream("GET", url) as response:
            total = int(response.headers["Content-Length"])

            with rich.progress.Progress(
                "[progress.percentage]{task.percentage:>3.0f}%",
                rich.progress.BarColumn(bar_width=None),
                rich.progress.DownloadColumn(),
                rich.progress.TransferSpeedColumn(),
            ) as progress:
                download_task = progress.add_task("Download", total=total)
                for chunk in response.iter_bytes():
                    download_file.write(chunk)
                    progress.update(
                        download_task, completed=response.num_bytes_downloaded
                    )


# def download_with_progress(url, target_path):
#     """
#     Copied from
#     """
#     with target_path.open("wb") as download_file:
#         with httpx.stream("GET", url) as response:
#             total = int(response.headers["Content-Length"])
#
#             with tqdm(total=total, unit_scale=True, unit_divisor=1024, unit="B") as progress:
#                 num_bytes_downloaded = response.num_bytes_downloaded
#                 for chunk in response.iter_bytes():
#                     download_file.write(chunk)
#                     progress.update(response.num_bytes_downloaded - num_bytes_downloaded)
#                     num_bytes_downloaded = response.num_bytes_downloaded


class Episode:
    def __init__(self, guid, audio, published, title):
        self.guid = guid
        self.audio = audio
        self.published = published
        self.title = title

    @classmethod
    def from_dict(cls, episode):
        return cls(*[episode[key] for key in ["guid", "audio", "published", "title"]])

    def __repr__(self):
        return f"{self.title}"

    def __str__(self):
        return self.__repr__()

    def dict(self):
        return self.__dict__

    def download(self):
        download_with_progress(self.audio, Path(self.title.lower().replace(" ", "_")))


class EpisodesRepository:
    name = "episodes.json"

    def __init__(self, feed):
        self.feed = feed

    @property
    def path(self):
        return Path(self.feed.episodes_directory) / self.name

    def get(self):
        json_episodes = []
        if not self.path.exists():
            return []
        with self.path.open("r") as f:
            try:
                json_episodes = json.loads(f.read())
            except json.JSONDecodeError:
                pass

        json_episodes = [
            e | {"published": datetime.fromisoformat(e["published"])}
            for e in json_episodes
        ]
        episodes = []
        for json_episode in json_episodes:
            episodes.append(Episode.from_dict(json_episode))
        return episodes

    def add(self, episodes):
        episodes = [e.dict() | {"published": e.published.isoformat()} for e in episodes]
        self.path.parent.mkdir(exist_ok=True)
        with self.path.open("w") as f:
            f.write(json.dumps(episodes, sort_keys=True, indent=4))


class FeedRepository:
    feed = None
    name = "feeds.json"

    def __init__(self, feed_url, episodes_repo_cls=EpisodesRepository):
        self.feed_url = feed_url
        self.episodes = episodes_repo_cls(self)

    @property
    def path(self):
        return Path(self.name)

    @property
    def episodes_directory(self):
        return self.feed["title"].lower().replace(" ", "_")

    def _fetch_all(self):
        feeds = {}
        if not self.path.exists():
            return {}
        with self.path.open("r") as f:
            try:
                feeds = json.loads(f.read())
            except Exception:
                pass
        return feeds

    def _fetch(self):
        feeds = self._fetch_all()
        self.feed = feed = feeds.get(self.feed_url)
        return feed

    def get(self):
        feed = self._fetch()
        if feed is None:
            return None
        # json to datetime
        feed |= {"updated": datetime.fromisoformat(feed["updated"])}
        feed["episodes"] = self.episodes.get()
        return feed

    def add(self, feed):
        feed = feed.copy()
        episodes = feed.pop("episodes", [])
        feed |= {"updated": feed["updated"].isoformat()}  # datetime to json
        self.feed = feed
        # To avoid race conditions implement proper locking of json file FIXME
        feeds = self._fetch_all() | {self.feed_url: feed}
        with self.path.open("w") as f:
            f.write(json.dumps(feeds, sort_keys=True, indent=4))
        self.episodes.add(episodes)


class FeedFetcher:
    def __init__(self, feed_url):
        self.feed_url = feed_url

    @staticmethod
    def parse_feed_entries(entries):
        episodes = []
        for entry in entries:
            episodes.append(
                Episode(
                    entry.id,
                    entry.enclosures[0]["href"],
                    datetime.fromtimestamp(mktime(entry.published_parsed)),
                    entry.title,
                )
            )
        episodes.sort(key=attrgetter("published"))
        return episodes

    def fetch(self):
        document = feedparser.parse(self.feed_url)
        return {
            "title": document["feed"]["title"],
            "updated": datetime.fromtimestamp(mktime(document["updated_parsed"])),
            "episodes": self.parse_feed_entries(document.entries),
        }


class Podcast:
    def __init__(self, feed_url, repository_cls=FeedRepository):
        self.feed_url = feed_url
        self.repository = repository_cls(feed_url)
        self.http = FeedFetcher(feed_url)
        self.load()

    def __repr__(self):
        return f"{self.title} - {len(self.episodes)} episodes"

    def __str__(self):
        return self.__repr__()

    def set_feed(self, feed):
        self.title = feed["title"]
        self.updated = feed["updated"]
        self.episodes = feed["episodes"]

    def load(self):
        if (feed := self.repository.get()) is None:
            feed = self.http.fetch()
            self.repository.add(feed)
        self.set_feed(feed)


@cli.command()
def main():
    help = """
Please provide a feed url.
    """
    if len(sys.argv) <= 1:
        print(help)
        sys.exit(0)
    feed_url = sys.argv[1]
    print("feed_url: ", feed_url)
    podcast = Podcast(feed_url)
    print(podcast)
    try:
        episode_index = int(sys.argv[2])
        print(podcast.episodes[episode_index])
        podcast.episodes[episode_index].download()
    except IndexError:
        pass


@cli.command()
def run():
    print("command run!")


if __name__ == "__main__":
    cli()
