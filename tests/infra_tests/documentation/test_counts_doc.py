"""Tests for ``infrastructure.documentation.counts_doc``.

Real I/O only (no mocks). The fast derivations (tracked-py count, package list)
run against the live repo tree; the renderer is exercised with a real
``CountsFacts`` value built in-test and against the on-disk ``COUNTS.md``.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import venv
from pathlib import Path

import pytest

from infrastructure.documentation.counts_doc import (
    COVERAGE_PROVENANCE_RELATIVE_PATH,
    COVERAGE_PROVENANCE_SCHEMA_VERSION,
    COVERAGE_MEASUREMENT_TIMEOUT_SECONDS,
    DOC_RELATIVE_PATH,
    EXEMPLAR_SNAPSHOT,
    CountsFacts,
    _coverage_measurement_data_file,
    _exemplar_collected_count,
    exemplar_source_hash,
    infrastructure_packages,
    render_counts_doc,
    tracked_infra_python_count,
    validate_coverage_provenance,
    write_counts_doc,
)
from infrastructure.documentation.counts_coverage import (
    ExemplarSnapshot,
    _finalize_exemplar_coverage_result,
)
from infrastructure.project.public_scope import public_project_names


# Several cases create temporary Git trees and exercise subprocess-backed
# provenance discovery. They are bounded, but can exceed the repository's
# 10-second default when the complete coverage suite is under load.
pytestmark = pytest.mark.timeout(30)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_tracked_infra_python_count_is_positive() -> None:
    """The tracked-py derivation returns the live git-tracked count."""
    count = tracked_infra_python_count(_repo_root())
    assert count > 100  # sanity floor; the tree has hundreds of modules


def test_infrastructure_packages_excludes_private_and_is_sorted() -> None:
    """Package discovery is sorted and skips dunder/underscore dirs."""
    pkgs = infrastructure_packages(_repo_root())
    assert pkgs == sorted(pkgs)
    assert "core" in pkgs
    assert all(not p.startswith("_") for p in pkgs)


def test_render_contains_parseable_markers() -> None:
    """The rendered doc carries the literals the consistency gates parse."""
    facts = CountsFacts(
        public_projects=["template_alpha", "template_beta"],
        packages=["core", "validation"],
        infra_py_count=553,
        project_tests=228,
        publishing_tests=395,
        exemplar_tests={"template_alpha": 7, "template_beta": 11},
    )
    doc = render_counts_doc(facts)

    count_match = re.search(r"Last refreshed count: \*\*(?P<count>\d+)\*\*", doc)
    assert count_match and int(count_match.group("count")) == 553

    collect_match = re.search(
        r"Result: \*\*(?P<project>\d+)\*\* project-scope infrastructure tests collected "
        r"and \*\*(?P<publishing>\d+)\*\* publishing tests collected",
        doc,
    )
    assert collect_match
    assert int(collect_match.group("project")) == 228
    assert int(collect_match.group("publishing")) == 395

    # Roster names round-trip into both roster blocks.
    assert "- `template_alpha`" in doc
    assert "- `template_beta`" in doc
    # Module count flows into the header and the mermaid diagram.
    assert "importable packages" in doc
    assert "(2)" in doc


def test_render_exemplar_table_one_row_per_snapshot() -> None:
    """Every measured snapshot row appears in the rendered table."""
    facts = CountsFacts(
        public_projects=[s.name for s in EXEMPLAR_SNAPSHOT],
        packages=["core"],
        infra_py_count=1,
        project_tests=1,
        publishing_tests=1,
        exemplar_tests={s.name: index for index, s in enumerate(EXEMPLAR_SNAPSHOT, 1)},
    )
    doc = render_counts_doc(facts)
    for index, snap in enumerate(EXEMPLAR_SNAPSHOT, 1):
        assert f"| `{snap.name}` | {index} | {snap.coverage_pct} |" in doc


def test_exemplar_snapshot_covers_public_scope() -> None:
    """The measured snapshot has exactly one row per public exemplar."""
    expected = {name.split("/")[-1] for name in public_project_names(_repo_root())}
    documented = {s.name for s in EXEMPLAR_SNAPSHOT}
    assert documented == expected


def test_coverage_measurement_uses_bounded_release_profile() -> None:
    """Coverage receipts must use the shared release selection and timeout policy."""
    from infrastructure.documentation.counts_doc import _coverage_measurement_command

    command = _coverage_measurement_command(Path("/tmp/project"))
    marker = command[command.index("-m") + 1]

    assert "not requires_ollama" in marker
    assert "not long_running" in marker
    assert "not bench" in marker
    assert COVERAGE_MEASUREMENT_TIMEOUT_SECONDS == 1800


def test_coverage_measurement_data_file_is_absolute_for_relative_checkout() -> None:
    """Coverage cleanup must target the same path the subprocess writes."""
    checkout = Path("relative-checkout")

    data_file = _coverage_measurement_data_file(checkout, "demo")

    assert data_file == checkout.resolve() / "projects" / "templates" / "demo" / ".coverage.measure_demo"
    assert data_file.is_absolute()


def test_write_round_trips_supplied_facts(tmp_path: Path) -> None:
    """Writing supplied facts exercises real I/O without 23 subprocesses."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    facts = CountsFacts(
        public_projects=[s.name for s in EXEMPLAR_SNAPSHOT],
        packages=["core"],
        infra_py_count=1,
        project_tests=2,
        publishing_tests=3,
        exemplar_tests={s.name: 1 for s in EXEMPLAR_SNAPSHOT},
    )
    target = tmp_path / "COUNTS.md"
    write_counts_doc(repo_root, out_path=target, facts=facts)
    assert target.read_text(encoding="utf-8") == render_counts_doc(facts)


def test_write_canonical_counts_requires_coverage_provenance(tmp_path: Path) -> None:
    """The canonical writer cannot bypass source-bound coverage provenance."""
    facts = CountsFacts(
        public_projects=[s.name for s in EXEMPLAR_SNAPSHOT],
        packages=["core"],
        infra_py_count=1,
        project_tests=2,
        publishing_tests=3,
        exemplar_tests={s.name: 1 for s in EXEMPLAR_SNAPSHOT},
    )

    with pytest.raises(RuntimeError, match="missing coverage provenance"):
        write_counts_doc(tmp_path, facts=facts)


def test_doc_relative_path_points_at_counts_md() -> None:
    """The generator targets COUNTS.md, not the retired COUNTS.md."""
    assert DOC_RELATIVE_PATH == Path("docs/_generated/COUNTS.md")
    assert COVERAGE_PROVENANCE_RELATIVE_PATH == Path("docs/_generated/coverage_snapshot.json")


def test_exemplar_source_hash_changes_with_source(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "templates" / "demo"
    (project / "src").mkdir(parents=True)
    (project / "tests").mkdir()
    source = project / "src" / "demo.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    before = exemplar_source_hash(tmp_path, "demo")
    source.write_text("VALUE = 2\n", encoding="utf-8")
    assert exemplar_source_hash(tmp_path, "demo") != before


def test_exemplar_source_hash_ignores_untracked_build_metadata(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "templates" / "demo"
    source = project / "src" / "demo.py"
    test_file = project / "tests" / "test_demo.py"
    source.parent.mkdir(parents=True)
    test_file.parent.mkdir()
    source.write_text("VALUE = 1\n", encoding="utf-8")
    test_file.write_text("def test_value():\n    assert True\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "--", source, test_file], cwd=tmp_path, check=True)

    before = exemplar_source_hash(tmp_path, "demo")
    metadata = project / "src" / "demo.egg-info" / "PKG-INFO"
    metadata.parent.mkdir()
    metadata.write_text("platform-specific generated metadata\n", encoding="utf-8")

    assert exemplar_source_hash(tmp_path, "demo") == before


def test_exemplar_source_hash_tracks_untracked_source_before_staging(tmp_path: Path) -> None:
    """A new source file changes provenance before it crosses the staging boundary."""
    project = tmp_path / "projects" / "templates" / "demo"
    source = project / "src" / "demo.py"
    test_file = project / "tests" / "test_demo.py"
    source.parent.mkdir(parents=True)
    test_file.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    test_file.write_text("def test_value():\n    assert True\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "--", source, test_file], cwd=tmp_path, check=True)

    before = exemplar_source_hash(tmp_path, "demo")
    new_source = project / "src" / "new_surface.py"
    new_source.write_text("VALUE = 2\n", encoding="utf-8")

    assert exemplar_source_hash(tmp_path, "demo") != before


def test_exemplar_source_hash_tracks_linked_shared_source(tmp_path: Path) -> None:
    """Tracked project symlinks include their in-repository target content."""
    project = tmp_path / "projects" / "templates" / "demo"
    shared = tmp_path / "projects" / "templates" / "shared" / "src"
    tests = project / "tests"
    (project / "src").mkdir(parents=True)
    shared.mkdir(parents=True)
    tests.mkdir()
    shared_source = shared / "shared.py"
    shared_source.write_text("VALUE = 1\n", encoding="utf-8")
    linked_source = project / "src" / "shared"
    linked_source.symlink_to(shared, target_is_directory=True)
    test_file = tests / "test_demo.py"
    test_file.write_text("def test_value():\n    assert True\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "--", linked_source, shared_source, test_file], cwd=tmp_path, check=True)

    before = exemplar_source_hash(tmp_path, "demo")
    shared_source.write_text("VALUE = 2\n", encoding="utf-8")

    assert exemplar_source_hash(tmp_path, "demo") != before


def test_coverage_provenance_rejects_legacy_hash_schema(tmp_path: Path) -> None:
    projects: dict[str, dict[str, str]] = {}
    for snapshot in EXEMPLAR_SNAPSHOT:
        project = tmp_path / "projects" / "templates" / snapshot.name
        (project / "src").mkdir(parents=True)
        (project / "tests").mkdir()
        projects[snapshot.name] = {
            "coverage_pct": snapshot.coverage_pct,
            "source_hash": exemplar_source_hash(tmp_path, snapshot.name),
        }
    path = tmp_path / COVERAGE_PROVENANCE_RELATIVE_PATH
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"schema_version": 1, "projects": projects}), encoding="utf-8")

    with pytest.raises(RuntimeError, match="schema mismatch"):
        validate_coverage_provenance(tmp_path)

    assert COVERAGE_PROVENANCE_SCHEMA_VERSION == 3


def test_coverage_provenance_requires_source_tree_identity(tmp_path: Path) -> None:
    path = tmp_path / COVERAGE_PROVENANCE_RELATIVE_PATH
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": COVERAGE_PROVENANCE_SCHEMA_VERSION,
                "source_inventory_mode": "tracked-and-nonignored-working-tree",
                "projects": {},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="source-tree identity"):
        validate_coverage_provenance(tmp_path)


@pytest.mark.timeout(300)
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
