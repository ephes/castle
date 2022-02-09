from datetime import datetime

import pytest

from pdcst.models import Episode, Feed, Podcast
from pdcst.repository import EpisodeRepository, PodcastRepository


@pytest.fixture
def feed():
    return Feed(url="https://example.com/rss.xml", updated=datetime.utcnow())


@pytest.fixture
def podcast(feed):
    return Podcast(feed=feed, title="Python Podcast", episodes_count=3)


def test_podcast_repository_add(podcast, tmpdir):
    podcast_repository = PodcastRepository(tmpdir)
    podcast_repository.add(podcast)
    podcast_from_repo = podcast_repository.list()[0]
    assert (
        podcast_from_repo == podcast
        and podcast_from_repo.feed.updated == podcast.feed.updated
    )


@pytest.fixture
def episode(podcast):
    attributes = {
        "podcast": podcast,
        "index": 0,
        "audio_url": "https://d2mmy4gxasde9x.cloudfront.net/cast_audio/pp38_refactoring.mp3",
        "guid": "dfd60a58-8bd3-4fe2-8dab-87f55093a0c7",
        "published": datetime.utcnow(),
        "title": "Refactoring",
    }
    return Episode.from_dict(attributes)


def test_episode_repository_add(episode, tmpdir):
    episode_repository = EpisodeRepository(tmpdir)
    episode_repository.add(episode)

    # list without podcast
    episode_from_repository = episode_repository.list()[0]
    assert episode_from_repository.podcast is None
    assert (
        episode_from_repository.title == episode.title
    )  # compare only title because of missing podcast

    # list with podcast
    episode_from_repository = episode_repository.list(
        additional_attributes={"podcast": episode.podcast}
    )[0]
    assert episode_from_repository == episode


def test_episode_repository_add_list(episode, tmpdir):
    episode_repository = EpisodeRepository(tmpdir)
    episode_repository.add_list([episode])

    # list without podcast
    episode_from_repository = episode_repository.list()[0]
    assert episode_from_repository.podcast is None
    assert (
        episode_from_repository.title == episode.title
    )  # compare only title because of missing podcast

    # list with podcast
    episode_from_repository = episode_repository.list(
        additional_attributes={"podcast": episode.podcast}
    )[0]
    assert episode_from_repository == episode
