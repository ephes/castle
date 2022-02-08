"""
Repositories to store podcasts/episodes.

Atm only uses json. But this could also be a sqlite or an
remote api, maybe fastAPI... hmm.
"""
from datetime import datetime
from operator import itemgetter
from pathlib import Path
from time import mktime

import feedparser

from pydantic import BaseModel, parse_file_as

from .models import Podcast, Episode, Feed


class FeedInDb(BaseModel):
    url: str
    updated: datetime


class EpisodeInDb(BaseModel):
    index: int
    guid: str
    audio: str
    published: datetime
    title: str


class EpisodeListInDb(BaseModel):
    """
    Used to make a list of episodes serializable to json.
    """
    __root__: list[EpisodeInDb]


class PodcastInDb(BaseModel):
    """
    The episodes attribute is omitted, because we use a different
    repository for that. One reason is to keep the podcasts json
    small and only fetch episodes when we need them. Another one
    is that we need to have a place to store audio files anyway, so
    we can use that for episodes metadata too.
    """
    feed: FeedInDb
    title: str
    episodes_count: int

    @property
    def pk(self):
        return self.feed.url


class PodcastListInDb(BaseModel):
    """
    Used to make a list of podcasts serializable to json.
    """
    __root__: list[PodcastInDb]


class JsonRepository:
    """
    Store a dict of serialized pydantic models in a json store.

    Use model.pk as primary key to be able to quickly locate models
    and maybe get/update/remove them.
    """
    _all = None

    def __init__(self, base_dir):
        self.base_dir = base_dir

    @property
    def path(self):
        return self.base_dir / self.name

    def _fetch_all(self):
        """
        Fetch dict of pydantic models from json in self.path
        """
        try:
            return {model.pk: model for model in parse_file_as(list[self.storage_model_type], self.path)}
        except FileNotFoundError:
            return {}

    @property
    def all(self):
        """
        Cache fetching all models from file.
        """
        if self._all is None:
            self._all = self._fetch_all()
        return self._all

    def list(self):
        """
        Just return a list of all stored models. Convert models from storage
        model type to domain model type.
        """
        return [self.domain_model_type.from_dict(model.dict()) for model in self.all.values()]


class EpisodeRepository(JsonRepository):
    """
    Store episodes metadata and audio files for a podcast.
    """
    name = "episodes.json"
    storage_model_type = EpisodeListInDb
    domain_model_type = Episode

    def list(self):
        """
        Build domain episodes from stored list of episodes.
        """
        return [Episode.from_dict(episode.dict() | {"podcast": self.podcast}) for episode in self.all]

    def add(self, episodes):
        episodes = EpisodeListInDb(__root__=[EpisodeInDb(**episode.dict()) for episode in episodes])
        self.path.parent.mkdir(exist_ok=True)
        with self.path.open("w") as f:
            f.write(episodes.json())


class PodcastRepository(JsonRepository):
    name = "podcasts.json"
    storage_model_type = PodcastInDb
    domain_model_type = Podcast

    @property
    def path(self):
        return Path(self.name)

    def _fetch_all(self):
        """
        Fetch list of podcasts from json in self.path

        Make it a dict to be able to look up podcasts by feed.
        """
        try:
            return {p.feed.url: p for p in parse_file_as(list[PodcastInDb], self.path)}
        except FileNotFoundError:
            return {}

    @property
    def all(self):
        """
        Cache fetching all podcasts from file.
        """
        if self._all is None:
            self._all = self._fetch_all()
        return self._all

    def list(self):
        return [Podcast.from_dict(podcast.dict()) for podcast in self.all.values()]

    def add(self, podcast):
        # To avoid race conditions implement proper locking of json file FIXME
        locked = self._fetch_all()
        locked[podcast.feed.url] = PodcastInDb(**podcast.dict())
        podcasts = PodcastListInDb(__root__=list(locked.values()))
        with self.path.open("w") as f:
            f.write(podcasts.json())


class FeedParserRepository:
    """
    Fetch/parse feed data from http.
    """
    @staticmethod
    def parse_feed_entries(entries):
        episodes = []
        for entry in entries:
            episodes.append(
                {
                    "guid": entry.id,
                    "audio": entry.enclosures[0]["href"],
                    "published": datetime.fromtimestamp(mktime(entry.published_parsed)),
                    "title": entry.title,
                }
            )
        episodes.sort(key=itemgetter("published"))
        # add index
        for index, episode in enumerate(episodes, 1):
            episode["index"] = index
        return episodes

    def get(self, url):
        """
        Fetch feed from http and parse/validate/build a podcast domain model.
        """
        document = feedparser.parse(url)

        # validate and build feed
        feed_in_db = FeedInDb(url=url, updated=datetime.fromtimestamp(mktime(document["updated_parsed"])))
        feed = Feed.from_dict(feed_in_db.dict())

        # validate episodes
        episodes_from_feed = self.parse_feed_entries(document.entries)
        validated_episodes = [EpisodeInDb(**episode) for episode in episodes_from_feed]

        # validate and build podcast
        podcast_in_db = PodcastInDb(feed=feed_in_db, title=document["feed"]["title"], episodes_count=len(validated_episodes))
        podcast = Podcast(feed, podcast_in_db.title, podcast_in_db.episodes_count)

        # validate and build episodes
        episodes = [Episode.from_dict(episode.dict() | {"podcast": podcast}) for episode in validated_episodes]

        return podcast, episodes
