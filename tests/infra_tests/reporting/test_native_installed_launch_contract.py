"""Real outer CLI refusals and diagnostic DATA; no native authority minted."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from infrastructure.reporting.native_current_reader_inputs import NativeCurrentAnalysisInputs
from infrastructure.reporting.native_installed_invocation import launch_prepared_native
from infrastructure.reporting.native_installed_launcher import _signed_failure
from infrastructure.reporting.native_preflight_budget import PREFLIGHT_MAX_OPERATION_SECONDS
from infrastructure.reporting.native_revalidation_progress import RevalidationProgress

ROOT = Path(__file__).resolve().parents[3]
MODULE = "infrastructure.reporting.native_installed_launcher"


def _arguments(tmp_path: Path, mode: str, budget: int) -> list[str]:
    source = tmp_path / "source"
    source.mkdir()
    return [
        "--mode",
        mode,
        "--source-root",
        str(source),
        "--source-commit",
        "0" * 40,
        "--source-identity",
        "a" * 64,
        "--current-root",
        str(tmp_path / "mirror"),
        "--scratch",
        str(tmp_path / "scratch"),
        "--python",
        sys.executable,
        "--uv",
        str(tmp_path / "never-executed-uv"),
        "--expected-platform",
        "Linux",
        "--mermaid-package-root",
        str(tmp_path / "mermaid"),
        "--mermaid-dependency-root",
        str(tmp_path / "node_modules"),
        "--mermaid-node-executable",
        str(tmp_path / "node"),
        "--mermaid-chrome-executable",
        str(tmp_path / "chrome"),
        "--repository",
        "diagnostic/local",
        "--run-id",
        "1",
        "--timeout",
        str(budget),
    ]


def _run(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    # These cases stop before capacity checks, Git, Source admission or installs.
    return subprocess.run(
        [sys.executable, "-m", MODULE, *arguments],
        cwd=ROOT,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


@pytest.mark.parametrize(
    "mode,budget",
    [("original", 0), ("original", -1), ("original", 14401), ("preflight", PREFLIGHT_MAX_OPERATION_SECONDS + 1)],
)
def test_real_launcher_refuses_invalid_original_budget_before_any_work(tmp_path: Path, mode: str, budget: int) -> None:
    result = _run(_arguments(tmp_path, mode, budget))
    message = (
        f"at most {PREFLIGHT_MAX_OPERATION_SECONDS} seconds"
        if mode == "preflight"
        else "existing whole-operation budget"
    )
    assert result.returncode == 2 and message in result.stderr
    assert sorted(path.name for path in tmp_path.iterdir()) == ["source"]


@pytest.mark.parametrize("mode,budget", [("preflight", PREFLIGHT_MAX_OPERATION_SECONDS), ("original", 14400)])
@pytest.mark.parametrize("occupied", ["mirror", "scratch", "dangling-mirror"])
def test_real_launcher_accepts_each_clock_bound_but_refuses_nonfresh_paths(
    tmp_path: Path, mode: str, budget: int, occupied: str
) -> None:
    arguments = _arguments(tmp_path, mode, budget)
    if occupied == "dangling-mirror":
        (tmp_path / "mirror").symlink_to(tmp_path / "absent-owner")
    else:
        (tmp_path / occupied).mkdir()
    before = sorted(path.name for path in tmp_path.iterdir())
    result = _run(arguments)
    assert result.returncode == 2 and "fresh owner-controlled mirror and scratch" in result.stderr
    assert sorted(path.name for path in tmp_path.iterdir()) == before


@pytest.mark.parametrize("missing", ["--current-root", "--scratch"])
def test_real_launcher_requires_both_explicit_fresh_destinations(tmp_path: Path, missing: str) -> None:
    arguments = _arguments(tmp_path, "preflight", PREFLIGHT_MAX_OPERATION_SECONDS)
    index = arguments.index(missing)
    del arguments[index : index + 2]
    result = _run(arguments)
    assert result.returncode == 2 and missing in result.stderr and "required" in result.stderr
    assert sorted(path.name for path in tmp_path.iterdir()) == ["source"]


@pytest.mark.parametrize("role", ["foreign.worker", "infrastructure.reporting.native_installed_preflight.other"])
def test_invocation_rejects_unknown_role_before_touching_prepared_runtime(role: str) -> None:
    with pytest.raises(ValueError, match="exact controller or independent-reader role"):
        launch_prepared_native(
            None,  # type: ignore[arg-type]
            Path("unused"),
            b"",
            role=role,
            arguments=(),
            pdfium_roots=(),
            pdfium_sources={},
            environment={},
        )


@pytest.mark.parametrize(
    "observation,expected",
    [
        ({"original_exit_code": -2, "timed_out": True}, 130),
        ({"original_exit_code": -9, "timed_out": True}, 124),
        ({"original_exit_code": -9, "timed_out": False}, 137),
        ({"original_exit_code": 7, "timed_out": False}, 7),
        ({"original_exit_code": 0, "timed_out": False}, 75),
    ],
)
def test_outer_failure_translation_preserves_actual_signed_outcome(
    observation: dict[str, object], expected: int
) -> None:
    assert _signed_failure(observation) == expected


def test_progress_rejects_data_in_place_of_actual_source_without_output(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(ValueError, match="fixed genuine Source/scopes/clock"):
        RevalidationProgress(
            None,
            "reader-runtimes",
            ("templates/template_code_project",),
            time.monotonic() + 10,  # type: ignore[arg-type]
        )
    observed = capsys.readouterr()
    assert observed.out == observed.err == ""


def test_current_reader_constructor_refuses_unadmitted_source_before_filesystem_reads(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="genuinely admitted Source context"):
        NativeCurrentAnalysisInputs(None, time.monotonic() + 10, {}, {})  # type: ignore[arg-type]
    assert not tuple(tmp_path.iterdir())
