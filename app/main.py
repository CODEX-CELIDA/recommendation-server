"""
Guideline Interface - FastAPI interface
"""

import logging
import tarfile
import tempfile
import warnings
from pathlib import Path
from typing import Dict

import requests
import yaml
from fastapi import FastAPI, HTTPException
from fhir.resources import construct_fhir_element
from pydantic import BaseSettings

logger = logging.getLogger("uvicorn")


class Settings(BaseSettings):
    """
    FastAPI Settings for guideline interface
    """

    gh_release_base: str
    package_name_template: str


def retrieve_latest_github_release() -> Path:
    """
    Retrieve the latest release of the guideline repository from GitHub.

    Returns: Path to the downloaded FHIR resources
    """

    base_path = Path(tempfile.mkdtemp())

    response = requests.get(settings.gh_release_base + "/latest")
    if response.history:
        package_version = response.url.split("/")[-1]
        package_name = settings.package_name_template.format(
            version=package_version[1:]
        )
    else:
        raise ValueError(
            "No redirect for recommendation URL, can't load latest package"
        )

    package_url = (
        f"{settings.gh_release_base}/download/{package_version}/{package_name}"
    )

    r = requests.get(package_url, allow_redirects=True)
    with open(base_path / package_name, "wb") as f:
        f.write(r.content)

    tar = tarfile.open(base_path / package_name, "r:gz")
    tar.extractall(base_path)
    tar.close()

    logger.info(f"Loaded recommendations from {package_url}")

    return base_path / "package"


def load_recommendations() -> Dict[str, Dict]:
    """
    Load all guideline recommendations from local storage into memory.
    """

    fhir_path = retrieve_latest_github_release()

    resource_store: Dict[str, Dict] = {}

    for fname in fhir_path.glob("*.json"):

        with open(fname) as file:
            data = yaml.full_load(file)

        if "resourceType" not in data:
            continue

        if data["resourceType"] == "ImplementationGuide":
            continue
        res = construct_fhir_element(data["resourceType"], data)

        if not hasattr(res, "url"):
            warnings.warn(
                f'Not loading "{fname.name}" of type "{data["resourceType"]}" because no url element provided.'
            )
            continue

        if not data["resourceType"] in resource_store:
            resource_store[data["resourceType"]] = {}

        if res.url in resource_store[data["resourceType"]]:
            warnings.warn(f'Resource "{res.url}" already loaded, overwriting..')

        resource_store[data["resourceType"]][res.url] = data

    logger.info(
        f"Loaded {sum([len(res) for res in resource_store.values()])} resources ({len(resource_store)} types) from {fhir_path}"
    )
    logger.info(
        f'Loaded types: {", ".join([f"{k} ({len(v)})" for k, v in resource_store.items()])}'
    )

    return resource_store


init = False
app = FastAPI()
settings = Settings()
resource_store = load_recommendations()
init = True


@app.get("/health")
async def health() -> str:
    """
    Health check endpoint.

    Returns: "OK"
    """
    if init:
        return "OK"
    else:
        raise HTTPException(status_code=500, detail="Not initialized")


@app.get("/fhir/{resource_name}")
async def serve_resources(resource_name: str, url: str) -> str:
    """
    Serve FHIR resources from the local storage.

    Returns: Requested FHIR Resource
    """
    if resource_name in resource_store and url in resource_store[resource_name]:
        return resource_store[resource_name][url]
    else:
        raise HTTPException(status_code=404, detail="Resource not found")
