"""Applicability preserves the actual complete census and every required target."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest

from infrastructure.project.public_acceptance_case_policy import POLICY_SCHEMA, RootCasePolicy
from infrastructure.project.public_root_case_admission import PREREQUISITE_SCHEMA, Prerequisite, admit_plan
from infrastructure.project.public_root_case_units import declared_units, required_cells
from infrastructure.project.public_root_lane_producer import produce_root_lane
from infrastructure.project.public_root_lane_readback import _read_lane_result
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from tests.infra_tests.project import test_root_case_census as census_controls
from tests.infra_tests.project.test_root_case_lanes import _epoch_call

pytestmark = pytest.mark.timeout(240)


@pytest.fixture(scope="module")
def genuine_census(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any], RootCasePolicy]:
    """Use the unchanged actual source fixture and its original guarded process evidence."""
    return census_controls.genuine_census.__wrapped__(tmp_path_factory)


def source_policy(policy: RootCasePolicy, platform_rows: list[dict[str, Any]]) -> RootCasePolicy:
    rows = []
    for family in policy.families:
        row = asdict(family)
        row["members"] = [asdict(member) for member in family.members]
        row["obligations"] = list(family.obligations)
        if family.lane == "core":
            row["obligations"].extend(item["id"] for item in platform_rows)
        rows.append(row)
    return RootCasePolicy.parse(
        {
            "schema_version": POLICY_SCHEMA,
            "runtimes": list(policy.runtimes),
            "platforms": list(policy.platforms),
            "families": rows,
            "obligations": [asdict(item) for item in policy.obligations] + platform_rows,
        }
    )


def prerequisites(policy: RootCasePolicy) -> tuple[Prerequisite, ...]:
    return tuple(Prerequisite(item.id, item.kind, (), (), ()) for item in policy.obligations)


def test_actual_full_census_members_remain_required_on_every_global_target(
    genuine_census: tuple[Path, dict[str, Any], RootCasePolicy],
) -> None:
    policy = genuine_census[2]
    expected = {member.nodeid for family in policy.families for member in family.members}
    units = declared_units(policy, prerequisites(policy))
    assert set(node for unit in units for node in unit.nodeids) == expected
    cells = required_cells(policy, prerequisites(policy))
    for node in expected:
        assert {(cell.platform, cell.runtime) for cell in cells if node in cell.nodeids} == {
            (platform, runtime) for platform in policy.platforms for runtime in policy.runtimes
        }
    assert {cell.lane for cell in cells} == {family.lane for family in policy.families}
    assert all(cell.policy_sha256 == policy.sha256 for cell in cells)


def test_explicit_platform_condition_narrows_only_its_family_and_keeps_all_minors(
    genuine_census: tuple[Path, dict[str, Any], RootCasePolicy],
) -> None:
    # This is a source-contract partition experiment using the real census;
    # it does not assert that the tiny arithmetic fixture needs macOS.
    policy = source_policy(genuine_census[2], [{"id": "owned-macos-contract", "kind": "platform", "eligibility": None}])
    obligations = tuple(
        Prerequisite(item.id, item.kind, (), (), ("darwin",) if item.kind == "platform" else ("linux",))
        for item in policy.obligations
    )
    units = declared_units(policy, obligations)
    core = next(unit for unit in units if unit.lane == "core")
    live = next(unit for unit in units if unit.lane == "live-unpaid")
    assert core.id == "core:darwin" and core.platforms == ("darwin",)
    assert core.runtimes == policy.runtimes
    assert live.platforms == policy.platforms, "provider/tool availability cannot silently narrow applicability"
    cells = required_cells(policy, obligations)
    assert {(cell.platform, cell.runtime) for cell in cells if cell.unit == core.id} == {
        ("darwin", runtime) for runtime in policy.runtimes
    }
    assert {(cell.platform, cell.runtime) for cell in cells if cell.unit == live.id} == {
        (platform, runtime) for platform in policy.platforms for runtime in policy.runtimes
    }


@pytest.mark.parametrize("fault", ["empty", "unsupported", "contradictory"])
def test_platform_condition_cannot_make_a_genuine_family_have_no_required_target(
    genuine_census: tuple[Path, dict[str, Any], RootCasePolicy], fault: str
) -> None:
    rows = [{"id": "owned-platform-one", "kind": "platform", "eligibility": None}]
    if fault == "contradictory":
        rows.append({"id": "owned-platform-two", "kind": "platform", "eligibility": None})
    policy = source_policy(genuine_census[2], rows)
    conditions = []
    for item in policy.obligations:
        targets = ()
        if item.kind == "platform":
            targets = (
                ("windows",)
                if fault == "unsupported"
                else ()
                if fault == "empty"
                else ("darwin" if item.id.endswith("one") else "linux",)
            )
        conditions.append(Prerequisite(item.id, item.kind, (), (), targets))
    with pytest.raises(ValueError):
        required_cells(policy, tuple(conditions))


@pytest.mark.parametrize("fault", ["missing", "extra", "duplicate", "wrong-kind"])
def test_source_owned_obligation_inventory_cannot_be_waived_or_replaced(
    genuine_census: tuple[Path, dict[str, Any], RootCasePolicy], fault: str
) -> None:
    policy = genuine_census[2]
    values = list(prerequisites(policy))
    if fault == "missing":
        values.pop()
    elif fault == "extra":
        values.append(Prerequisite("invented-extra", "tool", (), (), ()))
    elif fault == "duplicate":
        values.append(values[0])
    else:
        values[0] = Prerequisite(values[0].id, "tool", (), (), ())
    with pytest.raises(ValueError):
        required_cells(policy, tuple(values))


@pytest.mark.timeout(600)
def test_actual_source_admitted_wrong_host_cannot_be_rehashed_into_a_success(
    genuine_census: tuple[Path, dict[str, Any], RootCasePolicy],
) -> None:
    root, _, original = genuine_census
    other = "linux" if sys.platform == "darwin" else "darwin"
    policy = source_policy(original, [{"id": "owned-other-platform", "kind": "platform", "eligibility": None}])
    source = root / "pyproject.toml"
    before = source.read_bytes()
    infrastructure = root / "infrastructure"
    config = infrastructure / "config"
    infrastructure_existed, config_existed = infrastructure.exists(), config.exists()
    config.mkdir(parents=True, exist_ok=True)
    native_path: Path | None = None
    native_bytes: bytes | None = None
    policy_file, prerequisites_file = config / "unit-policy.json", config / "unit-prerequisites.json"
    try:
        policy_file.write_text(
            json.dumps(
                {
                    "schema_version": POLICY_SCHEMA,
                    "runtimes": list(policy.runtimes),
                    "platforms": list(policy.platforms),
                    "families": [
                        dict(asdict(family), obligations=list(family.obligations)) for family in policy.families
                    ],
                    "obligations": [asdict(item) for item in policy.obligations],
                }
            )
        )
        prerequisites_file.write_text(
            json.dumps(
                {
                    "schema_version": PREREQUISITE_SCHEMA,
                    "obligations": [
                        {
                            "id": item.id,
                            "kind": item.kind,
                            "environment_keys": []
                            if item.kind == "platform"
                            else ["TEMPLATE_OWNED_UNAVAILABLE_MODEL_CONFIGURATION"],
                            "executables": [] if item.kind == "platform" else ["python"],
                            "platforms": [other] if item.kind == "platform" else [],
                        }
                        for item in policy.obligations
                    ],
                }
            )
        )
        source.write_bytes(
            before
            + (
                "\n[tool.template.root_acceptance]\nschema_version=2\n"
                'policy="infrastructure/config/unit-policy.json"\n'
                'prerequisites="infrastructure/config/unit-prerequisites.json"\n'
            ).encode()
        )
        census = census_controls._produce_control(root, root / "output/readiness/wrong-host-census", 180)
        assert census["exit_code"] == 0, census
        admitted = admit_plan(SnapshotReader(root), census)
        assert admitted.plan.platform == sys.platform and admitted.plan.runtime in policy.runtimes
        bundle = _epoch_call(
            produce_root_lane,
            root,
            root / "output/readiness/wrong-host-lane",
            census_bundle=census,
            lane="core:" + other,
            timeout_seconds=180,
        )
        assert bundle["exit_code"] == 75, bundle
        assert not (root / "body-executed").exists()
        native_path = root / bundle["process_artifact"]["path"]
        native_bytes = native_path.read_bytes()
        process = json.loads(native_bytes)
        assert process["returncode"] == process["original_returncode"] == 75
        # Retain the real source-admitted specification/census and original blocked
        # result. A consistently rebound zero native assertion cannot make that
        # original host applicable; the independent reader checks it directly.
        process.update(returncode=0, original_returncode=0)
        rebound = write_json(root, root / bundle["process_artifact"]["path"], process)
        with pytest.raises(ValueError, match="source-owned applicability"):
            _read_lane_result(
                SnapshotReader(root),
                {
                    "spec_artifact": bundle["spec_artifact"],
                    "result_artifact": bundle["result_artifact"],
                    "process_artifact": rebound,
                },
            )
    finally:
        source.write_bytes(before)
        policy_file.unlink(missing_ok=True)
        prerequisites_file.unlink(missing_ok=True)
        if native_path is not None and native_bytes is not None:
            native_path.write_bytes(native_bytes)
        if not config_existed:
            config.rmdir()
        if not infrastructure_existed:
            infrastructure.rmdir()
