from pydantic import BaseSettings, Field, DirectoryPath

from pathlib import Path


class Settings(BaseSettings):
    root: DirectoryPath = Field(Path.home() / "castle", env="CASTLE_HOME")


settings = Settings()