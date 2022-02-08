"""
Castle is a little podcast command line utility to show
new episodes and download audio files.
"""


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

    def __eq__(self, other):
        return self.url == other.url


class Podcast:
    def __init__(
        self,
        feed,
        title,
        episodes_count,
        file_name_pattern="{index}_{title}.{file_format}",
        directory=None,
    ):
        self.feed = feed
        self.title = title
        self.file_name_pattern = file_name_pattern
        self.episodes_count = episodes_count
        self.directory = (
            self.title.lower().replace(" ", "_") if directory is None else directory
        )

    @classmethod
    def from_dict(cls, podcast):
        feed = Feed.from_dict(podcast["feed"])
        foo = cls(
            feed,
            podcast["title"],
            podcast.get("episodes_count", 0),
            file_name_pattern=podcast["file_name_pattern"],
            directory=podcast.get("directory"),
        )
        return foo

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

    def __eq__(self, other):
        equal = self.feed == other.feed and self.title == other.title
        return equal

    def get_base_dir(self):
        return self.title.lower().replace(" ", "_")

    def get_audio_file_name(self, episode):
        details = {
            # FIXME proper suffix from path? Or take info about format from feed?
            "file_format": episode.audio_url.split(".")[-1],
            "index": episode.index,
            "title": episode.title.lower().replace(" ", "_"),
        }
        return self.file_name_pattern.format(**details)


class Episode:
    def __init__(
        self,
        *args,
        index,
        guid,
        audio_url,
        published,
        title,
        podcast=None,
        audio_file=None,
    ):
        self.podcast = podcast
        self.index = index
        self.guid = guid
        self.audio_url = audio_url
        self.published = published
        self.title = title
        self.audio_file = audio_file

    @classmethod
    def from_dict(cls, episode):
        return cls(**episode)

        # podcast = episode.get("podcast")
        # return cls(
        #     podcast,
        #     *[episode[key] for key in ["index", "guid", "audio", "published", "title"]],
        #     audio_file_name=episode.get("audio_file_name")
        # )

    def __repr__(self):
        return f"{self.title}"

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return self.podcast == other.podcast and self.audio_url == other.audio_url

    def dict(self):
        return {
            "index": self.index,
            "guid": self.guid,
            "audio_url": self.audio_url,
            "published": self.published,
            "title": self.title,
            "audio_file": self.audio_file,
        }

    @property
    def audio_file_name(self):
        return self.podcast.get_audio_file_name(self)
