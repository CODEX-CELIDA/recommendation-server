import logging
import tarfile
import tempfile
import warnings
from pathlib import Path
from typing import Dict

import requests
import yaml
from fhir.resources import construct_fhir_element

HTTP_TIMEOUT = 10


def get_github_releases(owner: str, repo: str) -> dict:
    """
    Retrieve all releases of a GitHub repository.

    Args:
        owner: Owner of the repository
        repo: Name of the repository
    Returns: List of releases
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    response = requests.get(url, timeout=HTTP_TIMEOUT)

    if response.status_code != 200:
        raise RuntimeError(
            f"Could not retrieve releases from {url} (status code {response.status_code})"
        )

    return response.json()  # Returns a list of releases in JSON format


def retrieve_release_from_github(
    repository_url: str, include_versions: list[str] | None = None
) -> Dict[str, Path]:
    """
    Retrieve all releases of the guideline repository from GitHub.

    Args:
        repository_url: URL to the GitHub repository
        include_versions: List of versions to include (optional)
    Returns: Dict with paths to the downloaded FHIR resources for each release
    """

    owner, repo = repository_url.split("/")[3:5]

    base_path = Path(tempfile.mkdtemp())
    release_paths = {}

    releases = get_github_releases(owner, repo)

    for release in releases:
        package_version = release["tag_name"]

        if include_versions and package_version not in include_versions:
            continue

        assets = release["assets"]
        assert len(assets) == 1, "There should be exactly one asset per release"

        package_name = assets[0]["name"]
        package_url = assets[0]["browser_download_url"]

        r = requests.get(package_url, allow_redirects=True, timeout=HTTP_TIMEOUT)
        release_path = base_path / package_version
        release_path.mkdir(parents=True, exist_ok=True)

        with open(release_path / package_name, "wb") as f:
            f.write(r.content)

        tar = tarfile.open(release_path / package_name, "r:gz")
        tar.extractall(release_path)  # nosec (need to extract all files)
        tar.close()

        logging.info(f"Loaded recommendations from {package_url} into {release_path}")

        release_paths[package_version] = release_path

    release_paths["latest"] = release_paths[releases[0]["tag_name"]]

    return release_paths


def load_recommendations(
    repository_url: str, include_versions: list[str] | None = None
) -> Dict[str, Dict]:
    """
    Load all guideline recommendations from local storage into memory.
    """

    release_paths = retrieve_release_from_github(
        repository_url, include_versions=include_versions
    )

    resource_store: Dict[str, Dict] = {}

    for release_version, release_path in release_paths.items():
        resource_store[release_version] = {}

        for fname in (release_path / "package").glob("**/*.json"):
            with open(fname) as file:
                data = yaml.full_load(file)

            if "resourceType" not in data:
                continue

            if data["resourceType"] in ["ImplementationGuide", "Bundle"]:
                continue

            res = construct_fhir_element(data["resourceType"], data)

            if not hasattr(res, "url"):
                warnings.warn(
                    f'Not loading "{fname.name}" of type "{data["resourceType"]}" because no url element provided.'
                )
                continue

            if not data["resourceType"] in resource_store[release_version]:
                resource_store[release_version][data["resourceType"]] = {}

            if res.url in resource_store[release_version][data["resourceType"]]:
                warnings.warn(f'Resource "{res.url}" already loaded, overwriting..')

            resource_store[release_version][data["resourceType"]][res.url] = data

        if len(resource_store[release_version]) == 0:
            logging.info(f"No resources loaded from {release_path}")
            continue

        logging.info(
            f"Loaded {sum([len(res) for res in resource_store[release_version].values()])} resources ({len(resource_store[release_version])} types) from {release_path}"
        )

        logging.info(
            f'Loaded types: {", ".join([f"{k} ({len(v)})" for k, v in resource_store[release_version].items()])}'
        )

    return resource_store
