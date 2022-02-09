from pdcst.repository import EpisodeRepository, PodcastRepository


def test_podcast_repository_add(podcast, tmpdir):
    podcast_repository = PodcastRepository(tmpdir)
    podcast_repository.add(podcast)
    podcast_from_repo = podcast_repository.list()[0]
    assert (
        podcast_from_repo == podcast
        and podcast_from_repo.feed.updated == podcast.feed.updated
    )


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
