"""Real parent-index projection and independent nested-worktree membership."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from infrastructure.validation.rendered_snapshot._records import _fingerprint, _project_records, _stage_records
from infrastructure.validation.rendered_snapshot._scan import FileRecord, RenderedSnapshotError, cached_records


def _git(root: Path, *args: str, env: dict[str, str] | None = None) -> None:
    child_env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    child_env.update(LC_ALL="C", GIT_OPTIONAL_LOCKS="0", GIT_CONFIG_GLOBAL=os.devnull)
    if env is not None:
        child_env.update(env)
    subprocess.run(
        ["git", "-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false", "-C", str(root), *args],
        env=child_env,
        check=True,
        capture_output=True,
        timeout=30,
    )


def _parent_projection(tmp_path: Path) -> tuple[Path, Path, Path, dict[str, str]]:
    root = tmp_path / "parent"
    root.mkdir()
    stage = root / "infrastructure"
    stage.mkdir()
    (stage / "old.py").write_text("OLD = 1\n", encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "add", "infrastructure/old.py")
    new = stage / "new.py"
    new.write_text("NEW = 2\n", encoding="utf-8")
    (stage / "untracked.py").write_text("EXCLUDED = True\n", encoding="utf-8")
    index = tmp_path / "projected-index"
    shutil.copyfile(root / ".git" / "index", index)
    objects = tmp_path / "projected-objects"
    objects.mkdir()
    env = {
        "GIT_INDEX_FILE": str(index),
        "GIT_OBJECT_DIRECTORY": str(objects),
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(root / ".git" / "objects"),
        "GIT_DIR": str(root / ".git"),
        "GIT_WORK_TREE": str(root),
    }
    _git(root, "update-index", "--info-only", "--add", "--", "infrastructure/new.py", env=env)
    assert not tuple(objects.iterdir())
    return root, index, new, env


def _nested_worktree(root: Path) -> tuple[Path, Path]:
    nested = root / "infrastructure" / "vendor"
    nested.mkdir()
    _git(nested, "init", "-q")
    tracked = nested / "native.c"
    tracked.write_text("int native_value = 3;\n", encoding="utf-8")
    _git(nested, "add", "native.c")
    (nested / "untracked.c").write_text("int excluded = 4;\n", encoding="utf-8")
    return nested, tracked


def _route(monkeypatch: pytest.MonkeyPatch, env: dict[str, str]) -> None:
    for key, value in env.items():
        monkeypatch.setenv(key, value)


def test_parent_projection_preserves_real_nested_cached_membership(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The parent's new code and the nested repository's own tracked body both bind."""
    root, projection, _, env = _parent_projection(tmp_path)
    nested, tracked = _nested_worktree(root)
    parent_index = (root / ".git" / "index").read_bytes()
    nested_index = (nested / ".git" / "index").read_bytes()
    private_index = projection.read_bytes()
    _route(monkeypatch, env)

    records = _stage_records(root)

    assert {record.path for record in records} == {
        root / "infrastructure" / "old.py",
        root / "infrastructure" / "new.py",
        tracked,
    }
    assert (root / ".git" / "index").read_bytes() == parent_index
    assert (nested / ".git" / "index").read_bytes() == nested_index
    assert projection.read_bytes() == private_index
    assert not tuple(Path(env["GIT_OBJECT_DIRECTORY"]).iterdir())


def test_projected_stage_fingerprint_equals_final_ordinary_staging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Actual final Git membership yields the same full working-byte fingerprint."""
    root, _, new, env = _parent_projection(tmp_path)
    _nested_worktree(root)
    with monkeypatch.context() as route:
        _route(route, env)
        projected = _fingerprint(_stage_records(root))

    _git(root, "add", str(new))
    actual = _fingerprint(_stage_records(root))

    assert actual == projected
    new.write_text("NEW = 5\n", encoding="utf-8")
    assert _fingerprint(_stage_records(root)) != actual


def test_managed_external_source_uses_own_index_under_parent_projection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Parent routing cannot replace a managed sidecar's own tracked Source census."""
    root, projection, _, env = _parent_projection(tmp_path)
    external = tmp_path / "sidecar"
    source = external / "src"
    source.mkdir(parents=True)
    tracked = source / "analysis.py"
    tracked.write_text("VALUE = 7\n", encoding="utf-8")
    (source / "untracked.py").write_text("EXCLUDED = True\n", encoding="utf-8")
    configuration = external / "pyproject.toml"
    configuration.write_text('[project]\nname = "real-sidecar"\nversion = "0.1.0"\n', encoding="utf-8")
    _git(external, "init", "-q")
    _git(external, "add", "src/analysis.py", "pyproject.toml")
    external_index = (external / ".git" / "index").read_bytes()
    primary_index = (root / ".git" / "index").read_bytes()
    projected_index = projection.read_bytes()
    lexical = root / "projects" / "working" / "sidecar"
    lexical.parent.mkdir(parents=True)
    lexical.symlink_to(external, target_is_directory=True)
    _route(monkeypatch, env)

    records, config = _project_records(root, external, lexical_project_root=lexical)

    assert {record.path for record in records} == {tracked}
    assert {record.path for record in config} == {configuration}
    assert (external / ".git" / "index").read_bytes() == external_index
    assert (root / ".git" / "index").read_bytes() == primary_index
    assert projection.read_bytes() == projected_index


def test_parent_projection_cannot_hide_invalid_required_nested_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A malformed nested Git boundary refuses custody even with a valid parent index."""
    root, _, _, env = _parent_projection(tmp_path)
    nested = root / "infrastructure" / "invalid"
    nested.mkdir()
    _git(nested, "init", "-q")
    (nested / ".git" / "index").write_bytes(b"invalid-index")
    body = nested / "native.c"
    body.write_text("int value = 9;\n", encoding="utf-8")
    _route(monkeypatch, env)

    with pytest.raises(RenderedSnapshotError, match="Git worktree is unavailable") as error:
        cached_records([FileRecord("native.c", body)], root, require_worktrees=True)

    assert error.value.code == "PROJECT_REPOSITORY_INVALID"
