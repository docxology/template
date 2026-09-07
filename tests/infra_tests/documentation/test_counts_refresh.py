"""Tests for exemplar collection and coverage refresh/CLI publication (split from test_counts_doc.py)."""

from __future__ import annotations

import os
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
    ExemplarSnapshot,
    _finalize_exemplar_coverage_result,
)

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

    venv.EnvBuilder(with_pip=False, system_site_packages=True).create(project / ".venv")
    wrapper = project / ".venv" / "bin" / "pytest"
    stale_contents = b"#!/checkout/that/no/longer/exists/.venv/bin/python\n"
    wrapper.write_bytes(stale_contents)
    wrapper.chmod(0o755)

    assert _exemplar_collected_count(tmp_path, "moved_project") == 1
    assert wrapper.read_bytes() == stale_contents


def test_exemplar_snapshot_rewrite_updates_only_named_rows(tmp_path: Path) -> None:
    """`--verify-coverage --write` must rewrite measured rows and leave others alone.

    The recorded percentages were unverifiable until 2026-07-27: provenance only
    checked that the source had not changed since a number was written, never that
    the number was right. Two exemplars were found ~1.4pp and ~0.6pp adrift. This
    guards the rewrite path that now refreshes them from a real measurement.
    """
    from infrastructure.documentation import counts_doc

    module_copy = tmp_path / "counts_doc_copy.py"
    module_copy.write_text(
        'ExemplarSnapshot("template_alpha", "10.00 %"),\n'
        'ExemplarSnapshot("template_beta", "20.00 %"),\n'
        'ExemplarSnapshot("template_gamma", "30.00 %"),\n',
        encoding="utf-8",
    )
    counts_doc._rewrite_exemplar_snapshot({"template_beta": "77.77 %"}, module_copy)

    rewritten = module_copy.read_text(encoding="utf-8")
    assert 'ExemplarSnapshot("template_beta", "77.77 %")' in rewritten
    assert 'ExemplarSnapshot("template_alpha", "10.00 %")' in rewritten
    assert 'ExemplarSnapshot("template_gamma", "30.00 %")' in rewritten


def test_exemplar_snapshot_rewrite_is_a_noop_without_measurements(tmp_path: Path) -> None:
    """An empty measurement map must not blank out the recorded values."""
    from infrastructure.documentation import counts_doc

    module_copy = tmp_path / "counts_doc_copy.py"
    original = 'ExemplarSnapshot("template_alpha", "10.00 %"),\n'
    module_copy.write_text(original, encoding="utf-8")
    counts_doc._rewrite_exemplar_snapshot({}, module_copy)
    assert module_copy.read_text(encoding="utf-8") == original


def test_coverage_refresh_does_not_publish_partial_measurements(tmp_path: Path) -> None:
    """One failed exemplar leaves the complete recorded snapshot untouched."""
    snapshot = (
        ExemplarSnapshot("template_alpha", "10.00 %"),
        ExemplarSnapshot("template_beta", "20.00 %"),
    )
    module_copy = tmp_path / "counts_coverage_copy.py"
    original = 'ExemplarSnapshot("template_alpha", "10.00 %"),\nExemplarSnapshot("template_beta", "20.00 %"),\n'
    module_copy.write_text(original, encoding="utf-8")

    result = _finalize_exemplar_coverage_result(
        {"template_alpha": "77.77 %"},
        ["template_beta: coverage process failed"],
        rewrite=True,
        snapshot=snapshot,
        source_path=module_copy,
    )

    assert not result.all_match
    assert not result.measurement_complete
    assert not result.snapshot_rewritten
    assert result.failed_count == 1
    assert result.measured_count == 1
    assert "EXEMPLAR_SNAPSHOT not rewritten" in result.report
    assert module_copy.read_text(encoding="utf-8") == original


def test_coverage_refresh_publishes_complete_measurement_set(tmp_path: Path) -> None:
    """A complete measurement may replace every drifted recorded value."""
    snapshot = (
        ExemplarSnapshot("template_alpha", "10.00 %"),
        ExemplarSnapshot("template_beta", "20.00 %"),
    )
    module_copy = tmp_path / "counts_coverage_copy.py"
    module_copy.write_text(
        'ExemplarSnapshot("template_alpha", "10.00 %"),\nExemplarSnapshot("template_beta", "20.00 %"),\n',
        encoding="utf-8",
    )

    result = _finalize_exemplar_coverage_result(
        {"template_alpha": "77.77 %", "template_beta": "88.88 %"},
        [],
        rewrite=True,
        snapshot=snapshot,
        source_path=module_copy,
    )

    assert not result.all_match
    assert result.measurement_complete
    assert result.snapshot_rewritten
    assert result.failed_count == 0
    assert result.drifted_count == 2
    rewritten = module_copy.read_text(encoding="utf-8")
    assert 'ExemplarSnapshot("template_alpha", "77.77 %")' in rewritten
    assert 'ExemplarSnapshot("template_beta", "88.88 %")' in rewritten


def test_counts_cli_fails_when_coverage_measurements_are_missing(tmp_path: Path) -> None:
    """The real CLI exits nonzero and writes nothing for an incomplete checkout."""
    repo_root = _repo_root()
    source_script = repo_root / "scripts" / "docgen" / "counts.py"
    copied_script = tmp_path / "scripts" / "docgen" / "counts.py"
    copied_script.parent.mkdir(parents=True)
    copied_script.write_bytes(source_script.read_bytes())
    before = copied_script.read_bytes()
    environment = dict(os.environ)
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        f"{repo_root}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else str(repo_root)
    )

    run = subprocess.run(
        [sys.executable, str(copied_script), "--verify-coverage", "--write"],
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
