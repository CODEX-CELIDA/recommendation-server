from pathlib import Path

from pydantic import BaseSettings


class Settings(BaseSettings):  # type:ignore # mypy doesn't like BaseSettings ?
    """
    FastAPI Settings for guideline interface
    """

    gh_repository: str
    recommendation_path: Path = Path("./data")
