"""Deep modules remain required, isolated, and complementary to legacy smoke."""

from pathlib import Path

import yaml
import pytest

from infrastructure.core.testing.ci_contracts import CONTRACT_SECONDS, combined_groups, contract_files
from infrastructure.core.testing.ci_infra import infrastructure_shards, validate_plan, validate_shards

ROOT = Path(__file__).resolve().parents[3]


def test_deep_owner_files_are_complementary_without_removing_legacy_smoke() -> None:
    heavy = "tests/infra_tests/project/test_public_reference.py"
    legacy = "tests/infra_tests/project/test_public_source_body_admission.py"
    routine = "tests/infra_tests/core/test_ci_selection.py"
    files = (heavy, legacy, routine)
    assert contract_files(files, (legacy,)) == (heavy,)
    plan = {"infra_shards": [[legacy], [routine]], "contract_modules": [heavy]}
    validate_shards(combined_groups(plan), files)
    assert combined_groups(plan)[-1] == [heavy]


def test_required_contract_job_keeps_whole_root_budget_and_explicit_empty_outcome() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_bytes())
    jobs = workflow["jobs"]
    assert "test-contract" in jobs["ci-gate"]["needs"]
    contract = jobs["test-contract"]
    assert contract["timeout-minutes"] * 60 == 7200
    assert CONTRACT_SECONDS <= 7200
    assert jobs["test-infra"]["timeout-minutes"] == 10
    assert contract["strategy"]["max-parallel"] == 3
    assert contract["steps"][0]["if"] == "matrix.shard == -1"
    assert any(step.get("if") == "always() && matrix.shard != -1" for step in contract["steps"])


def test_actual_deep_owner_cannot_be_moved_back_into_smoke_or_omitted() -> None:
    for module in (
        "tests/infra_tests/project/test_public_reference.py",
        "tests/infra_tests/publishing/test_standalone_install_projection.py",
    ):
        changed = (module,)
        plan = {
            "changed_paths": changed,
            "infra_shards": infrastructure_shards(ROOT, changed),
            "contract_modules": list(changed),
        }
        validate_plan(ROOT, plan)
        assert not any(module in shard for shard in plan["infra_shards"])
        plan["contract_modules"] = []
        plan["infra_shards"][0].append(changed[0])
        with pytest.raises(ValueError, match="deep contract selection"):
            validate_plan(ROOT, plan)
