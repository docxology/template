"""Actual same-run Darwin auxiliary collection, separate from Root/full-native.

Only real fixed authenticated API calls mint the held print original. Parsed
API/process/receipt DATA alone has no constructor for this capability.
"""

from __future__ import annotations

import base64
import hashlib
import math
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.project.public_acceptance_evidence import evidence_directory
from infrastructure.project.public_hosted_origin import (
    HostedReadbackContext,
    MAX_ARCHIVE,
    MAX_LISTING_PAGES,
    WORKFLOW,
    _context,
    _merge_listing_pages,
)
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_auxiliary_print_custody import AuxiliaryPrintOriginal, _ORIGINAL
from infrastructure.reporting.native_hosted_transport_archive import _archive
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

ARTIFACT = "required-source-auxiliary-darwin"
PRODUCER_JOB = "root-original (3.14, macos-latest)"
PRODUCER_STEP = "Retain original designated macOS auxiliary audit"


@dataclass(frozen=True)
class AuxiliaryPrintHostedContext(HostedReadbackContext):
    """Existing Root context plus a separately live-authenticated print original."""

    print_original: AuxiliaryPrintOriginal

    def __post_init__(self) -> None:
        if type(self.print_original) is not AuxiliaryPrintOriginal or self.print_original.origin != "hosted":
            raise ValueError("hosted print context needs the genuine independently collected original")


def collect_auxiliary_print_original(
    root: Path,
    directory: Path,
    *,
    repository: str,
    run_id: int,
    head_sha: str,
    deadline: float,
    environment: dict[str, str],
) -> AuxiliaryPrintOriginal:
    """Collect the exact fixed producer artifact through genuine current API calls."""
    from infrastructure.project._hosted_api import fixed_hosted_api

    _context(repository, run_id, head_sha)
    remaining(deadline)
    directory = evidence_directory(root, directory, fresh=True)
    directory.mkdir(mode=0o700, parents=True)
    api = fixed_hosted_api(
        root,
        directory,
        repository=repository,
        run_id=run_id,
        head_sha=head_sha,
        deadline=deadline,
        environment=environment,
    )
    run, _ = api.run_metadata()
    repo = run.get("repository", {})
    if (
        run.get("id") != run_id
        or run.get("head_sha") != head_sha
        or run.get("path") != WORKFLOW
        or repo.get("full_name") != repository
        or type(repo.get("id")) is not int
        or run.get("head_repository", {}).get("id") != repo["id"]
    ):
        raise ValueError("auxiliary print original belongs to another Source workflow/run/head")
    workflow, _ = api.workflow_metadata()
    if (
        workflow.get("path") != WORKFLOW
        or base64.b64decode(workflow["content"]) != SnapshotReader(root).read(WORKFLOW).content
    ):
        raise ValueError("auxiliary print actual workflow differs from current Source")
    pages = []
    for page in range(1, MAX_LISTING_PAGES + 1):
        value, _ = api.artifact_page(page)
        pages.append(value)
        listing = _merge_listing_pages(pages, complete=False)
        if len(listing["artifacts"]) == listing["total_count"]:
            break
    rows = _merge_listing_pages(pages, complete=True)["artifacts"]
    selected = [row for row in rows if row.get("name") == ARTIFACT]
    if len(selected) != 1:
        raise ValueError("auxiliary print needs exactly one same-run fixed Darwin artifact")
    artifact = selected[0]
    origin = artifact.get("workflow_run", {})
    if (
        type(artifact.get("id")) is not int
        or artifact["id"] <= 0
        or artifact.get("expired") is not False
        or origin.get("id") != run_id
        or origin.get("head_sha") != head_sha
        or origin.get("repository_id") != repo["id"]
        or origin.get("head_repository_id") != repo["id"]
    ):
        raise ValueError("auxiliary print artifact has foreign or expired original custody")
    metadata, _ = api.artifact_metadata(artifact["id"])
    for key in ("id", "name", "digest", "size_in_bytes", "expired", "workflow_run"):
        if metadata.get(key) != artifact.get(key):
            raise ValueError("auxiliary print actual artifact metadata changed during collection")
    jobs = []
    total = None
    for page in range(1, MAX_LISTING_PAGES + 1):
        value, _ = api.job_page(page)
        if total is None:
            total = value.get("total_count")
        if (
            type(total) is not int
            or total > 1024
            or value.get("total_count") != total
            or not isinstance(value.get("jobs"), list)
        ):
            raise ValueError("auxiliary print actual producer job census is malformed")
        jobs.extend(value["jobs"])
        if len(jobs) >= total:
            break
    producers = [job for job in jobs if job.get("name") == PRODUCER_JOB]
    if len(jobs) != total or len({job.get("id") for job in jobs}) != len(jobs) or len(producers) != 1:
        raise ValueError("auxiliary print original producer job is absent or ambiguous")
    job = producers[0]
    steps = [step for step in job.get("steps", []) if step.get("name") == PRODUCER_STEP]
    if (
        job.get("run_id") != run_id
        or job.get("head_sha") != head_sha
        or job.get("status") != "completed"
        or job.get("conclusion") != "success"
        or type(run.get("run_attempt")) is not int
        or job.get("run_attempt") != run["run_attempt"]
        or len(steps) != 1
        or steps[0].get("conclusion") != "success"
    ):
        raise ValueError("auxiliary print lacks its actual completed Source-owned producer job/step")
    if not _utc(job.get("started_at")) <= _utc(artifact.get("created_at")) <= _utc(job.get("completed_at")):
        raise ValueError("auxiliary print artifact was not created by this actual producer attempt")
    body, _ = api.download_artifact(artifact["id"], directory / "auxiliary-darwin.zip")
    if len(body) != artifact["size_in_bytes"] or artifact.get("digest") != "sha256:" + hashlib.sha256(body).hexdigest():
        raise ValueError("auxiliary print downloaded original differs from actual API digest/size")
    members = _archive(body, maximum=MAX_ARCHIVE, count=10000)
    if "receipt.json" not in members:
        raise ValueError("auxiliary print original archive omitted its complete literal receipt")
    for relative, payload in members.items():
        remaining(deadline)
        target = root / "output/readiness/auxiliary-darwin" / relative
        if target.exists() or target.is_symlink():
            if read_bytes_confined(root, target, max_bytes=MAX_ARCHIVE) != payload:
                raise ValueError("auxiliary print authenticated original conflicts with retained DATA")
        else:
            atomic_write_bytes_confined(root, target, payload, mode=0o600)
    reader = SnapshotReader(root, operation_deadline=deadline)
    receipt = reader.read("output/readiness/auxiliary-darwin/receipt.json").json_object()
    from infrastructure.project.auxiliary_print_code import ROLE, validate_code
    from infrastructure.project.public_acceptance_auxiliary_bootstrap import WORKER, validate_audited_auxiliary_command
    from infrastructure.project.public_acceptance_auxiliary_supervision import complete_auxiliary_observation

    gate_ref = receipt.get("gates", {}).get(ROLE, {})
    _authenticate_closure(members, receipt, gate_ref, deadline=deadline)
    gate = reader.read(gate_ref["artifact"])
    if gate.sha256 != gate_ref.get("artifact_sha256") or gate_ref.get("status") != "pass":
        raise ValueError("auxiliary print original gate failed or its artifact changed")
    details = gate.json_object()["details"]
    process_binding = details["process_artifact"]
    process_snapshot = reader.read(process_binding["path"])
    process = process_snapshot.json_object()
    if (
        process_snapshot.sha256 != process_binding["sha256"]
        or not complete_auxiliary_observation(process)
        or process.get("exit_code") != 0
        or process.get("host", {}).get("system") != "Darwin"
    ):
        raise ValueError("auxiliary print original is not a successful actual supervised Darwin worker")
    held = process["auxiliary_print_launch"]
    spec = reader.read(process["spec_artifact"]["path"])
    declared = spec.json_object()
    if (
        spec.sha256 != held["spec_sha256"]
        or held["producer_root"] != process["producer_root"]
        or held["deadline"] != process["original_deadline_monotonic"]
        or held["parent_pid"] != process.get("auxiliary_print_owner_pid")
        or held["spec_path"] != str(Path(process["producer_root"]) / process["spec_artifact"]["path"])
        or declared.get("run_id") != held["run_id"]
        or declared.get("operation_deadline") != held["deadline"]
        or declared.get("parent_pid") != held["parent_pid"]
        or declared.get("gate") != ROLE
        or declared.get("negative", False) is not False
    ):
        raise ValueError("auxiliary print original parent spec/run/deadline differs")
    execution = str(Path(process_binding["path"]).parent / "execution")
    validate_audited_auxiliary_command(
        reader, process, module=WORKER, arguments=("--spec", held["spec_path"]), execution_relative=execution
    )
    raw_binding = details["raw_artifact"]
    raw_snapshot = reader.read(raw_binding["path"])
    raw = raw_snapshot.json_object()
    if raw_snapshot.sha256 != raw_binding["sha256"] or raw.get("pid") != process["pid"] or raw.get("exit_code") != 0:
        raise ValueError("auxiliary print original worker facts changed")
    code = reader.read(execution + "/print-code/receipt.json")
    code_binding = {"path": code.relative, "sha256": code.sha256}
    validate_code(reader, code_binding, held, process["pid"], deadline)
    completion = process.get("auxiliary_print_completion_monotonic")
    if (
        not isinstance(completion, (int, float))
        or isinstance(completion, bool)
        or not math.isfinite(completion)
        or not completion < held["deadline"]
    ):
        raise ValueError("auxiliary print original lacks its actual completed finite supervisor clock")
    original = AuxiliaryPrintOriginal(
        _ORIGINAL, root, held, process["pid"], raw["details"]["print_witness_artifact"], code_binding, float(completion)
    )
    if not reader.unchanged():
        raise ValueError("auxiliary print authenticated original changed during readback")
    remaining(deadline)
    return original


def _utc(value: object) -> datetime:
    if not isinstance(value, str) or len(value) > 128:
        raise ValueError("auxiliary print original API time is absent or excessive")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("auxiliary print original API time is not actual UTC")
    return parsed


def _authenticate_closure(
    members: dict[str, bytes], receipt: dict[str, Any], gate_ref: dict[str, Any], *, deadline: float
) -> None:
    """Close every relative evidence binding against the actual API archive."""
    from infrastructure.reporting.release_readiness_snapshot import json_object_from_bytes

    prefix = "output/readiness/auxiliary-darwin/"

    def payload(path: str, digest: str) -> bytes:
        if not path.startswith(prefix) or path[len(prefix) :] not in members:
            raise ValueError("auxiliary print evidence escapes its authenticated original archive")
        body = members[path[len(prefix) :]]
        if hashlib.sha256(body).hexdigest() != digest:
            raise ValueError("auxiliary print evidence differs from its actual authenticated archive")
        return body

    gate = payload(gate_ref["artifact"], gate_ref["artifact_sha256"])
    pending: list[Any] = [receipt, json_object_from_bytes(gate)]
    seen: set[str] = set()
    count = 0
    while pending:
        remaining(deadline)
        count += 1
        # A JSON container consumes at least two bytes in the actual bounded
        # archive. Source inventories legitimately exceed the Code-run bound.
        if count > MAX_ARCHIVE // 2 or len(seen) > 10000:
            raise ValueError("auxiliary print authenticated closure exceeds its existing work bound")
        value = pending.pop()
        if isinstance(value, dict):
            path, digest = value.get("path"), value.get("sha256")
            if isinstance(path, str) and isinstance(digest, str) and not Path(path).is_absolute():
                body = payload(path, digest)
                if path.endswith(".json") and path not in seen:
                    seen.add(path)
                    pending.append(json_object_from_bytes(body))
            pending.extend(item for item in value.values() if isinstance(item, (dict, list)))
        elif isinstance(value, list):
            pending.extend(item for item in value if isinstance(item, (dict, list)))
