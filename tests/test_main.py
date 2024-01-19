from pathlib import Path

import pytest
from fastapi import HTTPException

gh_repository = "https://github.com/CODEX-CELIDA/celida-recommendations"
versions = ["v1.2.1-snapshot", "v1.1.0-snapshot", "v1.0.1"]
resource_name = "ActivityDefinition"
url = "https://www.netzwerk-universitaetsmedizin.de/fhir/codex-celida/guideline/covid19-inpatient-therapy/recommended-action/drug-administration-action/no-antithrombotic-prophylaxis-nadroparin-administration-low-weight"


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("GH_REPOSITORY", gh_repository)


def test_get_github_releases():
    from app.utils import get_github_releases

    releases = get_github_releases("CODEX-CELIDA", "celida-recommendations")
    assert isinstance(releases, list)
    assert len(releases) > 0
    assert isinstance(releases[0], dict)
    assert "tag_name" in releases[0]
    assert "assets" in releases[0]

    for version in versions:
        assert any(release["tag_name"] == version for release in releases)


def test_retrieve_release_from_github():
    from app.utils import retrieve_release_from_github

    release_paths = retrieve_release_from_github(
        gh_repository, include_versions=versions
    )

    assert isinstance(release_paths, dict)
    assert "latest" in release_paths
    for version in versions:
        assert version in release_paths
        assert isinstance(release_paths[version], Path)
        assert release_paths[version].exists()
        assert len(list(release_paths[version].glob("*"))) > 0, "No resources loaded"
        assert (
            len(list((release_paths[version] / "package").glob("*"))) > 0
        ), "No resources loaded"


def test_load_recommendations():
    from app.utils import load_recommendations

    resource_store = load_recommendations(gh_repository, include_versions=versions)
    assert isinstance(resource_store, dict)
    assert "latest" in resource_store
    for version in versions:
        assert version in resource_store
        assert isinstance(resource_store[version], dict)
        assert len(resource_store[version]) > 0, "No resources loaded"


@pytest.mark.asyncio
async def test_serve_resources():
    from app.main import serve_resources

    for version in versions + ["latest"]:
        if version == "v1.0.1":
            with pytest.raises(HTTPException):
                await serve_resources(resource_name, url, version)
        else:
            resource = await serve_resources(resource_name, url, version)
            assert isinstance(resource, dict)
            assert resource["resourceType"] == resource_name
            assert resource["url"] == url
