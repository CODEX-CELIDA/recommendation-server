"""
This script downloads the latest release from the GitHub repository specified in the configuration file.
"""
import logging

from config import Settings
from utils import retrieve_release_from_github

settings = Settings()

retrieve_release_from_github(
    repository_url=settings.gh_repository, target_path=settings.recommendation_path
)
logging.info("Downloaded releases from GitHub")
