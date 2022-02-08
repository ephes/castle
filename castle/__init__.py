"""
Castle is a little podcast command line utility to show
new episodes and download audio files.
"""

import typer

from pathlib import Path

from .config import settings
from .repository import PodcastRepository, FeedParserRepository, EpisodeRepository
from .models import Feed, Podcast, Episode


__all__ = ["subscribe", "list_all_podcasts", "list_all_episodes"]

__version__ = "0.1"
cli = typer.Typer()


def subscribe(
        feed_url: str, name_pattern: str, podcast_dir: str | None,
        fp_repo=FeedParserRepository(),
        podcasts_repo=PodcastRepository(settings.root),
    ) -> Podcast:
    """
    Subscribe to a podcast feed url.
    """
    podcast, episodes = fp_repo.get(feed_url)

    # add fetched podcast metadata to repository
    podcast.file_name_pattern = name_pattern
    podcast.directory = podcast_dir
    podcasts_repo.add(podcast)

    # add fetched episodes metadata to repository
    episodes_repo = EpisodeRepository(Path(podcast.directory))
    episodes_repo.add(episodes)
    return podcast


def list_all_podcasts(podcasts=PodcastRepository(settings.root)) -> list[Podcast]:
    """
    List all podcasts.
    """
    return podcasts.list()


def list_all_episodes(podcast) -> list[Episode]:
    """
    List all episodes for a podcast.
    """
    episodes_repo = EpisodeRepository(podcast)
    return episodes_repo.list()


def find_podcast_by_identifier(identifier: str) -> Podcast | None:
    all_podcasts = list_all_podcasts()
    found = None
    for podcast in all_podcasts:
        if identifier in podcast.title.lower():
            found = podcast
            break
    return found


def find_episode_by_identifier(podcast: Podcast, identifier: str) -> Episode | None:
    episodes = list_all_episodes(podcast)
    found = None
    for episode in episodes:
        if identifier in episode.title.lower():
            found = episode
            break
    return found


@cli.command()
def add(
        feed_url: str,
        name_pattern: str = typer.Option(
            "{index}_{title}.{file_format}", help="Pattern to use for downloaded file names"
        ),
        podcasf_dir: str = typer.Option(
            None, help="base directory for storing podcast episodes"
        )
):
    """
    Subscribe to podcast with given FEED_URL.

    You can specify a file name pattern for downloaded audio files with --name-pattern
    """
    podcast = subscribe(feed_url, name_pattern, podcasf_dir)
    print(f"Podcast {podcast.title} added")


@cli.command(name="podcasts")
def list_podcasts():
    all_podcasts = list_all_podcasts()
    for podcast in all_podcasts:
        print(podcast)


@cli.command(name="episodes")
def list_episodes(identifier: str):
    podcast = find_podcast_by_identifier(identifier)
    if podcast is None:
        return
    episodes = list_all_episodes(podcast)
    for episode in episodes:
        print(episode)


@cli.command()
def download(podcast: str, episode: str):
    podcast = find_podcast_by_identifier(podcast)
    if podcast is None:
        return
    episode = find_episode_by_identifier(podcast, episode)
    episode.download()
    # FIXME readd to repo


if __name__ == "__main__":
    cli()
