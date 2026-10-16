"""Real sparse filesystem DATA controls; no package/process authority is mocked.

These fixtures exercise the package manifest leaf only. They neither impersonate
dpkg/Calibre nor qualify a native Linux runtime. Genuine host tests are separate.
"""

from __future__ import annotations

import copy
import hashlib
import os
import shutil
import time
from pathlib import Path
from typing import Any

import pytest

from infrastructure.project.native_linux_calibre_custody import (
    ROLE_NAMES,
    _held_parent,
    canonical_linux_member,
    linux_calibre_body_projection,
    observe_linux_calibre_packages,
    validate_linux_calibre_packages,
)
from infrastructure.project.native_reader_runtime_custody import _digest
from infrastructure.reporting.native_linux_calibre_runtime import (
    _layout,
    _owner,
    _package,
    _plugin,
    _plugin_command,
    _plugin_owners,
    require_linux_calibre_plugin_trace,
)


def _files(tmp_path: Path) -> tuple[list[dict[str, Any]], dict[str, str], Path]:
    root = tmp_path.resolve() / "installed-package-data"
    root.mkdir()
    roles = {}
    for name in sorted(ROLE_NAMES):
        path = root / name
        path.write_bytes(("actual file DATA for " + name).encode())
        roles[name] = str(path)
    alias = root / "plugin-alias"
    alias.symlink_to("platform_plugin")
    packages = [
        {
            "package": "calibre-data-control:amd64",
            "version": "1.0",
            "architecture": "amd64",
            "status": "install ok installed",
            "members": sorted([str(root), str(alias), *roles.values()]),
        }
    ]
    return packages, roles, root


def test_complete_sparse_members_replay_without_reopening_deleted_package(tmp_path: Path) -> None:
    packages, roles, root = _files(tmp_path)
    before = observe_linux_calibre_packages(packages, roles, deadline=time.monotonic() + 5)
    after = observe_linux_calibre_packages(packages, roles, deadline=time.monotonic() + 5)
    validate_linux_calibre_packages(before, after)
    unrelated = root.parent / "unselected.data"
    unrelated.write_bytes(b"not part of the selected installed package")
    assert str(unrelated) not in {row["path"] for row in before["files"]}
    shutil.rmtree(root)
    validate_linux_calibre_packages(before, after)


def test_actual_package_mutation_and_missing_member_refuse(tmp_path: Path) -> None:
    packages, roles, _ = _files(tmp_path)
    before = observe_linux_calibre_packages(packages, roles, deadline=time.monotonic() + 5)
    Path(roles["platform_plugin"]).write_bytes(b"changed actual selected Qt plugin")
    after = observe_linux_calibre_packages(packages, roles, deadline=time.monotonic() + 5)
    with pytest.raises(ValueError, match="custody changed"):
        validate_linux_calibre_packages(before, after)
    Path(roles["platform_plugin"]).unlink()
    with pytest.raises(FileNotFoundError):
        observe_linux_calibre_packages(packages, roles, deadline=time.monotonic() + 5)


def test_alias_escape_and_retained_alias_target_tampering_refuse(tmp_path: Path) -> None:
    packages, roles, root = _files(tmp_path)
    before = observe_linux_calibre_packages(packages, roles, deadline=time.monotonic() + 5)
    changed = copy.deepcopy(before)
    alias_row = next(row for row in changed["files"] if row["kind"] == "alias")
    alias_row["label"] = "qt_module"
    changed["digest"] = _digest({k: v for k, v in changed.items() if k != "digest"})
    with pytest.raises(ValueError, match="alias label/target"):
        validate_linux_calibre_packages(changed, changed)
    alias = root / "plugin-alias"
    alias.unlink()
    foreign = root.parent / "unowned-plugin"
    foreign.write_bytes(b"foreign")
    alias.symlink_to(foreign)
    with pytest.raises(ValueError, match="alias target"):
        observe_linux_calibre_packages(packages, roles, deadline=time.monotonic() + 5)


def test_sparse_directory_and_declared_role_do_not_grant_membership(tmp_path: Path) -> None:
    packages, roles, _ = _files(tmp_path)
    missing = copy.deepcopy(packages)
    missing[0]["members"].remove(roles["qt_module"])
    with pytest.raises(ValueError, match="role is absent"):
        observe_linux_calibre_packages(missing, roles, deadline=time.monotonic() + 5)
    missing[0]["status"] = "deinstall ok config-files"
    with pytest.raises(ValueError, match="owner/status"):
        observe_linux_calibre_packages(missing, roles, deadline=time.monotonic() + 5)
    with pytest.raises(TimeoutError):
        observe_linux_calibre_packages(packages, roles, deadline=time.monotonic() - 1)


def test_current_body_equivalence_allows_only_fresh_physical_metadata(tmp_path: Path) -> None:
    packages, roles, _ = _files(tmp_path)
    original = observe_linux_calibre_packages(packages, roles, deadline=time.monotonic() + 5)
    path = Path(roles["interpreter"])
    content = path.read_bytes()
    path.unlink()
    path.write_bytes(content)
    current = observe_linux_calibre_packages(packages, roles, deadline=time.monotonic() + 5)
    assert original != current
    assert linux_calibre_body_projection(original) == linux_calibre_body_projection(current)
    path.write_bytes(b"actual changed current interpreter bytes")
    changed = observe_linux_calibre_packages(packages, roles, deadline=time.monotonic() + 5)
    assert linux_calibre_body_projection(original) != linux_calibre_body_projection(changed)


def test_actual_loaded_plugin_line_required_even_with_complete_custody(tmp_path: Path) -> None:
    packages, roles, _ = _files(tmp_path)
    raw = observe_linux_calibre_packages(packages, roles, deadline=time.monotonic() + 5)
    with pytest.raises(ValueError, match="loaded-library trace"):
        require_linux_calibre_plugin_trace(raw, "metadata contains offscreen")
    require_linux_calibre_plugin_trace(raw, f'qt.core.library: "{roles["platform_plugin"]}" loaded library\n')
    with pytest.raises(ValueError, match="loaded-library trace"):
        require_linux_calibre_plugin_trace(raw, 'qt.core.library: "/foreign/plugin.so" loaded library')


def test_exact_signed_output_parsers_reject_ambiguity_and_path_guesses(tmp_path: Path) -> None:
    selected = str(tmp_path.resolve() / "reader")
    assert _owner("calibre:amd64: " + selected + "\n", selected) == "calibre:amd64"
    with pytest.raises(ValueError, match="one exact"):
        _owner("calibre: " + selected + "\nother: " + selected, selected)
    prefix = str(tmp_path.resolve())
    assert _plugin_owners("qt6-base:amd64: " + prefix + "/actual.so", prefix) == ["qt6-base:amd64"]
    with pytest.raises(ValueError, match="escaped"):
        _plugin_owners("foreign: /not-selected/plugin.so", prefix)
    package = _package("calibre:amd64\t1.0\tamd64\tinstall ok installed\n", selected + "\n", "calibre:amd64")
    assert package["members"] == [selected]
    with pytest.raises(ValueError, match="canonical"):
        canonical_linux_member("/usr/../foreign")
    with pytest.raises(ValueError, match="canonical"):
        canonical_linux_member("/usr/lib/*")
    with pytest.raises(ValueError, match="schema"):
        _layout('{"interpreter":"/guessed/python"}')
    package["members"] = [str(tmp_path.resolve() / "actual.so")]
    command, candidates = _plugin_command([package], {"qt_plugins": prefix})
    assert "QPluginLoader" in command and candidates == package["members"]
    with pytest.raises(ValueError, match="one actual"):
        _plugin(
            '{"schema_version":"template-calibre-qt-platform-selection-v1","platform":"offscreen","plugins":[]}',
            candidates,
        )


def test_sparse_package_bytes_require_search_but_no_ancestor_listing(tmp_path: Path) -> None:
    ancestor = tmp_path.resolve(strict=True) / "search-only"
    ancestor.mkdir()
    packages, roles, root = _files(ancestor)
    nonroot_posix = os.name == "posix" and os.geteuid() != 0
    ancestor.chmod(0o111)
    try:
        if nonroot_posix:
            with pytest.raises(PermissionError):
                list(ancestor.iterdir())
        if nonroot_posix and not hasattr(os, "O_PATH"):
            with pytest.raises(PermissionError):
                observe_linux_calibre_packages(packages, roles, deadline=time.monotonic() + 5)
        else:
            before = observe_linux_calibre_packages(packages, roles, deadline=time.monotonic() + 5)
            after = observe_linux_calibre_packages(packages, roles, deadline=time.monotonic() + 5)
            validate_linux_calibre_packages(before, after)
            indexed = {row["path"]: row for row in before["files"]}
            for label in roles.values():
                selected = Path(label)
                current = selected.stat()
                assert indexed[label]["sha256"] == hashlib.sha256(selected.read_bytes()).hexdigest()
                assert indexed[label]["metadata"] == {
                    "dev": current.st_dev,
                    "ino": current.st_ino,
                    "mode": current.st_mode,
                    "size": current.st_size,
                    "mtime_ns": current.st_mtime_ns,
                    "ctime_ns": current.st_ctime_ns,
                }
            assert indexed[str(ancestor)]["metadata"]["mode"] == ancestor.stat().st_mode
    finally:
        ancestor.chmod(0o755)
    if nonroot_posix:
        selected = Path(roles["launcher"])
        original_mode = selected.stat().st_mode & 0o777
        selected.chmod(0)
        try:
            with pytest.raises(PermissionError):
                observe_linux_calibre_packages(packages, roles, deadline=time.monotonic() + 5)
        finally:
            selected.chmod(original_mode)
    alias = ancestor.parent / "linked-prefix"
    alias.symlink_to(ancestor, target_is_directory=True)
    with pytest.raises(OSError):
        _held_parent(alias / root.name / "launcher")
    not_directory = ancestor.parent / "not-directory"
    not_directory.write_bytes(b"regular file cannot be an ancestor")
    with pytest.raises(NotADirectoryError):
        _held_parent(not_directory / "launcher")
