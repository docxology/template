"""Deep modules remain required, isolated, and complementary to baseline smoke."""

import json
import os
import subprocess
from pathlib import Path

import yaml
import pytest

from infrastructure.core.testing.ci_contracts import combined_groups, contract_files
from infrastructure.core.testing.ci_infra import (
    infrastructure_files,
    infrastructure_shards,
    validate_plan,
    validate_shards,
)

ROOT = Path(__file__).resolve().parents[3]


def test_deep_owner_files_are_complementary_without_removing_baseline_smoke() -> None:
    heavy = "tests/infra_tests/project/test_public_reference.py"
    baseline = "tests/infra_tests/project/test_public_source_body_admission.py"
    routine = "tests/infra_tests/core/test_ci_selection.py"
    files = (heavy, baseline, routine)
    assert contract_files(files, (baseline,)) == (heavy,)
    plan = {"infra_shards": [[baseline], [routine]], "contract_modules": [heavy]}
    validate_shards(combined_groups(plan), files)
    assert combined_groups(plan)[-1] == [heavy]


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
        "tests/infra_tests/reporting/test_native_original_launch_correctness.py",
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


_PAPER_NATIVE = (
    "tests/infra_tests/rendering/test_paper_frontmatter_native.py",
    "tests/infra_tests/reporting/test_paper_frontmatter_reconstruction_native.py",
)
_PAPER_PURE = (
    "tests/infra_tests/rendering/test_paper_frontmatter.py",
    "tests/infra_tests/reporting/test_paper_frontmatter_reconstruction.py",
)


def test_paper_compilers_are_required_and_pure_cases_remain_in_smoke() -> None:
    from infrastructure.core.testing.ci_selection import _contract_matrix, infrastructure_selection

    changed = (*_PAPER_PURE, *_PAPER_NATIVE)
    plan = infrastructure_selection(ROOT, {"changed_paths": changed})
    validate_plan(ROOT, plan)
    smoke = {module for shard in plan["infra_shards"] for module in shard}
    assert set(_PAPER_PURE) <= smoke
    assert set(_PAPER_NATIVE).isdisjoint(smoke)
    assert set(plan["contract_modules"]) == set(_PAPER_NATIVE)
    matrix = _contract_matrix(plan["infra_shards"], plan["contract_modules"])["include"]
    assert {row["module"] for row in matrix} == set(_PAPER_NATIVE)
    for row in matrix:
        assert row["documents"] == "converter"
        assert row["tex"] is True and row["browser"] is False
    # A plan that silently omits either compiler module cannot pass CI admission.
    for missing in _PAPER_NATIVE:
        incomplete = {**plan, "contract_modules": [m for m in plan["contract_modules"] if m != missing]}
        with pytest.raises(ValueError, match="deep contract selection"):
            validate_plan(ROOT, incomplete)


@pytest.mark.parametrize(
    "source",
    [
        "infrastructure/core/config/schema.py",
        *[
            f"infrastructure/rendering/{name}.py"
            for name in (
                "_paper_frontmatter",
                "_paper_frontmatter_render",
                "manuscript_discovery",
                "pipeline",
                "core",
                "_combined_exports",
                "_pdf_markdown_combine",
                "_pdf_combined_preamble",
                "pdf_renderer",
                "web_renderer",
                "manuscript_composition",
            )
        ],
        "infrastructure/reporting/native_hydration_reconstruction.py",
        "infrastructure/reporting/native_code_contextual_compare.py",
    ],
)
def test_paper_source_changes_retain_both_compiler_contracts(source: str) -> None:
    from infrastructure.core.testing.ci_selection import infrastructure_selection

    plan = infrastructure_selection(ROOT, {"changed_paths": (source,)})
    validate_plan(ROOT, plan)
    assert set(_PAPER_NATIVE) <= set(plan["contract_modules"])
    assert set(_PAPER_PURE) <= {module for shard in plan["infra_shards"] for module in shard}


def _native_union_gate_script(tmp_path: Path) -> Path:
    """Extract the union gate body from the workflow so the test cannot drift from it."""
    jobs = yaml.safe_load((ROOT / ".github/workflows/platform-required-acceptance.yml").read_bytes())["jobs"]
    step = next(
        step
        for step in jobs["complete"]["steps"]
        if step.get("name") == "Require the complete native cell union before any admission"
    )
    script = tmp_path / "union-gate.sh"
    script.write_text(step["run"], encoding="utf-8")
    return script


def _run_native_union_gate(tmp_path: Path, artifacts: str, cells: str) -> subprocess.CompletedProcess[str]:
    """Run the real gate body with the artifact census it reads from `gh api`."""
    script = _native_union_gate_script(tmp_path)
    # A real `gh` stand-in: it prints the artifact census to stdout, so the
    # workflow's own `> "$RUNNER_TEMP/native-artifacts.txt"` redirect still runs.
    runner = tmp_path / "gh"
    runner.write_text("#!/usr/bin/env bash\ncat <<'ARTIFACTS'\n" + artifacts + "ARTIFACTS\n", encoding="utf-8")
    runner.chmod(0o755)
    matrix = json.dumps({"include": [{"cell": cell} for cell in cells.split()]})
    environment = {
        **os.environ,
        "PATH": f"{tmp_path}{os.pathsep}{os.environ['PATH']}",
        "RUNNER_TEMP": str(tmp_path),
        "GITHUB_REPOSITORY": "docxology/template",
        "GITHUB_RUN_ID": "1",
        "NATIVE_MATRIX": matrix,
        "NATIVE_JOB_RESULT": "success",
    }
    return subprocess.run(["bash", str(script)], capture_output=True, text=True, env=environment, check=False)


def test_native_union_gate_counts_cells_not_their_shard_members(tmp_path: Path) -> None:
    """Each cell uploads a primary index plus its own shards; shards are not cells."""
    artifacts = "\n".join(
        [
            "required-source-native-cell-template_code_project",
            "required-source-native-cell-template_code_project-shard-0000",
            "required-source-native-cell-template_code_project-shard-0001",
            "required-source-native-cell-template_sia",
            "required-source-native-cell-template_sia-shard-0000",
            "required-source-common",
            "",
        ]
    )
    observed = _run_native_union_gate(tmp_path, artifacts, "template_code_project template_sia")
    assert observed.returncode == 0, observed.stdout + observed.stderr
    assert "complete native cell union: 2 of 2" in observed.stdout


def test_native_union_gate_names_a_missing_cell(tmp_path: Path) -> None:
    artifacts = "\n".join(
        [
            "required-source-native-cell-template_code_project",
            "required-source-native-cell-template_code_project-shard-0000",
            "",
        ]
    )
    observed = _run_native_union_gate(tmp_path, artifacts, "template_code_project template_sia")
    assert observed.returncode != 0
    assert "missing native cell artifacts for: template_sia" in observed.stdout


def test_native_union_gate_names_an_undeclared_cell(tmp_path: Path) -> None:
    artifacts = "\n".join(
        [
            "required-source-native-cell-template_code_project",
            "required-source-native-cell-template_sia",
            "required-source-native-cell-template_formal",
            "",
        ]
    )
    observed = _run_native_union_gate(tmp_path, artifacts, "template_code_project template_sia")
    assert observed.returncode != 0
    assert "unexpected native cell artifacts for: template_formal" in observed.stdout


READINESS_ACTION = ROOT / ".github/actions/setup-native-installed-readiness/action.yml"
ACCEPTANCE_WORKFLOW = ROOT / ".github/workflows/platform-required-acceptance.yml"


def test_readiness_action_creates_its_interpreter_before_deriving_cache_scopes() -> None:
    """A scope report must not outrun the `uv sync` that creates `.venv`.

    Negative control for hosted run 41952164694: every one of the 25 native cells
    died in 41-94 seconds with

      line 5: .venv/bin/python: No such file or directory
      ##[error]Process completed with exit code 127

    because a workflow step resolved the offline cache scopes before
    `setup-native-installed-readiness` had run its `uv sync`. No CI job exercises
    this workflow's steps, so `CI Gate` stayed green and the regression reached a
    dispatch.

    The action now derives the scopes itself, after that `uv sync`. This pins the
    order, because the failure mode is invisible to every other gate.
    """
    steps = yaml.safe_load(READINESS_ACTION.read_text(encoding="utf-8"))["runs"]["steps"]
    sync = next(
        (index for index, step in enumerate(steps) if "uv sync --locked" in (step.get("run") or "")),
        None,
    )
    derive = next((index for index, step in enumerate(steps) if step.get("id") == "cache-scopes"), None)
    assert sync is not None, "the readiness action must still create the project environment"
    assert derive is not None, "the readiness action must derive its own offline cache scopes"
    assert sync < derive, (
        "the cache-scope derivation runs before `uv sync` creates `.venv`; "
        "every cell would fail with exit 127 before any native work"
    )
    assert ".venv/bin/python" in (steps[derive].get("run") or "")


def test_acceptance_workflow_never_calls_python_before_the_readiness_action() -> None:
    """The workflow must not repeat the ordering mistake outside the action.

    A workflow step that runs `.venv/bin/python` before
    `setup-native-installed-readiness` cannot work: nothing has created `.venv` at
    that point. The cell lane passes `matrix-cell` and lets the action derive the
    scopes; the roster lanes omit it and receive the full roster.
    """
    workflow = yaml.safe_load(ACCEPTANCE_WORKFLOW.read_text(encoding="utf-8"))
    for job_name, job in workflow["jobs"].items():
        steps = job.get("steps") or []
        readiness = next(
            (
                index
                for index, step in enumerate(steps)
                if str(step.get("uses", "")).endswith("setup-native-installed-readiness")
            ),
            None,
        )
        if readiness is None:
            continue
        for index, step in enumerate(steps):
            body = step.get("run") or ""
            if ".venv/bin/python" not in body:
                continue
            assert index > readiness, (
                f"{job_name}: a step running `.venv/bin/python` precedes "
                "setup-native-installed-readiness, which is what creates it"
            )
    # The cell lane must hand the action the cell, not a pre-resolved scope list.
    cell_job = workflow["jobs"]["native-original-cell"]
    readiness_step = next(
        step for step in cell_job["steps"] if str(step.get("uses", "")).endswith("setup-native-installed-readiness")
    )
    assert readiness_step["with"]["matrix-cell"] == "${{ matrix.cell }}"
