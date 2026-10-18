"""Actually authenticate the exact completed candidate and every bounded shard."""

from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path
from typing import Any

from infrastructure.project._hosted_api import fixed_hosted_api
from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.project.public_acceptance_evidence import evidence_directory, write_json
from infrastructure.project.public_hosted_origin import (
    MAX_ARCHIVE,
    MAX_LISTING_PAGES,
    WORKFLOW,
    _merge_listing_pages,
)
from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.publishing.release_acceptance import ARTIFACT_NAME, validate_hosted_handoff
from infrastructure.reporting.native_hosted_original_custody import NativeHostedArtifactCustodian
from infrastructure.reporting.native_hosted_transport_archive import (
    MAX_CHUNK,
    MAX_MEMBERS,
    MAX_SHARD,
    MAX_SHARDS,
    MAX_TOTAL,
    _archive,
    _file_identity,
    _hash,
    _path,
)
from infrastructure.reporting.native_hosted_original_producer import _mutable_output
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.required_candidate_transport import INDEX_PATH, SCHEMA, SHARD_PREFIX
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader, json_object_from_bytes


def collect_required_candidate(
    source: NativeSourceContext,
    native_custodian: NativeHostedArtifactCustodian,
    *,
    directory: Path,
    repository: str,
    run_id: int,
    artifact_id: int,
    receipt_sha256: str,
    deadline: float,
) -> dict[str, str]:
    """Collect real API bytes now; retained JSON is never an authentication entry.

    Every shard is independently bound to the exact primary producer index and
    API digest. Existing mutable files require identical authenticated bytes
    and retained physical identity. This reuse does not grant native authority.
    Native semantic/Code/runtime gates remain the genuine reader's responsibility.
    """
    remaining(deadline)
    if not isinstance(source, NativeSourceContext) or not isinstance(native_custodian, NativeHostedArtifactCustodian):
        raise ValueError("candidate collection requires the actual Source/native collector owners")
    if deadline != native_custodian.deadline:
        raise ValueError("candidate collection cannot reset the genuine original reader clock")
    native_custodian.verify_source(source, scope=PUBLIC_PROJECT_NAMES[0])
    head = source.reference.commit
    _hash(receipt_sha256)
    root = source.bindings.current_root
    directory = evidence_directory(root, directory, fresh=True)
    directory.mkdir(parents=True, mode=0o700)

    api_transport = fixed_hosted_api(
        root,
        directory,
        repository=repository,
        run_id=run_id,
        head_sha=head,
        deadline=deadline,
        environment=os.environ.copy(),
    )

    def api_response(method: str, number: int | None = None) -> dict[str, Any]:
        if method == "run":
            response, observed = api_transport.run_metadata()
            label = "run"
        elif method == "workflow":
            response, observed = api_transport.workflow_metadata()
            label = "workflow"
        elif method == "primary-metadata":
            assert number is not None
            response, observed = api_transport.artifact_metadata(number)
            label = "primary-metadata"
        elif method == "jobs":
            assert number is not None
            response, observed = api_transport.job_page(number)
            label = f"jobs-{number}"
        else:
            assert method == "listing" and number is not None
            response, observed = api_transport.artifact_page(number)
            label = f"listing-{number}"
        write_json(root, directory / (label + "-response.json"), response)
        return response

    run = api_response("run")
    primary = api_response("primary-metadata", artifact_id)
    validate_hosted_handoff(
        run, primary, repository=repository, revision=head, run_id=str(run_id), artifact_id=str(artifact_id)
    )
    workflow = api_response("workflow")
    if (
        workflow.get("path") != WORKFLOW
        or base64.b64decode(workflow["content"]) != source.current_source_reader.read(WORKFLOW).content
    ):
        raise ValueError("candidate hosted workflow differs from the independently admitted Source")
    pages = []
    for ordinal in range(1, MAX_LISTING_PAGES + 1):
        pages.append(api_response("listing", ordinal))
        listing = _merge_listing_pages(pages, complete=False)
        if len(listing["artifacts"]) == listing["total_count"]:
            break
    listing = _merge_listing_pages(pages, complete=True)
    owned = [
        row
        for row in listing["artifacts"]
        if row.get("name") == ARTIFACT_NAME or str(row.get("name", "")).startswith(SHARD_PREFIX)
    ]
    selected = {row["name"]: row for row in owned}
    if len(selected) != len(owned) or selected.get(ARTIFACT_NAME) != primary or len(owned) > MAX_SHARDS + 1:
        raise ValueError("candidate primary/shard owner names are duplicate, ambiguous or incomplete")

    def download(name: str) -> dict[str, bytes]:
        metadata = selected[name]
        # Same typed provenance/expiry/size/digest constraints apply to every
        # separately named shard. Only its Source-declared name is substituted.
        normalized = {**metadata, "name": ARTIFACT_NAME}
        validate_hosted_handoff(
            run, normalized, repository=repository, revision=head, run_id=str(run_id), artifact_id=str(metadata["id"])
        )
        target = directory / (name + ".zip")
        content, process_binding = api_transport.download_artifact(metadata["id"], target)
        result = SnapshotReader(root).read(process_binding["path"]).json_object()
        digest = hashlib.sha256(content).hexdigest()
        if (
            metadata["digest"] != "sha256:" + digest
            or metadata["size_in_bytes"] != len(content)
            or json_object_from_bytes(result["stdout"].encode()) != {"original_exit_code": 0, "archive_sha256": digest}
        ):
            raise ValueError("candidate retrieved bytes differ from the actual authenticated API digest/size")
        return _archive(content, maximum=MAX_ARCHIVE, count=1)

    primary_bytes = download(ARTIFACT_NAME)
    if set(primary_bytes) != {INDEX_PATH}:
        raise ValueError("candidate primary archive lacks its exact Source-owned index member")
    index = json_object_from_bytes(primary_bytes[INDEX_PATH])
    if (
        set(index)
        != {
            "schema_version",
            "repository",
            "hosted_run_id",
            "source_commit",
            "source_identity",
            "receipt",
            "shards",
            "files",
        }
        or index.get("schema_version") != SCHEMA
        or index.get("repository") != repository
        or index.get("hosted_run_id") != run_id
        or index.get("source_commit") != head
        or index.get("source_identity") != source.reference.source_identity
        or index.get("receipt") != {"path": "output/readiness/release-candidate/receipt.json", "sha256": receipt_sha256}
    ):
        raise ValueError("candidate primary differs from the exact Source/handoff receipt identity")
    shards, files = index.get("shards"), index.get("files")
    if (
        not isinstance(shards, list)
        or not 0 < len(shards) <= MAX_SHARDS
        or not isinstance(files, list)
        or not 0 < len(files) <= MAX_MEMBERS
        or set(selected) != {ARTIFACT_NAME, *(SHARD_PREFIX + f"{ordinal:04d}" for ordinal in range(len(shards)))}
    ):
        raise ValueError("candidate shard/file membership census differs from its complete authenticated index")
    chunks: dict[str, Path] = {}
    total = 0
    for ordinal, shard in enumerate(shards):
        remaining(deadline)
        body = download(SHARD_PREFIX + f"{ordinal:04d}")
        filename = f"candidate-shard-{ordinal:04d}.zip"
        if (
            set(body) != {filename}
            or set(shard) != {"filename", "sha256", "members"}
            or shard["filename"] != filename
            or hashlib.sha256(body[filename]).hexdigest() != shard["sha256"]
        ):
            raise ValueError("candidate original shard filename/body hash differs")
        members = _archive(body[filename], maximum=MAX_SHARD, count=MAX_MEMBERS)
        if shard["members"] != [
            {"path": key, "sha256": hashlib.sha256(value).hexdigest(), "bytes": len(value)}
            for key, value in sorted(members.items())
        ]:
            raise ValueError("candidate original shard decoded member bytes/count/hash differ")
        for label, content in members.items():
            digest = _hash(label.removeprefix("chunks/"))
            total += len(content)
            if (
                label != "chunks/" + digest
                or digest in chunks
                or len(content) > MAX_CHUNK
                or hashlib.sha256(content).hexdigest() != digest
                or total > MAX_TOTAL
            ):
                raise ValueError("candidate chunk is repeated, changed or exceeds the Source-owned target cap")
            path = directory / label
            atomic_write_bytes_confined(root, path, content, mode=0o600)
            chunks[digest] = path
    used: set[str] = set()
    paths: set[str] = set()
    retained_identities: dict[Path, tuple[int, ...]] = {}
    total = 0
    for row in files:
        remaining(deadline)
        if not isinstance(row, dict) or set(row) != {"path", "sha256", "bytes", "chunks"}:
            raise ValueError("candidate logical file has unsupported fields")
        label, digest = _path(row["path"]), _hash(row["sha256"])
        if (
            not _mutable_output(label)
            or label in paths
            or type(row["bytes"]) is not int
            or not 0 <= row["bytes"] <= MAX_ARCHIVE
            or not isinstance(row["chunks"], list)
            or len(row["chunks"]) > 8
        ):
            raise ValueError("candidate logical file is unsafe, repeated or exceeds the unchanged64MiB cap")
        blocks = []
        for chunk in row["chunks"]:
            key = _hash(chunk)
            if key not in chunks:
                raise ValueError("candidate logical file references an unauthenticated chunk")
            used.add(key)
            blocks.append(read_bytes_confined(root, chunks[key], max_bytes=MAX_CHUNK))
        content = b"".join(blocks)
        total += len(content)
        if len(content) != row["bytes"] or hashlib.sha256(content).hexdigest() != digest or total > MAX_TOTAL:
            raise ValueError("candidate logical file differs from exact producer bytes or exceeds its whole target cap")
        retained = SnapshotReader(root)
        destination = retained.public_path(label)
        if destination.exists() or destination.is_symlink():
            actual = retained.read(label)
            if actual.content != content or actual.sha256 != digest:
                raise ValueError("candidate extraction cannot overwrite earlier evidence")
        else:
            atomic_write_bytes_confined(root, destination, content, mode=0o600)
            if retained.read(label).content != content:
                raise ValueError("candidate extraction differs from its authenticated bytes")
        if not retained.unchanged():
            raise ValueError("candidate file changed during authenticated extraction")
        retained_identities[destination] = _file_identity(destination)
        paths.add(label)
    if used != set(chunks) or index["receipt"]["path"] not in paths:
        raise ValueError("candidate membership is incomplete or contains unowned chunks")
    native_custodian.verify_source(source, scope=PUBLIC_PROJECT_NAMES[0])
    if any(_file_identity(path) != identity for path, identity in retained_identities.items()):
        raise ValueError("candidate retained files changed during exact membership extraction")
    remaining(deadline)
    return dict(index["receipt"])
