"""
Full-verification run, bounded-subprocess, and generator refresh-cache tests.
"""

from __future__ import annotations
import contextlib
import os
import signal
import sys
import time
from pathlib import Path
import pytest
from orchestration import full_verification
from orchestration.portable_execution import build_bounded_env, run_bounded_subprocess

from _coverage_partition_helpers import _write_coverage_partition_tree


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
