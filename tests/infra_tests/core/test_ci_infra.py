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


@pytest.mark.parametrize("fault", ["none", "missing", "duplicate", "members", "outcomes", "contract"])
def test_aggregate_receipt_checks_exact_selected_file_and_member_union(tmp_path: Path, fault: str) -> None:
    plan = {"infra_shards": [["tests/one.py"], ["tests/two.py"]]}
    if fault == "contract":
        plan = {"infra_shards": [["tests/one.py"]], "contract_modules": ["tests/two.py"]}
    from infrastructure.core.testing.ci_contracts import combined_groups

    for index, paths in enumerate(combined_groups(plan)):
        if fault == "missing" and index == 1:
            continue
        selected = [paths[0] + "::test_owned"]
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
