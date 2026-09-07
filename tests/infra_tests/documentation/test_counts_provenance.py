"""Tests for counts provenance validation and exemplar source hashing (split from test_counts_doc.py)."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from infrastructure.documentation.counts_doc import (
    COVERAGE_PROVENANCE_RELATIVE_PATH,
    COVERAGE_PROVENANCE_SCHEMA_VERSION,
    DOC_RELATIVE_PATH,
    EXEMPLAR_SNAPSHOT,
    CountsFacts,
    exemplar_source_hash,
    render_counts_doc,
    validate_coverage_provenance,
    write_counts_doc,
)
from infrastructure.documentation.counts_coverage import (
    COVERAGE_SOURCE_INVENTORY_MODE,
    COVERAGE_SUPPORT_IDENTITY_MODE,
    _coverage_total_from_report,
    _nul_delimited_git_paths,
    _validated_coverage_report,
    build_coverage_provenance,
)

from tests.infra_tests.documentation._counts_doc_helpers import (
    _initialize_test_git_repository,
    _write_test_coverage_support_closure,
)


# Several cases create temporary Git trees and exercise subprocess-backed
# provenance discovery. They are bounded, but can exceed the repository's
# 10-second default when the complete coverage suite is under load.
pytestmark = pytest.mark.timeout(30)


@pytest.mark.parametrize(
    "payload",
    (
        "no total row\n",
        "TOTAL 10 0 nan%\n",
        "TOTAL 10 0 inf%\n",
        "TOTAL 10 0 -0.01%\n",
        "TOTAL 10 0 100.01%\n",
        "TOTAL 10 0 92.63\n",
        "TOTAL 10 0 92.63%\nTOTAL 10 0 92.63%\n",
    ),
)
def test_coverage_total_parser_rejects_missing_or_nonfinite_percentages(payload: str) -> None:
    with pytest.raises(RuntimeError, match="invalid or missing TOTAL"):
        _coverage_total_from_report(payload, "demo")


def test_coverage_report_result_fails_closed_and_accepts_one_finite_total() -> None:
    from infrastructure.core.execution_boundary import BoundedSubprocessResult

    base = {"argv": ("coverage", "report"), "returncode": 0, "timed_out": False}
    assert (
        _validated_coverage_report(
            BoundedSubprocessResult(**base, stdout="Name Stmts Miss Cover\nTOTAL 10 1 92.63%\n"),
            "demo",
        )
        == "92.63 %"
    )
    with pytest.raises(RuntimeError, match="timed out"):
        _validated_coverage_report(BoundedSubprocessResult(**(base | {"timed_out": True})), "demo")
    with pytest.raises(RuntimeError, match="exit 4"):
        _validated_coverage_report(
            BoundedSubprocessResult(**(base | {"returncode": 4}), stderr="bad data"),
            "demo",
        )
    with pytest.raises(RuntimeError, match="cannot execute"):
        _validated_coverage_report(BoundedSubprocessResult(**base, command_error="cannot execute"), "demo")


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
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    before = exemplar_source_hash(tmp_path, "demo")
    source.write_text("VALUE = 2\n", encoding="utf-8")
    assert exemplar_source_hash(tmp_path, "demo") != before


def test_exemplar_source_hash_requires_git_inventory(tmp_path: Path) -> None:
    source = tmp_path / "projects" / "templates" / "demo" / "src" / "demo.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="requires successful Git tracked/nonignored queries"):
        exemplar_source_hash(tmp_path, "demo")


def test_coverage_provenance_ignores_ambient_git_repository_redirection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "canonical"
    for row in EXEMPLAR_SNAPSHOT:
        source = repo_root / "projects" / "templates" / row.name / "src" / "sentinel.py"
        source.parent.mkdir(parents=True)
        source.write_text(f'PROJECT = "{row.name}"\n', encoding="utf-8")
    _write_test_coverage_support_closure(repo_root)

    shared = repo_root / "shared" / "linked"
    shared.mkdir(parents=True)
    shared_source = shared / "sentinel.py"
    shared_source.write_text("VALUE = 'canonical'\n", encoding="utf-8")
    linked_source = repo_root / "projects" / "templates" / "template_active_inference" / "src" / "shared"
    try:
        linked_source.symlink_to(shared, target_is_directory=True)
    except OSError:
        # Repository/commit redirection remains testable on platforms where
        # creating a directory symlink is not available to this process.
        pass

    canonical_head = _initialize_test_git_repository(repo_root)
    canonical_active_hash = exemplar_source_hash(repo_root, "template_active_inference")

    attacker = tmp_path / "attacker"
    attacker_source = attacker / "attacker.py"
    attacker_source.parent.mkdir(parents=True)
    attacker_source.write_text("VALUE = 'attacker'\n", encoding="utf-8")
    attacker_head = _initialize_test_git_repository(attacker)
    attacker_before = attacker_source.read_bytes()
    excludes = attacker / "ambient-excludes"
    excludes.write_text("projects/\n", encoding="utf-8")

    monkeypatch.setenv("GIT_DIR", str(attacker / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(attacker))
    monkeypatch.setenv("GIT_INDEX_FILE", str(attacker / ".git" / "index"))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.excludesfile")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", str(excludes))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(attacker / "ambient.gitconfig"))

    payload = build_coverage_provenance(repo_root)

    assert payload["source_commit"] == canonical_head
    assert payload["projects"]["template_active_inference"]["source_hash"] == canonical_active_hash
    assert attacker_source.read_bytes() == attacker_before
    assert (
        subprocess.run(
            ["git", "-C", str(attacker), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            env={key: value for key, value in os.environ.items() if not key.startswith("GIT_")},
        ).stdout.strip()
        == attacker_head
    )


def test_coverage_provenance_fails_closed_when_git_cannot_start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATH", "")

    with pytest.raises(RuntimeError, match="Git context failed while resolving the coverage provenance source commit"):
        build_coverage_provenance(tmp_path)


def test_exemplar_source_hash_tracks_newline_named_direct_inputs(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "templates" / "demo"
    direct_tracked = project / "src" / "tracked\nsource.py"
    direct_untracked = project / "tests" / "untracked\ntest.py"
    direct_tracked.parent.mkdir(parents=True)
    direct_untracked.parent.mkdir(parents=True)
    direct_tracked.write_text("VALUE = 1\n", encoding="utf-8")
    direct_untracked.write_text("VALUE = 1\n", encoding="utf-8")

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "--", direct_tracked], cwd=tmp_path, check=True)

    for path in (direct_tracked, direct_untracked):
        before = exemplar_source_hash(tmp_path, "demo")
        path.write_text("VALUE = 2\n", encoding="utf-8")
        assert exemplar_source_hash(tmp_path, "demo") != before


def test_exemplar_source_hash_tracks_newline_named_linked_inputs(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "templates" / "demo"
    (project / "src").mkdir(parents=True)

    shared = tmp_path / "shared" / "source"
    shared.mkdir(parents=True)
    linked_tracked = shared / "tracked\nlinked.py"
    linked_untracked = shared / "untracked\nlinked.py"
    linked_tracked.write_text("VALUE = 1\n", encoding="utf-8")
    linked_untracked.write_text("VALUE = 1\n", encoding="utf-8")
    link = project / "src" / "shared"
    try:
        link.symlink_to(shared, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "add", "--", linked_tracked, link],
        cwd=tmp_path,
        check=True,
    )

    for path in (linked_tracked, linked_untracked):
        before = exemplar_source_hash(tmp_path, "demo")
        path.write_text("VALUE = 2\n", encoding="utf-8")
        assert exemplar_source_hash(tmp_path, "demo") != before


def test_nul_delimited_git_paths_preserve_newlines_and_fail_closed() -> None:
    assert _nul_delimited_git_paths("first\npath\0second path\0", inventory="test") == [
        "first\npath",
        "second path",
    ]
    assert _nul_delimited_git_paths("", inventory="test") == []
    with pytest.raises(RuntimeError, match="non-NUL-terminated"):
        _nul_delimited_git_paths("first\npath", inventory="test")
    with pytest.raises(RuntimeError, match="empty pathname"):
        _nul_delimited_git_paths("first\0\0", inventory="test")


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


@pytest.mark.parametrize(
    "relative_path",
    (
        "pyproject.toml",
        "uv.lock",
        ".coveragerc",
        "conftest.py",
        "scripts/run_full_verification.py",
        "config/settings.yaml",
        "data/fixture.json",
        "manuscript/config.yaml",
    ),
)
def test_exemplar_source_hash_tracks_project_coverage_inputs(tmp_path: Path, relative_path: str) -> None:
    project = tmp_path / "projects" / "templates" / "demo"
    path = project / relative_path
    path.parent.mkdir(parents=True)
    path.write_text("version = 1\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)

    before = exemplar_source_hash(tmp_path, "demo")
    path.write_text("version = 2\n", encoding="utf-8")

    assert exemplar_source_hash(tmp_path, "demo") != before


@pytest.mark.parametrize(
    "relative_path",
    (
        "output/data/result.json",
        "rendered/book.pdf",
        ".pytest_cache/v/cache/nodeids",
        ".coverage.measure_demo",
        ".env",
        ".direnv/python/runtime.py",
        ".pipeline/checkpoint.json",
        ".ipynb_checkpoints/notebook-checkpoint.ipynb",
        "build/generated.py",
        "env/lib/runtime.py",
        "venv/lib/runtime.py",
        "ENV/lib/runtime.py",
        "env.bak/lib/runtime.py",
        "venv.bak/lib/runtime.py",
    ),
)
def test_exemplar_source_hash_ignores_output_and_runtime_cache_changes(tmp_path: Path, relative_path: str) -> None:
    project = tmp_path / "projects" / "templates" / "demo"
    source = project / "src" / "demo.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    path = project / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("version = 1\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)

    before = exemplar_source_hash(tmp_path, "demo")
    path.write_text("version = 2\n", encoding="utf-8")

    assert exemplar_source_hash(tmp_path, "demo") == before


def test_exemplar_source_hash_ignores_untracked_gitignored_project_files(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "templates" / "demo"
    source = project / "src" / "demo.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    ignore = project / ".gitignore"
    ignore.write_text("scratch/\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "--", source, ignore], cwd=tmp_path, check=True)

    before = exemplar_source_hash(tmp_path, "demo")
    ignored = project / "scratch" / "runtime.txt"
    ignored.parent.mkdir()
    ignored.write_text("ephemeral\n", encoding="utf-8")

    assert exemplar_source_hash(tmp_path, "demo") == before


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
    shared_output = shared / "output" / "generated.json"
    shared_output.parent.mkdir()
    shared_output.write_text('{"value": 1}\n', encoding="utf-8")
    linked_source = project / "src" / "shared"
    linked_source.symlink_to(shared, target_is_directory=True)
    test_file = tests / "test_demo.py"
    test_file.write_text("def test_value():\n    assert True\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "add", "--", linked_source, shared_source, shared_output, test_file],
        cwd=tmp_path,
        check=True,
    )

    before = exemplar_source_hash(tmp_path, "demo")
    shared_output.write_text('{"value": 2}\n', encoding="utf-8")
    assert exemplar_source_hash(tmp_path, "demo") == before
    shared_source.write_text("VALUE = 2\n", encoding="utf-8")

    assert exemplar_source_hash(tmp_path, "demo") != before


def test_exemplar_source_hash_tracks_confined_file_symlink_target(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "templates" / "demo"
    shared = tmp_path / "projects" / "templates" / "shared" / "src" / "config_loader.py"
    link = project / "src" / "config_loader.py"
    shared.parent.mkdir(parents=True)
    link.parent.mkdir(parents=True)
    shared.write_text("VALUE = 1\n", encoding="utf-8")
    try:
        link.symlink_to(shared)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "--", shared, link], cwd=tmp_path, check=True)

    before = exemplar_source_hash(tmp_path, "demo")
    shared.write_text("VALUE = 2\n", encoding="utf-8")

    assert exemplar_source_hash(tmp_path, "demo") != before


def test_exemplar_source_hash_rejects_file_symlink_to_internal_output(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "templates" / "demo"
    generated = tmp_path / "projects" / "templates" / "shared" / "output" / "result.json"
    link = project / "src" / "linked_result.json"
    generated.parent.mkdir(parents=True)
    link.parent.mkdir(parents=True)
    generated.write_bytes(b"GENERATED\n")
    try:
        link.symlink_to(generated)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "--", generated, link], cwd=tmp_path, check=True)

    with pytest.raises(RuntimeError, match="targets an excluded runtime or output path"):
        exemplar_source_hash(tmp_path, "demo")

    assert generated.read_bytes() == b"GENERATED\n"


def test_exemplar_source_hash_rejects_file_symlink_outside_repository(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project = repo_root / "projects" / "templates" / "demo"
    external = tmp_path / "external.txt"
    link = project / "src" / "external.txt"
    external.write_bytes(b"EXTERNAL\n")
    link.parent.mkdir(parents=True)
    try:
        link.symlink_to(external)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "add", "--", link], cwd=repo_root, check=True)

    with pytest.raises(RuntimeError, match="escapes the repository"):
        exemplar_source_hash(repo_root, "demo")

    assert external.read_bytes() == b"EXTERNAL\n"


def test_coverage_provenance_rejects_legacy_hash_schema(tmp_path: Path) -> None:
    path = tmp_path / COVERAGE_PROVENANCE_RELATIVE_PATH
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"schema_version": 1, "projects": {}}), encoding="utf-8")

    with pytest.raises(RuntimeError, match="schema mismatch"):
        validate_coverage_provenance(tmp_path)

    assert COVERAGE_PROVENANCE_SCHEMA_VERSION == 5


def test_coverage_provenance_rejects_legacy_source_inventory_mode(tmp_path: Path) -> None:
    path = tmp_path / COVERAGE_PROVENANCE_RELATIVE_PATH
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": COVERAGE_PROVENANCE_SCHEMA_VERSION,
                "source_inventory_mode": "tracked-and-nonignored-working-tree",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="source inventory mode"):
        validate_coverage_provenance(tmp_path)

    assert COVERAGE_SOURCE_INVENTORY_MODE == "tracked-and-nonignored-coverage-inputs-v3"
    assert COVERAGE_SUPPORT_IDENTITY_MODE == "explicit-public-documentation-support-v1"


def test_coverage_provenance_requires_source_tree_identity(tmp_path: Path) -> None:
    path = tmp_path / COVERAGE_PROVENANCE_RELATIVE_PATH
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": COVERAGE_PROVENANCE_SCHEMA_VERSION,
                "source_inventory_mode": COVERAGE_SOURCE_INVENTORY_MODE,
                "projects": {},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="source-tree identity"):
        validate_coverage_provenance(tmp_path)


def test_coverage_provenance_rejects_extra_source_identity_project(tmp_path: Path) -> None:
    path = tmp_path / COVERAGE_PROVENANCE_RELATIVE_PATH
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": COVERAGE_PROVENANCE_SCHEMA_VERSION,
                "source_inventory_mode": COVERAGE_SOURCE_INVENTORY_MODE,
                "source_tree_identity": {
                    "algorithm": "sha256",
                    "inventory_mode": COVERAGE_SOURCE_INVENTORY_MODE,
                    "projects": {"unexpected": "0" * 64},
                },
                "projects": {},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="source-tree identity project roster"):
        validate_coverage_provenance(tmp_path)


def test_coverage_provenance_rejects_missing_measurement_support_identity(tmp_path: Path) -> None:
    _write_test_coverage_support_closure(tmp_path)
    source_hashes = {row.name: "0" * 64 for row in EXEMPLAR_SNAPSHOT}
    projects = {
        row.name: {"coverage_pct": row.coverage_pct, "source_hash": source_hashes[row.name]}
        for row in EXEMPLAR_SNAPSHOT
    }
    path = tmp_path / COVERAGE_PROVENANCE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": COVERAGE_PROVENANCE_SCHEMA_VERSION,
                "source_inventory_mode": COVERAGE_SOURCE_INVENTORY_MODE,
                "source_tree_identity": {
                    "algorithm": "sha256",
                    "inventory_mode": COVERAGE_SOURCE_INVENTORY_MODE,
                    "measurement_support": {},
                    "projects": source_hashes,
                },
                "projects": projects,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="measurement-support identity"):
        validate_coverage_provenance(tmp_path)
