"""Exact-run GitHub artifact custody; hosted handoff must authenticate its binding.

Retained API responses are integrity evidence, not an offline authentication oracle.
The caller supplies repository/run/commit from its admitted hosted context and must
bind the returned manifest in the outer hosted handoff. No receipt semantics are
inferred here. Collection uses only existing gh authentication and read APIs.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import re
import stat
import sys
import time
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any
from weakref import ref

from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess
from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.project._hosted_protocol import (
    DOWNLOAD_SCRIPT as DOWNLOAD_SCRIPT,
    MAX_ARCHIVE as MAX_ARCHIVE,
    MAX_LISTING_PAGES as MAX_LISTING_PAGES,
    MAX_RUN_ARTIFACTS as MAX_RUN_ARTIFACTS,
    WORKFLOW as WORKFLOW,
    _api_command as _api_command,
    _context as _context,
    _merge_listing_pages as _merge_listing_pages,
    _process as _process,
    collect_artifact_pages,
)
from infrastructure.project.public_acceptance_evidence import evidence_directory, write_json
from infrastructure.project.public_root_case_contract import _artifact
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader, json_object_from_bytes

SCHEMA = "template-public-hosted-origin-v2"
ARTIFACTS = {
    f"required-source-root-{host}-{minor}": (platform, minor)
    for host, platform in (("Linux", "linux"), ("macOS", "darwin"))
    for minor in ("3.14", "3.15")
}


@dataclass(frozen=True)
class HostedReadbackContext:
    """Expected context admitted by the external exact-commit hosted handoff."""

    manifest_binding: dict[str, str]
    repository: str
    run_id: int
    head_sha: str


@dataclass(frozen=True)
class HostedOriginIdentity:
    """Admitted original source identity for one complete artifact closure."""

    platform: str
    python_version: str
    source_commit: str
    repository: str
    run_id: int
    artifact_id: int


class HostedRootAuthorization:
    """Authorize portable Root closures within one physical snapshot's lifetime."""

    def __init__(self, reader: SnapshotReader) -> None:
        self._reader = ref(reader)
        self._origins: dict[str, HostedOriginIdentity] = {}
        self.observed: Mapping[str, HostedOriginIdentity] = MappingProxyType(self._origins)

    def authorize(self, reader: SnapshotReader, bindings: list[dict[str, str]]) -> HostedOriginIdentity:
        """Recheck held bytes on a hit and verify the complete original closure on a miss."""
        if self._reader() is not reader:
            raise ValueError("hosted authorization requires its original snapshot reader")
        context = reader.hosted_origin
        if not isinstance(context, HostedReadbackContext):
            raise ValueError("portable Root needs authenticated external hosted handoff context")
        _artifact(reader, context.manifest_binding)
        if not reader.unchanged():
            raise ValueError("portable original closure changed before hosted authentication")
        key = hashlib.sha256(
            json.dumps(
                {
                    "bindings": bindings,
                    "manifest": context.manifest_binding,
                    "repository": context.repository,
                    "run_id": context.run_id,
                    "head_sha": context.head_sha,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        origin = self._origins.get(key)
        if origin is None:
            origin = authorize_root_evidence(
                reader,
                bindings,
                manifest_binding=context.manifest_binding,
                repository=context.repository,
                run_id=context.run_id,
                head_sha=context.head_sha,
            )
            if not reader.unchanged():
                raise ValueError("portable hosted origin changed during original archive authentication")
            self._origins[key] = origin
        return origin


def _metadata(
    run: dict[str, Any], listing: dict[str, Any], repository: str, run_id: int, head_sha: str
) -> list[dict[str, Any]]:
    _context(repository, run_id, head_sha)
    repo = run.get("repository", {})
    head = run.get("head_repository", {})
    if (
        run.get("id") != run_id
        or run.get("head_sha") != head_sha
        or run.get("path") != WORKFLOW
        or repo.get("full_name") != repository
        or head.get("full_name") != repository
        or repo.get("id") != head.get("id")
        or type(repo.get("id")) is not int
    ):
        raise ValueError("foreign, stale or wrong-workflow source run")
    rows = listing.get("artifacts")
    if (
        not isinstance(rows, list)
        or listing.get("total_count") != len(rows)
        or len(rows) > MAX_RUN_ARTIFACTS
        or len({row.get("id") for row in rows}) != len(rows)
    ):
        raise ValueError("incomplete bounded artifact listing")
    selected = [row for row in rows if row.get("name") in ARTIFACTS]
    if len(selected) != len(ARTIFACTS) or {row.get("name") for row in selected} != set(ARTIFACTS):
        raise ValueError("missing or duplicate fixed source artifacts")
    ids: set[int] = set()
    for row in selected:
        artifact_id = row.get("id")
        origin = row.get("workflow_run", {})
        digest = row.get("digest")
        if (
            type(artifact_id) is not int
            or artifact_id <= 0
            or artifact_id in ids
            or row.get("expired") is not False
            or not isinstance(digest, str)
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest)
            or origin.get("id") != run_id
            or origin.get("head_sha") != head_sha
            or origin.get("repository_id") != repo["id"]
            or origin.get("head_repository_id") != repo["id"]
        ):
            raise ValueError("artifact has foreign, expired or incomplete custody")
        ids.add(artifact_id)
    return sorted(selected, key=lambda row: row["name"])


def _zip_members(content: bytes, name: str) -> dict[str, bytes]:
    if len(content) > MAX_ARCHIVE or name not in ARTIFACTS:
        raise ValueError("unbounded or unknown source archive")
    platform, minor = ARTIFACTS[name]
    prefix = f"root-{platform}-{minor}"
    members: dict[str, bytes] = {}
    seen: set[str] = set()
    total = 0
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        if len(archive.infolist()) > 10000:
            raise ValueError("too many archive members")
        for info in archive.infolist():
            path = PurePosixPath(info.filename)
            mode = info.external_attr >> 16
            if (
                str(path) != info.filename.rstrip("/")
                or not info.filename
                or "\\" in info.filename
                or "\0" in info.filename
                or path.is_absolute()
                or ".." in path.parts
                or not path.parts
                or path.parts[0] != prefix
                or str(path) in seen
                or info.flag_bits & 1
                or stat.S_ISLNK(mode)
                or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)
            ):
                raise ValueError("archive contains ambiguous or unsafe member")
            seen.add(str(path))
            if info.is_dir():
                continue
            total += info.file_size
            if total > MAX_ARCHIVE or info.file_size > MAX_ARCHIVE:
                raise ValueError("unbounded extracted source archive")
            members[f"output/readiness/{path}"] = archive.read(info)
    if f"output/readiness/{prefix}/receipt.json" not in members:
        raise ValueError("source archive lacks literal receipt")
    return members


def collect_hosted_origin(
    root: Path,
    directory: Path,
    *,
    repository: str,
    run_id: int,
    head_sha: str,
    timeout: float = 180,
    operation_deadline: float | None = None,
) -> dict[str, str]:
    """Collect six original archives with a single finite deadline, without auth changes."""
    _context(repository, run_id, head_sha)
    directory = evidence_directory(root, directory, fresh=True)
    directory.mkdir(parents=True)
    if not 0 < timeout <= 600:
        raise ValueError("hosted collection requires a finite bounded deadline")
    started = time.monotonic()
    deadline = min(started + timeout, operation_deadline) if operation_deadline is not None else started + timeout
    if deadline <= started:
        raise ValueError("hosted collection cannot restart an exhausted outer operation clock")
    observations: dict[str, Any] = {}
    from infrastructure.project._hosted_api import fixed_hosted_api

    api = fixed_hosted_api(
        root,
        directory,
        repository=repository,
        run_id=run_id,
        head_sha=head_sha,
        deadline=deadline,
        environment=os.environ.copy(),
    )

    def execute(command: list[str], label: str) -> dict[str, Any]:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("hosted origin collection deadline exhausted")
        result = run_bounded_subprocess(
            command,
            cwd=root,
            env=build_bounded_env(),
            guardian_env=build_bounded_env(),
            timeout=remaining,
            capture_output=True,
        )
        record = {
            "command": command,
            "exit_code": result.returncode,
            "original_exit_code": result.original_returncode,
            "timed_out": result.timed_out,
            "custody_refused": result.custody_refused,
            "diagnostic": result.command_error,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        observations[label] = write_json(root, directory / f"{label}-process.json", record)
        _process(record, command)
        return record

    commit = execute(["git", "rev-parse", "HEAD"], "commit")
    if commit["stdout"].strip() != head_sha:
        raise ValueError("checkout is not the source run commit")
    responses: dict[str, Any] = {}
    for label, collect in (("run", api.run_metadata), ("workflow", api.workflow_metadata)):
        responses[label], observations[label] = collect()
        observations[label + "_response"] = write_json(root, directory / f"{label}-response.json", responses[label])

    def read_listing_page(page: int) -> dict[str, Any]:
        label = f"listing-{page}"
        response, observations[label] = api.artifact_page(page)
        observations[label + "_response"] = write_json(root, directory / f"{label}-response.json", response)
        return response

    responses["listing"], observations["listing_pages"] = collect_artifact_pages(read_listing_page)
    selected = _metadata(responses["run"], responses["listing"], repository, run_id, head_sha)
    workflow = base64.b64decode(responses["workflow"]["content"], validate=False)
    if responses["workflow"].get("path") != WORKFLOW or workflow != SnapshotReader(root).read(WORKFLOW).content:
        raise ValueError("source workflow bytes disagree with current candidate")
    artifacts = []
    for row in selected:
        archive_path = directory / f"{row['id']}.zip"
        content, process_binding = api.download_artifact(row["id"], archive_path)
        observations[f"artifact-{row['id']}"] = process_binding
        record = SnapshotReader(root).read(process_binding["path"]).json_object()
        digest = hashlib.sha256(content).hexdigest()
        child = json_object_from_bytes(record["stdout"].encode())
        if child != {"original_exit_code": 0, "archive_sha256": digest} or row["digest"] != f"sha256:{digest}":
            raise ValueError("original downloaded archive digest disagrees with API")
        members = _zip_members(content, row["name"])
        mapping = []
        for relative, payload in sorted(members.items()):
            target = root / relative
            if target.exists() or target.is_symlink():
                raise ValueError("source artifact extraction would overwrite existing evidence")
            atomic_write_bytes_confined(root, target, payload)
            mapping.append({"path": relative, "sha256": hashlib.sha256(payload).hexdigest()})
        artifacts.append(
            {
                "metadata": row,
                "archive": {"path": str(archive_path.relative_to(root)), "sha256": digest},
                "members": mapping,
            }
        )
    manifest = {
        "schema_version": SCHEMA,
        "repository": repository,
        "run_id": run_id,
        "head_sha": head_sha,
        "workflow_path": WORKFLOW,
        "observations": observations,
        "collector_interpreter": sys.executable,
        "collector_directory": str(directory),
        "artifacts": artifacts,
    }
    return write_json(root, directory / "origin.json", manifest)


def authorize_root_evidence(
    reader: SnapshotReader,
    bindings: list[dict[str, str]],
    *,
    manifest_binding: dict[str, str],
    repository: str,
    run_id: int,
    head_sha: str,
) -> HostedOriginIdentity:
    """Verify bound hosted observations and whole closure; never infer test success."""
    _context(repository, run_id, head_sha)

    def bound(binding: dict[str, str]) -> bytes:
        snapshot = reader.read(binding["path"])
        if snapshot.sha256 != binding["sha256"]:
            raise ValueError("hosted evidence bytes disagree with binding")
        return snapshot.content

    manifest = json_object_from_bytes(bound(manifest_binding))
    if any(
        manifest.get(key) != value
        for key, value in {
            "schema_version": SCHEMA,
            "repository": repository,
            "run_id": run_id,
            "head_sha": head_sha,
            "workflow_path": WORKFLOW,
        }.items()
    ):
        raise ValueError("hosted origin context mismatch")
    for original in (manifest["collector_interpreter"], manifest["collector_directory"]):
        path = Path(original)
        if not path.is_absolute() or ".." in path.parts or "\\" in original or "\0" in original:
            raise ValueError("invalid original collector path")
    obs = manifest["observations"]
    base = f"repos/{repository}"
    responses = {}
    for label, endpoint in {
        "run": f"{base}/actions/runs/{run_id}",
        "workflow": f"{base}/contents/{WORKFLOW}?ref={head_sha}",
    }.items():
        process = json_object_from_bytes(bound(obs[label]))
        _process(process, _api_command(endpoint))
        response = json_object_from_bytes(bound(obs[label + "_response"]))
        if json_object_from_bytes(process["stdout"].encode()) != response:
            raise ValueError("API response disagrees with original process output")
        responses[label] = response
    page_count = obs.get("listing_pages")
    if type(page_count) is not int or not 0 < page_count <= MAX_LISTING_PAGES:
        raise ValueError("hosted origin lacks its exact bounded original pagination")
    pages = []
    for page in range(1, page_count + 1):
        label = f"listing-{page}"
        process = json_object_from_bytes(bound(obs[label]))
        _process(process, _api_command(f"{base}/actions/runs/{run_id}/artifacts?per_page=100&page={page}"))
        response = json_object_from_bytes(bound(obs[label + "_response"]))
        if json_object_from_bytes(process["stdout"].encode()) != response:
            raise ValueError("hosted listing page differs from its genuine original API output")
        pages.append(response)
    responses["listing"] = _merge_listing_pages(pages, complete=True)
    commit = json_object_from_bytes(bound(obs["commit"]))
    _process(commit, ["git", "rev-parse", "HEAD"])
    if commit["stdout"].strip() != head_sha:
        raise ValueError("original checkout commit mismatch")
    workflow = responses["workflow"]
    if workflow.get("path") != WORKFLOW or base64.b64decode(workflow["content"]) != reader.read(WORKFLOW).content:
        raise ValueError("current workflow is not exact source workflow")
    selected = _metadata(responses["run"], responses["listing"], repository, run_id, head_sha)
    rows = manifest["artifacts"]
    if len(rows) != len(ARTIFACTS) or [row["metadata"] for row in rows] != selected:
        raise ValueError("manifest artifact roster disagrees with original API")
    owner = None
    if not bindings or len({item["path"] for item in bindings}) != len(bindings):
        raise ValueError("empty or duplicate Root evidence closure")
    requested = {item["path"]: item["sha256"] for item in bindings}
    for row in rows:
        metadata = row["metadata"]
        archive = bound(row["archive"])
        digest = hashlib.sha256(archive).hexdigest()
        if metadata["digest"] != f"sha256:{digest}":
            raise ValueError("source ZIP digest mismatch")
        process = json_object_from_bytes(bound(obs[f"artifact-{metadata['id']}"]))
        command = process["command"]
        expected = [
            manifest["collector_interpreter"],
            "-I",
            "-c",
            DOWNLOAD_SCRIPT,
            str(Path(manifest["collector_directory"]) / f"{metadata['id']}.zip"),
            *_api_command(f"{base}/actions/artifacts/{metadata['id']}/zip"),
        ]
        if command != expected:
            raise ValueError("original archive command changed")
        _process(process, command)
        if json_object_from_bytes(process["stdout"].encode()) != {"original_exit_code": 0, "archive_sha256": digest}:
            raise ValueError("original archive download failed")
        members = _zip_members(archive, metadata["name"])
        mapping = [{"path": path, "sha256": hashlib.sha256(data).hexdigest()} for path, data in sorted(members.items())]
        if row["members"] != mapping:
            raise ValueError("incomplete or changed extracted-byte mapping")
        for item in mapping:
            if bound(item) != members[item["path"]]:
                raise ValueError("extracted source bytes disagree with archive")
        by_path = {item["path"]: item["sha256"] for item in mapping}
        if all(by_path.get(path) == digest for path, digest in requested.items()):
            if owner is not None:
                raise ValueError("ambiguous source artifact owner")
            platform, minor = ARTIFACTS[metadata["name"]]
            owner = HostedOriginIdentity(platform, minor, head_sha, repository, run_id, metadata["id"])
    if owner is None or not reader.unchanged():
        raise ValueError("Root closure is foreign, mixed, changed or incomplete")
    return owner
