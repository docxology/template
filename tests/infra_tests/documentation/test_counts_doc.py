"""Tests for ``infrastructure.documentation.counts_doc``.

Real I/O only (no mocks). The fast derivations (tracked-py count, package list)
run against the live repo tree; the renderer is exercised with a real
``CountsFacts`` value built in-test and against the on-disk ``COUNTS.md``.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

from infrastructure.documentation.counts_doc import (
    COVERAGE_PROVENANCE_RELATIVE_PATH,
    COVERAGE_PROVENANCE_SCHEMA_VERSION,
    DOC_RELATIVE_PATH,
    EXEMPLAR_SNAPSHOT,
    CountsFacts,
    _exemplar_collected_count,
    exemplar_source_hash,
    infrastructure_packages,
    render_counts_doc,
    tracked_infra_python_count,
    validate_coverage_provenance,
    write_counts_doc,
)
from infrastructure.project.public_scope import public_project_names


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


def test_write_round_trips_supplied_facts(tmp_path: Path) -> None:
    """Writing supplied facts exercises real I/O without 23 subprocesses."""
    facts = CountsFacts(
        public_projects=[s.name for s in EXEMPLAR_SNAPSHOT],
        packages=["core"],
        infra_py_count=1,
        project_tests=2,
        publishing_tests=3,
        exemplar_tests={s.name: 1 for s in EXEMPLAR_SNAPSHOT},
    )
    target = tmp_path / "COUNTS.md"
    write_counts_doc(_repo_root(), out_path=target, facts=facts)
    assert target.read_text(encoding="utf-8") == render_counts_doc(facts)


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

    assert COVERAGE_PROVENANCE_SCHEMA_VERSION == 2


def test_exemplar_collection_uses_declared_dev_dependencies() -> None:
    count = _exemplar_collected_count(_repo_root(), "template_literature_meta_analysis")
    assert count > 0
