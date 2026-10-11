"""Real filesystem/loopback HTTP ordering and exact artifact tests; no mocks."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest
import requests
from pytest_httpserver import HTTPServer
from werkzeug.wrappers import Response

from infrastructure.core.exceptions import PublishingError
from infrastructure.publishing.config_doi import read_publication_doi, read_publication_version_doi
from infrastructure.publishing.release.release_cli import build_release_parser
from infrastructure.publishing.release.release_workflow import ReleaseRequest, run_release_workflow

CONCEPT = "10.5281/zenodo.11111"
VERSION = "10.5281/zenodo.22222"
COMMIT = "a" * 40


def _project(root: Path) -> tuple[Path, Path]:
    manuscript = root / "projects/test_release/manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "00_abstract.md").write_text("# Abstract\n\nA real filesystem publication fixture.\n")
    config = manuscript / "config.yaml"
    config.write_text(
        'paper:\n  title: "Series Paper"\n  version: "2.0"\n'
        'authors:\n  - name: "Test Author"\n'
        f'publication:\n  doi: "{CONCEPT}"\n  version_doi: "10.5281/zenodo.99999"\n'
        'metadata:\n  license: "CC-BY-4.0"\n'
    )
    pdf = root / "output/test_release/pdf/test_release_combined.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(b"%PDF old version DOI 10.5281/zenodo.99999")
    return config, pdf


@pytest.fixture
def series_http():
    server = HTTPServer()
    server.start()
    base = server.url_for("").rstrip("/")
    state = {
        "events": [],
        "metadata": {},
        "reserved": False,
        "files": ["old-file"],
        "uploads": {},
        "missing_doi": False,
        "wrong_identity": False,
        "wrong_bucket": False,
        "mutate_pdf": None,
    }

    def respond(value):
        return Response(json.dumps(value), content_type="application/json")

    def records(_request):
        state["events"].append("records")
        return respond({"hits": {"hits": [{"id": 11111, "conceptdoi": CONCEPT}]}})

    def lookup(_request):
        state["events"].append("lookup")
        return respond({"hits": {"hits": [{"id": 7}]}})

    def new_version(_request):
        state["events"].append("newversion")
        return respond(
            {
                "id": 7,
                "state": "done",
                "submitted": True,
                "links": {
                    "bucket": base + "/files/original-record",
                    "latest_draft": base + "/deposit/depositions/8",
                },
            }
        )

    def get_draft(_request):
        state["events"].append("get-draft")
        metadata = dict(state["metadata"])
        if state["reserved"] and not state["missing_doi"]:
            metadata["prereserve_doi"] = {"doi": VERSION}
        return respond(
            {
                "id": 9 if state["wrong_identity"] and state["reserved"] else 8,
                "links": {
                    "bucket": base
                    + ("/files/wrong-draft" if state["wrong_bucket"] and state["reserved"] else "/files/new-draft")
                },
                "state": "unsubmitted",
                "submitted": False,
                "conceptdoi": CONCEPT,
                "metadata": metadata,
                "files": [{"id": name} for name in state["files"]],
            }
        )

    def delete_file(_request):
        state["events"].append("delete-old-file")
        state["files"] = []
        return respond({})

    def metadata(request):
        body = request.get_json()
        state["metadata"] = body["metadata"]
        if state["metadata"].get("prereserve_doi") is True:
            state["events"].append("reserve-metadata")
            state["reserved"] = True
        else:
            state["events"].append("metadata")
        return respond({"id": 8})

    def zenodo_upload(request):
        state["events"].append("zenodo-upload")
        state["uploads"]["zenodo"] = request.get_data()
        return respond({"key": request.path.rsplit("/", 1)[-1]})

    def publish(_request):
        state["events"].append("publish")
        if state["mutate_pdf"] is not None:
            state["mutate_pdf"].write_bytes(b"%PDF changed after the Zenodo publication")
        return respond({"doi": VERSION, "conceptdoi": CONCEPT, "state": "done"})

    def github(request):
        state["events"].append("github-release")
        state["github_payload"] = request.get_json()
        return respond(
            {
                "html_url": "https://github.com/testuser/testrepo/releases/tag/v2.0.0",
                "upload_url": base + "/github/assets{?name,label}",
            }
        )

    def github_upload(request):
        state["events"].append("github-upload")
        state["uploads"]["github"] = request.get_data()
        return respond({"state": "uploaded"})

    server.expect_request("/records", method="GET").respond_with_handler(records)
    server.expect_request("/deposit/depositions", method="GET").respond_with_handler(lookup)
    server.expect_request("/deposit/depositions/7/actions/newversion", method="POST").respond_with_handler(new_version)
    server.expect_request("/deposit/depositions/8", method="GET").respond_with_handler(get_draft)
    server.expect_request("/deposit/depositions/8/files/old-file", method="DELETE").respond_with_handler(delete_file)
    server.expect_request("/deposit/depositions/8", method="PUT").respond_with_handler(metadata)
    server.expect_request(re.compile(r"/files/new-draft/.+"), method="PUT").respond_with_handler(zenodo_upload)
    server.expect_request("/deposit/depositions/8/actions/publish", method="POST").respond_with_handler(publish)
    server.expect_request("/repos/testuser/testrepo/releases", method="POST").respond_with_handler(github)
    server.expect_request("/github/assets", method="POST").respond_with_handler(github_upload)
    for provider in ("zenodo", "github"):
        server.expect_request("/downloads/" + provider, method="GET").respond_with_handler(
            lambda _request, name=provider: Response(state["uploads"][name], content_type="application/pdf")
        )
    try:
        yield server, state
    finally:
        server.stop()


def _request(root: Path, server: HTTPServer, **kwargs) -> ReleaseRequest:
    return ReleaseRequest(
        repo_root=root,
        project_name="test_release",
        tag="v2.0.0",
        github_repo="testuser/testrepo",
        new_version=True,
        reserve_doi_first=True,
        zenodo_token="loopback-only",
        github_token="loopback-only",
        github_target_commit=COMMIT,
        zenodo_base_url=server.url_for(""),
        github_api_base_url=server.url_for(""),
        **kwargs,
    )


def test_existing_series_final_pdf_matches_both_uploaded_and_retrieved_bytes(tmp_path, series_http):
    server, state = series_http
    config, pdf = _project(tmp_path)
    request = _request(tmp_path, server)
    request.github_target_commit = None

    def render(_root, _project):
        assert read_publication_doi(config) == CONCEPT
        assert read_publication_version_doi(config) == VERSION
        state["events"].append("render")
        pdf.write_bytes(b"%PDF final version DOI " + VERSION.encode())
        destination = tmp_path / "standalone"
        destination.mkdir()
        (destination / "config.yaml").write_bytes(config.read_bytes())
        (destination / "final.pdf").write_bytes(pdf.read_bytes())
        subprocess.run(["git", "init", "--quiet"], cwd=destination, check=True)
        subprocess.run(["git", "add", "--", "config.yaml", "final.pdf"], cwd=destination, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Publication Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "Final DOI-bearing fixture",
            ],
            cwd=destination,
            check=True,
        )
        request.github_target_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=destination, capture_output=True, text=True, check=True
        ).stdout.strip()
        return 0

    result = run_release_workflow(request, render_fn=render)
    final = pdf.read_bytes()
    assert result.doi == VERSION and result.concept_doi == CONCEPT and result.render_exit_code == 0
    assert (
        state["events"].index("delete-old-file")
        < state["events"].index("reserve-metadata")
        < state["events"].index("render")
    )
    assert (
        state["events"].index("render")
        < state["events"].index("zenodo-upload")
        < state["events"].index("github-upload")
    )
    assert state["events"].index("records") < state["events"].index("lookup")
    assert state["files"] == [] and state["github_payload"]["target_commitish"] == request.github_target_commit
    expected = hashlib.sha256(final).hexdigest()
    assert result.pdf_sha256 == expected
    receipt = json.loads(result.receipt_path.read_text())
    assert receipt["final_rendered_pdf_sha256"] == receipt["pdf_sha256"] == expected
    assert receipt["github_target_commit"] == request.github_target_commit
    for provider in ("zenodo", "github"):
        response = requests.get(server.url_for("/downloads/" + provider), timeout=5)
        response.raise_for_status()
        assert final == state["uploads"][provider] == response.content
        assert hashlib.sha256(response.content).hexdigest() == expected
    server.check_assertions()


@pytest.mark.parametrize(
    "defect,reason",
    [("missing_doi", "prereserve"), ("wrong_identity", "identity differs"), ("wrong_bucket", "identity differs")],
)
def test_existing_series_invalid_reservation_never_renders_or_uploads(tmp_path, series_http, defect, reason):
    server, state = series_http
    config, pdf = _project(tmp_path)
    before = config.read_bytes(), pdf.read_bytes()
    state[defect] = True
    with pytest.raises(PublishingError, match=reason):
        run_release_workflow(_request(tmp_path, server))
    assert (config.read_bytes(), pdf.read_bytes()) == before
    assert not state["uploads"] and "publish" not in state["events"]


def test_existing_series_skip_rerender_refuses_before_reservation(tmp_path, series_http):
    server, state = series_http
    config, _pdf = _project(tmp_path)
    before = config.read_bytes()
    with pytest.raises(PublishingError, match="final DOI-bearing render"):
        run_release_workflow(_request(tmp_path, server, skip_rerender=True))
    assert config.read_bytes() == before and state["events"] == []


@pytest.mark.parametrize("commit", ["main", "a" * 39])
def test_explicit_series_route_requires_full_standalone_commit_before_reservation(tmp_path, series_http, commit):
    server, state = series_http
    _project(tmp_path)
    request = _request(tmp_path, server)
    request.github_target_commit = commit
    with pytest.raises(PublishingError, match="standalone"):
        run_release_workflow(request)
    assert state["events"] == []


def test_missing_final_standalone_target_refuses_after_render_before_upload(tmp_path, series_http):
    server, state = series_http
    _config, pdf = _project(tmp_path)
    request = _request(tmp_path, server)
    request.github_target_commit = None

    def render(_root, _project):
        state["events"].append("render")
        pdf.write_bytes(b"%PDF final " + VERSION.encode())
        return 0

    with pytest.raises(PublishingError, match="after render"):
        run_release_workflow(request, render_fn=render)
    assert "render" in state["events"] and not state["uploads"] and "publish" not in state["events"]


def test_render_failure_keeps_the_new_draft_unpublished(tmp_path, series_http):
    server, state = series_http
    _project(tmp_path)
    with pytest.raises(PublishingError, match="Pre-upload render"):
        run_release_workflow(_request(tmp_path, server), render_fn=lambda _root, _project: 1)
    assert not state["uploads"] and "publish" not in state["events"]


def test_changed_final_pdf_cannot_reach_github_or_a_success_receipt(tmp_path, series_http):
    server, state = series_http
    _config, pdf = _project(tmp_path)
    state["mutate_pdf"] = pdf

    def render(_root, _project):
        pdf.write_bytes(b"%PDF final " + VERSION.encode())
        return 0

    with pytest.raises(PublishingError, match="Final DOI-bearing rendered PDF differs"):
        run_release_workflow(_request(tmp_path, server), render_fn=render)
    assert "zenodo" in state["uploads"] and "github-release" not in state["events"]
    assert not (tmp_path / "output/test_release/release_bundle/RELEASE_RECEIPT.json").exists()


def test_existing_cli_accepts_explicit_standalone_commit():
    args = build_release_parser().parse_args(
        [
            "--project",
            "test_release",
            "--repo",
            "testuser/testrepo",
            "--tag",
            "v2.0.0",
            "--new-version",
            "--reserve-doi-first",
            "--github-target-commit",
            COMMIT,
        ]
    )
    assert args.github_target_commit == COMMIT and args.new_version and args.reserve_doi_first


def test_github_only_preserves_main_default_when_reserve_flag_is_dormant(tmp_path, series_http):
    server, state = series_http
    config, pdf = _project(tmp_path)
    before = config.read_bytes(), pdf.read_bytes()
    request = _request(tmp_path, server, skip_zenodo=True)
    request.github_target_commit = None
    result = run_release_workflow(request)
    assert result.github_release_url == "https://github.com/testuser/testrepo/releases/tag/v2.0.0"
    assert result.doi == CONCEPT and result.render_exit_code is None
    assert (config.read_bytes(), pdf.read_bytes()) == before
    assert state["events"] == ["github-release", "github-upload"]
    assert state["github_payload"]["target_commitish"] == "main"
    assert state["uploads"] == {"github": before[1]}
    receipt = json.loads(result.receipt_path.read_text())
    assert receipt["github_target_commit"] is None and receipt["final_rendered_pdf_sha256"] is None
    response = requests.get(server.url_for("/downloads/github"), timeout=5)
    response.raise_for_status()
    assert response.content == before[1]
    server.check_assertions()
