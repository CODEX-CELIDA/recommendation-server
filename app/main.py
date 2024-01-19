"""
Guideline Interface - FastAPI interface
"""

import logging

from fastapi import FastAPI, HTTPException

from app.config import Settings
from app.utils import load_recommendations

logger = logging.getLogger("uvicorn")

init = False
app = FastAPI()
settings = Settings()
resource_store = load_recommendations(repository_url=settings.gh_repository)
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
async def serve_resources(resource_name: str, url: str, version: str = "latest") -> str:
    """
    Serve FHIR resources from the local storage.

    Returns: Requested FHIR Resource
    """
    if (
        version in resource_store
        and resource_name in resource_store[version]
        and url in resource_store[version][resource_name]
    ):
        return resource_store[version][resource_name][url]
    else:
        raise HTTPException(status_code=404, detail="Resource not found")
