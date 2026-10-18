"""Deep modules remain required, isolated, and complementary to legacy smoke."""

from pathlib import Path

import yaml
import pytest

from infrastructure.core.testing.ci_contracts import (
    CONTRACT_SECONDS,
    combined_groups,
    contract_files,
    contract_preparation,
)
from infrastructure.core.testing.ci_infra import (
    infrastructure_files,
    infrastructure_shards,
    validate_plan,
    validate_shards,
)

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
    assert jobs["test-infra"]["strategy"]["max-parallel"] == 8
    from infrastructure.core.testing.ci_infra import _functional_selection

    assert _functional_selection(ROOT, is_contract=True) == {"marker_expression": "", "keyword_expression": ""}
    assert "not slow" in _functional_selection(ROOT)["marker_expression"]
    assert contract["strategy"]["max-parallel"] == 3
    assert contract["steps"][0]["if"] == "matrix.shard == -1"
    assert any(step.get("if") == "always() && matrix.shard != -1" for step in contract["steps"])
    pdf_modules = (
        "tests/infra_tests/project/test_scientific_reference_replay.py",
        "tests/infra_tests/reporting/test_native_pdf_citations.py",
        "tests/infra_tests/reporting/test_native_pdf_math.py",
        "tests/infra_tests/reporting/test_native_pdf_source_witness.py",
        "tests/infra_tests/reporting/test_pdf_raw_natbib_source.py",
    )
    converter = next(
        step
        for step in contract["steps"]
        if step.get("uses") == "./.github/actions/setup-acceptance-documents"
        and step.get("with", {}).get("mode") == "${{ matrix.documents }}"
    )
    tex = next(step for step in contract["steps"] if "texlive-xetex" in step.get("run", ""))
    browser = next(step for step in contract["steps"] if step.get("if") == "matrix.browser")
    assert converter["if"] == "matrix.documents != 'none'" and tex["if"] == "matrix.tex"
    for module in pdf_modules:
        assert contract_preparation(module) == {"documents": "converter", "tex": True, "browser": False}
    for module in (
        "tests/infra_tests/reporting/test_native_browser_oracles.py",
        "tests/infra_tests/reporting/test_native_browser_scientific_structure.py",
    ):
        assert contract_preparation(module) == {"documents": "converter", "tex": False, "browser": True}
    assert contract_preparation("tests/infra_tests/project/test_root_wheel_typing.py") == {
        "documents": "none",
        "tex": False,
        "browser": False,
    }
    assert contract_preparation("none") == {"documents": "none", "tex": False, "browser": False}
    assert (
        contract_preparation("tests/infra_tests/project/test_public_acceptance_auxiliary.py")["documents"] == "native"
    )
    for module in ("test_latex_texttt_native.py", "test_latex_utils.py"):
        assert contract_preparation("tests/infra_tests/rendering/" + module)["tex"] is True
    assert 'echo "CHROME_EXECUTABLE_PATH=$chrome" >> "$GITHUB_ENV"' in browser["run"]
    assert 'test ! -L "$chrome"' in browser["run"] and "resources.pak" in browser["run"]
    assert "poppler-utils" in tex["run"] and "kpsewhich plainnat.bst" in tex["run"]
    assert not any("texlive-" in step.get("run", "") for step in jobs["test-infra"]["steps"])
    prepare_account = next(
        index
        for index, step in enumerate(contract["steps"])
        if step.get("uses") == "./.github/actions/setup-ci-execution-user"
    )
    assert contract["steps"].index(converter) < contract["steps"].index(tex) < prepare_account
    assert contract["steps"].index(browser) < prepare_account

    # The original command still produces each receipt. Identity preparation
    # precedes it, and independent readable transport follows even a failure.
    for name in ("test-infra", "test-contract"):
        steps = jobs[name]["steps"]
        checkout = next(step for step in steps if step.get("uses", "").startswith("actions/checkout@"))
        assert checkout["with"]["persist-credentials"] is False
        prepare = next(
            index for index, step in enumerate(steps) if step.get("uses") == "./.github/actions/setup-ci-execution-user"
        )
        run = next(index for index, step in enumerate(steps) if "ci_infra" in step.get("run", ""))
        export = next(index for index, step in enumerate(steps) if "ci_execution_user export" in step.get("run", ""))
        upload = next(
            index for index, step in enumerate(steps) if step.get("uses", "").startswith("actions/upload-artifact@")
        )
        assert prepare < run < export < upload
        assert "ci_execution_user run" in steps[run]["run"]
        assert '--state "$RUNNER_TEMP/template-ci-execution/state.json" --' in steps[run]["run"]
        assert steps[export]["if"].startswith("always()")
        assert steps[upload]["with"]["path"] == "${{ env.TEMPLATE_CI_ARTIFACT_DIRECTORY }}/functional-infra/"

    required = yaml.safe_load((ROOT / ".github/workflows/platform-required-acceptance.yml").read_bytes())["jobs"]
    for name in ("root-original", "auxiliary-original"):
        steps = required[name]["steps"]
        prepare = next(step for step in steps if step.get("uses") == "./.github/actions/setup-ci-execution-user")
        if name == "root-original":
            assert prepare["if"] == "runner.os == 'Linux'"
            observation = next(step for step in steps if step.get("name") == "Original complete Root observation")
            assert 'if [ "$RUNNER_OS" = Linux ]' in observation["run"]
            assert 'exec "${root_command[@]}"' in observation["run"]
        else:
            assert prepare["with"]["docker"] == "${{ matrix.docker }}"
            assert required[name]["needs"] == "auxiliary-plan"
            assert required[name]["strategy"]["fail-fast"] is False
            assert required[name]["strategy"]["max-parallel"] == 4
            observation = next(step for step in steps if step.get("id") == "auxiliary")
        assert "ci_execution_user run" in observation["run"]
        assert observation["continue-on-error"] is True
        assert any(
            "ci_execution_user export" in step.get("run", "") and step["if"].startswith("always()") for step in steps
        )


def test_actual_deep_owner_cannot_be_moved_back_into_smoke_or_omitted() -> None:
    for module in (
        "tests/infra_tests/documentation/test_counts_coverage_measurement.py",
        "tests/infra_tests/documentation/test_counts_coverage_support.py",
        "tests/infra_tests/documentation/test_counts_provenance.py",
        "tests/infra_tests/documentation/test_counts_refresh.py",
        "tests/infra_tests/project/test_public_reference.py",
        "tests/infra_tests/project/test_root_wheel_typing.py",
        "tests/infra_tests/project/test_scientific_reference_replay.py",
        "tests/infra_tests/publishing/test_standalone_install_projection.py",
        "tests/infra_tests/reporting/test_native_browser_oracles.py",
        "tests/infra_tests/reporting/test_native_browser_scientific_structure.py",
        "tests/infra_tests/reporting/test_native_hosted_credentials.py",
        "tests/infra_tests/reporting/test_native_pdf_citations.py",
        "tests/infra_tests/reporting/test_native_pdf_math.py",
        "tests/infra_tests/reporting/test_native_pdf_source_witness.py",
        "tests/infra_tests/reporting/test_pdf_raw_natbib_source.py",
    ):
        changed = (module,)
        assert module not in infrastructure_files(ROOT)
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
