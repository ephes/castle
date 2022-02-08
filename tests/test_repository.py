from datetime import datetime

from castle.repository import PodcastRepository


# def test_podcast_updated_from_json_to_datetime():
#     repo = PodcastRepository()
#     updated_str = "2022-02-02T06:10:22"
#     podcast_dict = {
#         "feed": {
#             "url": "https://example.com/rss.xml",
#             "updated": updated_str,
#         },
#         "title": "Python Podcast",
#     }
#     repo._all = [podcast_dict]
#     podcast = repo.list()[0]
#     assert podcast.feed.updated == datetime.fromisoformat(updated_str)
