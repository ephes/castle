"""
Castle is a little podcast command line utility to show
new episodes and download audio files.
"""

import sys
import json
import httpx
import feedparser

from time import mktime
from pathlib import Path
from datetime import datetime
from operator import itemgetter, attrgetter

from tqdm import tqdm

__version__ = "0.1"


def download_with_progress(url, target_path):
    with target_path.open("wb") as download_file:
        with httpx.stream("GET", url) as response:
            total = int(response.headers["Content-Length"])

            with tqdm(total=total, unit_scale=True, unit_divisor=1024, unit="B") as progress:
                num_bytes_downloaded = response.num_bytes_downloaded
                for chunk in response.iter_bytes():
                    download_file.write(chunk)
                    progress.update(response.num_bytes_downloaded - num_bytes_downloaded)
                    num_bytes_downloaded = response.num_bytes_downloaded


class Episode:
    def __init__(self, guid, audio, published, title):
        self.guid = guid
        self.audio = audio
        self.published = published
        self.title = title

    @classmethod
    def from_dict(cls, episode):
        return cls(episode["guid"], episode["audio"], episode["published"], episode["title"])

    def __repr__(self):
        return f"{self.title}"

    def __str__(self):
        return self.__repr__()

    def dict(self):
        return self.__dict__


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

        json_episodes = [e | {"published": datetime.fromisoformat(e["published"])} for e in json_episodes]
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
            episodes.append(Episode(
                entry.id,
                entry.enclosures[0]["href"],
                datetime.fromtimestamp(mktime(entry.published_parsed)),
                entry.title,
            ))
        episodes.sort(key=attrgetter("published"))
        return episodes

    def fetch(self):
        feed = {}
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


if __name__ == "__main__":
    main()
