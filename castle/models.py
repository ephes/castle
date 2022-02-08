"""
Castle is a little podcast command line utility to show
new episodes and download audio files.
"""

from pathlib import Path

from .download import download_with_progress


class Feed:
    def __init__(self, url, updated):
        self.url = url
        self.updated = updated

    @classmethod
    def from_dict(cls, feed):
        return cls(feed["url"], feed["updated"])

    def dict(self):
        return {
            "url": self.url,
            "updated": self.updated,
        }


class Podcast:
    def __init__(self,
                 feed, title, episodes_count,
                 file_name_pattern="{index}_{title}.{file_format}",
                 directory=None
    ):
        self.feed = feed
        self.title = title
        self.file_name_pattern = file_name_pattern
        self.episodes_count = episodes_count
        if directory is None:
            self.directory = self.title.lower().replace(" ", "_")

    @classmethod
    def from_dict(cls, podcast):
        feed = Feed.from_dict(podcast["feed"])
        return cls(feed, podcast["title"], podcast.get("episodes_count", 0), episodes=podcast.get("episodes"))

    def dict(self):
        return {
            "title": self.title,
            "feed": self.feed.dict(),
            "episodes_count": self.episodes_count,
            "file_name_pattern": self.file_name_pattern,
            "directory": self.directory,
        }

    def __repr__(self):
        return f"{self.title} - {self.episodes_count} episodes"

    def __str__(self):
        return self.__repr__()

    def get_base_dir(self):
        return self.title.lower().replace(" ", "_")

    def get_audio_file_name(self, episode):
        details = {
            # FIXME proper suffix from path? Or take info about format from feed?
            "file_format": episode.audio.split(".")[-1],
            "index": episode.index,
            "title": episode.title.lower().replace(" ", "_"),
        }
        return self.file_name_pattern.format(**details)


class Episode:
    def __init__(self, podcast, index, guid, audio, published, title):
        self.podcast = podcast
        self.index = index
        self.guid = guid
        self.audio = audio
        self.published = published
        self.title = title

    @classmethod
    def from_dict(cls, episode):
        print(episode)
        print([episode[key] for key in ["podcast", "index", "guid", "audio", "published", "title"]])
        return cls(*[episode[key] for key in ["podcast", "index", "guid", "audio", "published", "title"]])

    def __repr__(self):
        return f"{self.title}"

    def __str__(self):
        return self.__repr__()

    def dict(self):
        return {
            "index": self.index,
            "guid": self.guid,
            "audio": self.audio,
            "published": self.published,
            "title": self.title,
        }

    @property
    def audio_file_name(self):
        return self.podcast.get_audio_file_name(self)

    def download(self):
        print(self.podcast.get_base_dir(), self.audio_file_name)
        download_with_progress(self.audio, Path(self.podcast.get_base_dir()) / self.audio_file_name)
