"""Tests for standalone-mirror syncing.

Two properties carry real consequences and are pinned in both directions:

1. **Update-only.** The mirror holds published artifacts the monorepo does not
   track (exemplar ``output/`` is gitignored in the monorepo but published in the
   mirror). A replace-style sync would have deleted 224 such files from
   ``template_advanced_literature_review`` alone on 2026-07-28.
2. **Symlinks are dereferenced.** Exemplars that share source by symlinking into
   a sibling must arrive self-contained; copying the link leaves it dangling,
   which is why one mirror was missing four whole source trees.

Real git repositories and real files under ``tmp_path`` — no mocks.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from infrastructure.publishing.standalone_mirror import (
    declared_repository,
    populate_mirror_tree,
    tracked_relative_paths,
)


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def _monorepo(tmp_path: Path) -> Path:
    root = tmp_path / "monorepo"
    project = root / "projects" / "templates" / "template_demo"
    (project / "src").mkdir(parents=True)
    (project / "output" / "data").mkdir(parents=True)
    (project / "src" / "core.py").write_text("VALUE = 1\n", encoding="utf-8")
    (project / "README.md").write_text("# Demo\n", encoding="utf-8")
    (project / "CITATION.cff").write_text(
        "cff-version: 1.2.0\ntitle: Demo\nrepository-code: https://github.com/example/template_demo\n",
        encoding="utf-8",
    )
    # Gitignored build output: present on disk, never tracked.
    (root / ".gitignore").write_text("projects/templates/*/output/*\n", encoding="utf-8")
    (project / "output" / "data" / "local_only.json").write_text("{}\n", encoding="utf-8")

    _git(["init", "-q"], root)
    _git(["config", "user.email", "t@example.com"], root)
    _git(["config", "user.name", "Test"], root)
    _git(["add", "-A"], root)
    _git(["commit", "-qm", "init"], root)
    return root


def test_tracked_paths_exclude_gitignored_output(tmp_path: Path) -> None:
    root = _monorepo(tmp_path)
    paths = tracked_relative_paths(root, "projects/templates/template_demo")
    assert "src/core.py" in paths
    assert "README.md" in paths
    assert not any(path.startswith("output/") for path in paths), "gitignored output must never be mirrored"


def test_declared_repository_reads_citation_cff(tmp_path: Path) -> None:
    root = _monorepo(tmp_path)
    project = root / "projects" / "templates" / "template_demo"
    assert declared_repository(project) == "https://github.com/example/template_demo"
    assert declared_repository(tmp_path / "absent") == ""


def test_sync_is_update_only_and_preserves_mirror_only_files(tmp_path: Path) -> None:
    """The behaviour that protects published artifacts.

    A mirror-only file (a published output artifact the monorepo does not track)
    must survive a sync. This is the control for the failure mode that would have
    deleted 224 real artifacts.
    """
    root = _monorepo(tmp_path)
    mirror = tmp_path / "mirror"
    (mirror / "output" / "pdf").mkdir(parents=True)
    published = mirror / "output" / "pdf" / "published_paper.pdf"
    published.write_bytes(b"%PDF-1.7 published artifact\n")
    (mirror / "README.md").write_text("# stale\n", encoding="utf-8")

    populate_mirror_tree(root, "projects/templates/template_demo", mirror)

    assert published.is_file(), "a published mirror-only artifact must not be deleted"
    assert published.read_bytes() == b"%PDF-1.7 published artifact\n"
    assert (mirror / "README.md").read_text(encoding="utf-8") == "# Demo\n", "tracked files must be updated"
    assert (mirror / "src" / "core.py").is_file()


def test_directory_symlinks_are_dereferenced_into_real_files(tmp_path: Path) -> None:
    """A standalone mirror has no sibling to resolve a cross-project symlink."""
    root = _monorepo(tmp_path)
    templates = root / "projects" / "templates"
    sibling = templates / "template_shared" / "src" / "analysis"
    sibling.mkdir(parents=True)
    (sibling / "engine.py").write_text("SHARED = True\n", encoding="utf-8")

    link = templates / "template_demo" / "src" / "analysis"
    link.symlink_to(Path("../../template_shared/src/analysis"))
    _git(["add", "-A"], root)
    _git(["commit", "-qm", "add shared symlink"], root)

    mirror = tmp_path / "mirror2"
    mirror.mkdir()
    populate_mirror_tree(root, "projects/templates/template_demo", mirror)

    mirrored = mirror / "src" / "analysis" / "engine.py"
    assert mirrored.is_file(), "symlinked source tree must be materialized in the mirror"
    assert not mirrored.is_symlink(), "the mirror must not contain a dangling link"
    assert mirrored.read_text(encoding="utf-8") == "SHARED = True\n"


def test_populate_reports_files_written(tmp_path: Path) -> None:
    root = _monorepo(tmp_path)
    mirror = tmp_path / "mirror3"
    mirror.mkdir()
    written = populate_mirror_tree(root, "projects/templates/template_demo", mirror)
    assert written == len(tracked_relative_paths(root, "projects/templates/template_demo"))
    assert written > 0
