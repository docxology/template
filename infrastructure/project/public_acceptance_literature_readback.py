"""Authenticate and freshly read one downloaded ARL diagnostic at the same SHA.

This selected-cell transport diagnostic grants no aggregate or release authority.
The original run must already be complete; no provider or model is restarted.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import os
import re
import stat
import subprocess
import sys
import time
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

WORKFLOW = ".github/workflows/platform-native-preflight.yml"
CELL = "template_advanced_literature_review"
ORIGINAL_DIRECTORY = f"output/readiness/auxiliary-linux/{CELL}"
SCHEMA = "template-arl-transport-readback-v1"
_REQUIRED_STEPS = (
    "Admit the exact dispatched Source revision",
    "Complete source-owned auxiliary project selection",
    "Independently read every original ARL gate and its complete group",
    "Stop only the owned model daemon and descendants",
    "Export original Linux readiness bytes for the artifact reader",
    "Retain original auxiliary audit",
)


@dataclass(frozen=True)
class ReadbackRequest:
    """Same-repository, same-SHA identities nominated by the manual workflow."""

    repository: str
    source_sha: str
    producer_run: int
    producer_attempt: int
    reader_run: int
    reader_attempt: int

    @property
    def artifact_name(self) -> str:
        """Return the exact original artifact name for this attempt."""
        return f"auxiliary-preflight-arl-{self.producer_run}-{self.producer_attempt}"

    @property
    def evidence_path(self) -> str:
        """Keep the reader's observations outside its immutable originals."""
        return f"output/readiness/arl-transport-readback/{self.reader_run}-{self.reader_attempt}"


def _positive(value: object, label: str) -> int:
    if not isinstance(value, str) or re.fullmatch(r"[1-9][0-9]{0,18}", value) is None:
        raise ValueError(f"{label} must be a positive decimal identity")
    return int(value)


def request_from_environment(environment: Mapping[str, str]) -> ReadbackRequest:
    """Refuse mixed modes, another SHA, and an incomplete/self-referential request."""
    if (
        environment.get("GITHUB_EVENT_NAME") != "workflow_dispatch"
        or environment.get("ARL_READBACK_MODE") != "true"
        or environment.get("ARL_PRODUCER_MODE") != "false"
    ):
        raise ValueError("ARL readback requires its exclusive manual mode")
    repository = environment.get("GITHUB_REPOSITORY", "")
    source = environment.get("ARL_ORIGINAL_SOURCE_SHA", "")
    if (
        re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is None
        or any(part in {".", ".."} for part in repository.split("/"))
        or re.fullmatch(r"[0-9a-f]{40}", source) is None
        or environment.get("GITHUB_SHA") != source
    ):
        raise ValueError("ARL workflow, subject and producer must use the same exact repository/SHA")
    request = ReadbackRequest(
        repository,
        source,
        _positive(environment.get("ARL_ORIGINAL_RUN_ID"), "producer run"),
        _positive(environment.get("ARL_ORIGINAL_RUN_ATTEMPT"), "producer attempt"),
        _positive(environment.get("GITHUB_RUN_ID"), "reader run"),
        _positive(environment.get("GITHUB_RUN_ATTEMPT"), "reader attempt"),
    )
    if request.producer_run == request.reader_run:
        raise ValueError("ARL readback requires a separate completed producer run")
    return request


def admit_checkout(root: Path, request: ReadbackRequest) -> None:
    """Bind the real checked-out commit without rewriting GitHub's subject context."""
    if root.absolute() != root.resolve(strict=True):
        raise ValueError("ARL readback requires a physical Source root")
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=root,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0 or result.stdout.strip() != request.source_sha:
        raise ValueError("ARL readback checkout differs from its workflow/producer SHA")


def _remaining(deadline: float) -> None:
    if type(deadline) not in (int, float) or not math.isfinite(deadline) or time.monotonic() >= deadline:
        raise TimeoutError("ARL transport reader deadline exhausted")


def validate_run(run: dict[str, Any], request: ReadbackRequest) -> None:
    """Discriminate API metadata; retained dictionaries alone grant no origin."""
    repository, head = run.get("repository", {}), run.get("head_repository", {})
    if (
        type(run.get("id")) is not int
        or run["id"] != request.producer_run
        or type(run.get("run_attempt")) is not int
        or run["run_attempt"] != request.producer_attempt
        or run.get("head_sha") != request.source_sha
        or run.get("path") != WORKFLOW
        or run.get("event") != "workflow_dispatch"
        or run.get("status") != "completed"
        or run.get("conclusion") != "success"
        or not isinstance(repository, dict)
        or not isinstance(head, dict)
        or repository.get("full_name") != request.repository
        or head.get("full_name") != request.repository
        or type(repository.get("id")) is not int
        or repository["id"] <= 0
        or head.get("id") != repository["id"]
    ):
        raise ValueError("ARL original is not a completed successful same-repository/SHA/attempt dispatch")


def select_original(
    run: dict[str, Any], artifacts: list[dict[str, Any]], jobs: list[dict[str, Any]], request: ReadbackRequest
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Require the original producer, successful reader and exact immutable carrier."""
    from infrastructure.project.auxiliary_print_hosted import _utc
    from infrastructure.project.public_hosted_origin import MAX_ARCHIVE

    validate_run(run, request)
    selected = [row for row in artifacts if row.get("name") == request.artifact_name]
    producers = [row for row in jobs if row.get("name") == "ARL auxiliary diagnostic"]
    if len(selected) != 1 or len(producers) != 1:
        raise ValueError("ARL original artifact/producer is missing or repeated")
    artifact, job = selected[0], producers[0]
    origin = artifact.get("workflow_run", {})
    if (
        type(artifact.get("id")) is not int
        or artifact["id"] <= 0
        or artifact.get("expired") is not False
        or type(artifact.get("size_in_bytes")) is not int
        or not 0 < artifact["size_in_bytes"] <= MAX_ARCHIVE
        or not isinstance(artifact.get("digest"), str)
        or re.fullmatch(r"sha256:[0-9a-f]{64}", artifact["digest"]) is None
        or not isinstance(origin, dict)
        or origin.get("id") != request.producer_run
        or origin.get("head_sha") != request.source_sha
        or origin.get("repository_id") != run["repository"]["id"]
        or origin.get("head_repository_id") != run["repository"]["id"]
        or type(job.get("id")) is not int
        or job["id"] <= 0
        or job.get("run_id") != request.producer_run
        or job.get("head_sha") != request.source_sha
        or type(job.get("run_attempt")) is not int
        or job["run_attempt"] != request.producer_attempt
        or job.get("status") != "completed"
        or job.get("conclusion") != "success"
    ):
        raise ValueError("ARL original lacks successful same-attempt artifact/job custody")
    steps = job.get("steps")
    if not isinstance(steps, list) or any(not isinstance(step, dict) for step in steps):
        raise ValueError("ARL original producer omitted its step census")
    positions = []
    for name in _REQUIRED_STEPS:
        matches = [(index, step) for index, step in enumerate(steps) if step.get("name") == name]
        if len(matches) != 1 or matches[0][1].get("conclusion") != "success":
            raise ValueError("ARL original omitted a successful required producer/reader/export step")
        positions.append(matches[0][0])
    if positions != sorted(positions):
        raise ValueError("ARL original producer/reader/export order changed")
    if not (
        _utc(job.get("started_at")) <= _utc(artifact.get("created_at")) <= _utc(job.get("completed_at"))
        and _utc(artifact.get("expires_at")) > datetime.now(timezone.utc)
    ):
        raise ValueError("ARL original artifact is expired or outside its producer's lifetime")
    return artifact, job


def validate_workflow(root: Path, payload: dict[str, Any]) -> None:
    """Compare authenticated workflow bytes with this same immutable Source."""
    from infrastructure.core.files.secure_write import read_bytes_confined

    if (
        payload.get("path") != WORKFLOW
        or payload.get("encoding") != "base64"
        or not isinstance(payload.get("content"), str)
    ):
        raise ValueError("ARL original workflow content is unavailable")
    body = base64.b64decode("".join(payload["content"].splitlines()), validate=True)
    expected = read_bytes_confined(root, root / WORKFLOW, max_bytes=2 * 1024 * 1024)
    blob = hashlib.sha1(b"blob " + str(len(body)).encode() + b"\0" + body, usedforsecurity=False).hexdigest()
    if payload.get("sha") != blob or body != expected:
        raise ValueError("ARL original workflow differs from the same-SHA reader Source")


def collect_carrier(
    root: Path, directory: Path, request: ReadbackRequest, deadline: float
) -> tuple[bytes, dict[str, Any]]:
    """Use only the existing fixed live GitHub executor, never retained API input."""
    from infrastructure.project._hosted_api import fixed_hosted_api
    from infrastructure.project.auxiliary_matrix_hosted import _jobs
    from infrastructure.project.public_acceptance_evidence import write_json
    from infrastructure.project._hosted_protocol import MAX_LISTING_PAGES, collect_artifact_pages

    api = fixed_hosted_api(
        root,
        directory,
        repository=request.repository,
        run_id=request.producer_run,
        head_sha=request.source_sha,
        deadline=deadline,
        environment=dict(os.environ),
    )
    run, observed = api.run_metadata()
    observations = [observed]
    validate_run(run, request)
    workflow, observed = api.arl_workflow_metadata()
    observations.append(observed)
    validate_workflow(root, workflow)
    job_pages = []

    def read_listing_page(page: int) -> dict[str, Any]:
        value, observed = api.artifact_page(page)
        observations.append(observed)
        return value

    listing, _ = collect_artifact_pages(read_listing_page)
    artifacts = listing["artifacts"]
    for page in range(1, MAX_LISTING_PAGES + 1):
        value, observed = api.job_page(page)
        job_pages.append(value)
        observations.append(observed)
        if sum(len(row.get("jobs", [])) for row in job_pages) == value.get("total_count"):
            break
    artifact, job = select_original(run, artifacts, _jobs(job_pages), request)
    metadata, observed = api.artifact_metadata(artifact["id"])
    observations.append(observed)
    keys = ("id", "name", "digest", "size_in_bytes", "expired", "workflow_run", "created_at", "expires_at")
    if any(metadata.get(key) != artifact.get(key) for key in keys):
        raise ValueError("ARL original artifact metadata changed during collection")
    archive, observed = api.download_artifact(artifact["id"], directory / "original.zip")
    observations.append(observed)
    if (
        len(archive) != artifact["size_in_bytes"]
        or "sha256:" + hashlib.sha256(archive).hexdigest() != artifact["digest"]
    ):
        raise ValueError("ARL downloaded carrier differs from the live API digest/size")
    binding = write_json(
        root,
        directory / "authenticated-origin.json",
        {
            "request": asdict(request),
            "run": run,
            "producer_job": job,
            "artifact": artifact,
            "observations": observations,
        },
    )
    _remaining(deadline)
    return archive, {"artifact": artifact, "origin": binding}


def import_originals(root: Path, archive: bytes, deadline: float) -> dict[str, Any]:
    """Import only a new immutable DATA tree using the existing archive/closure guards."""
    from infrastructure.core.pipeline.fingerprint_files import anchored_parent, verify_directory
    from infrastructure.core.testing._ci_execution_files import _entries
    from infrastructure.project.public_acceptance_evidence import evidence_directory
    from infrastructure.reporting.native_hosted_transport_archive import import_auxiliary_archive
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
    from infrastructure.reporting.required_acceptance_aggregate import _evidence_closure

    _remaining(deadline)
    destination = evidence_directory(root, root / ORIGINAL_DIRECTORY, fresh=True)
    members, _ = import_auxiliary_archive(root, destination, archive, deadline=deadline, mode=0o400, fresh=True)
    directories = {destination}
    for label in members:
        target = root / label
        directories.update(parent for parent in target.parents if parent.is_relative_to(destination))
    entries = _entries(destination, deadline)
    if set(entries) != directories | {root / label for label in members}:
        raise ValueError("ARL imported original file/directory census changed")
    for path in sorted(directories, key=lambda item: len(item.parts), reverse=True):
        _remaining(deadline)
        with anchored_parent(path) as parent:
            if parent is None:
                raise ValueError("ARL original directory disappeared")
            descriptor = os.open(path.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            try:
                os.fchmod(descriptor, 0o500)
                verify_directory(parent, path.name, descriptor)
            finally:
                os.close(descriptor)
    reader = SnapshotReader(root, operation_deadline=deadline)
    for label, digest in members.items():
        _remaining(deadline)
        held = reader.read(label)
        if held.sha256 != digest or stat.S_IMODE(held.path.stat(follow_symlinks=False).st_mode) != 0o400:
            raise ValueError("ARL imported original bytes/read-only role changed")
    closure = _evidence_closure(reader, ORIGINAL_DIRECTORY + "/receipt.json")
    _remaining(deadline)
    if not reader.unchanged():
        raise ValueError("ARL imported originals changed before the fresh consumer")
    return {"members": len(members), "closure_files": len(closure), "closure_bytes": sum(map(len, closure.values()))}


def run_consumer(root: Path, directory: Path) -> dict[str, Any]:
    """Run the actual full same-Source CLI with its own fresh 300-second clock."""
    from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess
    from infrastructure.core.files.secure_write import read_bytes_confined
    from infrastructure.core.secrets import is_secret_env_name
    from infrastructure.project.installed_acceptance_artifacts import write_binary
    from infrastructure.project.public_acceptance_evidence import write_json
    from infrastructure.reporting.release_readiness_snapshot import json_object_from_bytes

    output = directory / "reader.json"
    if os.path.lexists(output):
        raise ValueError("ARL fresh consumer output is occupied")
    command = [
        str(root / ".venv/bin/python"),
        "-I",
        "-B",
        "-m",
        "infrastructure.project.public_acceptance_literature_group_cli",
        "--repo-root",
        str(root),
        "--receipt",
        str(root / ORIGINAL_DIRECTORY / "receipt.json"),
        "--output",
        str(output),
        "--timeout-seconds",
        "300",
    ]
    environment = {
        key: value
        for key, value in build_bounded_env(dict(os.environ)).items()
        if not is_secret_env_name(key) and key not in {"GH_TOKEN", "GITHUB_TOKEN", "SSH_AUTH_SOCK", "GPG_AGENT_INFO"}
    }
    result = run_bounded_subprocess(
        command,
        cwd=root,
        env=environment,
        guardian_env=environment,
        timeout=330,
        capture_output=True,
    )
    streams = {
        "stdout": write_binary(root, directory / "reader.stdout", result.stdout.encode()),
        "stderr": write_binary(root, directory / "reader.stderr", result.stderr.encode()),
    }
    observation = write_json(
        root,
        directory / "reader-process.json",
        {
            "command": command,
            "exit_code": result.returncode,
            "original_exit_code": result.original_returncode,
            "timed_out": result.timed_out,
            "custody_refused": result.custody_refused,
            "diagnostic": result.command_error,
            "streams": streams,
        },
    )
    if (
        result.returncode != 0
        or result.original_returncode != 0
        or result.timed_out
        or result.custody_refused
        or result.command_error
    ):
        raise ValueError("actual downloaded-original ARL consumer failed; original process/streams retained")
    body = read_bytes_confined(root, output, max_bytes=16 * 1024 * 1024)
    reader = json_object_from_bytes(body)
    if (
        reader.get("schema_version") != "template-arl-capability-diagnostic-v1"
        or reader.get("status") != "passed"
        or reader.get("aggregate_acceptance_granted") is not False
        or reader.get("release_authorized") is not False
    ):
        raise ValueError("actual ARL consumer did not retain its complete diagnostic-only result")
    return {
        "process": observation,
        "reader": {"path": output.relative_to(root).as_posix(), "sha256": hashlib.sha256(body).hexdigest()},
    }


def closing_origin(root: Path, directory: Path, request: ReadbackRequest, artifact: dict[str, Any]) -> None:
    """Refuse a changed attempt or artifact using a distinct bounded closing API read."""
    from infrastructure.project._hosted_api import fixed_hosted_api
    from infrastructure.project.auxiliary_print_hosted import _utc
    from infrastructure.project.public_acceptance_evidence import write_json

    closing = directory / "closing"
    closing.mkdir(mode=0o700)
    api = fixed_hosted_api(
        root,
        closing,
        repository=request.repository,
        run_id=request.producer_run,
        head_sha=request.source_sha,
        deadline=time.monotonic() + 60,
        environment=dict(os.environ),
    )
    run, run_binding = api.run_metadata()
    validate_run(run, request)
    metadata, artifact_binding = api.artifact_metadata(artifact["id"])
    for key in ("id", "name", "digest", "size_in_bytes", "expired", "workflow_run", "created_at", "expires_at"):
        if metadata.get(key) != artifact.get(key):
            raise ValueError("ARL original attempt/artifact changed before closing readback")
    if metadata.get("expired") is not False or _utc(metadata.get("expires_at")) <= datetime.now(timezone.utc):
        raise ValueError("ARL original artifact expired before closing readback")
    write_json(root, closing / "verified.json", {"run": run_binding, "artifact": artifact_binding})


def main() -> int:
    """Keep admission, live collection and complete consumer failure explicit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("admit", "read"))
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.repo_root.absolute()
    try:
        request = request_from_environment(os.environ)
        admit_checkout(root, request)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.error(str(error))
    if args.mode == "admit":
        sys.stdout.write(json.dumps(asdict(request), sort_keys=True) + "\n")
        return 0
    from infrastructure.project.public_acceptance_evidence import evidence_directory, write_json

    directory = evidence_directory(root, root / request.evidence_path, fresh=True)
    directory.mkdir(parents=True, mode=0o700)
    result: dict[str, Any] = {
        "schema_version": SCHEMA,
        "request": asdict(request),
        "phase": "collect",
        "aggregate_acceptance_granted": False,
        "release_authorized": False,
    }
    try:
        deadline = time.monotonic() + 300
        archive, origin = collect_carrier(root, directory, request, deadline)
        result.update(origin=origin, phase="import")
        imported = import_originals(root, archive, deadline)
        result.update(imported=imported, phase="consumer")
        consumer = run_consumer(root, directory)
        result.update(consumer=consumer, phase="closing")
        closing_origin(root, directory, request, origin["artifact"])
        admit_checkout(root, request)
        result.update(status="passed", phase="complete")
    except (OSError, ValueError, TypeError, KeyError, TimeoutError, UnicodeError, zipfile.BadZipFile) as error:
        result.update(status="failed", diagnostic=re.sub(r"https?://\S+", "<URL>", str(error))[:1200])
    binding = write_json(root, directory / "readback.json", result)
    sys.stdout.write(json.dumps({**result, "receipt": binding}, sort_keys=True) + "\n")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
