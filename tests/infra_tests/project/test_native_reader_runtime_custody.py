"""Genuine confined filesystem observations, including deleted-producer replay."""

import hashlib
import shutil
import time
from pathlib import Path

import pytest

from infrastructure.project.native_reader_runtime_custody import (
    observe_native_reader_runtime,
    retain_native_reader_runtime,
    replay_retained_native_reader_runtime,
    validate_native_reader_runtime,
)


def test_actual_complete_app_replays_after_deletion_and_rejects_changed_plugin(tmp_path: Path) -> None:
    root = tmp_path / "Reader.app"
    executable = root / "Contents/MacOS/reader"
    plugin = root / "Contents/Frameworks/plugins/headless.so"
    executable.parent.mkdir(parents=True)
    plugin.parent.mkdir(parents=True)
    executable.write_bytes(b"actual bounded executable file control")
    plugin.write_bytes(b"actual plugin file control")
    (root / "Contents/plugin-alias").symlink_to("Frameworks/plugins/headless.so")
    consumed = ("Contents/Frameworks/plugins/headless.so",)
    before = observe_native_reader_runtime(executable, deadline=time.monotonic() + 5, consumed_members=consumed)
    after = observe_native_reader_runtime(executable, deadline=time.monotonic() + 5, consumed_members=consumed)
    sha = hashlib.sha256(executable.read_bytes()).hexdigest()
    validate_native_reader_runtime(before, after, executable_sha256=sha, consumed_members=consumed)
    plugin.write_bytes(b"changed genuine plugin file")
    changed = observe_native_reader_runtime(executable, deadline=time.monotonic() + 5, consumed_members=consumed)
    with pytest.raises(ValueError, match="changed"):
        validate_native_reader_runtime(before, changed, executable_sha256=sha, consumed_members=consumed)
    shutil.rmtree(root)
    validate_native_reader_runtime(before, after, executable_sha256=sha, consumed_members=consumed)
    with pytest.raises(ValueError, match="consumed"):
        validate_native_reader_runtime(before, after, executable_sha256=sha, consumed_members=("offscreen.so",))


def test_real_escaping_alias_and_unknown_prefix_blocked(tmp_path: Path) -> None:
    root = tmp_path / "Reader.app"
    root.mkdir()
    executable = root / "reader"
    executable.write_bytes(b"file")
    foreign = tmp_path / "foreign.so"
    foreign.write_bytes(b"foreign")
    (root / "escape.so").symlink_to(foreign)
    with pytest.raises(ValueError, match="escapes"):
        observe_native_reader_runtime(executable, deadline=time.monotonic() + 5)
    with pytest.raises(ValueError, match="source-declared"):
        observe_native_reader_runtime(foreign, deadline=time.monotonic() + 5)
    with pytest.raises(TimeoutError):
        observe_native_reader_runtime(executable, deadline=time.monotonic() - 1)


def test_shared_original_manifest_retains_twice_without_changing_admitted_bytes(tmp_path: Path) -> None:
    root = tmp_path / "Reader.app"
    executable = root / "reader"
    root.mkdir()
    executable.write_bytes(b"actual original reader executable")
    before = observe_native_reader_runtime(executable, deadline=time.monotonic() + 5)
    nonce = "a" * 32
    first = retain_native_reader_runtime(tmp_path, before, run_id=nonce)
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

    reader = SnapshotReader(tmp_path)
    held = reader.read(first["path"])
    second = retain_native_reader_runtime(tmp_path, before, run_id=nonce)
    assert first == second and reader.unchanged()
    shutil.rmtree(root)
    replay_retained_native_reader_runtime(
        first,
        second,
        read_artifact=lambda binding: reader.read(binding["path"]).content,
        run_id=nonce,
        executable=str(executable),
        executable_sha256=hashlib.sha256(b"actual original reader executable").hexdigest(),
    )
    assert held.sha256 == first["sha256"]
    with pytest.raises(ValueError, match="another run"):
        replay_retained_native_reader_runtime(
            first,
            second,
            read_artifact=lambda binding: reader.read(binding["path"]).content,
            run_id="b" * 32,
            executable=str(executable),
            executable_sha256=first["sha256"],
        )
