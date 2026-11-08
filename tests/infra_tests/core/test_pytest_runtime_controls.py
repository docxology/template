"""Real project sessions preserve native selection, private controls and option boundaries."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

import infrastructure.core.testing._pytest_runtime_controls as controls
from infrastructure.core.testing.pytest_observations import DIRECTORY_ENV, NONCE_ENV, ROOT_ENV
from infrastructure.core.testing.pytest_orchestration import (
    build_project_pytest_command,
    build_union_pytest_command,
    resolve_test_profile,
)

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("mode", ["present", "blocked", "autoload-disabled", "explicit-custom"])
@pytest.mark.timeout(60)
def test_actual_plugin_storage_is_default_only_and_optional(tmp_path: Path, mode: str) -> None:
    nominated = tmp_path / "output/.pipeline/benchmarks"
    explicit = tmp_path / "custom-user-storage"
    enabled = mode in {"present", "explicit-custom"}
    expected = explicit if mode == "explicit-custom" else nominated
    if enabled:
        body = (
            "def test_real_benchmark(benchmark, pytestconfig):\n"
            "    assert benchmark(lambda: sum(range(4))) == 6\n"
            f"    assert pytestconfig.option.benchmark_storage == {'file://' + str(expected)!r}\n"
        )
    else:
        body = (
            "def test_plugin_absent(pytestconfig):\n    assert not hasattr(pytestconfig.option, 'benchmark_storage')\n"
        )
    (tmp_path / "test_actual.py").write_text(body)
    arguments = ["-p", controls.__name__, f"--template-benchmark-storage={nominated}", "-q", "test_actual.py"]
    if enabled:
        arguments.extend(
            [
                "-p",
                "pytest_benchmark.plugin",
                "--benchmark-min-rounds=1",
                "--benchmark-min-time=0.000001",
                "--benchmark-max-time=0.001",
                "--benchmark-warmup=off",
            ]
        )
    elif mode == "blocked":
        arguments.extend(["-p", "no:benchmark"])
    if mode == "explicit-custom":
        arguments.append("--benchmark-storage=file://" + str(explicit))
    environment = {**os.environ, "PYTEST_ADDOPTS": ""}
    environment.pop("PYTEST_PLUGINS", None)
    if mode != "blocked":
        environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    else:
        environment.pop("PYTEST_DISABLE_PLUGIN_AUTOLOAD", None)
    bootstrap = (
        f"import sys,runpy;sys.path.insert(0,{str(ROOT)!r});"
        "sys.argv=['pytest',*sys.argv[1:]];runpy.run_module('pytest',run_name='__main__')"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", bootstrap, *arguments],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout
    assert not (tmp_path / ".benchmarks").exists()
    assert expected.is_dir() is enabled
    if mode == "explicit-custom":
        assert not nominated.exists()


@pytest.mark.parametrize("collection_only", [False, True])
@pytest.mark.timeout(60)
def test_native_selection_is_inert_without_behavioral_generated_policy(tmp_path: Path, collection_only: bool) -> None:
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\naddopts = --strict-markers -m native\nmarkers =\n native(payload): native signature\n slow: opt in\n"
    )
    (tmp_path / "test_actual.py").write_text(
        "import pytest\n"
        "@pytest.mark.native(payload='owned')\n"
        "@pytest.mark.slow\n"
        "def test_native(pytestconfig):\n assert pytestconfig.option.markexpr == 'native'\n"
        "def test_not_selected():\n pytest.fail('native selection was overwritten')\n"
    )
    command = build_project_pytest_command(
        tmp_path,
        ["-q", "test_actual.py", *(["--collect-only"] if collection_only else [])],
        interpreter=Path(sys.executable),
        generated_profile=resolve_test_profile() if collection_only else None,
    )
    environment = {**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": ""}
    environment.pop("PYTEST_PLUGINS", None)
    result = subprocess.run(
        command, cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=30, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    if collection_only:
        assert "test_actual.py::test_native" in result.stdout
        assert "test_actual.py::test_not_selected" not in result.stdout
    else:
        assert "1 passed" in result.stdout


@pytest.fixture
def native_policy_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A native slow selection distinguishable from the generated quick policy."""
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\naddopts = --strict-markers -m native\nmarkers =\n native(payload): native signature\n slow: opt in\n"
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src/__init__.py").write_text("")
    (tmp_path / "src/value.py").write_text("def value():\n return 7\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_actual.py").write_text(
        "import pytest\nfrom src.value import value\n"
        "@pytest.mark.native(payload='owned')\n"
        "@pytest.mark.slow\n"
        "def test_native_slow():\n assert value() == 7\n"
        "def test_unmarked():\n assert value() == 7\n"
    )
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setenv("PYTEST_ADDOPTS", "")
    monkeypatch.setenv("PYTEST_PLUGINS", "infrastructure.core.testing.pytest_receipt,pytest_cov.plugin,pytest_timeout")
    monkeypatch.delenv("PYTEST_XDIST_WORKERS", raising=False)
    monkeypatch.setenv("COVERAGE_FILE", str(tmp_path / ".coverage"))
    monkeypatch.setenv(DIRECTORY_ENV, str(tmp_path / "observations"))
    monkeypatch.setenv(NONCE_ENV, "native-policy")
    monkeypatch.setenv(ROOT_ENV, str(tmp_path))
    return tmp_path


@pytest.mark.parametrize(
    ("marker_args", "expression"),
    [
        (["-m", "native"], "native"),
        (["-mnative"], "native"),
        (["-m=native"], "native"),
        (["-qm", "native"], "native"),
        (["-qmnative"], "native"),
        (["-m", "unknown_native_expression", "-m", "native"], "native"),
        (["-m", ""], ""),
    ],
)
@pytest.mark.timeout(60)
def test_shared_builder_explicit_marker_wins_generated_profile(
    native_policy_project: Path, marker_args: list[str], expression: str
) -> None:
    project = native_policy_project
    command = build_project_pytest_command(
        project,
        ["-q", *marker_args, "--", "tests/"],
        interpreter=Path(sys.executable),
        generated_profile=resolve_test_profile("quick"),
    )
    result = subprocess.run(
        command, cwd=project, env=os.environ.copy(), capture_output=True, text=True, timeout=30, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    receipt = json.loads(next((project / "observations").glob("execution-*.json")).read_text())
    assert receipt["selection_profile"]["marker_expression"] == expression
    native = "tests/test_actual.py::test_native_slow"
    unmarked = "tests/test_actual.py::test_unmarked"
    assert receipt["selected"] == ([native] if expression else [native, unmarked])
    assert receipt["deselected"] == ([unmarked] if expression else [])
    assert receipt["reports"][native]["call"] == "passed"


@pytest.mark.parametrize("route", ["project", "union"])
@pytest.mark.parametrize("expression", ["native", "", "unknown_native_expression", "native and ("])
@pytest.mark.timeout(60)
def test_composed_marker_policy_preserves_native_selection_and_errors(
    native_policy_project: Path, route: str, expression: str
) -> None:
    project = native_policy_project
    profile = resolve_test_profile("quick")
    if route == "union":
        command = build_union_pytest_command(
            project,
            project,
            project / "tests",
            is_first=True,
            marker_expr=expression,
            timeout=30,
            fail_under=100,
            generated_profile=profile,
        )
    else:
        command = build_project_pytest_command(
            project,
            ["-q", "-m", expression, "tests/"],
            interpreter=Path(sys.executable),
            generated_profile=profile,
        )
    result = subprocess.run(
        command, cwd=project, env=os.environ.copy(), capture_output=True, text=True, timeout=30, check=False
    )
    combined = result.stdout + result.stderr
    receipt = json.loads(next((project / "observations").glob("execution-*.json")).read_text())
    assert receipt["selection_profile"]["marker_expression"] == expression
    if expression in {"native", ""}:
        assert result.returncode == 0, combined
        native = "tests/test_actual.py::test_native_slow"
        unmarked = "tests/test_actual.py::test_unmarked"
        assert receipt["selected"] == ([native] if expression else [native, unmarked])
        assert receipt["deselected"] == ([unmarked] if expression else [])
        assert receipt["reports"][native]["call"] == "passed"
        assert ("1 passed" if expression else "2 passed") in result.stdout
    else:
        assert result.returncode == 4, combined
        assert receipt["reports"] == {}
        diagnostic = "unknown_native_expression" if expression.startswith("unknown") else "expected"
        assert diagnostic in combined


@pytest.mark.parametrize("generated", [False, True])
@pytest.mark.parametrize("collection_only", [False, True])
@pytest.mark.parametrize("collection_path", ["tests", "-munknown"])
@pytest.mark.timeout(60)
def test_shared_builder_preserves_separator_collection(
    native_policy_project: Path, generated: bool, collection_only: bool, collection_path: str
) -> None:
    project = native_policy_project
    if collection_path != "tests":
        (project / "tests").rename(project / collection_path)
    command = build_project_pytest_command(
        project,
        [
            "-q",
            "-o",
            "cache_dir=-mnot_an_expression",
            *(["--collect-only"] if collection_only else []),
            "--",
            collection_path + "/",
        ],
        interpreter=Path(sys.executable),
        generated_profile=resolve_test_profile("quick") if generated else None,
    )
    result = subprocess.run(
        command, cwd=project, env=os.environ.copy(), capture_output=True, text=True, timeout=30, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    receipt = json.loads(next((project / "observations").glob("execution-*.json")).read_text())
    generated_selection = generated and not collection_only
    selected = f"{collection_path}/test_actual.py::test_" + ("unmarked" if generated_selection else "native_slow")
    deselected = f"{collection_path}/test_actual.py::test_" + ("native_slow" if generated_selection else "unmarked")
    assert receipt["selection_profile"]["marker_expression"] == ("not slow" if generated_selection else "native")
    assert receipt["selected"] == [selected]
    assert receipt["deselected"] == [deselected]
    if collection_only:
        assert selected in result.stdout
        assert deselected not in result.stdout
        assert receipt["reports"] == {}
    else:
        assert "1 passed" in result.stdout
        assert receipt["reports"][selected]["call"] == "passed"
