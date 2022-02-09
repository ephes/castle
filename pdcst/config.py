"""
Base settings for pdcst.
"""
from pathlib import Path

from pydantic import BaseSettings, DirectoryPath, Field


class Settings(BaseSettings):
    root: DirectoryPath = Field(Path.home() / "pdcst", env="PDCST_HOME")


settings = Settings()
