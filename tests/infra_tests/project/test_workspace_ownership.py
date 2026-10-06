"""Real files and symlinks prove session guards never delete unowned work."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.workspace_ownership import TEST_WORKSPACE_NAMES, guard_test_workspaces


@pytest.mark.parametrize("name", TEST_WORKSPACE_NAMES)
def test_preexisting_named_workspace_retains_exact_bytes_and_directory_identity(tmp_path: Path, name: str) -> None:
    projects = tmp_path / "projects"
    directory = projects / name
    directory.mkdir(parents=True)
    content = directory / "existing.txt"
    original = b"invented preexisting local work; preserve exactly\n"
    content.write_bytes(original)
    identity = (directory.stat().st_dev, directory.stat().st_ino)
    with guard_test_workspaces(projects):
        pass
    assert content.read_bytes() == original
    assert (directory.stat().st_dev, directory.stat().st_ino) == identity


@pytest.mark.parametrize("name", TEST_WORKSPACE_NAMES)
def test_new_persistent_workspace_fails_without_deleting_its_evidence(tmp_path: Path, name: str) -> None:
    projects = tmp_path / "projects"
    projects.mkdir()
    directory = projects / name
    with pytest.raises(RuntimeError, match="All contents were preserved"):
        with guard_test_workspaces(projects):
            directory.mkdir()
            (directory / "new.txt").write_bytes(b"owned disposable negative control\n")
    assert (directory / "new.txt").read_bytes() == b"owned disposable negative control\n"


@pytest.mark.parametrize("dangling", [False, True])
def test_preexisting_link_is_preserved_without_following_or_deleting_target(tmp_path: Path, dangling: bool) -> None:
    projects = tmp_path / "projects"
    projects.mkdir()
    target = tmp_path / "outside"
    if not dangling:
        target.mkdir()
        (target / "existing.txt").write_bytes(b"invented external symlink target\n")
    link = projects / "test_project"
    link.symlink_to(target, target_is_directory=True)
    with guard_test_workspaces(projects):
        pass
    assert link.is_symlink() and link.readlink() == target
    if not dangling:
        assert (target / "existing.txt").read_bytes() == b"invented external symlink target\n"
    else:
        assert not target.exists()


def test_new_dangling_link_fails_and_stays_available_for_diagnosis(tmp_path: Path) -> None:
    projects = tmp_path / "projects"
    projects.mkdir()
    target = tmp_path / "missing-target"
    link = projects / "test"
    with pytest.raises(RuntimeError, match="All contents were preserved"):
        with guard_test_workspaces(projects):
            link.symlink_to(target, target_is_directory=True)
    assert link.is_symlink() and link.readlink() == target and not target.exists()


def test_temporary_owned_workspace_is_not_reported_as_a_persistent_leak(tmp_path: Path) -> None:
    projects = tmp_path / "projects"
    projects.mkdir()
    with guard_test_workspaces(projects):
        directory = projects / "test"
        directory.mkdir()
        directory.rmdir()
    assert not directory.exists()


def test_existing_regular_file_is_preserved(tmp_path: Path) -> None:
    projects = tmp_path / "projects"
    projects.mkdir()
    file = projects / "test_project"
    file.write_bytes(b"invented existing file\n")
    with guard_test_workspaces(projects):
        pass
    assert file.read_bytes() == b"invented existing file\n"


def test_body_failure_never_triggers_unowned_deletion(tmp_path: Path) -> None:
    projects = tmp_path / "projects"
    projects.mkdir()
    file = projects / "project1"
    with pytest.raises(ValueError, match="actual body failure"):
        with guard_test_workspaces(projects):
            file.write_bytes(b"invented failure evidence\n")
            raise ValueError("actual body failure")
    assert file.read_bytes() == b"invented failure evidence\n"
