"""
Full-verification run, bounded-subprocess, and generator refresh-cache tests.
"""

from __future__ import annotations
import contextlib
import os
import signal
import sys
import time
import subprocess
import json
import venv
import shutil
import importlib.util
import marshal
import struct
from pathlib import Path
import pytest
from orchestration import full_verification, verification_refresh
from orchestration.portable_execution import build_bounded_env, run_bounded_subprocess
from orchestration.verification_execution import (
    VerificationCommandFailed,
    VerificationDeadlineExceeded,
    VerificationRuntimeUnavailable,
    selected_verification_python,
    verification_deadline,
)

from _coverage_partition_helpers import _write_coverage_partition_tree


def _script_command(root: Path, source: str, *, arguments: tuple[str, ...] = ()) -> list[str]:
    script = root / "scripts/command.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(source + "\n")
    return [sys.executable, str(script), *arguments]


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
        [sys.executable, "-m", "pytest", "-q"],
        "Smoke",
        env={"EXTRA_FLAG": "1"},
        process_runner=fake_run,
        clock=lambda: next(ticks),
    )

    assert calls[0]["cmd"] == [sys.executable, "-m", "pytest", "-q"]
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


@pytest.mark.timeout(90)
def test_full_verification_run_reports_bounded_stdout_and_stderr(tmp_path: Path) -> None:
    stdout = '{"outputs": {"artifact_provenance_schema": false}}'
    stderr = "warning: VIRTUAL_ENV does not match the project environment"
    child_code = f"import sys; print({stdout!r}); print({stderr!r}, file=sys.stderr); raise SystemExit(1)"

    with pytest.raises(RuntimeError) as exc_info:
        full_verification._run(tmp_path, _script_command(tmp_path, child_code), "Output gate")

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


def test_run_verification_can_use_monolithic_coverage(tmp_path: Path) -> None:
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
        sys.executable,
        "-m",
        "pytest",
        "tests/test_track_consolidation_negative.py",
        "-q",
    ]
    assert chunks["Sheaf consolidation surface checks"] == [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_track_consolidation_surface.py",
        "tests/test_track_consolidation_support_contracts.py",
        "-q",
    ]


def test_refresh_cache_skips_an_unchanged_generator_fixed_point(tmp_path: Path) -> None:
    calls: list[str] = []
    cache = verification_refresh.RefreshCache()
    command = ["uv", "run", "python", "scripts", "compose_manuscript.py"]

    def run(_root: Path, _cmd: list[str], label: str) -> None:
        calls.append(label)

    cache.run(tmp_path, command, "first", run)
    cache.run(tmp_path, command, "second", run)

    assert calls == ["first"]


@pytest.mark.parametrize("observer_flag", ["--check", "--list-tracks", "--validate-only"])
def test_refresh_cache_never_skips_generator_observer_commands(tmp_path: Path, observer_flag: str) -> None:
    calls: list[str] = []
    cache = verification_refresh.RefreshCache()
    command = ["uv", "run", "python", "scripts/compose_manuscript.py", observer_flag]

    cache.run(tmp_path, command, "first", lambda _root, _cmd, label: calls.append(label))
    cache.run(tmp_path, command, "second", lambda _root, _cmd, label: calls.append(label))

    assert verification_refresh._generator_name(command) is None
    assert calls == ["first", "second"]


def test_refresh_cache_runs_validate_compose_after_unchanged_compose(tmp_path: Path) -> None:
    calls: list[str] = []
    cache = verification_refresh.RefreshCache()
    compose = ["uv", "run", "python", "scripts/compose_manuscript.py"]
    validate = [*compose, "--validate-only", "--strict"]

    cache.run(tmp_path, compose, "Compose manuscript sections", lambda _root, _cmd, label: calls.append(label))
    cache.run(tmp_path, validate, "Validate compose contracts", lambda _root, _cmd, label: calls.append(label))

    assert verification_refresh._generator_name(validate) is None
    assert calls == ["Compose manuscript sections", "Validate compose contracts"]


def test_refresh_cache_invalidates_after_a_generator_input_or_output_changes(tmp_path: Path) -> None:
    calls: list[str] = []
    cache = verification_refresh.RefreshCache()
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
    cache = verification_refresh.RefreshCache(clock=lambda: next(ticks))
    command = ["uv", "run", "python", "scripts", "compose_manuscript.py"]
    calls: list[str] = []

    cache.run(tmp_path, command, "first", lambda _root, _cmd, label: calls.append(label))
    cache.run(tmp_path, command, "second", lambda _root, _cmd, label: calls.append(label))

    receipt = cache.receipt(baseline_seconds=3.0)
    assert calls == ["first"]
    assert receipt["schema_version"] == "template-active-inference/refresh-receipt/1"
    assert receipt["target_met"] is True
    assert receipt["events"][1]["action"] == "skipped"


def test_verifier_executes_existing_lexical_project_runtime_without_resolver(tmp_path: Path) -> None:
    venv.EnvBuilder(with_pip=False, symlinks=True).create(tmp_path / ".venv")
    selected = selected_verification_python(tmp_path)
    observation = tmp_path / "runtime.json"
    result = run_bounded_subprocess(
        [
            selected,
            "-I",
            "-c",
            'import json,sys;from pathlib import Path;Path(sys.argv[1]).write_text(json.dumps({"executable":sys.executable,"prefix":sys.prefix}))',
            str(observation),
        ],
        cwd=tmp_path,
        env=build_bounded_env(),
        timeout=10,
    )
    assert result.returncode == 0
    actual = json.loads(observation.read_text())
    assert actual["executable"] == selected and actual["prefix"] == str(tmp_path / ".venv")
    assert selected_verification_python(tmp_path, receipt_bound=True) == sys.executable


@pytest.mark.parametrize("kind", ["empty", "missing_configuration"])
def test_missing_nominated_verifier_runtime_never_falls_back(tmp_path: Path, kind: str) -> None:
    (tmp_path / ".venv").mkdir()
    if kind == "missing_configuration":
        binary = tmp_path / ".venv/bin"
        binary.mkdir()
        (binary / "python").symlink_to(sys.executable)
    with pytest.raises(VerificationRuntimeUnavailable):
        selected_verification_python(tmp_path)


def test_expired_verifier_session_refuses_before_actual_child(tmp_path: Path) -> None:
    marker = tmp_path / "forbidden-child"
    runner = full_verification._bounded_session_runner(
        tmp_path, sys.executable, time.monotonic() - 1, full_verification._run
    )
    with pytest.raises(VerificationDeadlineExceeded):
        runner(
            tmp_path, _script_command(tmp_path, f"from pathlib import Path;Path({str(marker)!r}).touch()"), "Expired"
        )
    assert not marker.exists()


def test_verifier_whole_deadline_clamps_actual_supervised_command(tmp_path: Path) -> None:
    marker = tmp_path / "late-child"
    runner = full_verification._bounded_session_runner(
        tmp_path, sys.executable, time.monotonic() + 0.2, full_verification._run
    )
    with pytest.raises(VerificationCommandFailed) as failure:
        runner(
            tmp_path,
            _script_command(
                tmp_path, f"import time;from pathlib import Path;time.sleep(1);Path({str(marker)!r}).touch()"
            ),
            "Finite",
        )
    assert not marker.exists()
    assert failure.value.exit_code == 124
    assert failure.value.timed_out
    assert failure.value.original_exit_code is None
    assert failure.value.attempt_exit_codes == ()


@pytest.mark.parametrize("code,expected", [(2, 1), (7, 1), (75, 75), (124, 124), (130, 130)])
@pytest.mark.parametrize("binary_diagnostic", [False, True])
@pytest.mark.timeout(90)
def test_verifier_retains_actual_child_exit_without_inventing_timeout(
    tmp_path: Path, code: int, expected: int, binary_diagnostic: bool
) -> None:
    diagnostic = "import sys;sys.stdout.buffer.write(b'\\xffdiagnostic\\n');" if binary_diagnostic else ""
    with pytest.raises(VerificationCommandFailed) as failure:
        full_verification._run(
            tmp_path, _script_command(tmp_path, f"{diagnostic}raise SystemExit({code})"), "Actual child"
        )
    assert failure.value.original_exit_code == code
    assert failure.value.attempt_exit_codes == (code,)
    assert failure.value.exit_code == expected
    assert not failure.value.timed_out
    assert not failure.value.custody_refused
    assert f"original child exit {code}" in str(failure.value)
    if binary_diagnostic:
        assert "\ufffddiagnostic" in str(failure.value)


@pytest.mark.parametrize("original,expected", [(130, 130), (-2, 130), (124, 124), (7, 1), (0, 75), (None, 75)])
def test_verifier_custody_refusal_preserves_observed_outcome_precedence(original: int | None, expected: int) -> None:
    failure = VerificationCommandFailed("custody refused", original_exit_code=original, custody_refused=True)
    assert failure.exit_code == expected
    assert failure.attempt_exit_codes == ((original,) if original is not None else ())


def test_actual_interruption_exit_outranks_late_supervisory_deadline() -> None:
    failure = VerificationCommandFailed("late cleanup", original_exit_code=130, timed_out=True, custody_refused=True)
    assert failure.exit_code == 130
    assert failure.attempt_exit_codes == (130,)


@pytest.mark.timeout(60)
@pytest.mark.parametrize("code,expected", [(7, 1), (124, 124), (130, 130)])
def test_full_verifier_cli_retains_real_producer_exit_and_stops(tmp_path: Path, code: int, expected: int) -> None:
    project_root = _write_coverage_partition_tree(tmp_path)
    source_root = Path(full_verification.__file__).parent
    package = project_root / "src/orchestration"
    package.mkdir(parents=True)
    # This owned partial fixture must be a regular package: an installed
    # orchestration provider can otherwise outrank its implicit namespace.
    # The six production controller modules below remain exact source copies.
    (package / "__init__.py").write_text('"""Owned CLI producer-exit fixture package."""\n')
    for module in (
        "full_verification.py",
        "portable_execution.py",
        "verification_execution.py",
        "verification_refresh.py",
        "semantic_coverage.py",
        "_verification_launcher.py",
    ):
        shutil.copyfile(source_root / module, package / module)
    scripts = project_root / "scripts"
    scripts.mkdir()
    shutil.copyfile(source_root.parents[1] / "scripts/run_full_verification.py", scripts / "run_full_verification.py")
    (scripts / "compose_manuscript.py").write_text(
        f"from pathlib import Path\nPath('producer-started').touch()\nraise SystemExit({code})\n"
    )
    (scripts / "validate_compose_contracts.py").write_text("from pathlib import Path\nPath('later-producer').touch()\n")
    environment = build_bounded_env()
    for key in (
        "TEMPLATE_PROJECT_TEST_RECEIPT",
        "TEMPLATE_PROJECT_TEST_RUN_ID",
        "TEMPLATE_PROJECT_TEST_PROJECT",
        "TEMPLATE_PROJECT_TEST_COMMAND_SHA256",
    ):
        environment.pop(key, None)
    child = subprocess.run(
        [sys.executable, str(scripts / "run_full_verification.py"), "--skip-chunks"],
        cwd=project_root,
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert child.returncode == expected, child.stdout + child.stderr
    assert (project_root / "producer-started").exists()
    assert not (project_root / "later-producer").exists()
    assert f"original child exit {code}" in child.stdout


def test_verifier_refuses_real_child_zero_after_total_deadline(tmp_path: Path) -> None:
    observed = []

    def actual_child(root: Path, command: list[str], label: str) -> None:
        result = subprocess.run(command, cwd=root, check=False, timeout=2)
        observed.append(result.returncode)

    runner = full_verification._bounded_session_runner(tmp_path, sys.executable, time.monotonic() + 0.04, actual_child)
    with pytest.raises(VerificationDeadlineExceeded):
        runner(tmp_path, [sys.executable, "-c", "import time;time.sleep(.08)"], "Actual late zero")
    assert observed == [0]


@pytest.mark.parametrize("requested", [True, float("nan"), float("inf"), -float("inf")])
def test_verifier_deadline_requires_finite_values(requested: float) -> None:
    with pytest.raises(ValueError):
        verification_deadline(time.monotonic(), [1800, 2400], requested=requested)


def test_verifier_composes_command_budgets_under_declared_ceiling() -> None:
    assert verification_deadline(10, [1800, 2400]) == 4210
    assert verification_deadline(10, [1800] * 10) == 6910
    assert verification_deadline(10, [1800], requested=20) == 20


@pytest.mark.timeout(120)
@pytest.mark.parametrize("target", ["producer", "pytest"])
def test_full_verifier_actual_children_ignore_valid_poisoned_scientific_cache(tmp_path: Path, target: str) -> None:
    source = tmp_path / "src/science.py"
    source.parent.mkdir()
    source.write_text("VALUE = 17\n")
    original = source.read_bytes()
    observed = source.stat()
    marker = tmp_path / "poison-marker"
    compiled = compile(f"from pathlib import Path\nPath({str(marker)!r}).touch()\nVALUE = 17\n", str(source), "exec")
    cache = source.parent / "__pycache__" / f"{source.stem}.{sys.implementation.cache_tag}.pyc"
    cache.parent.mkdir()
    cache.write_bytes(
        importlib.util.MAGIC_NUMBER
        + struct.pack("<III", 0, int(observed.st_mtime), observed.st_size)
        + marshal.dumps(compiled)
    )
    ordinary = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import sys;sys.path.insert(0,sys.argv[1]);import science;assert science.VALUE==17",
            str(source.parent),
        ],
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert ordinary.returncode == 0 and marker.exists()
    marker.unlink()
    result = tmp_path / "numeric-result"
    body = f"import science\nfrom pathlib import Path\nassert science.VALUE == 17\nPath({str(result)!r}).write_text(str(science.VALUE))\n"
    if target == "producer":
        command = _script_command(tmp_path, body)
    else:
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_science.py").write_text(
            "def test_science():\n" + "".join("    " + line + "\n" for line in body.splitlines())
        )
        command = [sys.executable, "-m", "pytest", "tests/test_science.py", "-q"]
    full_verification._run(tmp_path, command, "Actual audited scientific child")
    assert result.read_text() == "17"
    assert not marker.exists()
    assert source.read_bytes() == original


@pytest.mark.timeout(90)
def test_full_verifier_missing_selected_dev_stack_blocks_without_acquisition(tmp_path: Path) -> None:
    venv.EnvBuilder(with_pip=False, symlinks=True).create(tmp_path / ".venv")
    command = _script_command(tmp_path, "from pathlib import Path;Path('forbidden-domain-child').touch()")
    command[0] = selected_verification_python(tmp_path)
    with pytest.raises(VerificationRuntimeUnavailable):
        full_verification._run(tmp_path, command, "Missing prepared verifier stack")
    assert not (tmp_path / "forbidden-domain-child").exists()
    assert not (tmp_path / ".venv/bin/uv").exists()
    assert not (tmp_path / "uv.lock").exists()


@pytest.mark.parametrize("profile", ["quick", "release", "exhaustive", None])
def test_real_prepass_accounts_filtered_slice_and_runs_next_group(tmp_path: Path, capsys, profile) -> None:
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\naddopts = -v --assert=plain\nmarkers = long_running: explicit slow selection\n"
    )
    (tmp_path / "test_long.py").write_text(
        "import pytest\nfrom pathlib import Path\n@pytest.mark.long_running\n"
        "def test_long(): Path('long-executed').touch()\n"
    )
    (tmp_path / "test_ordinary.py").write_text(
        "from pathlib import Path\ndef test_ordinary(): Path('ordinary-executed').touch()\n"
    )
    full_verification._run_chunked_prepasses(
        tmp_path,
        [("all-long checks", ["test_long.py"]), ("ordinary checks", ["test_ordinary.py"])],
        python=sys.executable,
        profile=profile,
        command_runner=full_verification._run,
    )
    bounded = profile in {"quick", "release"}
    assert (tmp_path / "long-executed").exists() is not bounded
    assert (tmp_path / "ordinary-executed").is_file()
    assert ("selected no tests" in capsys.readouterr().out) is bounded


@pytest.mark.parametrize("profile", ["quick", "release", "exhaustive", None])
@pytest.mark.parametrize("source,exit_code", [("", 5), ("def test_fails(): assert False\n", 1)])
def test_real_prepass_never_accepts_missing_collection_or_failure(tmp_path: Path, profile, source, exit_code) -> None:
    (tmp_path / "pytest.ini").write_text("[pytest]\naddopts = -v --assert=plain\n")
    (tmp_path / "test_case.py").write_text(source)
    with pytest.raises(VerificationCommandFailed) as error:
        full_verification._run_chunked_prepasses(
            tmp_path,
            [("actual negative control", ["test_case.py"])],
            python=sys.executable,
            profile=profile,
            command_runner=full_verification._run,
        )
    assert error.value.original_exit_code == exit_code
    assert not error.value.timed_out and not error.value.custody_refused
