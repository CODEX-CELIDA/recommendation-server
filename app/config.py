import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):  # type:ignore # mypy doesn't like BaseSettings ?
    """
    FastAPI Settings for guideline interface
    """

    model_config = SettingsConfigDict(
        env_file=os.environ.get("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
    )

    gh_repository: str
    git_username: str | None = None
    git_token: str | None = None
    recommendation_path: Path = Path("./data")
