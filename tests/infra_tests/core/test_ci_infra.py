"""Functional sharding preserves the legacy roster and changed-test ownership."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.core.testing.ci_infra import (
    infrastructure_files,
    infrastructure_shards,
    validate_shards,
    verify_shard_receipts,
)
from infrastructure.core.testing.pytest_observations import member_digest

ROOT = Path(__file__).resolve().parents[3]


def test_actual_shards_are_nonempty_disjoint_complete_and_include_changed_source_owners() -> None:
    changed = ("infrastructure/core/testing/ci_selection.py", "tests/infra_tests/core/test_ci_infra.py")
    files = infrastructure_files(ROOT, changed)
    shards = infrastructure_shards(ROOT, changed)
    validate_shards(shards, files)
    assert len(shards) == 3
    assert "tests/infra_tests/core/test_ci_selection.py" in files
    assert "tests/infra_tests/core/test_ci_infra.py" in files
    assert set(infrastructure_files(ROOT)) <= set(files)
    assert shards == infrastructure_shards(ROOT, changed)
    for asset in ("_mermaid_v11_adapter.mjs", "_mermaid_v11_batch_adapter.mjs"):
        asset_files = infrastructure_files(ROOT, ("infrastructure/rendering/" + asset,))
        assert "tests/infra_tests/reporting/test_native_mermaid_runtime_profile.py" in asset_files
        assert set(infrastructure_files(ROOT)) <= set(asset_files)


def test_deleted_test_routes_existing_owner_without_executing_nonexistent_path() -> None:
    deleted = "tests/infra_tests/core/test_removed_contract.py"
    files = infrastructure_files(ROOT, (deleted,))
    assert deleted not in files
    assert "tests/infra_tests/core/test_ci_selection.py" in files
    assert all((ROOT / name).is_file() for name in files)


def test_broad_package_ownership_scales_shards_without_losing_selected_work() -> None:
    from infrastructure.core.testing.ci_contracts import combined_groups, contract_files

    heavy = (
        "tests/infra_tests/core/test_execution_contract.py",
        "tests/infra_tests/core/test_project_test_measurement.py",
    )
    changed = ("infrastructure/reporting/__init__.py", "infrastructure/validation/__init__.py", *heavy)
    files = infrastructure_files(ROOT, changed)
    shards = infrastructure_shards(ROOT, changed)
    assert 3 < len(shards) <= 8
    assert all([module] in shards for module in heavy)
    small = infrastructure_shards(ROOT, heavy)
    assert len(small) >= 5 and all([module] in small for module in heavy)
    plan = {"infra_shards": shards, "contract_modules": list(contract_files(files, infrastructure_files(ROOT)))}
    validate_shards(combined_groups(plan), files)
    assert shards == infrastructure_shards(ROOT, changed)
    for count in (1, 3, 8):
        explicit = infrastructure_shards(ROOT, changed, count)
        validate_shards(combined_groups({**plan, "infra_shards": explicit}), files)
        assert len(explicit) == count
    for invalid in (0, 9, True, 1.5):
        with pytest.raises(ValueError, match="between one and eight"):
            infrastructure_shards(ROOT, changed, invalid)


@pytest.mark.parametrize("fault", ["missing", "duplicate", "empty", "extra"])
def test_shard_manifest_refuses_missing_duplicate_empty_and_extra_work(fault: str) -> None:
    shards = [["one.py"], ["two.py"]]
    if fault == "missing":
        shards.pop()
    elif fault == "duplicate":
        shards[0].append("two.py")
    elif fault == "empty":
        shards.append([])
    else:
        shards[0].append("three.py")
    with pytest.raises(ValueError):
        validate_shards(shards, ("one.py", "two.py"))


@pytest.mark.parametrize(
    "fault", ["none", "missing", "duplicate", "members", "outcomes", "contract", "contract-deselected"]
)
def test_aggregate_receipt_checks_exact_selected_file_and_member_union(tmp_path: Path, fault: str) -> None:
    from infrastructure.core.testing.ci_infra import _functional_selection

    plan = {"infra_shards": [["tests/one.py"], ["tests/two.py"]]}
    if fault.startswith("contract"):
        plan = {"infra_shards": [["tests/one.py"]], "contract_modules": ["tests/two.py"]}
    from infrastructure.core.testing.ci_contracts import combined_groups

    for index, paths in enumerate(combined_groups(plan)):
        if fault == "missing" and index == 1:
            continue
        selected = [paths[0] + "::test_owned"]
        deselected = [paths[0] + "::test_omitted"] if fault == "contract-deselected" and index == 1 else []
        collected = selected + deselected
        phases = {"setup": "passed", "call": "passed", "teardown": "passed"}
        outcomes = [selected[0] + "|" + json.dumps(phases, sort_keys=True, separators=(",", ":"))]
        row = {
            "shard": index,
            "nonce": "owned-" + str(index),
            "files": paths,
            "selected": selected,
            "outcomes": outcomes,
            "member_sha256": member_digest(tuple(selected)),
            "outcome_sha256": member_digest(tuple(outcomes)),
            "collected": collected,
            "deselected": deselected,
            "selection_profile": {
                "arguments": [
                    *paths,
                    "--no-cov",
                    "-q",
                    "--benchmark-disable",
                    "-p",
                    "infrastructure.core.testing.pytest_receipt",
                    *(["-m", "", "-k", ""] if fault.startswith("contract") and index == 1 else []),
                    "--junitxml=diagnostic.xml",
                    "--timeout=120" if fault.startswith("contract") and index == 1 else "--timeout=60",
                ],
                **_functional_selection(ROOT, is_contract=fault.startswith("contract") and index == 1),
                "workers": None,
                "ambient_addopts": False,
            },
            "collection_sha256": member_digest(tuple(collected)),
            "deselected_sha256": member_digest(tuple(deselected)),
        }
        if fault == "members":
            row["selected"] = []
        if fault == "outcomes":
            row["outcomes"] = []
        directory = tmp_path / str(index)
        directory.mkdir()
        observed = directory / "execution"
        observed.mkdir()
        (observed / "execution-1.json").write_text(
            json.dumps(
                {
                    "schema_version": "template-pytest-execution/v1",
                    "nonce": row["nonce"],
                    "worker": "controller",
                    "selected": selected,
                    "collected": collected,
                    "deselected": deselected,
                    "selection_profile": row["selection_profile"],
                    "reports": {selected[0]: phases},
                    "collection_errors": 0,
                    "exit_code": 0,
                }
            )
        )
        (directory / "summary.json").write_text(json.dumps(row))
        if fault == "duplicate" and index == 0:
            duplicate = tmp_path / "duplicate"
            duplicate.mkdir()
            (duplicate / "summary.json").write_text(json.dumps(row))
    if fault in {"none", "contract"}:
        assert verify_shard_receipts(plan, tmp_path)["members"] == 2
    else:
        with pytest.raises(ValueError):
            verify_shard_receipts(plan, tmp_path)
