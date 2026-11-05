"""Real transport/admission controls; fixture DATA grants no producer/model origin."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import stat
import subprocess
import sys
import time
import zipfile
from copy import deepcopy
from pathlib import Path

import pytest

from infrastructure.project.public_acceptance_literature_readback import (
    _REQUIRED_STEPS,
    ORIGINAL_DIRECTORY,
    WORKFLOW,
    import_originals,
    request_from_environment,
    select_original,
    validate_workflow,
)

ROOT = Path(__file__).resolve().parents[3]


def _environment() -> dict[str, str]:
    return {
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_REPOSITORY": "docxology/template",
        "GITHUB_SHA": "a" * 40,
        "GITHUB_RUN_ID": "22",
        "GITHUB_RUN_ATTEMPT": "1",
        "ARL_READBACK_MODE": "true",
        "ARL_PRODUCER_MODE": "false",
        "ARL_ORIGINAL_RUN_ID": "11",
        "ARL_ORIGINAL_RUN_ATTEMPT": "1",
        "ARL_ORIGINAL_SOURCE_SHA": "a" * 40,
    }


def _metadata():
    request = request_from_environment(_environment())
    run = {
        "id": 11,
        "run_attempt": 1,
        "head_sha": "a" * 40,
        "path": WORKFLOW,
        "event": "workflow_dispatch",
        "status": "completed",
        "conclusion": "success",
        "repository": {"id": 17, "full_name": request.repository},
        "head_repository": {"id": 17, "full_name": request.repository},
    }
    artifact = {
        "id": 33,
        "name": request.artifact_name,
        "expired": False,
        "size_in_bytes": 100,
        "digest": "sha256:" + "b" * 64,
        "created_at": "2026-01-01T00:01:00Z",
        "expires_at": "2099-01-01T00:00:00Z",
        "workflow_run": {"id": 11, "head_sha": "a" * 40, "repository_id": 17, "head_repository_id": 17},
    }
    job = {
        "id": 44,
        "name": "ARL auxiliary diagnostic",
        "run_id": 11,
        "run_attempt": 1,
        "head_sha": "a" * 40,
        "status": "completed",
        "conclusion": "success",
        "started_at": "2026-01-01T00:00:00Z",
        "completed_at": "2026-01-01T00:02:00Z",
        "steps": [{"name": name, "conclusion": "success"} for name in _REQUIRED_STEPS],
    }
    return request, run, artifact, job


def test_origin_metadata_predicate_admits_only_the_complete_declared_shape() -> None:
    # This is parsed API-shape discrimination, not an authenticated API or process result.
    request, run, artifact, job = _metadata()
    assert select_original(run, [artifact], [job], request) == (artifact, job)


@pytest.mark.parametrize(
    "defect",
    [
        "run-id",
        "run-attempt",
        "sha",
        "workflow",
        "event",
        "in-progress",
        "failed-run",
        "repo",
        "head-repo",
        "repo-id",
        "artifact-id",
        "artifact-name",
        "artifact-size",
        "digest",
        "expired",
        "expired-time",
        "artifact-run",
        "artifact-head",
        "artifact-repo",
        "job-id",
        "job-attempt",
        "job-head",
        "job-run",
        "job-failure",
        "step-missing",
        "step-failure",
        "step-order",
        "artifact-time",
        "duplicate-artifact",
        "duplicate-job",
    ],
)
def test_origin_metadata_refuses_foreign_partial_expired_or_mixed_custody(defect: str) -> None:
    request, run, artifact, job = deepcopy(_metadata())
    artifacts, jobs = [artifact], [job]
    if defect == "run-id":
        run["id"] = 99
    elif defect == "run-attempt":
        run["run_attempt"] = 2
    elif defect == "sha":
        run["head_sha"] = "c" * 40
    elif defect == "workflow":
        run["path"] = ".github/workflows/ci.yml"
    elif defect == "event":
        run["event"] = "pull_request"
    elif defect == "in-progress":
        run["status"] = "in_progress"
    elif defect == "failed-run":
        run["conclusion"] = "failure"
    elif defect == "repo":
        run["repository"]["full_name"] = "foreign/template"
    elif defect == "head-repo":
        run["head_repository"]["full_name"] = "foreign/template"
    elif defect == "repo-id":
        run["head_repository"]["id"] = 18
    elif defect == "artifact-id":
        artifact["id"] = True
    elif defect == "artifact-name":
        artifact["name"] += "-foreign"
    elif defect == "artifact-size":
        artifact["size_in_bytes"] = True
    elif defect == "digest":
        artifact["digest"] = "sha256:bad"
    elif defect == "expired":
        artifact["expired"] = True
    elif defect == "expired-time":
        artifact["expires_at"] = "2020-01-01T00:00:00Z"
    elif defect == "artifact-run":
        artifact["workflow_run"]["id"] = 99
    elif defect == "artifact-head":
        artifact["workflow_run"]["head_sha"] = "c" * 40
    elif defect == "artifact-repo":
        artifact["workflow_run"]["repository_id"] = 18
    elif defect == "job-id":
        job["id"] = True
    elif defect == "job-attempt":
        job["run_attempt"] = 2
    elif defect == "job-head":
        job["head_sha"] = "c" * 40
    elif defect == "job-run":
        job["run_id"] = 99
    elif defect == "job-failure":
        job["conclusion"] = "failure"
    elif defect == "step-missing":
        job["steps"].pop(2)
    elif defect == "step-failure":
        job["steps"][2]["conclusion"] = "failure"
    elif defect == "step-order":
        job["steps"][1:3] = reversed(job["steps"][1:3])
    elif defect == "artifact-time":
        artifact["created_at"] = "2026-01-01T00:03:00Z"
    elif defect == "duplicate-artifact":
        artifacts.append(deepcopy(artifact))
    elif defect == "duplicate-job":
        jobs.append(deepcopy(job))
    with pytest.raises(ValueError):
        select_original(run, artifacts, jobs, request)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("ARL_PRODUCER_MODE", "true"),
        ("ARL_READBACK_MODE", "false"),
        ("ARL_ORIGINAL_SOURCE_SHA", "b" * 40),
        ("GITHUB_EVENT_NAME", "pull_request"),
        ("ARL_ORIGINAL_RUN_ID", "22"),
        ("ARL_ORIGINAL_RUN_ATTEMPT", "0"),
        ("ARL_ORIGINAL_RUN_ID", "11; echo injected"),
        ("GITHUB_REPOSITORY", "../template"),
    ],
)
def test_same_sha_exclusive_request_refuses_ambiguous_or_injected_context(key: str, value: str) -> None:
    environment = _environment()
    environment[key] = value
    with pytest.raises(ValueError):
        request_from_environment(environment)


def test_workflow_api_bytes_must_match_the_actual_same_source(tmp_path: Path) -> None:
    body = b"name: original fixed ARL workflow\n"
    target = tmp_path / WORKFLOW
    target.parent.mkdir(parents=True)
    target.write_bytes(body)
    payload = {
        "path": WORKFLOW,
        "encoding": "base64",
        "content": base64.b64encode(body).decode(),
        "sha": hashlib.sha1(b"blob " + str(len(body)).encode() + b"\0" + body, usedforsecurity=False).hexdigest(),
    }
    validate_workflow(tmp_path, payload)
    target.write_bytes(body + b"actual Source drift\n")
    with pytest.raises(ValueError, match="differs"):
        validate_workflow(tmp_path, payload)


def _zip(files: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, body in files.items():
            archive.writestr(name, body)
    return output.getvalue()


def _transport_packet() -> dict[str, bytes]:
    body = b'{"schema_version":"transport-DATA-only","original_exit_code":0}\n'
    path = "pipeline-outputs/.pipeline/execution.json"
    receipt = {
        "schema_version": "transport-fixture-DATA-only",
        "original": {
            "path": ORIGINAL_DIRECTORY + "/" + path,
            "sha256": hashlib.sha256(body).hexdigest(),
            "bytes": len(body),
        },
    }
    return {"receipt.json": json.dumps(receipt).encode(), path: body, "unreferenced-original.bin": b"retained extra"}


@pytest.fixture
def transport_root(tmp_path: Path):
    yield tmp_path
    # Only disposable component DATA is made writable for pytest's own cleanup.
    for directory, _, files in os.walk(tmp_path):
        Path(directory).chmod(0o700)
        for name in files:
            path = Path(directory) / name
            if not path.is_symlink():
                path.chmod(0o600)


def test_real_zip_import_retains_hidden_bytes_and_freezes_the_actual_tree(transport_root: Path) -> None:
    files = _transport_packet()
    observed = import_originals(transport_root, _zip(files), time.monotonic() + 60)
    target = transport_root / ORIGINAL_DIRECTORY
    assert observed["members"] == 3 and observed["closure_files"] == 2
    for relative, body in files.items():
        path = target / relative
        assert path.read_bytes() == body
        assert stat.S_IMODE(path.stat().st_mode) == 0o400
    assert stat.S_IMODE(target.stat().st_mode) == 0o500
    assert stat.S_IMODE((target / "pipeline-outputs/.pipeline").stat().st_mode) == 0o500
    assert "status" not in observed  # Codec success is not complete cell admission.


@pytest.mark.parametrize("defect", ["missing-hidden", "changed-hidden", "wrong-size"])
def test_imported_original_closure_refuses_missing_or_changed_hidden_bytes(transport_root: Path, defect: str) -> None:
    files = _transport_packet()
    hidden = "pipeline-outputs/.pipeline/execution.json"
    if defect == "missing-hidden":
        del files[hidden]
    elif defect == "changed-hidden":
        files[hidden] += b"actual changed retained byte"
    else:
        receipt = json.loads(files["receipt.json"])
        receipt["original"]["bytes"] += 1
        files["receipt.json"] = json.dumps(receipt).encode()
    with pytest.raises((OSError, ValueError)):
        import_originals(transport_root, _zip(files), time.monotonic() + 60)


def test_occupied_originals_are_preserved_even_if_new_bytes_match(transport_root: Path) -> None:
    target = transport_root / ORIGINAL_DIRECTORY
    target.mkdir(parents=True)
    sentinel = target / "receipt.json"
    sentinel.write_bytes(b"prior original must remain\n")
    with pytest.raises(ValueError, match="fresh"):
        import_originals(transport_root, _zip(_transport_packet()), time.monotonic() + 60)
    assert sentinel.read_bytes() == b"prior original must remain\n"


@pytest.mark.parametrize("defect", ["parent", "absolute", "symlink", "directory", "duplicate", "oversize"])
def test_actual_archive_decoder_refuses_unsafe_or_unbounded_members(transport_root: Path, defect: str) -> None:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("receipt.json", b"{}")
        if defect == "parent":
            archive.writestr("../escape", b"must not escape")
        elif defect == "absolute":
            archive.writestr("/escape", b"must not escape")
        elif defect == "directory":
            archive.writestr("folder/", b"")
        elif defect == "duplicate":
            with pytest.warns(UserWarning, match="Duplicate"):
                archive.writestr("receipt.json", b"{}")
        elif defect == "symlink":
            member = zipfile.ZipInfo("aliased")
            member.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(member, b"outside")
        else:
            from infrastructure.project.public_hosted_origin import MAX_ARCHIVE

            archive.writestr("decoded-too-large.bin", b"x" * (MAX_ARCHIVE + 1))
    with pytest.raises(ValueError):
        import_originals(transport_root, output.getvalue(), time.monotonic() + 60)
    assert not (transport_root / ORIGINAL_DIRECTORY).exists()


def test_original_import_refuses_an_aliased_parent_before_writing(tmp_path: Path) -> None:
    root, outside = tmp_path / "root", tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "output").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        import_originals(root, _zip(_transport_packet()), time.monotonic() + 60)
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("deadline", [0, -1, True, float("nan"), float("inf")])
def test_expired_or_invalid_transport_clock_cannot_import(tmp_path: Path, deadline: float) -> None:
    with pytest.raises(TimeoutError):
        import_originals(tmp_path, _zip(_transport_packet()), deadline)
    assert not (tmp_path / ORIGINAL_DIRECTORY).exists()


def test_real_stdlib_cli_rejects_mixed_modes_before_sdk_or_network(tmp_path: Path) -> None:
    environment = {**os.environ, **_environment(), "ARL_PRODUCER_MODE": "true"}
    for name in ("GH_TOKEN", "GITHUB_TOKEN"):
        environment.pop(name, None)
    result = subprocess.run(
        [
            sys.executable,
            "-S",
            str(ROOT / "infrastructure/project/public_acceptance_literature_readback.py"),
            "admit",
            "--repo-root",
            str(tmp_path),
        ],
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 2
    assert "exclusive manual mode" in result.stderr
    assert not (tmp_path / "output").exists()


def test_fixed_api_refuses_an_arbitrary_workflow_endpoint_before_execution(tmp_path: Path) -> None:
    from infrastructure.project._hosted_api import fixed_hosted_api
    from infrastructure.project.public_hosted_origin import _api_command

    directory = tmp_path / "output/readiness/api"
    directory.mkdir(parents=True)
    api = fixed_hosted_api(
        tmp_path,
        directory,
        repository="docxology/template",
        run_id=11,
        head_sha="a" * 40,
        deadline=time.monotonic() + 30,
        environment={},
    )
    command = _api_command("repos/docxology/template/contents/.github/workflows/foreign.yml?ref=" + "a" * 40)
    with pytest.raises(ValueError, match="arbitrary"):
        api._execute(command, "foreign")
    assert list(directory.iterdir()) == []
