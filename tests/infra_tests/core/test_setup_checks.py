"""Prepared Stage00 availability, structure, and non-executing hook checks."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from infrastructure.core.pipeline.outcomes import StageStatus
from infrastructure.core.runtime.prepared_runtime import PreparedRuntimeUnavailable, check_prepared_packages
from infrastructure.core.runtime.setup_checks import (
    SetupCheckResult,
    aggregate_check_results,
    check_setup_hook_prerequisites,
    run_environment_setup_checks,
    validate_project_discovery,
)


def _make_valid_project(base: Path, name: str) -> Path:
    project = base / "projects/templates" / name
    for directory in ("src", "tests", "scripts"):
        (project / directory).mkdir(parents=True)
    (project / "src/__init__.py").write_text("")
    (project / "tests/__init__.py").write_text("")
    (project / "tests/test_domain.py").write_text("def test_domain(): assert 17 == 17\n")
    return project


@pytest.mark.parametrize(
    ("states", "expected"),
    [
        ([], 1),
        ([StageStatus.SUCCEEDED], 0),
        ([StageStatus.BLOCKED], 75),
        ([StageStatus.FAILED], 1),
        ([StageStatus.BLOCKED, StageStatus.FAILED], 1),
    ],
)
def test_check_summary_preserves_preparation_and_failure(states: list[StageStatus], expected: int) -> None:
    checks = [SetupCheckResult(f"check{index}", status, "observed") for index, status in enumerate(states)]
    code, lines = aggregate_check_results(checks)
    assert code == expected
    assert len(lines) == len(checks)
    assert all("observed" in line for line in lines)


def test_prepared_packages_check_actual_distribution_version() -> None:
    check_prepared_packages(["pytest>=7.0", "not-real-package; python_version < '3.0'"])
    with pytest.raises(PreparedRuntimeUnavailable, match="installed"):
        check_prepared_packages(["pytest>99999"])
    with pytest.raises(PreparedRuntimeUnavailable, match="unavailable"):
        check_prepared_packages(["template-deliberately-missing-prepared-requirement"])


def test_valid_project_discovery_and_missing_structure(tmp_path: Path) -> None:
    _make_valid_project(tmp_path, "domain")
    assert validate_project_discovery(tmp_path, "templates/domain")
    assert not validate_project_discovery(tmp_path, "templates/missing")


def test_hook_prerequisites_never_execute_provisioner(tmp_path: Path) -> None:
    project = _make_valid_project(tmp_path, "domain")
    marker = project / "must-not-provision"
    (project / "scripts/setup_hook.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('installed')\nraise SystemExit(7)\n"
    )
    assert check_setup_hook_prerequisites(tmp_path, "templates/domain")
    assert not marker.exists()
    (project / "scripts/setup_hook.yaml").write_text("required_tools: [template-tool-deliberately-not-installed]\n")
    assert not check_setup_hook_prerequisites(tmp_path, "templates/domain")
    assert not marker.exists()


@pytest.mark.parametrize(
    "metadata",
    ["broken: [", "- not-a-mapping\n", "required_tools: tools\n", "timeout_sec: true\n", "misspelled_tools: []\n"],
)
def test_malformed_hook_metadata_is_structural_refusal(tmp_path: Path, metadata: str) -> None:
    project = _make_valid_project(tmp_path, "domain")
    (project / "scripts/setup_hook.py").write_text("raise SystemExit(7)\n")
    (project / "scripts/setup_hook.yaml").write_text(metadata)
    with pytest.raises(ValueError):
        check_setup_hook_prerequisites(tmp_path, "templates/domain")


def test_hook_manifest_link_is_refused_without_external_mutation(tmp_path: Path) -> None:
    project = _make_valid_project(tmp_path, "domain")
    (project / "scripts/setup_hook.py").write_text("raise SystemExit(7)\n")
    outside = tmp_path / "external-private-manifest"
    outside.write_text("required_tools: []\n")
    (project / "scripts/setup_hook.yaml").symlink_to(outside)
    with pytest.raises((ValueError, OSError)):
        check_setup_hook_prerequisites(tmp_path, "templates/domain")
    assert outside.read_text() == "required_tools: []\n"


@pytest.mark.parametrize("name", ["setup_hook.py", "setup_hook.sh"])
@pytest.mark.parametrize("kind", ["directory", "fifo", "broken-link", "regular-link"])
def test_declared_nonregular_hook_without_manifest_is_refused(tmp_path: Path, name: str, kind: str) -> None:
    project = _make_valid_project(tmp_path, "domain")
    hook = project / "scripts" / name
    outside = tmp_path / "outside-hook"
    outside.write_text("raise SystemExit(7)\n")
    if kind == "directory":
        hook.mkdir()
    elif kind == "fifo":
        os.mkfifo(hook)
    else:
        hook.symlink_to(outside if kind == "regular-link" else tmp_path / "absent-hook")
    with pytest.raises((OSError, ValueError)):
        check_setup_hook_prerequisites(tmp_path, "templates/domain")
    assert outside.read_text() == "raise SystemExit(7)\n"
    assert not (project / "scripts/setup_hook.yaml").exists()


def test_valid_preferred_hook_cannot_hide_malformed_fallback(tmp_path: Path) -> None:
    project = _make_valid_project(tmp_path, "domain")
    (project / "scripts/setup_hook.py").write_text("raise SystemExit(7)\n")
    (project / "scripts/setup_hook.sh").mkdir()
    with pytest.raises((OSError, ValueError)):
        check_setup_hook_prerequisites(tmp_path, "templates/domain")


def test_whole_check_registry_never_syncs_or_runs_hook(tmp_path: Path) -> None:
    project = _make_valid_project(tmp_path, "domain")
    (tmp_path / "infrastructure").mkdir()
    marker = project / "must-not-provision"
    (project / "scripts/setup_hook.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('installed')\n"
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname="prepared-check"\nversion="0.0.0"\ndependencies=["template-deliberately-missing-prepared-requirement"]\n'
    )
    original = dict(os.environ)
    try:
        os.environ["TEMPLATE_ROOT_PYTHON"] = sys.executable
        results = run_environment_setup_checks(tmp_path, "templates/domain")
    finally:
        os.environ.clear()
        os.environ.update(original)
    assert next(row for row in results if row.name == "Dependencies").status is StageStatus.BLOCKED
    assert aggregate_check_results(results)[0] == 75
    assert not marker.exists() and not (tmp_path / ".venv").exists()
    assert not (tmp_path / "uv.lock").exists() and not (project / "output").exists()
    assert not (tmp_path / "output").exists()


def test_malformed_declared_dependencies_are_failure_not_unavailable(tmp_path: Path) -> None:
    _make_valid_project(tmp_path, "domain")
    (tmp_path / "pyproject.toml").write_text('[project]\nname="broken"\ndependencies="bad"\n')
    original = dict(os.environ)
    try:
        os.environ["TEMPLATE_ROOT_PYTHON"] = sys.executable
        results = run_environment_setup_checks(tmp_path, "templates/domain")
    finally:
        os.environ.clear()
        os.environ.update(original)
    assert next(row for row in results if row.name == "Dependencies").status is StageStatus.FAILED
    assert aggregate_check_results(results)[0] == 1
