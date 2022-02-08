"""
Base settings for castle.
"""
from pathlib import Path

from pydantic import BaseSettings, DirectoryPath, Field


class Settings(BaseSettings):
    root: DirectoryPath = Field(Path.home() / "castle", env="CASTLE_HOME")


settings = Settings()
