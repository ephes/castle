"""
Just some helper functions for downloading audio urls etc.
"""

import httpx
import rich.progress


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
    return target_path
