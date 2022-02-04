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


def main(args):
    print(args)


if __name__ == "__main__":
    main(sys.argv[1:])
