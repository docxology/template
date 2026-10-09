"""Tests for exemplar collection and coverage refresh/CLI publication (split from test_counts_doc.py)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

import pytest

from infrastructure.documentation.counts_doc import (
    EXEMPLAR_SNAPSHOT,
    _exemplar_collected_count,
)
from infrastructure.documentation.counts_coverage import (
    _finalize_exemplar_coverage_result,
)
from infrastructure.documentation._coverage_snapshot_output import CoverageSnapshotOutput

from tests.infra_tests.documentation._counts_doc_helpers import (
    _repo_root,
)


# Several cases create temporary Git trees and exercise subprocess-backed
# provenance discovery. They are bounded, but can exceed the repository's
# 10-second default when the complete coverage suite is under load.
pytestmark = pytest.mark.timeout(30)


def test_exemplar_collection_uses_declared_dev_dependencies() -> None:
    count = _exemplar_collected_count(_repo_root(), "template_literature_meta_analysis")
    assert count > 0


@pytest.mark.timeout(300)
def test_exemplar_collection_injects_runner_when_project_venv_lacks_pytest() -> None:
    count = _exemplar_collected_count(_repo_root(), "template_autoresearch_project")
    assert count > 0


def test_exemplar_collection_ignores_stale_relocated_pytest_wrapper(tmp_path: Path) -> None:
    """Collection uses the resolved interpreter, never an absolute console wrapper."""
    project = tmp_path / "projects" / "templates" / "moved_project"
    tests = project / "tests"
    tests.mkdir(parents=True)
    (tests / "test_moved.py").write_text("def test_moved():\n    assert True\n", encoding="utf-8")

    venv.EnvBuilder(with_pip=False, symlinks=True).create(project / ".venv")
    selected = project / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    uv = shutil.which("uv")
    assert uv is not None
    environment = dict(os.environ)
    environment["UV_PROJECT_ENVIRONMENT"] = str(project / ".venv")
    # Locked sync consumes authenticated wheel URLs without needing cached index discovery.
    # Exclude the source project and optional Git scanner; install genuine Rootdev runners.
    installed = subprocess.run(
        [
            uv,
            "sync",
            "--project",
            str(_repo_root()),
            "--locked",
            "--offline",
            "--no-python-downloads",
            "--only-group",
            "dev",
            "--no-install-project",
            "--no-install-package",
            "desloppify",
            "--python",
            str(selected),
        ],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert installed.returncode == 0, installed.stderr
    wrapper = project / ".venv" / "bin" / "pytest"
    stale_contents = b"#!/checkout/that/no/longer/exists/.venv/bin/python\n"
    wrapper.write_bytes(stale_contents)
    wrapper.chmod(0o755)

    assert _exemplar_collected_count(tmp_path, "moved_project") == 1
    assert wrapper.read_bytes() == stale_contents


def _snapshot_data(tmp_path: Path) -> tuple[CoverageSnapshotOutput, bytes]:
    from infrastructure.documentation import counts_coverage

    protected_repo = tmp_path / "repo"
    protected_repo.mkdir()
    selected_source = Path(counts_coverage.__file__)
    data_copy = tmp_path / "counts_coverage.snapshot.data"
    shutil.copy2(selected_source, data_copy)
    original = data_copy.read_bytes()
    return CoverageSnapshotOutput.admit(protected_repo, data_copy, selected_source), original


def test_exemplar_snapshot_rewrite_updates_only_named_rows(tmp_path: Path) -> None:
    """The existing writer changes retained DATA and preserves consumed Source."""
    from infrastructure.documentation import counts_doc

    output, original = _snapshot_data(tmp_path)
    name = EXEMPLAR_SNAPSHOT[0].name
    counts_doc._rewrite_exemplar_snapshot({name: "77.77 %"}, output)

    rewritten = output.path.read_text(encoding="utf-8")
    expected = original.decode().replace(
        f'ExemplarSnapshot("{name}", "{EXEMPLAR_SNAPSHOT[0].coverage_pct}")',
        f'ExemplarSnapshot("{name}", "77.77 %")',
    )
    assert rewritten == expected
    assert output.source.read_bytes() == original
    assert output.path.stat().st_nlink == 1


def test_exemplar_snapshot_rewrite_is_a_noop_without_measurements(tmp_path: Path) -> None:
    """An empty measurement map preserves the admitted copy and Source."""
    from infrastructure.documentation import counts_doc

    output, original = _snapshot_data(tmp_path)
    counts_doc._rewrite_exemplar_snapshot({}, output)
    assert output.path.read_bytes() == original
    assert output.source.read_bytes() == original


def test_coverage_refresh_does_not_publish_partial_measurements(tmp_path: Path) -> None:
    """One failed exemplar leaves the complete retained DATA snapshot untouched."""
    output, original = _snapshot_data(tmp_path)
    snapshot = EXEMPLAR_SNAPSHOT[:2]

    result = _finalize_exemplar_coverage_result(
        {snapshot[0].name: "77.77 %"},
        [f"{snapshot[1].name}: coverage process failed"],
        rewrite=True,
        snapshot=snapshot,
        snapshot_output=output,
    )

    assert not result.all_match
    assert not result.measurement_complete
    assert not result.snapshot_rewritten
    assert result.failed_count == 1
    assert result.measured_count == 1
    assert "EXEMPLAR_SNAPSHOT not rewritten" in result.report
    assert output.path.read_bytes() == original
    assert output.source.read_bytes() == original


def test_coverage_refresh_publishes_complete_measurement_set(tmp_path: Path) -> None:
    """The real finalizer writes DATA only for its complete nominated row set."""
    output, original = _snapshot_data(tmp_path)
    snapshot = EXEMPLAR_SNAPSHOT[:2]
    result = _finalize_exemplar_coverage_result(
        {snapshot[0].name: "77.77 %", snapshot[1].name: "88.88 %"},
        [],
        rewrite=True,
        snapshot=snapshot,
        snapshot_output=output,
    )

    assert not result.all_match
    assert result.measurement_complete
    assert result.snapshot_rewritten
    assert result.failed_count == 0
    assert result.drifted_count == 2
    rewritten = output.path.read_text(encoding="utf-8")
    assert f'ExemplarSnapshot("{snapshot[0].name}", "77.77 %")' in rewritten
    assert f'ExemplarSnapshot("{snapshot[1].name}", "88.88 %")' in rewritten
    assert output.source.read_bytes() == original


def test_counts_cli_fails_when_coverage_measurements_are_missing(tmp_path: Path) -> None:
    """The real CLI exits nonzero and writes nothing for an incomplete checkout."""
    repo_root = _repo_root()
    source_script = repo_root / "scripts" / "docgen" / "counts.py"
    copied_script = tmp_path / "checkout" / "scripts" / "docgen" / "counts.py"
    copied_script.parent.mkdir(parents=True)
    copied_script.write_bytes(source_script.read_bytes())
    before = copied_script.read_bytes()
    environment = dict(os.environ)
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        f"{repo_root}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else str(repo_root)
    )

    from infrastructure.documentation import counts_coverage

    retained_data = tmp_path / "counts_coverage.snapshot.data"
    shutil.copy2(Path(counts_coverage.__file__), retained_data)
    original_data = retained_data.read_bytes()
    run = subprocess.run(
        [
            sys.executable,
            str(copied_script),
            "--verify-coverage",
            "--write",
            "--coverage-snapshot-output",
            str(retained_data),
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert run.returncode == 1, run.stdout + run.stderr
    assert f"{len(EXEMPLAR_SNAPSHOT)} failed, 0 measured" in run.stdout
    assert "coverage snapshot not refreshed" in run.stdout
    assert not (tmp_path / "docs").exists()
    assert copied_script.read_bytes() == before
    assert retained_data.read_bytes() == original_data
