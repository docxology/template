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
from orchestration.portable_execution import build_bounded_env, run_bounded_subprocess
from ontology.bindings import load_section_ontology, validate_gnn_ontology
from simulation.logging_utils import RunLogger


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


def test_run_verification_skip_chunks_orders_preflight_and_postflight(tmp_path: Path) -> None:
    calls: list[tuple[str, list[str]]] = []
    full_verification.run_verification(
        tmp_path,
        skip_chunks=True,
        command_runner=lambda project_root, cmd, label, env=None: calls.append((label, cmd)),
    )

    labels = [label for label, _ in calls]
    assert labels[0] == "Compose manuscript sections"
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
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
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


def test_refresh_cache_skips_an_unchanged_generator_fixed_point(tmp_path: Path) -> None:
    calls: list[str] = []
    cache = full_verification._RefreshCache()
    command = ["uv", "run", "python", "scripts", "compose_manuscript.py"]

    def run(_root: Path, _cmd: list[str], label: str) -> None:
        calls.append(label)

    cache.run(tmp_path, command, "first", run)
    cache.run(tmp_path, command, "second", run)

    assert calls == ["first"]


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
