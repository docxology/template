"""Actual fixture isolation and refusal of foreign cleanup targets."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from infrastructure.core.testing.pytest_scratch import external_pytest_scratch


def test_actual_pytest_fixture_does_not_inherit_source_git_or_ignore_rules(tmp_path: Path) -> None:
    root = tmp_path / "source"
    root.mkdir()
    subprocess.run(["git", "init", "--quiet", str(root)], check=True)
    (root / ".gitignore").write_text("ignored/\n")
    (root / "pyproject.toml").write_text('[tool.pytest.ini_options]\naddopts = ""\n')
    observed = tmp_path / "actual-fixture.json"
    case = root / "test_fixture.py"
    case.write_text(
        "from pathlib import Path\nimport json,subprocess\n"
        "def test_fixture(tmp_path):\n"
        f"    root=Path({str(root)!r})\n"
        "    assert not tmp_path.is_relative_to(root)\n"
        "    result=subprocess.run(['git','-C',str(tmp_path),'rev-parse','--show-toplevel'],capture_output=True)\n"
        "    assert result.returncode != 0\n"
        f"    Path({str(observed)!r}).write_text(json.dumps({{'fixture':str(tmp_path)}}))\n"
    )
    with external_pytest_scratch(root, token="actual-owned-regression") as scratch:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-c",
                str(root / "pyproject.toml"),
                str(case),
                "--basetemp=" + str(scratch / "fixtures"),
                "-q",
            ],
            cwd=root,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        fixture = Path(json.loads(observed.read_bytes())["fixture"])
        assert fixture.is_relative_to(scratch) and fixture.is_dir()
    assert not scratch.exists()


def test_changed_scratch_root_cannot_delete_a_replacement_directory(tmp_path: Path) -> None:
    root = tmp_path / "source"
    root.mkdir()
    scratch = moved = None
    try:
        with pytest.raises(ValueError, match="cleanup refused"):
            with external_pytest_scratch(root, token="actual-physical-refusal") as scratch:
                moved = scratch.with_name(scratch.name + "-held")
                scratch.rename(moved)
                scratch.mkdir(mode=0o700)
                (scratch / "foreign.txt").write_text("keep this replacement")
        assert (scratch / "foreign.txt").read_text() == "keep this replacement"
    finally:
        if scratch is not None and scratch.exists():
            shutil.rmtree(scratch)
        if moved is not None and moved.exists():
            shutil.rmtree(moved)


def test_actual_source_local_temp_configuration_is_refused_before_fixture_creation(tmp_path: Path) -> None:
    root = tmp_path / "source"
    root.mkdir()
    subprocess.run(["git", "init", "--quiet", str(root)], check=True)
    configured = root / "ignored-temp"
    configured.mkdir()
    sdk_root = Path(__file__).resolve().parents[3]
    code = (
        "import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);"
        "from infrastructure.core.testing.pytest_scratch import external_pytest_scratch;"
        "scope=external_pytest_scratch(Path(sys.argv[2]),token='actual-refusal');"
        "scope.__enter__()"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(sdk_root), str(root)],
        env={**os.environ, "TMPDIR": str(configured), "TEMP": str(configured), "TMP": str(configured)},
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode != 0
    assert "outside Source, Git and selected runtime trees" in result.stderr
    assert not list(configured.iterdir())


@pytest.mark.parametrize("event", ["os.listdir", "shutil.rmtree"])
def test_actual_cleanup_race_never_traverses_replacement_contents(tmp_path: Path, event: str) -> None:
    """A real subprocess audit hook swaps the root after the helper's check."""
    root = tmp_path / "source"
    root.mkdir()
    sdk_root = Path(__file__).resolve().parents[3]
    code = r"""
import os, shutil, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from infrastructure.core.testing.pytest_scratch import external_pytest_scratch
state = {"armed": False, "switched": False}
def audit(event, args):
    if state["armed"] and event == sys.argv[3]:
        state["armed"] = False
        state["switched"] = True
        scratch = state["scratch"]
        scratch.rename(state["moved"])
        scratch.mkdir(mode=0o700)
        (scratch / "foreign.txt").write_text("keep replacement contents")
sys.addaudithook(audit)
scratch = moved = None
try:
    try:
        with external_pytest_scratch(Path(sys.argv[2]), token="actual-cleanup-race") as scratch:
            moved = scratch.with_name(scratch.name + "-held")
            (scratch / "owned-child").mkdir()
            (scratch / "owned-child/data.txt").write_text("owned fixtures")
            state.update(scratch=scratch, moved=moved, armed=True)
    except ValueError as error:
        assert "cleanup refused" in str(error), str(error)
    else:
        raise AssertionError("replacement root was not refused")
    assert state["switched"]
    assert (scratch / "foreign.txt").read_text() == "keep replacement contents"
    assert not list(moved.iterdir()), "cleanup must traverse the original held root only"
finally:
    state["armed"] = False
    for path in (scratch, moved):
        if path is not None and path.exists():
            shutil.rmtree(path)
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(sdk_root), str(root), event],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_changed_owned_temp_parent_is_refused_without_foreign_cleanup(tmp_path: Path) -> None:
    """Rename only this subprocess's private TMPDIR, never the host temp root."""
    source, base = tmp_path / "source", tmp_path / "owned-temp"
    source.mkdir()
    base.mkdir()
    sdk_root = Path(__file__).resolve().parents[3]
    code = r"""
import shutil, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from infrastructure.core.testing.pytest_scratch import external_pytest_scratch
base = Path(sys.argv[3]).resolve()
moved = base.with_name(base.name + '-held')
try:
    try:
        with external_pytest_scratch(Path(sys.argv[2]), token='actual-parent-refusal') as scratch:
            (scratch / 'owned.txt').write_text('original owned data')
            base.rename(moved)
            base.mkdir()
            scratch.mkdir()
            (scratch / 'foreign.txt').write_text('foreign replacement')
    except ValueError as error:
        assert 'parent changed physical ownership' in str(error), str(error)
    else:
        raise AssertionError('changed fixture pathname was accepted')
    assert (scratch / 'foreign.txt').read_text() == 'foreign replacement'
    assert (moved / scratch.name / 'owned.txt').read_text() == 'original owned data'
finally:
    for directory in (base, moved):
        if directory.exists():
            shutil.rmtree(directory)
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(sdk_root), str(source), str(base)],
        env={**os.environ, "TMPDIR": str(base), "TEMP": str(base), "TMP": str(base)},
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_owned_read_only_fixture_metadata_is_removed_without_following_links(tmp_path: Path) -> None:
    source, outside = tmp_path / "source", tmp_path / "outside"
    source.mkdir()
    outside.mkdir()
    sentinel = outside / "sentinel.txt"
    sentinel.write_text("preserve external data and permissions")
    sentinel.chmod(0o400)
    outside.chmod(0o500)
    try:
        with external_pytest_scratch(source, token="actual-read-only-metadata") as scratch:
            metadata = scratch / "fixtures/locked-metadata/projects/example"
            metadata.mkdir(parents=True)
            (metadata / "uv.lock").write_text("retained genuine fixture metadata")
            (metadata / "uv.lock").chmod(0o400)
            (metadata / "outside").symlink_to(outside, target_is_directory=True)
            for directory in (metadata, metadata.parent, metadata.parent.parent, scratch / "fixtures"):
                directory.chmod(0o500)
            scratch.chmod(0o500)
        assert not scratch.exists()
        assert outside.stat().st_mode & 0o777 == 0o500
        assert sentinel.stat().st_mode & 0o777 == 0o400
        assert sentinel.read_text() == "preserve external data and permissions"
    finally:
        outside.chmod(0o700)
        sentinel.chmod(0o600)
