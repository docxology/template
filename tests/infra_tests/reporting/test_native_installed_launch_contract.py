"""Real outer CLI refusals and diagnostic DATA; no native authority minted."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from infrastructure.project.public_package_dependencies import local_dependency_closure
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_current_reader_inputs import NativeCurrentAnalysisInputs
from infrastructure.reporting.native_installed_invocation import launch_prepared_native
from infrastructure.reporting.native_installed_launcher import (
    _signed_failure,
    native_cell_scope,
    native_preparation_scopes,
)
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


def test_native_cell_scope_resolves_only_declared_public_exemplars() -> None:
    assert native_cell_scope("template_code_project") == "templates/template_code_project"
    with pytest.raises(ValueError, match="one declared public exemplar"):
        native_cell_scope("template_not_declared")


@pytest.mark.parametrize("mode", ["reader", "handoff"])
def test_native_preparation_scopes_keeps_whole_roles_unsharded(mode: str) -> None:
    assert native_preparation_scopes(mode, ROOT) == PUBLIC_PROJECT_NAMES


@pytest.mark.parametrize("cell", PUBLIC_PROJECT_NAMES)
def test_native_preparation_scopes_prepares_each_cells_local_closure(cell: str) -> None:
    """Every scope the provider install looks up must have a prepared wheel.

    Negative control for hosted run 41940842593 (job 126961680263): the cell
    `template_advanced_literature_review` failed after 8m51s with
    `KeyError: 'templates/template_literature_meta_analysis'` because
    preparation built wheels only for `("root", cell)` while the provider
    install demanded the cell's transitive local closure. `root` is prepared
    unconditionally, so only non-root closure members must be added.
    """
    short = cell.removeprefix("templates/")
    scopes = native_preparation_scopes("original", ROOT, cell=short)

    # The declared selection is still the cell itself: preparation adds only
    # dependencies and never drops the selected scope.
    assert scopes[0] == cell

    # `native_installed_preparation` builds a wheel for ("root", *scopes) and
    # then looks up every non-root closure member of every prepared scope.
    # Assert that exact invariant rather than a hard-coded expectation.
    built = {"root", *scopes}
    needed = {provider for scope in scopes for provider in local_dependency_closure(ROOT, scope) if provider != "root"}
    assert needed <= built, f"cell {cell} would raise KeyError for {sorted(needed - built)}"

    # No duplicates, and no accidental roster-wide expansion.
    assert len(scopes) == len(set(scopes))
    assert set(scopes) <= set(PUBLIC_PROJECT_NAMES)


def test_native_preparation_scopes_adds_nothing_for_a_root_only_cell() -> None:
    """The 24 exemplars declaring only the root source keep a one-scope tuple.

    This is the assertion that makes the fix safe: it changes exactly one
    cell's preparation and cannot move any other.
    """
    assert native_preparation_scopes("original", ROOT, cell="template_code_project") == (
        "templates/template_code_project",
    )
    assert native_preparation_scopes("original", ROOT, cell="template_textbook") == ("templates/template_textbook",)


def test_native_preparation_scopes_adds_the_sibling_local_dependency() -> None:
    """The one sibling edge in the public roster is prepared with its dependent."""
    assert native_preparation_scopes("original", ROOT, cell="template_advanced_literature_review") == (
        "templates/template_advanced_literature_review",
        "templates/template_literature_meta_analysis",
    )


def test_only_one_exemplar_declares_a_sibling_local_dependency() -> None:
    """Guard the premise above: a second edge means this expectation must change."""
    dependent = [
        name.removeprefix("templates/")
        for name in PUBLIC_PROJECT_NAMES
        if any(provider != "root" for provider in local_dependency_closure(ROOT, name))
    ]
    assert dependent == ["template_advanced_literature_review"]


def test_offline_cache_scope_report_matches_prepared_scopes() -> None:
    """Cache warming must ask this CLI, not re-derive the selection in shell.

    Negative control for hosted run 41940842593 (job 126961680266): the cell
    `template_autoresearch_project` warmed only the Root lock and then failed
    offline at fixture setup with `Failed to download packaging==26.2`, because
    the Root lock pins `packaging==26.3`. The report must name exactly the scopes
    the preparation loop installs, so warming cannot drift from preparation.
    """
    observed = subprocess.run(
        (
            sys.executable,
            "-m",
            MODULE,
            "--mode",
            "original",
            "--matrix-cell",
            "template_autoresearch_project",
            "--source-root",
            str(ROOT),
            "--print-preparation-scopes",
        ),
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
        cwd=ROOT,
    )
    assert observed.stdout.split() == list(
        native_preparation_scopes("original", ROOT, cell="template_autoresearch_project")
    )


def test_offline_cache_scope_report_covers_every_roster_lock() -> None:
    """The roster-wide lane prepares all 25 exemplars and must warm all 25 locks."""
    observed = subprocess.run(
        (
            sys.executable,
            "-m",
            MODULE,
            "--mode",
            "original",
            "--source-root",
            str(ROOT),
            "--print-preparation-scopes",
        ),
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
        cwd=ROOT,
    )
    assert tuple(observed.stdout.split()) == PUBLIC_PROJECT_NAMES


def test_offline_cache_scope_report_refuses_an_undeclared_cell() -> None:
    """A typo must fail loudly; warming nothing silently reintroduces the defect."""
    observed = subprocess.run(
        (
            sys.executable,
            "-m",
            MODULE,
            "--mode",
            "original",
            "--matrix-cell",
            "template_not_declared",
            "--source-root",
            str(ROOT),
            "--print-preparation-scopes",
        ),
        capture_output=True,
        text=True,
        timeout=120,
        cwd=ROOT,
    )
    assert observed.returncode != 0
    assert "matrix cell must name one declared public exemplar" in observed.stderr


def test_offline_cache_scope_report_creates_no_custody_destination(tmp_path: Path) -> None:
    """Warming runs before custody, so the report must not make a mirror or scratch."""
    mirror = tmp_path / "mirror"
    scratch = tmp_path / "scratch"
    subprocess.run(
        (
            sys.executable,
            "-m",
            MODULE,
            "--mode",
            "original",
            "--source-root",
            str(ROOT),
            "--print-preparation-scopes",
            "--current-root",
            str(mirror),
            "--scratch",
            str(scratch),
        ),
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
        cwd=ROOT,
    )
    assert not mirror.exists()
    assert not scratch.exists()


def test_native_preparation_scopes_refuses_a_cell_outside_the_original_and_reader_roles() -> None:
    with pytest.raises(ValueError, match="only to the original and reader roles"):
        native_preparation_scopes("handoff", Path("unused-source"), cell="template_code_project")


def test_native_preparation_scopes_keeps_the_reader_roster_wide_for_a_cell() -> None:
    # The reader's provider admission still demands every public nomination, so a
    # cell shards only its Current-side execution, never its preparation.
    assert native_preparation_scopes("reader", Path("unused-source"), cell="template_code_project") == (
        PUBLIC_PROJECT_NAMES
    )


def test_real_launcher_refuses_an_undeclared_matrix_cell_before_any_work(tmp_path: Path) -> None:
    arguments = _arguments(tmp_path, "original", 14400)
    arguments += ["--matrix-cell", "template_not_declared"]
    result = _run(arguments)
    assert result.returncode == 2 and "one declared public exemplar" in result.stderr
    assert sorted(path.name for path in tmp_path.iterdir()) == ["source"]


@pytest.mark.parametrize("mode", ["handoff", "preflight"])
def test_real_launcher_refuses_matrix_cell_scoping_outside_the_original_and_reader_roles(
    tmp_path: Path, mode: str
) -> None:
    budget = PREFLIGHT_MAX_OPERATION_SECONDS if mode == "preflight" else 14400
    arguments = _arguments(tmp_path, mode, budget)
    arguments += ["--matrix-cell", "template_code_project"]
    result = _run(arguments)
    assert result.returncode == 2 and "only to the original and reader roles" in result.stderr
    assert sorted(path.name for path in tmp_path.iterdir()) == ["source"]


def test_real_launcher_admits_a_declared_matrix_cell_for_the_reader_before_touching_fresh_paths(
    tmp_path: Path,
) -> None:
    arguments = _arguments(tmp_path, "reader", 14400)
    arguments += ["--matrix-cell", "template_code_project"]
    (tmp_path / "mirror").mkdir()
    result = _run(arguments)
    assert result.returncode == 2 and "fresh owner-controlled mirror and scratch" in result.stderr


def test_real_launcher_admits_a_declared_matrix_cell_before_touching_fresh_paths(tmp_path: Path) -> None:
    # A declared cell passes cell admission and stops at the fresh-destination
    # guard, so the flag is proven admitted without running any preparation.
    arguments = _arguments(tmp_path, "original", 14400)
    arguments += ["--matrix-cell", "template_code_project"]
    (tmp_path / "mirror").mkdir()
    result = _run(arguments)
    assert result.returncode == 2 and "fresh owner-controlled mirror and scratch" in result.stderr
