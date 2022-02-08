"""
Turn a rss feed into an object.
"""

from datetime import datetime
from operator import itemgetter
from time import mktime

import feedparser


class Feed:
    def __init__(self, url, updated):
        self.url = url
        self.updated = updated

    @classmethod
    def from_dict(cls, feed):
        return cls(feed["url"], feed["updated"])

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
        return episodes

    def fetch(self):
        document = feedparser.parse(self.feed_url)
        return {
            "title": document["feed"]["title"],
            "updated": datetime.fromtimestamp(mktime(document["updated_parsed"])),
            "episodes": self.parse_feed_entries(document.entries),
        }
