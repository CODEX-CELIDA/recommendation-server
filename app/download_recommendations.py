"""
This script downloads the latest release from the GitHub repository specified in the configuration file.
"""
import logging
import shutil

from config import Settings
from utils import retrieve_release_from_github

settings = Settings()

# first, clean the recommendation directory if it exists
shutil.rmtree(settings.recommendation_path)

retrieve_release_from_github(
    repository_url=settings.gh_repository, target_path=settings.recommendation_path
)
logging.info("Downloaded releases from GitHub")
