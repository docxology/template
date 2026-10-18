"""Live same-attempt collection of the complete auxiliary project matrix.

Receipt JSON and retained API output are DATA. Only this fixed live collector
mints the held original; fresh release readers repeat the actual collection.
"""

from __future__ import annotations

import base64
import hashlib
import os
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, cast

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.project.auxiliary_matrix_plan import matrix_plan, receipt_path, validate_cell
from infrastructure.project.auxiliary_print_hosted import AuxiliaryPrintHostedContext, _utc
from infrastructure.project.public_acceptance_evidence import evidence_directory, write_json
from infrastructure.project.public_hosted_origin import (
    MAX_ARCHIVE,
    MAX_LISTING_PAGES,
    WORKFLOW,
    _context,
    _merge_listing_pages,
)
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_hosted_transport_archive import _archive
from infrastructure.reporting.original_job_outcome import validate_auxiliary_receipt_closure
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-auxiliary-project-hosted-v1"
_KEY = object()


class AuxiliaryMatrixOriginal:
    """Immutable commitments obtained from actual successful fixed API calls."""

    __slots__ = ("root", "pid", "repository", "run_id", "head_sha", "binding", "_cells", "members", "deadline")
    root: Path
    pid: int
    repository: str
    run_id: int
    head_sha: str
    binding: Mapping[str, str]
    _cells: bytes
    members: Mapping[str, str]
    deadline: float

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("held auxiliary original is immutable")

    def __init__(
        self,
        key: object,
        root: Path,
        repository: str,
        run_id: int,
        head_sha: str,
        binding: dict[str, str],
        cells: dict[str, Any],
        members: dict[str, str],
        deadline: float,
    ) -> None:
        if key is not _KEY or sys._getframe(1).f_code is not collect_auxiliary_matrix.__code__:
            raise ValueError("auxiliary matrix original requires the actual live fixed collector")
        for name, value in dict(
            root=root,
            deadline=deadline,
            pid=os.getpid(),
            repository=repository,
            run_id=run_id,
            head_sha=head_sha,
            binding=MappingProxyType(dict(binding)),
            _cells=json.dumps(cells, sort_keys=True).encode(),
            members=MappingProxyType(dict(members)),
        ).items():
            object.__setattr__(self, name, value)

    @property
    def cells(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self._cells))


@dataclass(frozen=True)
class AuxiliaryMatrixHostedContext(AuxiliaryPrintHostedContext):
    """Held Root, Darwin print and separate Linux project originals."""

    matrix_original: AuxiliaryMatrixOriginal

    def __post_init__(self) -> None:
        super().__post_init__()
        if type(self.matrix_original) is not AuxiliaryMatrixOriginal:
            raise ValueError("hosted context requires the genuine auxiliary matrix collector")
        if (self.repository, self.run_id, self.head_sha) != (
            self.matrix_original.repository,
            self.matrix_original.run_id,
            self.matrix_original.head_sha,
        ):
            raise ValueError("held auxiliary matrix belongs to another hosted context")


def _jobs(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not pages or len(pages) > MAX_LISTING_PAGES:
        raise ValueError("auxiliary producer job census is absent or unbounded")
    total = pages[0].get("total_count")
    if type(total) is not int or not 0 < total <= 1024:
        raise ValueError("auxiliary producer job census is invalid")
    rows = []
    for index, page in enumerate(pages):
        current = page.get("jobs")
        if (
            page.get("total_count") != total
            or not isinstance(current, list)
            or len(current) > 100
            or (index < len(pages) - 1 and len(current) != 100)
        ):
            raise ValueError("auxiliary producer pagination changed or is incomplete")
        rows.extend(current)
    if (
        len(rows) != total
        or any(not isinstance(row, dict) or type(row.get("id")) is not int for row in rows)
        or len({row["id"] for row in rows}) != total
    ):
        raise ValueError("auxiliary producer jobs are repeated or incomplete")
    return rows


def _producer(
    cell: str, artifacts: list[dict[str, Any]], jobs: list[dict[str, Any]], run: dict[str, Any]
) -> dict[str, Any]:
    selected = [row for row in artifacts if row.get("name") == f"required-source-auxiliary-linux-{cell}"]
    producers = [row for row in jobs if row.get("name") == f"auxiliary-original ({cell})"]
    if len(selected) != 1 or len(producers) != 1:
        raise ValueError("auxiliary matrix original artifact/producer is missing or repeated")
    artifact, job = selected[0], producers[0]
    repo = run["repository"]["id"]
    origin = artifact.get("workflow_run", {})
    steps = [step for step in job.get("steps", []) if step.get("name") == "Retain original auxiliary audit"]
    if (
        type(artifact.get("id")) is not int
        or artifact["id"] <= 0
        or artifact.get("expired") is not False
        or origin.get("id") != run["id"]
        or origin.get("head_sha") != run["head_sha"]
        or origin.get("repository_id") != repo
        or origin.get("head_repository_id") != repo
        or job.get("run_id") != run["id"]
        or job.get("head_sha") != run["head_sha"]
        or type(run.get("run_attempt")) is not int
        or job.get("run_attempt") != run["run_attempt"]
        or job.get("status") != "completed"
        or job.get("conclusion") != "success"
        or len(steps) != 1
        or steps[0].get("conclusion") != "success"
        or not _utc(job.get("started_at")) <= _utc(artifact.get("created_at")) <= _utc(job.get("completed_at"))
    ):
        raise ValueError("auxiliary original lacks successful same-attempt producer custody")
    return artifact


def collect_auxiliary_matrix(
    root: Path,
    directory: Path,
    *,
    repository: str,
    run_id: int,
    head_sha: str,
    requirements: Any,
    deadline: float,
    environment: dict[str, str],
) -> AuxiliaryMatrixOriginal:
    """Authenticate every project original with the existing outer reader clock."""
    from infrastructure.project._hosted_api import fixed_hosted_api

    _context(repository, run_id, head_sha)
    remaining(deadline)
    plan = matrix_plan(requirements)
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
    run, run_observation = api.run_metadata()
    repo, head = run.get("repository", {}), run.get("head_repository", {})
    if (
        run.get("id") != run_id
        or run.get("head_sha") != head_sha
        or run.get("path") != WORKFLOW
        or repo.get("full_name") != repository
        or head.get("full_name") != repository
        or type(repo.get("id")) is not int
        or head.get("id") != repo["id"]
    ):
        raise ValueError("auxiliary matrix belongs to another Source workflow/run/head")
    workflow, workflow_observation = api.workflow_metadata()
    reader = SnapshotReader(root, operation_deadline=deadline)
    if workflow.get("path") != WORKFLOW or base64.b64decode(workflow["content"]) != reader.read(WORKFLOW).content:
        raise ValueError("auxiliary matrix workflow differs from current Source")
    artifact_pages, job_pages, observations = [], [], [run_observation, workflow_observation]
    for page in range(1, MAX_LISTING_PAGES + 1):
        value, binding = api.artifact_page(page)
        artifact_pages.append(value)
        observations.append(binding)
        listing = _merge_listing_pages(artifact_pages, complete=False)
        if len(listing["artifacts"]) == listing["total_count"]:
            break
    artifacts = _merge_listing_pages(artifact_pages, complete=True)["artifacts"]
    for page in range(1, MAX_LISTING_PAGES + 1):
        value, binding = api.job_page(page)
        job_pages.append(value)
        observations.append(binding)
        if sum(len(row.get("jobs", [])) for row in job_pages) == value.get("total_count"):
            break
    jobs = _jobs(job_pages)
    expected_names = {f"required-source-auxiliary-linux-{cell}" for cell in plan}
    actual_names = [
        row.get("name") for row in artifacts if str(row.get("name", "")).startswith("required-source-auxiliary-linux")
    ]
    if set(actual_names) != expected_names or len(actual_names) != len(expected_names):
        raise ValueError("auxiliary artifact roster differs from complete Source matrix")
    cells, members, archives = {}, {}, []
    for cell in plan:
        remaining(deadline)
        artifact = _producer(cell, artifacts, jobs, run)
        metadata, observed = api.artifact_metadata(artifact["id"])
        observations.append(observed)
        if any(
            metadata.get(key) != artifact.get(key)
            for key in ("id", "name", "digest", "size_in_bytes", "expired", "workflow_run")
        ):
            raise ValueError("auxiliary artifact metadata changed during live collection")
        archive_path = directory / f"{artifact['id']}.zip"
        content, observed = api.download_artifact(artifact["id"], archive_path)
        observations.append(observed)
        digest = hashlib.sha256(content).hexdigest()
        if artifact.get("size_in_bytes") != len(content) or artifact.get("digest") != "sha256:" + digest:
            raise ValueError("auxiliary original archive differs from live API digest/size")
        archives.append({"path": archive_path.relative_to(root).as_posix(), "sha256": digest})
        payloads = _archive(content, maximum=MAX_ARCHIVE, count=10000)
        if "receipt.json" not in payloads:
            raise ValueError("auxiliary original omitted its literal receipt")
        for relative, content in payloads.items():
            label = (Path(receipt_path(cell)).parent / relative).as_posix()
            target = reader.public_path(label)
            if target.exists() or target.is_symlink():
                if reader.read(label).content != content:
                    raise ValueError("auxiliary authenticated original conflicts with existing DATA")
            else:
                atomic_write_bytes_confined(root, target, content, mode=0o600)
            members[label] = hashlib.sha256(content).hexdigest()
        receipt = reader.read(receipt_path(cell))
        validate_cell(receipt.json_object(), requirements, cell)
        validate_auxiliary_receipt_closure(receipt.json_object())
        cells[cell] = {
            "artifact_id": artifact["id"],
            "archive_sha256": digest,
            "receipt": {"path": receipt.relative, "sha256": receipt.sha256},
        }
    if len({row["artifact_id"] for row in cells.values()}) != len(plan) or not reader.unchanged():
        raise ValueError("auxiliary originals repeated artifact identity or changed during collection")
    binding = write_json(
        root,
        directory / "matrix.json",
        dict(
            schema_version=SCHEMA,
            repository=repository,
            run_id=run_id,
            head_sha=head_sha,
            cells=cells,
            archives=archives,
            observations=observations,
        ),
    )
    return AuxiliaryMatrixOriginal(_KEY, root, repository, run_id, head_sha, binding, cells, members, deadline)
