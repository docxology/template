"""RunLogger and small support-module tests."""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import signal
import sys
import time
from pathlib import Path

import pytest

from orchestration import full_verification
from orchestration import semantic_coverage
from orchestration.portable_execution import build_bounded_env, run_bounded_subprocess
from ontology.bindings import load_section_ontology, validate_gnn_ontology
from simulation.logging_utils import RunLogger


def _write_coverage_partition_tree(tmp_path: Path) -> Path:
    """Create a minimal real-file tree satisfying the live coverage partition."""
    live_root = Path(__file__).resolve().parents[1]
    for module in full_verification._all_test_modules(live_root):
        source = live_root / module
        target = tmp_path / module
        target.parent.mkdir(parents=True, exist_ok=True)
        if module == full_verification._SEMANTIC_SHEAF_COVERAGE_MODULE:
            shutil.copyfile(source, target)
        else:
            target.write_text("# coverage partition fixture\n", encoding="utf-8")
    return tmp_path


def _copied_coverage_groups(project_root: Path) -> list[tuple[str, list[str]]]:
    """Return mutable copies of the validated live coverage groups."""
    return [
        (label, list(selectors)) for label, selectors in full_verification._validated_coverage_test_groups(project_root)
    ]


def test_run_logger_emit_and_records(tmp_path: Path) -> None:
    log = RunLogger(tmp_path / "runs.jsonl")
    log.fresh()
    log.emit({"event": "test", "value": 1})
    records = log.records()
    assert len(records) == 1
    assert records[0]["event"] == "test"


def test_run_logger_emit_recreates_missing_parent_after_fresh(tmp_path: Path) -> None:
    log = RunLogger(tmp_path / "logs" / "runs.jsonl")
    log.fresh()
    shutil.rmtree(log.path.parent)

    log.emit({"event": "test", "value": 2})

    assert log.records()[0]["value"] == 2


def test_sheaf_package_exports_public_symbols() -> None:
    from manuscript.sheaf import (
        GENERATED_RENDERERS,
        ImradBlock,
        SectionKind,
        coverage_cell_symbol,
        resolve_track_body,
    )

    assert coverage_cell_symbol("black") == "P"
    assert "section_figures" in GENERATED_RENDERERS
    assert resolve_track_body.__name__ == "resolve_track_body"
    assert ImradBlock is not None
    assert SectionKind is not None


def test_ontology_helpers() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "manuscript" / "sections" / "imrad" / "intro_contributions" / "ontology.yaml"
    terms = load_section_ontology(path)
    assert "location" in terms
    discussion = root / "manuscript" / "sections" / "imrad" / "discussion_outlook" / "ontology.yaml"
    discussion_terms = load_section_ontology(discussion)
    assert discussion_terms["pedagogical_scope"] == "Pedagogical scope"
    gnn = root / "gnn" / "bernoulli_toy.gnn.md"
    assert not validate_gnn_ontology(gnn)


def test_full_verification_run_sets_defaults(tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict] = []

    receipt_keys = (
        "TEMPLATE_PROJECT_TEST_RECEIPT",
        "TEMPLATE_PROJECT_TEST_RUN_ID",
        "TEMPLATE_PROJECT_TEST_PROJECT",
        "TEMPLATE_PROJECT_TEST_COMMAND_SHA256",
    )
    for key in receipt_keys:
        monkeypatch.setenv(key, "outer-only")

    class Result:
        returncode = 0

    def fake_run(cmd, *, cwd, env, text, check):
        calls.append({"cmd": cmd, "cwd": cwd, "env": env, "text": text, "check": check})
        return Result()

    ticks = iter((10.0, 12.5))
    full_verification._run(
        tmp_path,
        ["uv", "run", "pytest", "-q"],
        "Smoke",
        env={"EXTRA_FLAG": "1"},
        process_runner=fake_run,
        clock=lambda: next(ticks),
    )

    assert calls[0]["cmd"] == ["uv", "run", "pytest", "-q"]
    assert calls[0]["cwd"] == tmp_path
    assert calls[0]["env"]["MPLBACKEND"] == "Agg"
    assert calls[0]["env"]["PYTHONUNBUFFERED"] == "1"
    assert calls[0]["env"]["TEMPLATE_ACTIVE_INFERENCE_FIXED_POINT_PASSES"] == "2"
    assert calls[0]["env"]["EXTRA_FLAG"] == "1"
    assert not any(key in calls[0]["env"] for key in receipt_keys)
    assert "Smoke" in capsys.readouterr().out


def test_full_verification_run_raises_on_failure(tmp_path: Path) -> None:
    class Result:
        returncode = 7

    with pytest.raises(RuntimeError, match="Explode failed"):
        full_verification._run(
            tmp_path,
            ["false"],
            "Explode",
            process_runner=lambda *args, **kwargs: Result(),
            clock=lambda: 1.0,
        )


def test_full_verification_run_reports_bounded_stdout_and_stderr(tmp_path: Path) -> None:
    stdout = '{"outputs": {"artifact_provenance_schema": false}}'
    stderr = "warning: VIRTUAL_ENV does not match the project environment"
    child_code = f"import sys; print({stdout!r}); print({stderr!r}, file=sys.stderr); raise SystemExit(1)"

    with pytest.raises(RuntimeError) as exc_info:
        full_verification._run(tmp_path, [sys.executable, "-c", child_code], "Output gate")

    message = str(exc_info.value)
    assert f"[stdout]\n{stdout}" in message
    assert f"[stderr]\n{stderr}" in message


def test_failure_detail_tail_bounds_each_labeled_stream() -> None:
    stdout_tail = "validator-false-key"
    stderr_tail = "uv-warning"
    detail = full_verification._bounded_failure_detail(
        command_error="",
        stdout="discarded-stdout-prefix" + "x" * 5_000 + stdout_tail,
        stderr="discarded-stderr-prefix" + "y" * 5_000 + stderr_tail,
    )

    assert "[stdout]" in detail
    assert "[stderr]" in detail
    assert stdout_tail in detail
    assert stderr_tail in detail
    assert "discarded-stdout-prefix" not in detail
    assert "discarded-stderr-prefix" not in detail


@pytest.mark.skipif(os.name == "nt", reason="detached POSIX session regression")
def test_portable_timeout_kills_detached_descendant(tmp_path: Path) -> None:
    marker = tmp_path / "detached-child-finished"
    pid_file = tmp_path / "detached-child.pid"
    child_code = (
        f"import pathlib,time; time.sleep(3.0); pathlib.Path({str(marker)!r}).write_text('leaked', encoding='utf-8')"
    )
    parent_code = (
        "import pathlib,subprocess,sys,time; "
        "child=subprocess.Popen([sys.executable, '-c', sys.argv[1]], start_new_session=True); "
        "pathlib.Path(sys.argv[2]).write_text(str(child.pid), encoding='utf-8'); "
        "time.sleep(30)"
    )
    child_pid: int | None = None
    try:
        result = run_bounded_subprocess(
            [sys.executable, "-c", parent_code, child_code, str(pid_file)],
            cwd=tmp_path,
            env=build_bounded_env(),
            timeout=1.5,
        )
        assert result.timed_out
        child_pid = int(pid_file.read_text(encoding="utf-8"))
        time.sleep(1.8)
        assert not marker.exists()
    finally:
        if child_pid is not None:
            with contextlib.suppress(ProcessLookupError):
                os.kill(child_pid, signal.SIGKILL)


@pytest.mark.skipif(os.name == "nt", reason="detached POSIX session regression")
@pytest.mark.parametrize("capture_output", [True, False])
def test_portable_early_root_exit_cannot_leak_reparented_child(
    tmp_path: Path,
    capture_output: bool,
) -> None:
    marker = tmp_path / "reparented-child-finished"
    child_code = (
        f"import pathlib,time; time.sleep(1.5); pathlib.Path({str(marker)!r}).write_text('leaked', encoding='utf-8')"
    )
    parent_code = "import subprocess,sys; subprocess.Popen([sys.executable, '-c', sys.argv[1]], start_new_session=True)"

    started = time.monotonic()
    run_bounded_subprocess(
        [sys.executable, "-c", parent_code, child_code],
        cwd=tmp_path,
        env=build_bounded_env(),
        timeout=0.3,
        capture_output=capture_output,
    )
    assert time.monotonic() - started < 1.5
    time.sleep(1.6)
    assert not marker.exists()


def test_coverage_command_defers_threshold_until_final_chunk() -> None:
    partial = full_verification._coverage_command(["tests/test_one.py"], append=False, final=False)
    final = full_verification._coverage_command(["tests/test_two.py"], append=True, final=True)

    assert "--cov-fail-under=0" in partial
    assert "--cov-fail-under=90" not in partial
    assert "--cov-fail-under=90" in final
    assert partial[:3] == [sys.executable, "-m", "pytest"]


def test_coverage_command_emits_machine_readable_junit_when_requested(tmp_path: Path) -> None:
    junit = tmp_path / "coverage.xml"
    evidence = tmp_path / "coverage-evidence.json"

    command = full_verification._coverage_command(
        ["tests/test_one.py"],
        append=False,
        final=True,
        junit_path=junit,
        evidence_path=evidence,
    )

    assert f"--junitxml={junit}" in command
    assert f"--template-test-evidence={evidence}" in command


def test_project_test_receipt_aggregates_final_coverage_groups_once(tmp_path: Path) -> None:
    first = tmp_path / "first.xml"
    second = tmp_path / "second.xml"
    first.write_text(
        '<testsuites><testsuite tests="3" failures="0" errors="0" skipped="1" time="0.1"/></testsuites>',
        encoding="utf-8",
    )
    second.write_text(
        '<testsuites><testsuite tests="2" failures="0" errors="0" skipped="0" time="0.1"/></testsuites>',
        encoding="utf-8",
    )

    assert full_verification._junit_outcomes([first, second]) == {
        "passed": 4,
        "failed": 0,
        "skipped": 1,
        "total": 5,
        "collection_errors": 0,
    }

    first_evidence = tmp_path / "first-evidence.json"
    second_evidence = tmp_path / "second-evidence.json"
    first_evidence.write_text(
        json.dumps(
            {
                "schema_version": "template-active-inference/pytest-evidence/1",
                "warnings": 2,
                "discovery_count": 4,
            }
        ),
        encoding="utf-8",
    )
    second_evidence.write_text(
        json.dumps(
            {
                "schema_version": "template-active-inference/pytest-evidence/1",
                "warnings": 1,
                "discovery_count": 2,
            }
        ),
        encoding="utf-8",
    )
    assert full_verification._pytest_evidence([first_evidence, second_evidence]) == (3, 6)


def test_profile_args_are_additive_and_keep_live_services_opt_in() -> None:
    quick = full_verification._profile_marker_args("quick")
    release = full_verification._profile_marker_args("release")
    exhaustive = full_verification._profile_marker_args("exhaustive")

    assert quick[0] == release[0] == exhaustive[0] == "-m"
    assert "not slow" in quick[1]
    assert "not slow" not in release[1]
    assert "not long_running" in release[1]
    assert "not long_running" not in exhaustive[1]
    assert all("not requires_ollama" in expression[1] for expression in (quick, release, exhaustive))
    assert all("not private_project" in expression[1] for expression in (quick, release, exhaustive))
    assert all("not external_fixture" in expression[1] for expression in (quick, release, exhaustive))


def test_chunked_coverage_records_empty_bounded_profile_slice(tmp_path: Path) -> None:
    """A filtered all-long group is skipped without weakening later coverage."""
    calls: list[str] = []
    groups = [
        ("ordinary checks", ["tests/test_ordinary.py"]),
        ("all-long checks", ["tests/test_long_running.py"]),
        ("final checks", ["tests/test_final.py"]),
    ]

    def command_runner(root: Path, command: list[str], label: str) -> None:
        del root, command
        calls.append(label)
        if label == "Coverage pass: all-long checks":
            raise RuntimeError(
                "Coverage pass: all-long checks failed with return code 5:\n"
                "collected 4 items / 4 deselected / 0 selected"
            )

    junit_paths, evidence_paths = full_verification._run_chunked_coverage(
        tmp_path,
        groups,
        profile="release",
        receipt_context=(tmp_path / "receipt.json", "run-id", "project", "command-sha"),
        command_runner=command_runner,
    )

    assert calls == [f"Coverage pass: {label}" for label, _ in groups]
    empty_junit = junit_paths[1]
    assert 'name="all-long checks"' in empty_junit.read_text(encoding="utf-8")
    assert 'tests="0"' in empty_junit.read_text(encoding="utf-8")
    assert json.loads(evidence_paths[1].read_text(encoding="utf-8")) == {
        "discovery_count": 0,
        "schema_version": "template-active-inference/pytest-evidence/1",
        "warnings": 0,
    }


def test_coverage_only_uses_complete_release_partition(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    calls: list[tuple[str, list[str]]] = []

    full_verification.run_coverage_only(
        project_root,
        profile="release",
        command_runner=lambda root, cmd, label: calls.append((label, cmd)),
    )

    expected_groups = full_verification._validated_coverage_test_groups(project_root)
    assert [label for label, _ in calls] == [f"Coverage pass: {label}" for label, _ in expected_groups]
    assert [len(selectors) for _, selectors in expected_groups] == [4, 3, 11, 1, 2, 1, 29, 7, 7, 8, 7, 13]
    assert expected_groups[2] == (
        "Roadmap and sheaf consolidation checks",
        [
            "tests/test_roadmap_promotion.py",
            *sorted(str(path.relative_to(project_root)) for path in (project_root / "tests").glob("test_sheaf_*.py")),
        ],
    )
    assert len(expected_groups[2][1]) == 11
    assert expected_groups[3] == (
        "Canonical sheaf negative-control checks",
        ["tests/test_track_consolidation_negative.py"],
    )
    assert expected_groups[4] == (
        "Sheaf consolidation surface checks",
        [
            "tests/test_track_consolidation_surface.py",
            "tests/test_track_consolidation_support_contracts.py",
        ],
    )
    assert expected_groups[5] == (
        "Fixed-point settlement checks",
        ["tests/test_fixed_point_direct.py"],
    )
    assert expected_groups[6] == (
        "Analytical, figure, and formal checks",
        [
            "tests/test_aggregate_forgery_controls.py",
            "tests/test_analytical_guards.py",
            "tests/test_bernoulli_toy.py",
            "tests/test_claim_ledger_direct.py",
            "tests/test_coverage_pipeline.py",
            "tests/test_cue_tmaze_model.py",
            "tests/test_decomposition.py",
            "tests/test_dirichlet_learning.py",
            "tests/test_efe_decomposition.py",
            "tests/test_efe_lean_identity.py",
            "tests/test_extension_scripts.py",
            "tests/test_figure_io_direct.py",
            "tests/test_figure_style.py",
            "tests/test_figures.py",
            "tests/test_figures_sheaf_direct.py",
            "tests/test_formal_interop_direct.py",
            "tests/test_free_energy.py",
            "tests/test_gnn.py",
            "tests/test_graph_world.py",
            "tests/test_helpers_direct.py",
            "tests/test_image_content_hash.py",
            "tests/test_integration_audit_modularity.py",
            "tests/test_integrity_remediations.py",
            "tests/test_invariants.py",
            "tests/test_joint_dist.py",
            "tests/test_layers_report.py",
            "tests/test_lean_boundary.py",
            "tests/test_lean_gate.py",
            "tests/test_lean_gate_direct.py",
        ],
    )
    assert expected_groups[7] == (
        "Manuscript, pipeline, precision, and configuration checks",
        [
            "tests/test_manuscript_hydrate.py",
            "tests/test_manuscript_refresh_direct.py",
            "tests/test_manuscript_variables.py",
            "tests/test_pipeline_artifacts.py",
            "tests/test_pipeline_manifest.py",
            "tests/test_precision_sweep.py",
            "tests/test_pymdp_config.py",
        ],
    )
    assert expected_groups[8] == (
        "Rendering, scholarship, and semantic validation checks",
        [
            "tests/test_render_pdf.py",
            "tests/test_scholarship_direct.py",
            "tests/test_self_contained.py",
            "tests/test_semantic_certificate_direct.py",
            "tests/test_semantic_extensions.py",
            "tests/test_semantic_issues_direct.py",
            "tests/test_semantic_issues_more_direct.py",
        ],
    )
    assert expected_groups[9] == (
        "Semantic sheaf certificate integrity checks",
        [
            "tests/test_semantic_sheaf.py::test_semantic_certificate_covers_tracks_symbols_and_variables",
            "tests/test_semantic_sheaf.py::test_semantic_certificate_key_surface_is_stable",
            "tests/test_semantic_sheaf.py::test_semantic_gluing_rejects_wrong_si_ontology",
            "tests/test_semantic_sheaf.py::test_semantic_certificate_is_written_as_generated_artifact",
            "tests/test_semantic_sheaf.py::test_semantic_outputs_settle_contract_and_staleness_artifacts",
            "tests/test_semantic_sheaf.py::test_semantic_gluing_rejects_stale_saved_certificate",
            "tests/test_semantic_sheaf.py::test_semantic_validators_reject_forged_omitted_certificate_fields",
            "tests/test_semantic_sheaf.py::test_semantic_gluing_rejects_missing_or_malformed_saved_certificate",
        ],
    )
    assert expected_groups[10] == (
        "Semantic dependency, evidence, and manuscript checks",
        [
            "tests/test_semantic_sheaf.py::test_dependency_graph_rejects_required_artifact_without_configured_producer",
            "tests/test_semantic_sheaf.py::test_dependency_graph_distinguishes_missing_from_unconfigured_existing",
            "tests/test_semantic_sheaf.py::test_semantic_gluing_rejects_mutated_policy_posterior",
            "tests/test_semantic_sheaf.py::test_semantic_certificate_records_lean_graph_world_topology_witnesses",
            "tests/test_semantic_sheaf.py::test_typed_claim_evidence_rejects_wrong_expected_value",
            "tests/test_semantic_sheaf.py::test_typed_claim_evidence_supports_structured_predicates",
            "tests/test_semantic_sheaf.py::test_validate_manuscript_checks_semantic_certificate",
        ],
    )
    assert expected_groups[11] == (
        "Simulation, support, and visualization checks",
        [
            "tests/test_si_policy_direct.py",
            "tests/test_si_runner.py",
            "tests/test_si_statistics.py",
            "tests/test_simulation_invariants.py",
            "tests/test_simulation_invariants_direct.py",
            "tests/test_supplemental_direct.py",
            "tests/test_support_modules.py",
            "tests/test_support_primitives_direct.py",
            "tests/test_sweep_io.py",
            "tests/test_toy_sweep_builders_direct.py",
            "tests/test_toy_sweep_direct.py",
            "tests/test_typography_contract.py",
            "tests/test_visualization_audit_direct.py",
        ],
    )
    assert "tests/test_fixed_point_direct.py" not in expected_groups[-1][1]
    semantic_selectors = full_verification._semantic_sheaf_test_selectors(project_root)
    assert [*expected_groups[9][1], *expected_groups[10][1]] == semantic_selectors

    planned_selectors: list[str] = []
    for index, (_, command) in enumerate(calls):
        coverage_index = command.index("--cov=src")
        planned_selectors.extend(command[3:coverage_index])
        marker_index = command.index("-m", 3)
        marker = command[marker_index + 1]
        assert "not long_running" in marker
        assert "not private_project" in marker
        assert "not external_fixture" in marker
        assert ("--cov-append" in command) is (index > 0)
        assert ("--cov-fail-under=90" in command) is (index == len(calls) - 1)
        assert ("--cov-report=term-missing" in command) is (index == len(calls) - 1)
        assert ("--durations=20" in command) is (index == len(calls) - 1)
        assert ("--cov-fail-under=0" in command) is (index < len(calls) - 1)
        assert ("--cov-report=" in command) is (index < len(calls) - 1)

    expected_modules = set(full_verification._all_test_modules(project_root))
    planned_ordinary_modules = [selector for selector in planned_selectors if "::" not in selector]
    assert sorted(planned_ordinary_modules) == sorted(
        expected_modules - {full_verification._SEMANTIC_SHEAF_COVERAGE_MODULE}
    )
    assert [selector for selector in planned_selectors if "::" in selector] == semantic_selectors
    assert len(planned_selectors) == len(set(planned_selectors))

    receipt = tmp_path / "test-receipt.json"
    receipt_calls: list[tuple[str, list[str]]] = []
    junit_paths, evidence_paths = full_verification._run_chunked_coverage(
        project_root,
        expected_groups,
        profile="release",
        receipt_context=(receipt, "run-id", "templates/template_active_inference", "command-sha"),
        command_runner=lambda root, cmd, label: receipt_calls.append((label, cmd)),
    )
    assert junit_paths == [tmp_path / f"coverage-{index:02d}.xml" for index in range(12)]
    assert evidence_paths == [tmp_path / f"coverage-{index:02d}-evidence.json" for index in range(12)]
    assert [label for label, _ in receipt_calls] == [f"Coverage pass: {label}" for label, _ in expected_groups]
    for index, (_, command) in enumerate(receipt_calls):
        assert f"--junitxml={junit_paths[index]}" in command
        assert f"--template-test-evidence={evidence_paths[index]}" in command


def test_semantic_selector_partition_rejects_missing_selector() -> None:
    project_root = Path(__file__).resolve().parents[1]
    groups = _copied_coverage_groups(project_root)
    groups[9][1].pop()

    with pytest.raises(RuntimeError, match="missing_semantic_selectors"):
        full_verification._validate_coverage_test_groups(project_root, groups)


def test_semantic_selector_partition_rejects_duplicate_selector() -> None:
    project_root = Path(__file__).resolve().parents[1]
    groups = _copied_coverage_groups(project_root)
    groups[10][1].append(groups[9][1][0])

    with pytest.raises(RuntimeError, match="duplicates"):
        full_verification._validate_coverage_test_groups(project_root, groups)


def test_semantic_selector_partition_rejects_unexpected_selector() -> None:
    project_root = Path(__file__).resolve().parents[1]
    groups = _copied_coverage_groups(project_root)
    groups[10][1].append("tests/test_semantic_sheaf.py::test_unregistered_dynamic_case")

    with pytest.raises(RuntimeError, match="unexpected_semantic_selectors"):
        full_verification._validate_coverage_test_groups(project_root, groups)


def test_semantic_selector_partition_rejects_bare_module_overlap() -> None:
    project_root = Path(__file__).resolve().parents[1]
    groups = _copied_coverage_groups(project_root)
    groups[9][1].append(full_verification._SEMANTIC_SHEAF_COVERAGE_MODULE)

    with pytest.raises(RuntimeError, match="semantic_bare_module"):
        full_verification._validate_coverage_test_groups(project_root, groups)


@pytest.mark.parametrize(
    ("mutation", "detail"),
    [
        ("missing", "missing_modules"),
        ("duplicate", "duplicates"),
        ("unexpected", "unexpected_modules"),
        ("foreign_node", "unexpected_node_selectors"),
        ("empty", "empty"),
    ],
)
def test_ordinary_module_partition_rejects_nonexact_coverage(mutation: str, detail: str) -> None:
    project_root = Path(__file__).resolve().parents[1]
    groups = _copied_coverage_groups(project_root)
    if mutation == "missing":
        groups[0][1].pop()
    elif mutation == "duplicate":
        groups[0][1].append(groups[0][1][0])
    elif mutation == "unexpected":
        groups[0][1].append("tests/test_unregistered_module.py")
    elif mutation == "foreign_node":
        groups[0][1].append("tests/test_support_modules.py::test_unregistered_node")
    else:
        groups[0][1].clear()

    with pytest.raises(RuntimeError, match=detail):
        full_verification._validate_coverage_test_groups(project_root, groups)


@pytest.mark.parametrize(
    ("source", "detail"),
    [
        ("class TestGenerated:\n    def test_case(self):\n        pass\n", "ClassDef"),
        (
            "import pytest\n@pytest.mark.parametrize('value', [1, 2])\ndef test_case(value):\n    pass\n",
            "parametrized test",
        ),
        ("def pytest_generate_tests(metafunc):\n    pass\ndef test_case():\n    pass\n", "pytest_generate_tests"),
        (
            "def _register():\n    globals()['test_dynamic'] = lambda: None\n_register()\n",
            "top-level helper function",
        ),
        ("globals()['test_dynamic'] = lambda: None\n", "unsupported top-level assignment"),
        ("(test_dynamic := lambda: None)\n", "unsupported top-level Expr"),
        ("from helper import *\n", "unsupported import"),
        ("from helper import fn as testCase\n", "unsupported import"),
        ("from helper import Case as TestCase\n", "unsupported import"),
        ("from helper import apparently_safe\n", "unsupported import"),
        ("import json as json_module\n", "unsupported import"),
        ("for name in ['test_dynamic']:\n    globals()[name] = lambda: None\n", "unsupported top-level For"),
        ("with open('fixture') as handle:\n    test_dynamic = handle.read\n", "unsupported top-level With"),
        ("if True:\n    def test_dynamic():\n        pass\n", "unsupported top-level If"),
        ("import pytest\n@pytest.mark.slow\ndef test_case():\n    pass\n", "decorated test"),
        ("async def test_case():\n    pass\n", "AsyncFunctionDef"),
        ("test_dynamic = lambda: None\n", "unsupported top-level assignment"),
        ("def test_case():\n    yield 1\n", "generator-style test"),
        ("import pytest\npytestmark = pytest.mark.parametrize('value', [1])\n", "top-level assignment"),
        ("def test_case():\n    pass\n", "pytestmark assignments"),
        (
            "import pytest\n"
            "pytestmark = [pytest.mark.slow, pytest.mark.requires_gate_artifacts]\n"
            "pytestmark = [pytest.mark.slow, pytest.mark.requires_gate_artifacts]\n"
            "def test_case():\n    pass\n",
            "pytestmark assignments",
        ),
        ("import pytest\npytestmark = [pytest.mark.slow, pytest.mark.requires_gate_artifacts]\n", "no supported"),
        ("def test_broken(:\n    pass\n", "cannot parse"),
    ],
)
def test_semantic_selector_derivation_rejects_unsupported_collection_forms(
    tmp_path: Path,
    source: str,
    detail: str,
) -> None:
    semantic_path = tmp_path / full_verification._SEMANTIC_SHEAF_COVERAGE_MODULE
    semantic_path.parent.mkdir(parents=True)
    semantic_path.write_text(source, encoding="utf-8")

    with pytest.raises(RuntimeError, match=detail):
        full_verification._semantic_sheaf_test_selectors(tmp_path)


def test_semantic_selector_derivation_accepts_static_top_level_tests(tmp_path: Path) -> None:
    semantic_path = tmp_path / full_verification._SEMANTIC_SHEAF_COVERAGE_MODULE
    semantic_path.parent.mkdir(parents=True)
    semantic_path.write_text(
        "\n".join(
            [
                '"""Static semantic test fixture."""',
                "from pathlib import Path",
                "import pytest",
                "pytestmark = [pytest.mark.slow, pytest.mark.requires_gate_artifacts]",
                "def test_first(tmp_path: Path):",
                "    assert tmp_path.name",
                "def test_second():",
                "    def helper():",
                "        return True",
                "    assert helper()",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert full_verification._semantic_sheaf_test_selectors(tmp_path) == [
        "tests/test_semantic_sheaf.py::test_first",
        "tests/test_semantic_sheaf.py::test_second",
    ]


def test_semantic_selector_import_allowlist_cannot_be_rebound(tmp_path: Path) -> None:
    signature = ("import", "", 0, (("subprocess", None),))
    assert not hasattr(semantic_coverage, "_ALLOWED_IMPORTS")
    semantic_coverage._ALLOWED_IMPORTS = frozenset({signature})
    try:
        semantic_path = tmp_path / full_verification._SEMANTIC_SHEAF_COVERAGE_MODULE
        semantic_path.parent.mkdir(parents=True)
        semantic_path.write_text(
            "import subprocess\n"
            "import pytest\n"
            "pytestmark = [pytest.mark.slow, pytest.mark.requires_gate_artifacts]\n"
            "def test_case():\n"
            "    assert subprocess.__name__\n",
            encoding="utf-8",
        )
        with pytest.raises(RuntimeError, match="unsupported import"):
            full_verification._semantic_sheaf_test_selectors(tmp_path)
    finally:
        del semantic_coverage._ALLOWED_IMPORTS


def test_both_coverage_entry_points_fail_closed_on_unsupported_semantic_source(tmp_path: Path) -> None:
    project_root = _write_coverage_partition_tree(tmp_path)
    semantic_path = project_root / full_verification._SEMANTIC_SHEAF_COVERAGE_MODULE
    semantic_path.write_text("class TestUnsupported:\n    def test_case(self):\n        pass\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="ClassDef"):
        full_verification.run_coverage_only(
            project_root,
            profile="release",
            command_runner=lambda *_args, **_kwargs: None,
        )
    with pytest.raises(RuntimeError, match="ClassDef"):
        full_verification.run_verification(
            project_root,
            skip_chunks=True,
            command_runner=lambda *_args, **_kwargs: None,
        )


def test_command_timeout_policy_is_narrowly_scoped_to_fixed_point_coverage() -> None:
    project_root = Path(__file__).resolve().parents[1]
    groups = full_verification._validated_coverage_test_groups(project_root)

    for label, _ in groups:
        command_label = f"Coverage pass: {label}"
        expected = 2400 if label == "Fixed-point settlement checks" else 1800
        assert full_verification._command_timeout_seconds(command_label) == expected

    assert full_verification._command_timeout_seconds("Fixed-point settlement checks") == 1800
    assert full_verification._command_timeout_seconds("Coverage pass: fixed-point settlement checks") == 1800
    assert full_verification._command_timeout_seconds("Coverage pass: Canonical sheaf negative-control checks") == 1800
    assert full_verification._command_timeout_seconds("Coverage pass: Sheaf consolidation surface checks") == 1800
    assert full_verification._command_timeout_seconds("Coverage pass: Analytical, figure, and formal checks") == 1800
    assert (
        full_verification._command_timeout_seconds(
            "Coverage pass: Manuscript, pipeline, precision, and configuration checks"
        )
        == 1800
    )
    assert (
        full_verification._command_timeout_seconds(
            "Coverage pass: Rendering, scholarship, and semantic validation checks"
        )
        == 1800
    )
    assert (
        full_verification._command_timeout_seconds("Coverage pass: Semantic sheaf certificate integrity checks") == 1800
    )
    assert (
        full_verification._command_timeout_seconds(
            "Coverage pass: Semantic dependency, evidence, and manuscript checks"
        )
        == 1800
    )
    assert (
        full_verification._command_timeout_seconds("Coverage pass: semantic sheaf certificate integrity checks") == 1800
    )
    assert (
        full_verification._command_timeout_seconds("Coverage pass: Simulation, support, and visualization checks")
        == 1800
    )
    assert full_verification._command_timeout_seconds("Generate canonical sheaf tracks") == 1800


def test_run_verification_skip_chunks_orders_preflight_and_postflight(tmp_path: Path) -> None:
    calls: list[tuple[str, list[str]]] = []
    project_root = _write_coverage_partition_tree(tmp_path)
    full_verification.run_verification(
        project_root,
        skip_chunks=True,
        command_runner=lambda project_root, cmd, label, env=None: calls.append((label, cmd)),
    )

    labels = [label for label, _ in calls]
    assert labels[0] == "Compose manuscript sections"
    assert "Validate compose contracts" in labels
    assert "Simulate SI T-maze" in labels
    assert "Generate validation spine" in labels
    assert "Generate canonical sheaf tracks" in labels
    assert "Focused contract and infrastructure checks" not in labels
    assert "Full suite coverage pass" not in labels
    assert "Coverage pass: Focused contract and infrastructure checks" in labels
    first_coverage_cmd = dict(calls)["Coverage pass: Focused contract and infrastructure checks"]
    second_coverage_cmd = dict(calls)["Coverage pass: Gate and manuscript-focused checks"]
    assert "--cov=src" in first_coverage_cmd
    assert "--cov-append" not in first_coverage_cmd
    assert "--cov-append" in second_coverage_cmd


def test_run_verification_can_use_legacy_monolithic_coverage(tmp_path: Path) -> None:
    calls: list[tuple[str, list[str]]] = []
    full_verification.run_verification(
        tmp_path,
        skip_chunks=True,
        monolithic_coverage=True,
        command_runner=lambda project_root, cmd, label, env=None: calls.append((label, cmd)),
    )

    labels = [label for label, _ in calls]
    assert "Coverage pass: Focused contract and infrastructure checks" not in labels
    assert "Full suite coverage pass" in labels
    coverage_cmd = dict(calls)["Full suite coverage pass"]
    assert coverage_cmd[-1] == "--maxfail=1"


def test_run_verification_includes_chunked_sheaf_modules(tmp_path: Path) -> None:
    _write_coverage_partition_tree(tmp_path)
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(exist_ok=True)
    sheaf_path = tests_dir / "test_sheaf_alpha.py"
    sheaf_path.write_text("", encoding="utf-8")
    calls: list[tuple[str, list[str]]] = []
    full_verification.run_verification(
        tmp_path,
        skip_chunks=False,
        command_runner=lambda project_root, cmd, label, env=None: calls.append((label, cmd)),
    )

    chunks = dict(calls)
    assert "Focused contract and infrastructure checks" in chunks
    assert "Gate and manuscript-focused checks" in chunks
    roadmap_cmd = chunks["Roadmap and sheaf consolidation checks"]
    assert str(sheaf_path.relative_to(tmp_path)) in roadmap_cmd
    assert chunks["Canonical sheaf negative-control checks"] == [
        "uv",
        "run",
        "pytest",
        "tests/test_track_consolidation_negative.py",
        "-q",
    ]
    assert chunks["Sheaf consolidation surface checks"] == [
        "uv",
        "run",
        "pytest",
        "tests/test_track_consolidation_surface.py",
        "tests/test_track_consolidation_support_contracts.py",
        "-q",
    ]


def test_refresh_cache_skips_an_unchanged_generator_fixed_point(tmp_path: Path) -> None:
    calls: list[str] = []
    cache = full_verification._RefreshCache()
    command = ["uv", "run", "python", "scripts", "compose_manuscript.py"]

    def run(_root: Path, _cmd: list[str], label: str) -> None:
        calls.append(label)

    cache.run(tmp_path, command, "first", run)
    cache.run(tmp_path, command, "second", run)

    assert calls == ["first"]


@pytest.mark.parametrize("observer_flag", ["--check", "--list-tracks", "--validate-only"])
def test_refresh_cache_never_skips_generator_observer_commands(tmp_path: Path, observer_flag: str) -> None:
    calls: list[str] = []
    cache = full_verification._RefreshCache()
    command = ["uv", "run", "python", "scripts/compose_manuscript.py", observer_flag]

    cache.run(tmp_path, command, "first", lambda _root, _cmd, label: calls.append(label))
    cache.run(tmp_path, command, "second", lambda _root, _cmd, label: calls.append(label))

    assert full_verification._generator_name(command) is None
    assert calls == ["first", "second"]


def test_refresh_cache_runs_validate_compose_after_unchanged_compose(tmp_path: Path) -> None:
    calls: list[str] = []
    cache = full_verification._RefreshCache()
    compose = ["uv", "run", "python", "scripts/compose_manuscript.py"]
    validate = [*compose, "--validate-only", "--strict"]

    cache.run(tmp_path, compose, "Compose manuscript sections", lambda _root, _cmd, label: calls.append(label))
    cache.run(tmp_path, validate, "Validate compose contracts", lambda _root, _cmd, label: calls.append(label))

    assert full_verification._generator_name(validate) is None
    assert calls == ["Compose manuscript sections", "Validate compose contracts"]


def test_refresh_cache_invalidates_after_a_generator_input_or_output_changes(tmp_path: Path) -> None:
    calls: list[str] = []
    cache = full_verification._RefreshCache()
    command = ["uv", "run", "python", "scripts", "z_generate_manuscript_variables.py"]

    def run(root: Path, _cmd: list[str], label: str) -> None:
        calls.append(label)
        target = root / "output" / "data" / "variables.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(len(calls)), encoding="utf-8")

    cache.run(tmp_path, command, "first", run)
    (tmp_path / "input.txt").write_text("changed", encoding="utf-8")
    cache.run(tmp_path, command, "second", run)
    cache.run(tmp_path, command, "third", run)

    assert calls == ["first", "second"]


def test_refresh_cache_receipt_records_skips_and_reduction_target(tmp_path: Path) -> None:
    ticks = iter((10.0, 12.0))
    cache = full_verification._RefreshCache(clock=lambda: next(ticks))
    command = ["uv", "run", "python", "scripts", "compose_manuscript.py"]
    calls: list[str] = []

    cache.run(tmp_path, command, "first", lambda _root, _cmd, label: calls.append(label))
    cache.run(tmp_path, command, "second", lambda _root, _cmd, label: calls.append(label))

    receipt = cache.receipt(baseline_seconds=3.0)
    assert calls == ["first"]
    assert receipt["schema_version"] == "template-active-inference/refresh-receipt/1"
    assert receipt["target_met"] is True
    assert receipt["events"][1]["action"] == "skipped"
