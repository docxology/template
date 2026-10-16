"""Independent scoped sandbox upload/API/source artifact custody."""

from __future__ import annotations

import json
import re
from typing import Any

from infrastructure.project.public_acceptance_auxiliary_supervision import complete_auxiliary_observation

from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def validate_sandbox_transfer(details: dict[str, Any], reader: SnapshotReader) -> None:
    """Bind genuine official/API upload facts to independently admitted Root bytes."""

    def bound(binding: Any) -> Any:
        if not isinstance(binding, dict) or set(binding) != {"path", "sha256"}:
            raise ValueError("sandbox transfer needs exact artifact bindings")
        snapshot = reader.read(binding["path"])
        if snapshot.sha256 != binding["sha256"]:
            raise ValueError("sandbox transfer artifact changed")
        return snapshot

    raw = bound(details.get("transfer_artifact")).json_object()
    if raw.get("schema_version") != "template-github-sandbox-transfer-v1":
        raise ValueError("unsupported actual sandbox transfer schema")
    repository, run_id, revision = raw.get("repository"), raw.get("run_id"), raw.get("source_commit")
    if (
        not isinstance(repository, str)
        or re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is None
        or not isinstance(run_id, str)
        or re.fullmatch(r"[1-9][0-9]*", run_id) is None
        or not isinstance(revision, str)
        or re.fullmatch(r"[0-9a-f]{40}", revision) is None
    ):
        raise ValueError("sandbox transfer omitted exact source/repository/run custody")
    outputs = raw.get("upload_outputs", {})
    artifact_id = outputs.get("artifact-id")
    digest = outputs.get("artifact-digest")
    if (
        not isinstance(artifact_id, str)
        or re.fullmatch(r"[1-9][0-9]*", artifact_id) is None
        or not isinstance(digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        or outputs.get("artifact-url")
        != f"https://github.com/{repository}/actions/runs/{run_id}/artifacts/{artifact_id}"
    ):
        raise ValueError("official uploaded artifact identity is invalid")
    if bound(raw.get("upload_outputs_artifact")).json_object() != outputs:
        raise ValueError("official upload outputs differ from retained original bytes")
    checkout = bound(raw.get("checkout_process")).json_object()
    command = checkout.get("command", [])
    if (
        not complete_auxiliary_observation(checkout)
        or len(command) != 3
        or command[1:] != ["rev-parse", "HEAD"]
        or checkout.get("exit_code") != 0
        or checkout.get("timed_out") is not False
        or checkout.get("output_limit_exceeded") is not False
        or checkout.get("executable_sha256_before") != checkout.get("executable_sha256_after")
        or bound(checkout.get("streams", {}).get("stdout")).content.decode().strip() != revision
    ):
        raise ValueError("sandbox transfer lacks the actual matching checkout revision observation")
    bound(checkout.get("streams", {}).get("stderr"))
    observed = {}
    for label, endpoint in (
        ("artifact", f"repos/{repository}/actions/artifacts/{artifact_id}"),
        ("repository", f"repos/{repository}"),
    ):
        observation = raw.get("api_observations", {}).get(label, {})
        process = bound(observation.get("process")).json_object()
        command = process.get("command")
        if (
            not complete_auxiliary_observation(process)
            or not isinstance(command, list)
            or len(command) != 5
            or command[1:] != ["api", "--hostname", "github.com", endpoint]
            or process.get("exit_code") != 0
            or process.get("timed_out") is not False
            or process.get("output_limit_exceeded") is not False
            or process.get("executable_sha256_before") != process.get("executable_sha256_after")
        ):
            raise ValueError("sandbox transfer lacks actual bounded scoped GitHub API observations")
        data = json.loads(bound(process.get("streams", {}).get("stdout")).content)
        if data != observation.get("data"):
            raise ValueError("sandbox transfer summary differs from exact actual API response bytes")
        bound(process.get("streams", {}).get("stderr"))
        observed[label] = data
    metadata, repo = observed["artifact"], observed["repository"]
    workflow = metadata.get("workflow_run", {})
    if (
        metadata.get("id") != int(artifact_id)
        or metadata.get("name") != "root-candidate-export"
        or metadata.get("expired") is not False
        or metadata.get("digest") != "sha256:" + digest
        or workflow.get("id") != int(run_id)
        or workflow.get("head_sha") != revision
        or repo.get("full_name") != repository
        or workflow.get("repository_id") != repo.get("id")
        or workflow.get("head_repository_id") != repo.get("id")
    ):
        raise ValueError("sandbox artifact is not the actual same-repository/run/source upload")
    export, retrieved = bound(raw.get("export_artifact")), bound(raw.get("retrieved_artifact"))
    if (
        export.sha256 != retrieved.sha256
        or reader.validated_exports.get("root") != export.sha256
        or details.get("export_artifact") != raw.get("export_artifact")
        or details.get("retrieved_artifact") != raw.get("retrieved_artifact")
    ):
        raise ValueError("sandbox retrieval differs from independently validated Root source export")
