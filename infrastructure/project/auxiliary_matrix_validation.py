"""Bind every Linux gate to the freshly collected original project graph."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from infrastructure.project.auxiliary_matrix_hosted import AuxiliaryMatrixHostedContext, AuxiliaryMatrixOriginal, SCHEMA
from infrastructure.project.auxiliary_matrix_plan import matrix_plan, receipt_path, validate_cell
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.original_job_outcome import validate_auxiliary_receipt_closure
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def authenticate_matrix(reader: SnapshotReader, receipt: dict[str, Any], requirements: Any) -> None:
    """Retained manifests cannot replace current live same-attempt originals."""
    context = reader.hosted_origin
    if (
        type(context) is not AuxiliaryMatrixHostedContext
        or type(context.matrix_original) is not AuxiliaryMatrixOriginal
    ):
        raise ValueError("hosted acceptance requires the genuinely collected complete auxiliary matrix")
    original = context.matrix_original
    if original.pid != os.getpid() or original.root != reader.root:
        raise ValueError("auxiliary matrix original lost its live reader process/root")
    deadline = reader.operation_deadline
    if deadline is None and reader.native_operation is not None:
        deadline = reader.native_operation.deadline
    if deadline is None or deadline > original.deadline:
        raise ValueError("auxiliary matrix requires its existing finite reader clock")
    remaining(deadline)
    binding = receipt.get("auxiliary_matrix_artifact")
    if (
        not isinstance(binding, dict)
        or set(binding) != {"path", "sha256"}
        or any(not isinstance(binding[key], str) for key in ("path", "sha256"))
    ):
        raise ValueError("hosted candidate omitted its complete auxiliary matrix binding")
    held = reader.read(binding["path"])
    manifest = held.json_object()
    if held.sha256 != binding["sha256"] or any(
        manifest.get(key) != value
        for key, value in dict(
            schema_version=SCHEMA,
            repository=context.repository,
            run_id=context.run_id,
            head_sha=context.head_sha,
            cells=original.cells,
        ).items()
    ):
        raise ValueError("candidate auxiliary matrix differs from freshly authenticated originals")
    directory = Path(held.relative).parent
    _authenticate_archives(reader, manifest.get("archives"), original.cells, directory)
    _authenticate_observations(reader, manifest.get("observations"), original.cells, directory)
    paths = receipt.get("original_receipts")
    if (
        not isinstance(paths, list)
        or any(not isinstance(row, dict) or set(row) != {"path", "sha256"} for row in paths)
        or len({row["path"] for row in paths}) != len(paths)
    ):
        raise ValueError("candidate original receipt graph is absent or repeated")
    for cell, gates in matrix_plan(requirements).items():
        remaining(deadline)
        cell_binding = original.cells[cell]["receipt"]
        if cell_binding not in paths or cell_binding["path"] != receipt_path(cell):
            raise ValueError("candidate omitted an original auxiliary project receipt")
        cell_receipt = reader.read(cell_binding["path"])
        report = cell_receipt.json_object()
        if cell_receipt.sha256 != cell_binding["sha256"]:
            raise ValueError("auxiliary original receipt changed after live collection")
        validate_cell(report, requirements, cell)
        validate_auxiliary_receipt_closure(report)
        for gate in gates:
            if receipt["gates"].get(gate) != report["gates"][gate]:
                raise ValueError("candidate replaced an original auxiliary gate observation")
        _authenticate_graph(reader, report, Path(receipt_path(cell)).parent, original.members, deadline)


def _authenticate_graph(
    reader: SnapshotReader, report: dict[str, Any], prefix: Path, members: Any, deadline: float
) -> None:
    """Every referenced readiness byte belongs to this actual producer archive."""
    pending: list[Any] = [report]
    seen: set[str] = set()
    count = 0
    while pending:
        remaining(deadline)
        count += 1
        if count > 64 * 1024 * 1024 // 2 or len(seen) > 10000:
            raise ValueError("auxiliary matrix graph exceeds its original archive bound")
        value = pending.pop()
        if isinstance(value, dict):
            bindings = []
            if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
                bindings.append((value["path"], value["sha256"]))
            if isinstance(value.get("artifact"), str) and isinstance(value.get("artifact_sha256"), str):
                bindings.append((value["artifact"], value["artifact_sha256"]))
            for path, digest in bindings:
                if not Path(path).is_relative_to("output/readiness"):
                    continue  # Source/tool declarations retain their own stricter validators.
                if not Path(path).is_relative_to(prefix) or members.get(path) != digest:
                    raise ValueError("auxiliary project graph escapes its actual authenticated archive")
                held = reader.read(path)
                if held.sha256 != digest:
                    raise ValueError("auxiliary project evidence changed after live collection")
                if path not in seen and path.endswith(".json"):
                    seen.add(path)
                    pending.append(held.json_object())
            pending.extend(item for item in value.values() if isinstance(item, (dict, list)))
        elif isinstance(value, list):
            pending.extend(item for item in value if isinstance(item, (dict, list)))


def _authenticate_archives(reader: SnapshotReader, archives: Any, cells: dict[str, Any], directory: Path) -> None:
    if not isinstance(archives, list) or len(archives) != len(cells):
        raise ValueError("candidate omitted complete original auxiliary archive bytes")
    expected = {cell["artifact_id"] for cell in cells.values()}
    observed = set()
    for archive in archives:
        if (
            not isinstance(archive, dict)
            or set(archive) != {"path", "sha256"}
            or any(not isinstance(archive[key], str) for key in ("path", "sha256"))
        ):
            raise ValueError("candidate auxiliary archive binding is malformed")
        selected = [cell for cell in cells.values() if Path(archive["path"]).name == str(cell["artifact_id"]) + ".zip"]
        if len(selected) != 1 or selected[0]["artifact_id"] in observed or Path(archive["path"]).parent != directory:
            raise ValueError("candidate auxiliary archive identities are missing or repeated")
        observed.add(selected[0]["artifact_id"])
        retained = reader.read(archive["path"])
        if retained.sha256 != archive["sha256"] or retained.sha256 != selected[0]["archive_sha256"]:
            raise ValueError("candidate archive bytes differ from freshly authenticated original")
    if observed != expected:
        raise ValueError("candidate omitted an actual original auxiliary archive identity")


def _authenticate_observations(
    reader: SnapshotReader, observations: Any, cells: dict[str, Any], directory: Path
) -> None:
    # Retention integrity only: these old API captures never mint live authority.
    import re
    from infrastructure.project.public_hosted_origin import MAX_LISTING_PAGES

    if not isinstance(observations, list):
        raise ValueError("candidate omitted original auxiliary API observation bindings")
    names = set()
    for binding in observations:
        if (
            not isinstance(binding, dict)
            or set(binding) != {"path", "sha256"}
            or any(not isinstance(binding[key], str) for key in ("path", "sha256"))
        ):
            raise ValueError("auxiliary original observation binding is malformed")
        path = Path(binding["path"])
        if path.parent != directory or path.name in names:
            raise ValueError("auxiliary original observations escaped or repeated")
        names.add(path.name)
        held = reader.read(binding["path"])
        if held.sha256 != binding["sha256"]:
            raise ValueError("auxiliary original observation changed after retention")
        held.json_object()
    expected = {"run-process.json", "workflow-process.json"}
    for cell in cells.values():
        expected.update(
            {f"metadata-{cell['artifact_id']}-process.json", f"artifact-{cell['artifact_id']}-process.json"}
        )
    for category in ("listing", "jobs"):
        pages = sorted(
            int(match.group(1))
            for name in names
            if (match := re.fullmatch(category + r"-([1-9][0-9]*)-process\.json", name))
        )
        if not pages or pages != list(range(1, len(pages) + 1)) or len(pages) > MAX_LISTING_PAGES:
            raise ValueError("auxiliary original API page retention is incomplete or unbounded")
        expected.update(f"{category}-{page}-process.json" for page in pages)
    if names != expected:
        raise ValueError("auxiliary original API observation retention is incomplete or foreign")
