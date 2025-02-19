"""
Guideline Interface - FastAPI interface
"""

import logging

from config import Settings
from fastapi import FastAPI, HTTPException
from utils import get_release_paths_from_disk, load_recommendations

logger = logging.getLogger("uvicorn")

init = False
app = FastAPI()
settings = Settings()

settings.recommendation_path.mkdir(exist_ok=True)

resource_store = load_recommendations(
    get_release_paths_from_disk(settings.recommendation_path)
)
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


@app.get("/fhir/version-history")
async def get_versions() -> list:
    """
    Retrieve available FHIR versions.

    Returns: Available FHIR versions
    """
    return list(resource_store.keys())


@app.get("/fhir/{resource_name}")
async def serve_resources(
    resource_name: str, url: str, version: str = "latest"
) -> dict:
    """
    Serve FHIR resources from the local storage.

    Returns: Requested FHIR Resource
    """

    if version not in resource_store:
        raise HTTPException(status_code=404, detail=f"Version {version} not found")

    if resource_name not in resource_store[version]:
        raise HTTPException(
            status_code=404, detail=f"Resource {resource_name} not found"
        )

    if url not in resource_store[version][resource_name]:
        raise HTTPException(status_code=404, detail=f"Resource nod found: {url}")

    return resource_store[version][resource_name][url]
