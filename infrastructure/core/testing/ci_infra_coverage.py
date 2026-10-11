"""Export actual shard data and enforce the complete ordinary-CI union floor."""

from __future__ import annotations

import hashlib
import io
import json
import math
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

from coverage import Coverage, CoverageData

from infrastructure.core.files.secure_write import (
    atomic_write_bytes_confined,
    atomic_write_text_confined,
    read_bytes_confined,
)
from infrastructure.core.pipeline.fingerprints import tree_records
from infrastructure.core.testing.ci_infra_partition import (
    INFRA_MARKERS,
    SCHEMA,
    SHARD_COUNT,
    partition,
    read_receipt,
    receipt_path,
    selected_runtime,
    selection_source,
    validate_receipts,
)

INFRA_COVERAGE_FLOOR = 60.0
ARTIFACT_DIRECTORY = Path("output/readiness/ordinary-infra-ci/coverage-data")


def _identity(root: Path) -> tuple[int, int]:
    metadata = root.lstat()
    return metadata.st_dev, metadata.st_ino


def export_shard(root: Path, shard: int) -> Path:
    """Package exact current successful selection plus actual Coverage bytes."""
    root = root.absolute()
    identity = _identity(root)
    record = read_receipt(root, receipt_path(root, shard))
    source = selection_source(root)
    nodes = record.get("all_node_ids")
    if not isinstance(nodes, list) or not all(type(node) is str for node in nodes):
        raise ValueError("coverage export lacks actual collection")
    assigned = partition(nodes)[shard]
    if (
        record.get("schema_version") != SCHEMA
        or record.get("shard") != shard
        or record.get("shard_count") != SHARD_COUNT
        or record.get("source_sha256") != source
        or record.get("python_minor") != selected_runtime()
        or record.get("marker_expression") != INFRA_MARKERS
        or record.get("original_pytest_exit_code") != 0
        or record.get("exit_code") != 0
        or record.get("complete") is not True
        or record.get("diagnostics") != []
        or record.get("assigned_node_ids") != list(assigned)
        or record.get("completed_node_ids") != list(assigned)
    ):
        raise ValueError("coverage export refuses an unsuccessful or stale infrastructure shard")
    data = read_bytes_confined(root, root / ".coverage.infra", max_bytes=64 * 1024 * 1024)
    if not data or selection_source(root) != source:
        raise ValueError("infrastructure coverage data is empty or source changed before export")
    destination = root / ARTIFACT_DIRECTORY / f"infra-coverage-shard-{shard}"
    if destination.exists() or destination.is_symlink():
        raise ValueError("coverage export requires a fresh owned artifact directory")
    atomic_write_bytes_confined(root, destination / "coverage.data", data, expected_root_identity=identity)
    payload = {**record, "coverage_sha256": hashlib.sha256(data).hexdigest()}
    atomic_write_text_confined(
        root,
        destination / "selection.json",
        json.dumps(payload, sort_keys=True, indent=2) + "\n",
        expected_root_identity=identity,
    )
    return destination


def merge_shards(root: Path) -> float:
    """Read each exact transfer, merge actual arcs in memory, then require 60%.

    Coverage reads only a disposable copy of the already confined transferred
    bytes. Its JSON/XML output goes to memory; mature confined writers publish
    the union under the originally admitted physical checkout.
    """
    root = root.absolute()
    identity = _identity(root)
    source = selection_source(root)
    admitted_inventory = tree_records(root / ARTIFACT_DIRECTORY)
    expected_entries = {"."} | {
        name
        for shard in range(SHARD_COUNT)
        for name in (
            f"./infra-coverage-shard-{shard}",
            f"./infra-coverage-shard-{shard}/selection.json",
            f"./infra-coverage-shard-{shard}/coverage.data",
        )
    }
    if {name for name, _, _ in admitted_inventory} != expected_entries:
        raise ValueError("coverage merge requires exactly the complete declared artifact inventory")
    records = [
        read_receipt(root, root / ARTIFACT_DIRECTORY / f"infra-coverage-shard-{shard}" / "selection.json")
        for shard in range(SHARD_COUNT)
    ]
    validate_receipts(records, expected_source=source, expected_runtime=selected_runtime())
    blobs: list[bytes] = []
    for shard, record in enumerate(records):
        data = read_bytes_confined(
            root,
            root / ARTIFACT_DIRECTORY / f"infra-coverage-shard-{shard}" / "coverage.data",
            max_bytes=64 * 1024 * 1024,
        )
        if not data or hashlib.sha256(data).hexdigest() != record.get("coverage_sha256"):
            raise ValueError("infrastructure coverage transfer has a missing or changed data hash")
        blobs.append(data)
    with tempfile.TemporaryDirectory(prefix="ordinary-infra-coverage-") as directory:
        # A private file-backed union: coverage's shared-cache in-memory
        # database cannot ATTACH more than one shard ("other_db is already in use").
        union = Coverage(
            data_file=str(Path(directory) / "union.coverage"),
            config_file=str(root / "pyproject.toml"),
            source=[str(root / "infrastructure")],
        )
        for shard, data in enumerate(blobs):
            copy = Path(directory) / f"shard-{shard}.coverage"
            copy.write_bytes(data)
            actual = CoverageData(basename=str(copy))
            actual.read()
            if not actual.has_arcs() or not actual.measured_files():
                raise ValueError("infrastructure coverage shard lacks real branch measurements")
            for filename in actual.measured_files():
                path = Path(filename)
                if (
                    not path.is_absolute()
                    or ".." in path.parts
                    or str(path) != filename
                    or not path.is_relative_to(root / "infrastructure")
                    or path.suffix != ".py"
                ):
                    raise ValueError("infrastructure coverage data names a foreign source path")
                read_bytes_confined(root, path, max_bytes=4 * 1024 * 1024)
            union.get_data().update(actual)
        report = io.StringIO()
        with redirect_stdout(report):
            union.json_report(outfile="-")
        payload = json.loads(report.getvalue())
        percent = payload["totals"]["percent_covered"]
        if type(percent) not in (int, float) or not math.isfinite(percent) or percent < INFRA_COVERAGE_FLOOR:
            raise ValueError(f"complete infrastructure union coverage {percent} is below {INFRA_COVERAGE_FLOOR}%")
        xml = io.StringIO()
        with redirect_stdout(xml):
            union.xml_report(outfile="-")
    if selection_source(root) != source or tree_records(root / ARTIFACT_DIRECTORY) != admitted_inventory:
        raise ValueError("infrastructure selection source changed while merging coverage")
    atomic_write_text_confined(root, root / "coverage-infra.xml", xml.getvalue(), expected_root_identity=identity)
    atomic_write_text_confined(
        root, root / "output/readiness/ordinary-infra-ci/union.json", report.getvalue(), expected_root_identity=identity
    )
    return float(percent)


__all__ = ["INFRA_COVERAGE_FLOOR", "ARTIFACT_DIRECTORY", "export_shard", "merge_shards"]
