import os
import shutil
import tempfile
from pathlib import Path

import pytest

gh_repository = "https://github.com/CODEX-CELIDA/celida-recommendations"
versions = ["v1.3.0", "v1.2.1-snapshot", "v1.1.0-snapshot", "v1.0.1", "latest"]
resources = [
    {
        "name": "ActivityDefinition",
        "url": "https://www.netzwerk-universitaetsmedizin.de/fhir/codex-celida/guideline/covid19-inpatient-therapy/recommended-action/drug-administration-action/no-antithrombotic-prophylaxis-nadroparin-administration-low-weight",
        "version": "v1.2.1-snapshot",
    },
    {
        "name": "PlanDefinition",
        "url": "https://www.netzwerk-universitaetsmedizin.de/fhir/codex-celida/guideline/covid19-inpatient-therapy/intervention-plan/peep-fio2-point4",
        "version": "v1.3.0",
    },
    {
        "name": "PlanDefinition",
        "url": "https://www.netzwerk-universitaetsmedizin.de/fhir/codex-celida/guideline/covid19-inpatient-therapy/intervention-plan/peep-fio2-point4",
        "version": "latest",
    },
]


@pytest.fixture(scope="session")
def session_tmp_dir():
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)

    yield temp_path

    shutil.rmtree(temp_dir)


@pytest.fixture(autouse=True)
def set_env(monkeypatch, session_tmp_dir):
    monkeypatch.setenv("GH_REPOSITORY", gh_repository)
    monkeypatch.setenv("RECOMMENDATION_PATH", session_tmp_dir)


@pytest.fixture(scope="session")
def release_paths(session_tmp_dir):
    from app.utils import retrieve_release_from_github

    release_paths = retrieve_release_from_github(
        gh_repository, include_versions=versions, target_path=session_tmp_dir
    )

    yield release_paths

    for version in versions:
        path = release_paths[version]

        if os.path.islink(path):
            path.unlink()
        else:
            shutil.rmtree(release_paths[version])


def test_get_github_releases():
    from app.utils import get_github_releases

    releases = get_github_releases("CODEX-CELIDA", "celida-recommendations")

    assert isinstance(releases, list)
    assert len(releases) > 0
    assert isinstance(releases[0], dict)
    assert "tag_name" in releases[0]
    assert "assets" in releases[0]

    for version in versions:
        if version == "latest":
            continue
        assert any(release["tag_name"] == version for release in releases)


def test_retrieve_release_from_github(release_paths):
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


def test_get_release_paths_from_disk(release_paths, session_tmp_dir):
    from app.utils import get_release_paths_from_disk

    release_paths_disk = get_release_paths_from_disk(session_tmp_dir)

    assert release_paths == release_paths_disk


def test_load_recommendations(release_paths):
    from app.utils import load_recommendations

    resource_store = load_recommendations(release_paths)

    assert isinstance(resource_store, dict)
    assert "latest" in resource_store
    for version in versions:
        assert version in resource_store
        assert isinstance(resource_store[version], dict)
        assert len(resource_store[version]) > 0, "No resources loaded"


@pytest.mark.asyncio
async def test_serve_resources(release_paths):
    from app.main import serve_resources

    for resource in resources:
        res = await serve_resources(
            resource["name"], resource["url"], resource["version"]
        )
        assert isinstance(resource, dict)
        assert res["resourceType"] == resource["name"]
        assert res["url"] == resource["url"]
