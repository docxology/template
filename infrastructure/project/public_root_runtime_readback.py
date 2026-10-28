"""Independent Root runtime readback in the genuinely selected interpreter; no cross-minor reconstruction."""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from infrastructure.project.public_root_case_admission import admit_plan
from infrastructure.project.public_root_case_contract import _artifact, _json
from infrastructure.project.public_root_case_readback import _within_deadline
from infrastructure.project.public_root_case_units import admitted_units, required_cells, optional_external_records
from infrastructure.project.public_root_lane_coverage import measurement, merge, report
from infrastructure.project.public_root_lane_readback import _zero, read_lane
from infrastructure.project.public_root_runtime_contract import (
    BUNDLE_ROLE,
    CELL_SCHEMA,
    PROCESS_SCHEMA,
    selection,
    worker_command,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def read_runtime_cohort(reader: SnapshotReader, bundle: object, *, origin: Any = None) -> dict[str, Any]:
    """Validate the full operational cohort and every original passing applicability unit.

    This runs only in the actual selected interpreter. Its original full census
    remains independently authenticated; a parent cannot substitute another
    minor's runtime, installed dependencies, SDK bytes or code observations.
    """
    if (
        not isinstance(bundle, dict)
        or set(bundle) != {"role", "exit_code", "spec_artifact", "result_artifact", "process_artifact"}
        or bundle["role"] != BUNDLE_ROLE
        or type(bundle["exit_code"]) is not int
        or bundle["exit_code"] != 0
    ):
        raise ValueError("Root runtime requires its exact successful original guarded cohort bundle")
    snapshot = _artifact(reader, bundle["spec_artifact"])
    spec = selection(reader, snapshot, origin=origin)
    directory = reader.root / spec["directory"]
    native_snapshot = _artifact(reader, bundle["process_artifact"])
    result_snapshot = _artifact(reader, bundle["result_artifact"])
    native, result = _json(native_snapshot), _json(result_snapshot)
    _zero(native, worker_command(Path(sys.executable), reader.root, snapshot, origin=origin))
    if (
        set(native)
        != {
            "schema_version",
            "run_id",
            "nonce",
            "spec_artifact",
            "result_artifact",
            "command",
            "returncode",
            "original_returncode",
            "timed_out",
            "custody_refused",
            "command_error",
            "admission_duration_seconds",
            "launch_budget_seconds",
            "duration_seconds",
        }
        or native["schema_version"] != PROCESS_SCHEMA
        or native["run_id"] != spec["run_id"]
        or native["nonce"] != spec["nonce"]
        or native_snapshot.path != directory / "runtime-process.json"
        or native["spec_artifact"] != bundle["spec_artifact"]
        or native["result_artifact"] != bundle["result_artifact"]
        or not _within_deadline(native["duration_seconds"], spec["timeout_seconds"])
        or not _within_deadline(native["admission_duration_seconds"], spec["timeout_seconds"])
        or native["duration_seconds"] < native["admission_duration_seconds"]
        or type(native["launch_budget_seconds"]) is not int
        or native["launch_budget_seconds"] < 1
        or native["launch_budget_seconds"] != math.floor(spec["timeout_seconds"] - native["admission_duration_seconds"])
        or result_snapshot.path != directory / "runtime-cell.json"
        or set(result)
        != {
            "schema_version",
            "role",
            "run_id",
            "nonce",
            "spec_artifact",
            "runtime",
            "platform",
            "mode",
            "source_identity",
            "deliverables_identity",
            "policy_artifact",
            "prerequisites_artifact",
            "census_bundle_artifact",
            "census_sha256",
            "required_cells",
            "selected_units",
            "optional_external",
            "units",
            "coverage_artifact",
            "exit_code",
            "duration_seconds",
            "diagnostic",
        }
        or result["schema_version"] != CELL_SCHEMA
        or result["role"] != BUNDLE_ROLE
        or any(
            result[key] != spec[key]
            for key in (
                "run_id",
                "nonce",
                "runtime",
                "mode",
                "source_identity",
                "deliverables_identity",
                "policy_artifact",
                "prerequisites_artifact",
            )
        )
        or result["spec_artifact"] != bundle["spec_artifact"]
        or result["platform"] != (origin.platform if origin else sys.platform)
        or type(result["exit_code"]) is not int
        or result["exit_code"] != 0
        or result["diagnostic"] != ""
        or not _within_deadline(result["duration_seconds"], native["launch_budget_seconds"])
        or result["duration_seconds"] > native["duration_seconds"] - native["admission_duration_seconds"]
    ):
        raise ValueError("Root runtime original source, native boundary or finite timeline is incompatible")
    census_snapshot = _artifact(reader, result["census_bundle_artifact"])
    if census_snapshot.path != directory / "census-bundle.json":
        raise ValueError("Root runtime full census is outside its original cohort")
    census_bundle = _json(census_snapshot)
    admitted = admit_plan(reader, census_bundle, origin=origin)
    units = admitted_units(admitted)
    selected = [
        unit.id
        for unit in units
        if admitted.plan.platform in unit.platforms
        and (spec["mode"] == "live" or unit.lane in {"core", "offline-benchmark"})
    ]
    cells = [
        dict(asdict(cell), nodeids=list(cell.nodeids), obligations=list(cell.obligations))
        for cell in required_cells(admitted.policy, admitted.prerequisites)
    ]
    if (
        admitted.plan.runtime != spec["runtime"]["python_version"]
        or admitted.plan.platform != result["platform"]
        or admitted.plan.census_sha256 != result["census_sha256"]
        or result["required_cells"] != cells
        or not selected
        or result["selected_units"] != selected
        or result["optional_external"] != optional_external_records(admitted.policy)
        or not isinstance(result["units"], list)
        or len(result["units"]) != len(units)
    ):
        raise ValueError("Root runtime omitted or changed its complete original applicable unit inventory")
    measured = measurement(reader.root)
    counts: dict[str, int] = {}
    for index, (unit, row) in enumerate(zip(units, result["units"], strict=True)):
        attempted = unit.id in selected
        expected = {
            "unit": unit.id,
            "lane": unit.lane,
            "nodeids": list(unit.nodeids),
            "obligations": list(unit.obligations),
            "runtimes": list(unit.runtimes),
            "platforms": list(unit.platforms),
            "attempted": attempted,
        }
        if (
            not isinstance(row, dict)
            or set(row) != set(expected) | {"exit_code", "blockers", "bundle_artifact"}
            or any(row[key] != value for key, value in expected.items())
            or row["attempted"] is not attempted
            or type(row["exit_code"]) is not int
        ):
            raise ValueError("Root runtime repeated, invented or reclassified a source-owned applicability unit")
        if not attempted:
            blockers = (
                [{"id": unit.id, "reason": "required-applicable-platform-unavailable"}]
                if (origin.platform if origin else sys.platform) not in unit.platforms
                else [{"id": unit.id, "reason": "explicit-live-mode-required"}]
            )
            if row["exit_code"] != 75 or row["bundle_artifact"] is not None or row["blockers"] != blockers:
                raise ValueError("Root runtime unselected unit lacks its fresh source-bound mode/platform reason")
            continue
        if row["exit_code"] != 0 or row["blockers"] != []:
            raise ValueError("Root runtime applicable selected unit did not succeed")
        lane_snapshot = _artifact(reader, row["bundle_artifact"])
        if lane_snapshot.path != directory / f"unit-{index:03d}" / "runtime-lane-bundle.json":
            raise ValueError("Root runtime lane bundle is outside its original applicability unit")
        lane_bundle = _json(lane_snapshot)
        lane = read_lane(reader, lane_bundle, origin=origin)
        if lane["lane"] != unit.id or lane["selected_nodes"] != list(unit.nodeids) or lane["mode"] != spec["mode"]:
            raise ValueError("Root runtime actual executed unit differs from source-owned selection")
        lane_spec = _json(_artifact(reader, lane_bundle["spec_artifact"]))
        if _json(_artifact(reader, lane_spec["census_bundle_artifact"])) != census_bundle:
            raise ValueError("Root runtime unit replaced its single original full census")
        census_spec = _json(_artifact(reader, census_bundle["spec_artifact"]))
        for record in lane["records"] if unit.lane != "private-contract" else ():
            chunk = _json(_artifact(reader, record["receipt_artifact"]))
            merge(measured, _json(_artifact(reader, chunk["coverage_data_artifact"])), census_spec["implementation"])
        counts[unit.id] = len(unit.nodeids)
    coverage_snapshot = _artifact(reader, result["coverage_artifact"])
    coverage = _json(coverage_snapshot)
    reconstructed = report(measured)
    if (
        coverage_snapshot.path != directory / "coverage.json"
        or any(coverage.get(key) != reconstructed.get(key) for key in ("files", "totals"))
        or not reader.unchanged()
    ):
        raise ValueError("Root runtime whole-unit branch coverage differs from original source-bound arcs")
    return {
        "role": BUNDLE_ROLE,
        "exit_code": 0,
        "runtime": spec["runtime"],
        "platform": result["platform"],
        "source_identity": spec["source_identity"],
        "deliverables_identity": spec["deliverables_identity"],
        "policy_artifact": spec["policy_artifact"],
        "census_sha256": result["census_sha256"],
        "required_cells": cells,
        "selected_units": selected,
        "optional_external": optional_external_records(admitted.policy),
        "passed_counts": counts,
        "coverage_artifact": result["coverage_artifact"],
        "coverage": coverage,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--bundle-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve(strict=True)
        reader = SnapshotReader(root)
        snapshot = reader.read(args.bundle.absolute().relative_to(root).as_posix())
        if snapshot.sha256 != args.bundle_sha256:
            raise ValueError("Root runtime original cohort bundle bytes changed")
        result = read_runtime_cohort(reader, _json(snapshot))
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        return 0
    except KeyboardInterrupt:
        return 130
    except OSError, ValueError, TypeError, KeyError, RuntimeError:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
