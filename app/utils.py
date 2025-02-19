import logging
import os
import tarfile
import tempfile
import warnings
from pathlib import Path
from typing import Dict

import requests
import yaml
from fhir.resources import construct_fhir_element

DISABLE_SSL_VERIFY: bool = os.environ.get("DISABLE_SSL_VERIFY", "0") == "1"

if DISABLE_SSL_VERIFY:
    requests.packages.urllib3.disable_warnings()  # type: ignore # (requests _has_ attribute packages)
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ":HIGH:!DH:!aNULL"  # type: ignore # (requests _has_ attribute packages)
    try:
        requests.packages.urllib3.contrib.pyopenssl.util.ssl_.DEFAULT_CIPHERS += (  # type: ignore # (requests _has_ attribute packages)
            ":HIGH:!DH:!aNULL"
        )
    except AttributeError:
        # no pyopenssl support used / needed / available
        pass


HTTP_TIMEOUT = 10


def get_github_releases(
    owner: str, repo: str, username: str | None = None, password: str | None = None
) -> dict:
    """
    Get all releases from GitHub.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    auth = (username, password) if username and password else None

    response = requests.get(
        url, timeout=HTTP_TIMEOUT, verify=not DISABLE_SSL_VERIFY, auth=auth
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Could not retrieve releases from {url} (status code {response.status_code})"
        )

    return response.json()


def get_latest_release_tag(
    owner: str, repo: str, username: str | None = None, password: str | None = None
) -> str:
    """
    Get latest release.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    auth = (username, password) if username and password else None

    response = requests.get(
        url, timeout=HTTP_TIMEOUT, verify=not DISABLE_SSL_VERIFY, auth=auth
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Could not retrieve latest release from {url} (status code {response.status_code})"
        )

    return response.json()["tag_name"]


def retrieve_release_from_github(
    repository_url: str,
    include_versions: list[str] | None = None,
    target_path: Path | None = None,
    username: str | None = None,
    password: str | None = None,
) -> Dict[str, Path]:
    """
    Download releases from GitHub.

    """
    owner, repo = repository_url.split("/")[3:5]

    if target_path is None:
        base_path = Path(tempfile.mkdtemp())
    else:
        base_path = target_path
        if not base_path.exists():
            base_path.mkdir(parents=True, exist_ok=True)

    base_path = base_path.resolve()
    release_paths = {}

    releases = get_github_releases(owner, repo, username, password)
    latest_tag = get_latest_release_tag(owner, repo, username, password)

    for release in releases:
        package_version = release["tag_name"]

        if (
            include_versions
            and (package_version not in include_versions)
            and (package_version != latest_tag)
        ):
            continue

        assets = release["assets"]
        assert len(assets) == 1, "There should be exactly one asset per release"

        package_name = assets[0]["name"]
        package_url = assets[0]["url"]

        headers = {"Accept": "application/octet-stream"}
        if username and password:
            headers["Authorization"] = "token " + password

        r = requests.get(
            package_url,
            allow_redirects=True,
            timeout=HTTP_TIMEOUT,
            verify=not DISABLE_SSL_VERIFY,
            headers=headers,
        )

        assert r.status_code == 200, f"Invalid status code {r.status_code}"

        release_path = base_path / package_version
        release_path.mkdir(parents=True, exist_ok=True)

        with open(release_path / package_name, "wb") as f:
            f.write(r.content)

        tar = tarfile.open(release_path / package_name, "r:gz")
        tar.extractall(release_path)  # nosec
        tar.close()

        logging.info(f"Loaded recommendations from {package_url} into {release_path}")
        release_paths[package_version] = release_path

        if package_version == latest_tag:
            latest_path = base_path / "latest"
            os.symlink(release_path, latest_path)
            release_paths["latest"] = latest_path

    return release_paths


def get_release_paths_from_disk(target_path: str) -> dict[str, Path]:
    """
    Retrieve all releases of the guideline repository from GitHub.
    """
    release_paths = {}

    for entry in os.listdir(target_path):
        full_path = Path(target_path) / entry

        if full_path.is_dir():
            release_paths[entry] = full_path

    return release_paths


def load_recommendations(release_paths: dict[str, Path]) -> Dict[str, Dict]:
    """
    Load all guideline recommendations from local storage into memory.
    """

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
