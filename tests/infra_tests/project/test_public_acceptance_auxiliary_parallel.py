"""Real owned subprocess overlap, scope serialization and cold pytest storage."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

import pytest

from infrastructure.core.pipeline.fingerprints import tree_records
from infrastructure.project.public_acceptance_auxiliary_parallel import (
    AuxiliaryDeadlineExceeded,
    AuxiliaryOperation,
    AuxiliaryProcess,
    execute_auxiliary_operations,
)


@pytest.mark.parametrize("workers", (1, 2, 3))
@pytest.mark.timeout(90)
def test_real_children_overlap_only_across_scopes(tmp_path: Path, workers: int) -> None:
    controller = threading.get_ident()
    deadline = time.monotonic() + 60
    barrier = tmp_path / "barrier"
    barrier.mkdir()

    def operation(scope: str, ordinal: int) -> AuxiliaryOperation:
        assert threading.get_ident() == controller
        previous = barrier / (scope + "-admitted")
        if ordinal:
            assert previous.is_file()
        command = [
            sys.executable,
            "-I",
            "-c",
            "import pathlib,sys,time; p=pathlib.Path(sys.argv[1]); "
            "(p/(sys.argv[2]+'-started')).write_text('actual child'); "
            "limit=time.monotonic()+30\n"
            "while len(list(p.glob('*-started')))<int(sys.argv[3]):\n"
            " if time.monotonic()>limit: raise SystemExit(19)\n"
            " time.sleep(0.01)\n"
            "print('actual scope '+sys.argv[2])",
            str(barrier),
            scope,
            str(workers),
        ]
        observation = yield AuxiliaryProcess(
            command, tmp_path, tmp_path / "output/readiness" / scope / str(ordinal), deadline
        )
        assert threading.get_ident() == controller
        assert observation["exit_code"] == 0
        assert observation["timed_out"] is False
        previous.write_text(str(observation["pid"]))
        return scope + ":" + str(ordinal), observation

    # Round-robin across scopes, but the second gate must await full admission
    # of its own first gate. The first children require real overlap to finish.
    operations = [(str(scope), operation(str(scope), ordinal)) for ordinal in (0, 1) for scope in range(workers)]
    results = execute_auxiliary_operations(operations, workers=workers, deadline=deadline)
    assert [gate for gate, _ in results] == [str(scope) + ":" + str(n) for n in (0, 1) for scope in range(workers)]
    assert len({row["pid"] for _, row in results}) == 2 * workers


@pytest.mark.parametrize("workers", (0, 4, True))
def test_invalid_parallel_bound_refuses_before_controller(tmp_path: Path, workers: int) -> None:
    def operation() -> AuxiliaryOperation:
        (tmp_path / "unexpected").write_text("must not start")
        yield AuxiliaryProcess([], tmp_path, tmp_path, time.monotonic())
        return "unreachable", {}

    with pytest.raises(ValueError, match="one, two or three"):
        execute_auxiliary_operations([("scope", operation())], workers=workers, deadline=time.monotonic() + 10)
    assert not tuple(tmp_path.iterdir())


@pytest.mark.timeout(60)
def test_one_worker_preserves_multi_scope_serial_execution_order(tmp_path: Path) -> None:
    deadline = time.monotonic() + 45
    order = tmp_path / "actual-order.txt"
    selected = (("A", "A:0"), ("A", "A:1"), ("B", "B:0"), ("B", "B:1"), ("A", "A:2"))

    def operation(gate: str) -> AuxiliaryOperation:
        observation = yield AuxiliaryProcess(
            [
                sys.executable,
                "-I",
                "-c",
                "import pathlib,sys; p=pathlib.Path(sys.argv[1]); f=p.open('a'); f.write(sys.argv[2]+'\\n'); f.close()",
                str(order),
                gate,
            ],
            tmp_path,
            tmp_path / "output/readiness" / gate,
            deadline,
        )
        assert observation["exit_code"] == 0
        return gate, observation

    results = execute_auxiliary_operations(
        [(scope, operation(gate)) for scope, gate in selected], workers=1, deadline=deadline
    )
    assert order.read_text().splitlines() == [gate for _, gate in selected]
    assert [gate for gate, _ in results] == [gate for _, gate in selected]


@pytest.mark.timeout(20)
def test_real_controller_refuses_admission_completed_after_original_deadline(tmp_path: Path) -> None:
    deadline = time.monotonic() + 8

    def operation() -> AuxiliaryOperation:
        observation = yield AuxiliaryProcess(
            [sys.executable, "-I", "-c", "print('original child completed')"],
            tmp_path,
            tmp_path / "output/readiness/late-admission",
            deadline,
        )
        assert observation["exit_code"] == 0
        while time.monotonic() < deadline + 0.01:
            time.sleep(0.005)
        return "late", observation

    def early() -> AuxiliaryOperation:
        observed = yield AuxiliaryProcess(
            [sys.executable, "-I", "-c", "print('original early child')"],
            tmp_path,
            tmp_path / "output/readiness/early-admission",
            deadline,
        )
        return "early", observed

    def never() -> AuxiliaryOperation:
        (tmp_path / "must-not-launch").write_text("late queued controller")
        yield AuxiliaryProcess([], tmp_path, tmp_path, deadline)
        return "unreachable", {}

    with pytest.raises(AuxiliaryDeadlineExceeded, match="original auxiliary deadline") as observed:
        execute_auxiliary_operations(
            [("scope", early()), ("scope", operation()), ("scope", never())], workers=1, deadline=deadline
        )
    assert len(observed.value.results) == 1 and observed.value.results[0][0] == "early"
    assert observed.value.results[0][1]["exit_code"] == 0
    assert not (tmp_path / "must-not-launch").exists()
    child = observed.value.observations[1][0]
    assert child["exit_code"] == 0
    assert (tmp_path / child["streams"]["stdout"]["path"]).read_text() == "original child completed\n"


def test_declared_pytest_benchmark_storage_preserves_cold_source(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[3] / "projects/templates/template_active_inference/pyproject.toml"
    environment = {key: value for key, value in os.environ.items() if key not in {"PYTEST_ADDOPTS", "PYTEST_PLUGINS"}}
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    for selected in (True, False):
        project = tmp_path / str(selected)
        project.mkdir()
        (project / "tests").mkdir()
        shutil.copyfile(source, project / "pyproject.toml")
        excluded = frozenset({(project / "output").absolute()})
        before = tree_records(project, source=True, excluded_roots=excluded)
        command = [sys.executable, "-B", "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"]
        if not selected:
            command += ["-o", "addopts=-q"]
        result = subprocess.run(
            command, cwd=project, env=environment, capture_output=True, text=True, check=False, timeout=30
        )
        assert result.returncode == 5, result.stderr
        after = tree_records(project, source=True, excluded_roots=excluded)
        assert (before == after) is selected
        assert (project / ".benchmarks").exists() is not selected
        if selected:
            assert (project / "output/.pipeline/benchmarks").is_dir()


@pytest.mark.skipif(sys.platform != "darwin", reason="requires an actual macOS process host")
@pytest.mark.timeout(30)
def test_macos_control_observes_real_descendant_after_guardian_startup(tmp_path: Path) -> None:
    from infrastructure.project.public_acceptance_auxiliary_worker import execute

    result = execute(tmp_path, "root:macos:process", 20, directory=tmp_path / "output/readiness/macos-control")
    process = result["descendant_process"]
    assert result["assertions"]["descendant_cleanup"] is True
    assert type(process["pid"]) is int and process["pid"] > 0
    assert type(process["exit_code"]) is int and process["exit_code"] < 0
    assert process["timed_out"] is True
    # This is a deliberately timed-out control, never a passing child receipt.
    assert process["accepted"] is False
