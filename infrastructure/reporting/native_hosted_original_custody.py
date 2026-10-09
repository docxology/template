"""Live exact-run authenticated collection of Source-owned native artifact bytes.

Only the real authenticated collector can mint this capability. Retained API
JSON and producer indexes remain DATA and cannot reopen this custody boundary.
Native/Code/provider predicates independently admit their actual observations.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import sys
import types
from pathlib import Path
from typing import Any

from infrastructure.core.execution_boundary import run_bounded_subprocess
from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.project.public_acceptance_evidence import evidence_directory, write_json
from infrastructure.project.public_hosted_origin import (
    DOWNLOAD_SCRIPT,
    MAX_ARCHIVE,
    WORKFLOW,
    _api_command,
    _context,
    _process,
)
from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader, json_object_from_bytes

from infrastructure.reporting.native_hosted_transport_archive import (
    SCHEMA,
    INDEX_ARTIFACT,
    SHARD_PREFIX,
    MAX_SHARDS,
    MAX_MEMBERS,
    MAX_TOTAL,
    MAX_CHUNK,
    MAX_SHARD,
    _path,
    _hash,
    _archive,
    _file_identity,
)

_COLLECTOR_KEY = object()


class NativeHostedArtifactCustodian:
    """Genuinely collected original bytes under externally nominated Source/run.

    File membership comes from actual API-digest-authenticated archive bytes.
    This capability persists only in the real collector process and its same
    reader operation deadline. Exporting its DATA never exports the capability.
    """

    def __init__(
        self,
        source: NativeSourceContext,
        index: dict[str, Any],
        members: dict[str, dict[str, Any]],
        observations: tuple[dict[str, str], ...],
        *,
        deadline: float,
        key: object,
    ) -> None:
        if key is not _COLLECTOR_KEY or not isinstance(source, NativeSourceContext):
            raise ValueError("native hosted custody requires its actual authenticated collector")
        self._source = source
        self._index = index
        self._members = types.MappingProxyType(
            {name: types.MappingProxyType(dict(row)) for name, row in members.items()}
        )
        self._observations = tuple(dict(row) for row in observations)
        self._owner_pid = os.getpid()
        self._deadline = deadline
        self._root = source.bindings.current_root
        self._observation_identities: dict[str, tuple[int, ...]] = {}
        for binding in self._observations:
            reader = SnapshotReader(self._root)
            snapshot = reader.read(binding["path"])
            if snapshot.sha256 != binding["sha256"] or not reader.unchanged():
                raise ValueError("native hosted authenticated collection observation changed")
            self._observation_identities[binding["path"]] = _file_identity(snapshot.path)
        self.repository = index["repository"]
        self.run_id = index["hosted_run_id"]
        self.head_sha = index["source_commit"]
        self.verify_source(source, scope=index["scopes"][0])

    @property
    def deadline(self) -> float:
        remaining(self._deadline)
        if os.getpid() != self._owner_pid:
            raise ValueError("native hosted custody belongs to its actual collector process")
        return self._deadline

    def verify_source(self, source: NativeSourceContext, *, scope: str) -> None:
        remaining(self._deadline)
        if os.getpid() != self._owner_pid or source is not self._source or scope not in self._index["scopes"]:
            raise ValueError("native hosted bytes lost their actual collector/current Source owner")
        source.verify_correspondence(
            source.reference, source.bindings.current_root, source.current_source_reader, self._deadline
        )
        if (
            source.reference.commit != self.head_sha
            or source.reference.source_identity != self._index["source_identity"]
        ):
            raise ValueError("native hosted original differs from independently admitted current Source")
        for binding in self._observations:
            path = SnapshotReader(self._root).public_path(binding["path"])
            if _file_identity(path) != self._observation_identities[binding["path"]]:
                raise ValueError("native hosted retained genuine API/process observation changed")
        remaining(self._deadline)

    def read_original_file(self, scope: str, binding: object) -> bytes:
        self.verify_source(self._source, scope=scope)
        if not isinstance(binding, dict) or set(binding) not in ({"path", "sha256"}, {"path", "sha256", "bytes"}):
            raise ValueError("native hosted original requires an exact retained artifact binding")
        label, digest = _path(binding["path"]), _hash(binding["sha256"])
        member = self._members.get(label)
        if member is None or member["sha256"] != digest or ("bytes" in binding and binding["bytes"] != member["bytes"]):
            raise ValueError("native hosted original file is absent from authenticated archive membership")
        reader = SnapshotReader(self._root)
        observed = reader.read(label)
        if observed.sha256 != digest or len(observed.content) != member["bytes"]:
            raise ValueError("native hosted retrieved original file changed")
        if _file_identity(observed.path) != member["identity"] or not reader.unchanged():
            raise ValueError("native hosted retrieved original file lost its collected physical identity")
        self.verify_source(self._source, scope=scope)
        return observed.content

    def original_source_binding(self, scope: str) -> tuple[str, str, str]:
        self.verify_source(self._source, scope=scope)
        value = self._index["originals"][scope]["source_binding"]
        if (
            not isinstance(value, list)
            or len(value) != 3
            or value[1:] != [self.head_sha, self._index["source_identity"]]
        ):
            raise ValueError("native hosted scope Source binding differs from authenticated exact Source")
        return value[0], value[1], value[2]

    def original_pdfium_inputs(self, scope: str) -> dict[str, Any]:
        original = self._index["originals"][scope]
        raw = self.read_original_file(
            scope, {"path": original["specification_relative"], "sha256": original["specification_sha256"]}
        )
        specification = json_object_from_bytes(raw)
        if specification["scope"] != scope or specification["run_id"] != original["run_id"]:
            raise ValueError("native hosted exact spec scope/run differs")
        return dict(specification["source_inputs"]["pdfium"])

    def read_original_pdfium_wheel(self, scope: str) -> tuple[str, bytes]:
        row = self._index["pdfium_wheels"][scope]
        name = row["filename"]
        if not isinstance(name, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.+-]*\.whl", name) is None:
            raise ValueError("native hosted original PDFium wheel filename differs")
        content = self.read_original_file(scope, row["artifact"])
        inputs = self.original_pdfium_inputs(scope)
        if inputs["wheel"]["sha256"] != hashlib.sha256(content).hexdigest() or inputs["wheel"]["bytes"] != len(content):
            raise ValueError("native hosted original PDFium wheel differs from actual Source-owned inputs")
        return name, content

    def original_launch_data(self, scope: str) -> dict[str, Any]:
        """Authenticated Source producer DATA; genuine launcher factory owns admission."""
        self.verify_source(self._source, scope=scope)
        return json_object_from_bytes(json.dumps(self._index["originals"][scope], allow_nan=False).encode())


def collect_native_hosted_originals(
    source: NativeSourceContext,
    directory: Path,
    *,
    repository: str,
    run_id: int,
    head_sha: str,
    deadline: float,
) -> NativeHostedArtifactCustodian:
    """Actually authenticate exact Source/job/API digests and retrieve all shards.

    The caller supplies the already-live reader Source and clock. Collection
    never accepts retained API JSON as authentication and never changes auth.
    Native semantics are still independently checked by the original/readback
    validators; this factory authenticates the exact producer's byte custody.
    """
    remaining(deadline)
    _context(repository, run_id, head_sha)
    if not isinstance(source, NativeSourceContext) or source.reference.commit != head_sha:
        raise ValueError("native hosted collector requires independently admitted exact-commit Source")
    root = source.bindings.current_root
    source.verify_correspondence(source.reference, root, source.current_source_reader, deadline)
    directory = evidence_directory(root, directory, fresh=True)
    directory.mkdir(parents=True, mode=0o700)
    observations: list[dict[str, str]] = []

    def execute(command: list[str], label: str) -> dict[str, Any]:
        result = run_bounded_subprocess(
            command, cwd=root, env=os.environ.copy(), timeout=remaining(deadline), capture_output=True
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
        observations.append(write_json(root, directory / (label + "-process.json"), record))
        _process(record, command)
        remaining(deadline)
        return record

    def api(endpoint: str, label: str) -> dict[str, Any]:
        raw = execute(_api_command(endpoint), label)
        response = json_object_from_bytes(raw["stdout"].encode())
        observations.append(write_json(root, directory / (label + "-response.json"), response))
        return response

    base = f"repos/{repository}"
    run = api(f"{base}/actions/runs/{run_id}", "run")
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
        raise ValueError("native hosted producer is foreign or not the exact Source workflow")
    workflow = api(f"{base}/contents/{WORKFLOW}?ref={head_sha}", "workflow")
    if (
        workflow.get("path") != WORKFLOW
        or base64.b64decode(workflow["content"]) != source.current_source_reader.read(WORKFLOW).content
    ):
        raise ValueError("native hosted Source workflow bytes differ")
    jobs: list[dict[str, Any]] = []
    job_count: int | None = None
    for page in range(1, 6):
        response = api(f"{base}/actions/runs/{run_id}/jobs?per_page=100&page={page}", f"jobs-{page}")
        count, rows = response.get("total_count"), response.get("jobs")
        if (
            type(count) is not int
            or not 0 < count <= 500
            or not isinstance(rows, list)
            or (job_count is not None and count != job_count)
        ):
            raise ValueError("native hosted producer job census is invalid or exceeds its Source bound")
        job_count = count
        jobs.extend(rows)
        if len(jobs) == count:
            break
        if len(rows) != 100 or len(jobs) > count:
            raise ValueError("native hosted producer job pagination is incomplete")
    if len(jobs) != job_count:
        raise ValueError("native hosted producer job listing is incomplete")
    selected_jobs = [job for job in jobs if job.get("name") == "native-original"]
    if (
        len(selected_jobs) != 1
        or selected_jobs[0].get("status") != "completed"
        or selected_jobs[0].get("conclusion") != "success"
        or selected_jobs[0].get("head_sha") != head_sha
    ):
        raise ValueError("native hosted exact original producer did not genuinely complete successfully")
    steps = [
        step
        for step in selected_jobs[0].get("steps", [])
        if step.get("name") == "Original authenticated installed native format inventory"
    ]
    if len(steps) != 1 or steps[0].get("status") != "completed" or steps[0].get("conclusion") != "success":
        raise ValueError("native hosted source-declared installed producer step did not pass")
    artifacts: list[dict[str, Any]] = []
    expected_count: int | None = None
    for page in range(1, 6):
        response = api(f"{base}/actions/runs/{run_id}/artifacts?per_page=100&page={page}", f"listing-{page}")
        count = response.get("total_count")
        rows = response.get("artifacts")
        if (
            type(count) is not int
            or count > 500
            or not isinstance(rows, list)
            or (expected_count is not None and count != expected_count)
        ):
            raise ValueError("native hosted artifact listing exceeds its bounded exact census")
        expected_count = count
        artifacts.extend(rows)
        if len(artifacts) == count:
            break
        if len(rows) != 100 or len(artifacts) > count:
            raise ValueError("native hosted artifact pagination is incomplete")
    if len(artifacts) != expected_count:
        raise ValueError("native hosted complete artifact census is missing")
    selected = {
        row["name"]: row
        for row in artifacts
        if row.get("name") == INDEX_ARTIFACT or str(row.get("name", "")).startswith(SHARD_PREFIX)
    }
    if (
        len(selected)
        != sum(
            row.get("name") == INDEX_ARTIFACT or str(row.get("name", "")).startswith(SHARD_PREFIX) for row in artifacts
        )
        or INDEX_ARTIFACT not in selected
        or len(selected) > MAX_SHARDS + 1
    ):
        raise ValueError("native hosted artifact owner roster is duplicated or missing")

    def download(name: str) -> dict[str, bytes]:
        row = selected[name]
        origin = row.get("workflow_run", {})
        if (
            row.get("expired") is not False
            or type(row.get("id")) is not int
            or row["id"] <= 0
            or origin.get("id") != run_id
            or origin.get("head_sha") != head_sha
            or origin.get("repository_id") != repo["id"]
            or origin.get("head_repository_id") != repo["id"]
        ):
            raise ValueError("native hosted artifact is foreign, expired or unbound")
        target = directory / (name + ".zip")
        raw = execute(
            [
                sys.executable,
                "-I",
                "-c",
                DOWNLOAD_SCRIPT,
                str(target),
                *_api_command(f"{base}/actions/artifacts/{row['id']}/zip"),
            ],
            name,
        )
        content = read_bytes_confined(root, target, max_bytes=MAX_ARCHIVE)
        digest = hashlib.sha256(content).hexdigest()
        if row.get("digest") != "sha256:" + digest or json_object_from_bytes(raw["stdout"].encode()) != {
            "original_exit_code": 0,
            "archive_sha256": digest,
        }:
            raise ValueError("native hosted actual retrieved bytes differ from authenticated API digest")
        observations.append({"path": target.relative_to(root).as_posix(), "sha256": digest})
        return _archive(content, maximum=MAX_ARCHIVE, count=1)

    original_index = download(INDEX_ARTIFACT)
    if set(original_index) != {"native-index.json"}:
        raise ValueError("native hosted index archive membership differs")
    index = json_object_from_bytes(original_index["native-index.json"])
    if (
        set(index)
        != {
            "schema_version",
            "repository",
            "hosted_run_id",
            "source_commit",
            "source_identity",
            "scopes",
            "originals",
            "pdfium_wheels",
            "shards",
            "files",
        }
        or index.get("schema_version") != SCHEMA
        or index.get("repository") != repository
        or index.get("hosted_run_id") != run_id
        or index.get("source_commit") != head_sha
        or index.get("source_identity") != source.reference.source_identity
        or index.get("scopes") != list(PUBLIC_PROJECT_NAMES)
        or set(index.get("originals", {})) != set(PUBLIC_PROJECT_NAMES)
        or set(index.get("pdfium_wheels", {})) != set(PUBLIC_PROJECT_NAMES)
    ):
        raise ValueError("native hosted index differs from complete externally admitted Source/public roster")
    shards = index.get("shards")
    files = index.get("files")
    if (
        not isinstance(shards, list)
        or not 0 < len(shards) <= MAX_SHARDS
        or not isinstance(files, list)
        or len(files) > MAX_MEMBERS
        or set(selected) != {INDEX_ARTIFACT, *(SHARD_PREFIX + f"{i:04d}" for i in range(len(shards)))}
    ):
        raise ValueError("native hosted bounded shard/file census differs")
    chunk_paths: dict[str, Path] = {}
    total_chunks = 0
    for ordinal, shard in enumerate(shards):
        remaining(deadline)
        archive_members = download(SHARD_PREFIX + f"{ordinal:04d}")
        filename = f"native-shard-{ordinal:04d}.zip"
        if (
            set(archive_members) != {filename}
            or shard.get("filename") != filename
            or hashlib.sha256(archive_members[filename]).hexdigest() != shard.get("sha256")
        ):
            raise ValueError("native hosted retrieved shard differs from exact producer bytes")
        chunks = _archive(archive_members[filename], maximum=MAX_SHARD, count=MAX_MEMBERS)
        declared = shard.get("members")
        actual = [
            {"path": name, "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}
            for name, body in sorted(chunks.items())
        ]
        if declared != actual:
            raise ValueError("native hosted shard chunk census differs")
        for label, body in chunks.items():
            digest = _hash(label.removeprefix("chunks/"))
            if (
                label != "chunks/" + digest
                or digest in chunk_paths
                or len(body) > MAX_CHUNK
                or hashlib.sha256(body).hexdigest() != digest
            ):
                raise ValueError("native hosted chunk hash/type/count differs")
            total_chunks += len(body)
            if total_chunks > MAX_TOTAL:
                raise ValueError("native hosted whole target exceeds its separately declared8GiB census")
            path = directory / label
            atomic_write_bytes_confined(root, path, body, mode=0o600)
            chunk_paths[digest] = path
    members: dict[str, dict[str, Any]] = {}
    total = 0
    used_chunks: set[str] = set()
    for row in files:
        remaining(deadline)
        if not isinstance(row, dict) or set(row) != {"path", "sha256", "bytes", "chunks"}:
            raise ValueError("native hosted logical file fields differ")
        label, digest = _path(row["path"]), _hash(row["sha256"])
        source.current_source_reader.public_path(label)
        if (
            label in members
            or type(row["bytes"]) is not int
            or not 0 <= row["bytes"] <= MAX_ARCHIVE
            or not isinstance(row["chunks"], list)
            or len(row["chunks"]) > 8
        ):
            raise ValueError("native hosted logical file census/type/bytes differs")
        blocks = []
        for chunk in row["chunks"]:
            selected_digest = _hash(chunk)
            if selected_digest not in chunk_paths:
                raise ValueError("native hosted logical file references an unauthenticated chunk")
            used_chunks.add(selected_digest)
            blocks.append(read_bytes_confined(root, chunk_paths[selected_digest], max_bytes=MAX_CHUNK))
        body = b"".join(blocks)
        total += len(body)
        if len(body) != row["bytes"] or hashlib.sha256(body).hexdigest() != digest or total > MAX_TOTAL:
            raise ValueError("native hosted original whole-file hash/length/census differs")
        target = root / label
        if target.exists() or target.is_symlink():
            raise ValueError("native hosted extraction refuses overwriting current Source/evidence")
        atomic_write_bytes_confined(root, target, body, mode=0o600)
        members[label] = {"sha256": digest, "bytes": len(body), "identity": _file_identity(target)}
    if used_chunks != set(chunk_paths):
        raise ValueError("native hosted shard census contains unowned unused chunk bytes")
    observations.append(write_json(root, directory / "native-index.json", index))
    source.verify_correspondence(source.reference, root, source.current_source_reader, deadline)
    return NativeHostedArtifactCustodian(
        source, index, members, tuple(observations), deadline=deadline, key=_COLLECTOR_KEY
    )
