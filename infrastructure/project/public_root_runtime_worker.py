"""One genuine full census and exact applicability units in the selected Root interpreter."""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from infrastructure.project.public_acceptance_evidence import runtime_identity, verify_runtime_execution
from infrastructure.project.public_acceptance_scope import MissingRootCasePolicy, RuntimeScope
from infrastructure.project.public_root_case_admission import admit_plan, lane_blockers
from infrastructure.project.public_root_case_census import produce_root_census
from infrastructure.project.public_root_case_contract import _artifact, _json, _root_identity
from infrastructure.project.public_root_case_units import admitted_units, required_cells, optional_external_records
from infrastructure.project.public_root_lane_coverage import measurement, merge, report
from infrastructure.project.public_root_lane_contract import write
from infrastructure.project.public_root_lane_producer import produce_root_lane
from infrastructure.project.public_root_lane_readback import read_lane
from infrastructure.project.public_root_runtime_contract import CELL_SCHEMA, remaining, selection
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


class _CensusStopped(RuntimeError):
    """Original collection outcome stops execution without inventing a later failure."""


class _AdmissionError(ValueError):
    """Invalid source-owned invocation refused before original collection or case execution."""


def precedence(codes: list[int]) -> int:
    return (
        130
        if 130 in codes
        else 124
        if 124 in codes
        else 1
        if any(code not in {0, 75} for code in codes)
        else 75
        if 75 in codes
        else 0
    )


def coordinate(root: Path, spec_path: Path, expected_hash: str) -> int:
    started = time.monotonic()
    try:
        reader = SnapshotReader(root)
        snapshot = reader.read(spec_path.relative_to(root).as_posix())
        if snapshot.sha256 != expected_hash:
            raise ValueError("Root runtime original specification changed before admission")
        spec = selection(reader, snapshot)
        directory = root / spec["directory"]
    except MissingRootCasePolicy:
        raise
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise _AdmissionError("Root runtime source-owned admission refused") from error
    identity = spec["root_identity"]
    deadline = started + spec["timeout_seconds"]
    records: list[dict[str, Any]] = []
    census_binding = None
    coverage_binding = None
    census_sha256 = ""
    expected_cells: list[dict[str, Any]] = []
    selected_units: list[str] = []
    optional_external: list[dict[str, object]] = []
    diagnostic = ""
    portable_before = None
    portable_after = None
    codes: list[int] = []
    measured = measurement(root)
    try:
        limit = min(spec["census_timeout_seconds"], remaining(deadline, time.monotonic()))
        census_bundle = produce_root_census(root, directory / "census", timeout_seconds=limit)
        census_binding = write(root, directory / "census-bundle.json", census_bundle, identity)
        if type(census_bundle.get("exit_code")) is not int or census_bundle["exit_code"] != 0:
            original = census_bundle.get("exit_code")
            codes.append(original if original in {124, 130, 75} else 1)
            raise _CensusStopped("original whole census did not succeed")
        admitted = admit_plan(reader, census_bundle)
        from infrastructure.project.public_root_portable import observe_origin

        original_census_spec = _json(_artifact(reader, census_bundle["spec_artifact"]))
        original_census_receipt = _json(_artifact(reader, census_bundle["receipt_artifact"]))
        portable_before = observe_origin(reader, original_census_spec, original_census_receipt["cases"])
        if admitted.plan.runtime != spec["runtime"]["python_version"] or admitted.plan.platform != sys.platform:
            raise ValueError("original full census belongs to a different selected runtime/platform")
        census_sha256 = admitted.plan.census_sha256
        units = admitted_units(admitted)
        optional_external = optional_external_records(admitted.policy)
        expected_cells = [asdict(cell) for cell in required_cells(admitted.policy, admitted.prerequisites)]
        selected_units = [
            unit.id
            for unit in units
            if sys.platform in unit.platforms and (spec["mode"] == "live" or unit.lane in {"core", "offline-benchmark"})
        ]
        if not selected_units:
            codes.append(75)
            raise MissingRootCasePolicy("Root selected mode/host has no nonempty required applicability unit")
        for index, unit in enumerate(units):
            blockers = lane_blockers(admitted, unit.id, spec["mode"])
            attempted = unit.id in selected_units
            row: dict[str, Any] = {
                "unit": unit.id,
                "lane": unit.lane,
                "nodeids": list(unit.nodeids),
                "obligations": list(unit.obligations),
                "runtimes": list(unit.runtimes),
                "platforms": list(unit.platforms),
                "attempted": attempted,
                "exit_code": 75,
                "blockers": blockers,
                "bundle_artifact": None,
            }
            if not attempted or blockers:
                if attempted:
                    codes.append(75)
                records.append(row)
                continue
            limit = remaining(deadline, time.monotonic())
            unit_directory = directory / f"unit-{index:03d}"
            bundle = produce_root_lane(
                root,
                unit_directory,
                census_bundle=census_bundle,
                lane=unit.id,
                mode=spec["mode"],
                timeout_seconds=limit,
                test_timeout_seconds=spec["test_timeout_seconds"],
            )
            row["bundle_artifact"] = write(root, unit_directory / "runtime-lane-bundle.json", bundle, identity)
            raw_code = bundle.get("exit_code")
            code = raw_code if type(raw_code) is int and raw_code in {0, 75, 124, 130} else 1
            row["exit_code"] = code
            if code == 0:
                result = read_lane(reader, bundle)
                if result["selected_nodes"] != list(unit.nodeids):
                    raise ValueError(
                        "original executed Root unit differs from its source-owned complete case membership"
                    )
                lane_spec = _json(_artifact(reader, bundle["spec_artifact"]))
                original_census = _json(_artifact(reader, lane_spec["census_bundle_artifact"]))
                census_spec = _json(_artifact(reader, original_census["spec_artifact"]))
                # Private provider integration is a separate obligation and may
                # never contribute to public infrastructure coverage.
                for chunk in result["records"] if unit.lane != "private-contract" else ():
                    child = _json(_artifact(reader, chunk["receipt_artifact"]))
                    merge(
                        measured,
                        _json(_artifact(reader, child["coverage_data_artifact"])),
                        census_spec["implementation"],
                    )
            codes.append(code)
            records.append(row)
            if code in {124, 130}:
                break
        if len(records) != len(units):
            diagnostic = "Root runtime stopped before its entire declared unit inventory was observed"
        elif precedence(codes) == 0:
            coverage_binding = write(root, directory / "coverage.json", report(measured), identity)
        verify_runtime_execution(root, root=root, scope="root")
        portable_after = observe_origin(reader, original_census_spec, original_census_receipt["cases"])
        if portable_before != portable_after:
            raise ValueError("original portable custody changed during actual Root cases")
        current = RuntimeScope(root, "root")
        if (
            current.source_identity() != spec["source_identity"]
            or current.deliverables_identity() != spec["deliverables_identity"]
            or runtime_identity() != spec["runtime"]
            or not reader.unchanged()
            or _root_identity(root) != identity
        ):
            raise ValueError("Root source/runtime/deliverables changed before recording cohort completion")
    except _CensusStopped:
        diagnostic = "Original whole census stopped with its preserved native outcome"
    except KeyboardInterrupt:
        codes.append(130)
        diagnostic = "Root runtime interrupted"
    except TimeoutError:
        codes.append(124)
        diagnostic = "Root runtime whole deadline exhausted"
    except MissingRootCasePolicy:
        codes.append(75)
        diagnostic = "Required source-owned Root execution prerequisite is unavailable"
    except (OSError, ValueError, TypeError, KeyError, RuntimeError):
        codes.append(1)
        diagnostic = "Original Root census, unit execution or independent readback refused"
    code = precedence(codes)
    if time.monotonic() >= deadline and code != 130:
        code = 124
    if code == 0:
        from infrastructure.project.public_root_portable import SCHEMA as PORTABLE_SCHEMA

        write(
            root,
            directory / "portable-observation.json",
            {
                "schema_version": PORTABLE_SCHEMA,
                "spec_artifact": {"path": snapshot.relative, "sha256": snapshot.sha256},
                "before": portable_before,
                "after": portable_after,
            },
            identity,
        )
    write(
        root,
        directory / "runtime-cell.json",
        {
            "schema_version": CELL_SCHEMA,
            "role": "actual-root-runtime-cohort",
            "run_id": spec["run_id"],
            "nonce": spec["nonce"],
            "spec_artifact": {"path": snapshot.relative, "sha256": snapshot.sha256},
            "runtime": spec["runtime"],
            "platform": sys.platform,
            "mode": spec["mode"],
            "source_identity": spec["source_identity"],
            "deliverables_identity": spec["deliverables_identity"],
            "policy_artifact": spec["policy_artifact"],
            "prerequisites_artifact": spec["prerequisites_artifact"],
            "census_bundle_artifact": census_binding,
            "census_sha256": census_sha256,
            "required_cells": expected_cells,
            "selected_units": selected_units,
            "optional_external": optional_external,
            "units": records,
            "coverage_artifact": coverage_binding,
            "exit_code": code,
            "duration_seconds": time.monotonic() - started,
            "diagnostic": diagnostic,
        },
        identity,
    )
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--spec-sha256", required=True)
    args = parser.parse_args(argv)
    if len(args.spec_sha256) != 64 or any(char not in "0123456789abcdef" for char in args.spec_sha256):
        parser.error("Root runtime original specification needs exact SHA-256")
    try:
        return coordinate(args.root.resolve(strict=True), args.spec.absolute(), args.spec_sha256)
    except MissingRootCasePolicy:
        return 75
    except _AdmissionError:
        return 2
    except KeyboardInterrupt:
        return 130
    except TimeoutError:
        return 124
    except (OSError, ValueError, TypeError, KeyError, RuntimeError):
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
