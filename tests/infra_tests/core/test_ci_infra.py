"""Functional sharding preserves the baseline roster and changed-test ownership."""

from __future__ import annotations

import ast
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
    assert len(shards) >= 3
    assert "tests/infra_tests/core/test_ci_selection.py" in files
    assert "tests/infra_tests/core/test_ci_infra.py" in files
    assert set(infrastructure_files(ROOT)) <= set(files)
    assert shards == infrastructure_shards(ROOT, changed)
    for asset in ("_mermaid_v11_adapter.mjs", "_mermaid_v11_batch_adapter.mjs"):
        asset_files = infrastructure_files(ROOT, ("infrastructure/rendering/" + asset,))
        assert "tests/infra_tests/reporting/test_native_mermaid_runtime_profile.py" in asset_files
        assert set(infrastructure_files(ROOT)) <= set(asset_files)

    from infrastructure.core.testing.ci_contracts import combined_groups, contract_files

    # Every alias retains its actual reexport/protocol consumers plus all
    # preexisting conventional owners, without selecting the whole core tree.
    expected_owners = {
        "infrastructure/core/pipeline/artifacts/_manifest.py": (
            "tests/infra_tests/benchmark/test_template_benchmark_harness.py",
            "tests/infra_tests/core/pipeline/test_artifact_finalization.py",
            "tests/infra_tests/core/test_analysis_pipeline.py",
            "tests/infra_tests/core/test_manifest_parsing.py",
            "tests/infra_tests/core/test_manifest_snapshot.py",
            "tests/infra_tests/core/test_manifest_validation.py",
            "tests/infra_tests/core/test_pipeline_control_artifacts.py",
            "tests/infra_tests/core/test_stable_local_mode.py",
            "tests/infra_tests/methods/test_methods_cli.py",
            "tests/infra_tests/methods/test_methods_orchestration.py",
            "tests/infra_tests/publishing/test_repro_bundle.py",
            "tests/infra_tests/publishing/test_repro_bundle_absent_output.py",
            "tests/infra_tests/regression/test_manifest_contract.py",
            "tests/infra_tests/rendering/test_manifest.py",
            "tests/infra_tests/reporting/test_native_office_semantic_source.py",
            "tests/infra_tests/validation/test_publication_audit.py",
            "tests/infra_tests/validation/test_rendered_provenance_composition_parser.py",
            "tests/infra_tests/validation/test_rendered_provenance_confinement.py",
            "tests/infra_tests/validation/test_rendered_provenance_external_lifecycle.py",
            "tests/infra_tests/validation/test_rendered_provenance_placeholder_scan.py",
            "tests/infra_tests/validation/test_rendered_provenance_receipt_lifecycle.py",
            "tests/infra_tests/validation/test_rendered_provenance_roles.py",
            "tests/infra_tests/validation/test_rendered_provenance_stage_closures.py",
        ),
        "infrastructure/core/pipeline/executor.py": (
            "tests/infra_tests/core/pipeline/test_artifact_finalization.py",
            "tests/infra_tests/core/pipeline/test_cache_identity.py",
            "tests/infra_tests/core/pipeline/test_execution_deadline.py",
            "tests/infra_tests/core/pipeline/test_execution_records.py",
            "tests/infra_tests/core/pipeline/test_executor_log_ownership.py",
            "tests/infra_tests/core/pipeline/test_incremental_executor.py",
            "tests/infra_tests/core/pipeline/test_modularity_boundaries.py",
            "tests/infra_tests/core/pipeline/test_opt_in_tags.py",
            "tests/infra_tests/core/pipeline/test_plan_admission_custody.py",
            "tests/infra_tests/core/pipeline/test_plan_compilation.py",
            "tests/infra_tests/core/pipeline/test_plugins.py",
            "tests/infra_tests/core/pipeline/test_plugins_executor.py",
            "tests/infra_tests/core/pipeline/test_report_custody_review.py",
            "tests/infra_tests/core/pipeline/test_report_finalization.py",
            "tests/infra_tests/core/pipeline/test_run_matrix.py",
            "tests/infra_tests/core/pipeline/test_tool_bindings.py",
            "tests/infra_tests/core/test_analysis_launch.py",
            "tests/infra_tests/core/test_execution_contract.py",
            "tests/infra_tests/core/test_execution_policy.py",
            "tests/infra_tests/core/test_pipeline.py",
            "tests/infra_tests/core/test_pipeline_control_hitl.py",
            "tests/infra_tests/methods/test_methods_cli.py",
            "tests/infra_tests/methods/test_methods_orchestration.py",
        ),
        "infrastructure/core/testing/ci_infra.py": (
            "tests/infra_tests/core/test_ci_module_durations.py",
            "tests/infra_tests/core/test_ci_infra.py",
            "tests/infra_tests/core/test_ci_infra_partition.py",
            "tests/infra_tests/core/test_pytest_receipt.py",
            "tests/infra_tests/core/test_ci_contracts.py",
            "tests/infra_tests/core/test_ci_test_ownership.py",
            "tests/infra_tests/core/test_ci_infra_process.py",
        ),
        "infrastructure/core/testing/ci_contracts.py": (
            "tests/infra_tests/core/test_ci_module_durations.py",
            "tests/infra_tests/core/test_ci_contracts.py",
            "tests/infra_tests/core/test_ci_infra.py",
            "tests/infra_tests/core/test_ci_infra_process.py",
        ),
        "infrastructure/core/testing/ci_test_ownership.py": (
            "tests/infra_tests/core/test_ci_infra.py",
            "tests/infra_tests/core/test_ci_infra_partition.py",
            "tests/infra_tests/core/test_ci_test_ownership.py",
        ),
    }
    baseline = infrastructure_files(ROOT)
    for source, owners in expected_owners.items():
        selected = infrastructure_files(ROOT, (source,))
        assert set(selected) == set(baseline) | set(owners)
        conventional = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "tests/infra_tests").rglob("test_" + Path(source).stem.lstrip("_") + "*.py")
        }
        assert conventional <= set(owners)
        shards = infrastructure_shards(ROOT, (source,))
        contracts = contract_files(selected, baseline)
        validate_shards(combined_groups({"infra_shards": shards, "contract_modules": list(contracts)}), selected)
        assert shards == infrastructure_shards(ROOT, (source,))
    executor = "infrastructure/core/pipeline/executor.py"
    actual_executor_consumers = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "tests/infra_tests/core").rglob("test_*.py")
        if any(
            isinstance(node, ast.Call)
            and (
                isinstance(node.func, ast.Name)
                and node.func.id == "PipelineExecutor"
                or isinstance(node.func, ast.Attribute)
                and node.func.attr == "PipelineExecutor"
            )
            for node in ast.walk(ast.parse(path.read_bytes()))
        )
    }
    methods_owners = {
        "tests/infra_tests/methods/test_methods_cli.py",
        "tests/infra_tests/methods/test_methods_orchestration.py",
    }
    assert set(expected_owners[executor]) == actual_executor_consumers | methods_owners
    assert methods_owners <= set(expected_owners["infrastructure/core/pipeline/artifacts/_manifest.py"])
    # Methods validates actual executor methods and delegates its manifest parser
    # to this same public defining implementation, through real wrappers.
    from infrastructure.methods import _plan_validation
    from infrastructure.core.pipeline import PipelineExecutor
    from infrastructure.core.pipeline.artifacts import artifact_manifest_from_payload

    assert _plan_validation.PipelineExecutor is PipelineExecutor
    assert _plan_validation.artifact_manifest_from_payload is artifact_manifest_from_payload
    assert (
        _plan_validation._artifact_manifest_from_payload(
            {"inventory_mode": "stable-shippable-output-v1", "entries": [], "issues": []}
        ).entries
        == ()
    )


def test_deleted_test_routes_existing_owner_without_executing_nonexistent_path() -> None:
    deleted = "tests/infra_tests/core/test_removed_contract.py"
    files = infrastructure_files(ROOT, (deleted,))
    assert deleted not in files
    assert "tests/infra_tests/core/test_ci_selection.py" in files
    assert all((ROOT / name).is_file() for name in files)


def test_broad_package_ownership_scales_shards_without_losing_selected_work() -> None:
    from infrastructure.core.testing.ci_contracts import combined_groups, contract_files

    heavy = (
        "tests/infra_tests/core/pipeline/test_artifact_finalization.py",
        "tests/infra_tests/core/pipeline/test_cache_identity.py",
        "tests/infra_tests/core/pipeline/test_incremental_cli_flag.py",
        "tests/infra_tests/core/pipeline/test_run_matrix.py",
        "tests/infra_tests/core/pipeline/test_shared_runtime_namespace.py",
        "tests/infra_tests/core/test_analysis_launch.py",
        "tests/infra_tests/core/test_execution_contract.py",
        "tests/infra_tests/core/test_project_test_measurement.py",
        "tests/infra_tests/project/test_public_acceptance.py",
        "tests/infra_tests/project/test_root_acceptance.py",
        "tests/infra_tests/publishing/test_standalone_mirror.py",
    )
    changed = ("infrastructure/reporting/__init__.py", "infrastructure/validation/__init__.py", *heavy)
    files = infrastructure_files(ROOT, changed)
    shards = infrastructure_shards(ROOT, changed)
    assert len(shards) > 3
    assert all(len(shard) <= 12 for shard in shards)
    assert all([module] in shards for module in heavy)
    small = infrastructure_shards(ROOT, heavy)
    assert len(small) >= 5 and all([module] in small for module in heavy)
    plan = {"infra_shards": shards, "contract_modules": list(contract_files(files, infrastructure_files(ROOT)))}
    validate_shards(combined_groups(plan), files)
    from infrastructure.core.testing.ci_selection import _contract_matrix
    from infrastructure.core.testing.ci_contracts import contract_preparation

    original_modules = list(plan["contract_modules"])
    rows = _contract_matrix(shards, plan["contract_modules"])["include"]
    expected = [
        {"shard": len(shards) + index, "module": module, **contract_preparation(module)}
        for index, module in enumerate(original_modules)
    ]
    assert sorted(rows, key=lambda row: row["shard"]) == expected
    assert plan["contract_modules"] == original_modules
    assert rows == _contract_matrix(shards, original_modules)["include"]
    if "tests/infra_tests/project/test_root_runtime_v2.py" in original_modules:
        assert rows[0]["module"] == "tests/infra_tests/project/test_root_runtime_v2.py"
    fallback = ["tests/unknown_z.py", "tests/unknown_a.py"]
    assert _contract_matrix(shards, fallback)["include"] == [
        {"shard": len(shards) + index, "module": module, **contract_preparation(module)}
        for index, module in reversed(list(enumerate(fallback)))
    ]
    assert _contract_matrix(shards, [])["include"] == [{"shard": -1, "module": "none", **contract_preparation("none")}]
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


@pytest.mark.timeout(45)
@pytest.mark.parametrize("test_root", ["tests/infra_tests", "tests/integration"])
def test_changed_python_helper_routes_complete_actual_consumer_package(tmp_path: Path, test_root: str) -> None:
    """Changed helpers select real consumers; an actual original receipt stays strict."""
    import os
    import subprocess
    import sys
    from uuid import uuid4

    from infrastructure.core.testing.ci_infra import CI_EXTRA_PATHS, _shard_collection
    from infrastructure.core.testing.pytest_observations import DIRECTORY_ENV, NONCE_ENV, ROOT_ENV

    actual_helper = "tests/infra_tests/llm/real_ollama_client.py"
    actual_files = infrastructure_files(ROOT, (actual_helper,))
    actual_consumers = {
        path.relative_to(ROOT).as_posix() for path in (ROOT / "tests/infra_tests/llm").rglob("test_*.py")
    }
    assert actual_helper not in actual_files
    assert {path for path in actual_files if path.startswith("tests/infra_tests/llm/")} == actual_consumers
    assert {
        "tests/infra_tests/llm/test_llm_core.py",
        "tests/infra_tests/llm/test_core.py",
        "tests/infra_tests/llm/test_review_generators.py",
        "tests/infra_tests/llm/test_llm_review_integration.py",
    } <= actual_consumers

    root = tmp_path / "owned-helper-project"
    root.mkdir()
    # The real selector retains the baseline roster. These placeholder paths are
    # selector inputs only; this control executes the two actual consumers below.
    for name in infrastructure_files(ROOT):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# owned baseline selector input\n")
    (root / "pyproject.toml").write_bytes((ROOT / "pyproject.toml").read_bytes())
    package = root / test_root / "owned_consumers"
    package.mkdir(parents=True)
    marker = root / "actual-helper-calls.txt"
    helper = package / "shared_driver.py"
    helper.write_text(
        "from pathlib import Path\n"
        "def score(value):\n"
        f"    with Path({str(marker)!r}).open('a') as stream: stream.write(str(value)+'\\n')\n"
        "    return value + 17\n"
    )
    consumers = (package / "test_left.py", package / "nested/test_right.py")
    for index, path in enumerate(consumers):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "import importlib.util\nfrom pathlib import Path\n"
            f"spec=importlib.util.spec_from_file_location('actual_owned_helper',Path({str(helper)!r}))\n"
            "helper=importlib.util.module_from_spec(spec)\nspec.loader.exec_module(helper)\n"
            f"def test_actual_consumer():\n    assert helper.score({index}) == {index + 17}\n"
        )
    selected = infrastructure_files(root, (helper.relative_to(root).as_posix(),))
    files = [name for name in selected if name.startswith(package.relative_to(root).as_posix() + "/")]
    assert files == sorted(path.relative_to(root).as_posix() for path in consumers)
    assert helper.relative_to(root).as_posix() not in selected

    directory = root / "observations"
    nonce = uuid4().hex
    environment = {
        **os.environ,
        "PYTEST_ADDOPTS": "",
        DIRECTORY_ENV: str(directory),
        NONCE_ENV: nonce,
        ROOT_ENV: str(root),
    }
    omitted = root / CI_EXTRA_PATHS[0]
    omitted.write_text("def test_actual_requested_but_omitted():\n    assert 17 + 2 == 19\n")
    command = [
        sys.executable,
        "-m",
        "pytest",
        *files,
        "--no-cov",
        "-q",
        "--benchmark-disable",
        "-p",
        "infrastructure.core.testing.pytest_receipt",
        "--junitxml=" + str(root / "actual-consumers.xml"),
        "--timeout=60",
    ]
    result = subprocess.run(command, cwd=root, env=environment, capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert sorted(marker.read_text().splitlines()) == ["0", "1"]
    collection = _shard_collection(directory, nonce, files, root)
    assert len(collection["collected"]) == 2 and collection["deselected"] == []
    # A real collectable additional module still cannot disappear merely
    # because another package's genuine cases completed successfully.
    with pytest.raises(ValueError, match="omitted a requested test file"):
        _shard_collection(directory, nonce, [*files, omitted.relative_to(root).as_posix()], root)


@pytest.mark.parametrize("measured", [False, True])
def test_automatic_shard_count_uses_seconds_only_with_measured_weights(tmp_path: Path, measured: bool) -> None:
    from infrastructure.core.testing.ci_module_durations import MANIFEST_RELATIVE_PATH, SCHEMA_VERSION

    files = infrastructure_files(ROOT)
    for name in files:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("def test_real():\n    assert 2 + 2 == 4\n" + "#" * 1000 + "\n")
    if measured:
        manifest = tmp_path / MANIFEST_RELATIVE_PATH
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "unit": "seconds",
                    "provenance": "owned scheduling control",
                    "modules": {name: 200.0 for name in files},
                }
            )
        )
    shards = infrastructure_shards(tmp_path)
    validate_shards(shards, files)
    capacity_jobs = max(3, (len(files) + 11) // 12)
    assert len(shards) > capacity_jobs if measured else len(shards) == capacity_jobs
    assert len(shards) <= 64
    assert all(len(shard) <= 12 for shard in shards)


@pytest.mark.parametrize("target", ["0", "-1", "nan", "inf"])
def test_shard_seconds_target_refuses_invalid_values(target: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEMPLATE_CI_SHARD_TARGET_SECONDS", target)
    with pytest.raises(ValueError, match="finite positive"):
        infrastructure_shards(ROOT)


def test_complete_infrastructure_change_preserves_roster_above_load_job_preference() -> None:
    from infrastructure.core.testing.ci_contracts import combined_groups, contract_files
    from infrastructure.core.testing.ci_infra import AUTOMATIC_SHARD_LOAD_MAX_JOBS, AUTOMATIC_SHARD_MAX_MODULES

    changed = ("tests/conftest.py",)
    selected = infrastructure_files(ROOT, changed)
    shards = infrastructure_shards(ROOT, changed)
    contracts = contract_files(selected, infrastructure_files(ROOT))
    validate_shards(combined_groups({"infra_shards": shards, "contract_modules": list(contracts)}), selected)
    assert len(selected) > AUTOMATIC_SHARD_LOAD_MAX_JOBS * AUTOMATIC_SHARD_MAX_MODULES
    assert all(len(shard) <= AUTOMATIC_SHARD_MAX_MODULES for shard in shards)
