"""Permission contract for the shared confined publication writer."""

import os
import stat
from pathlib import Path

import pytest

from infrastructure.core.files.secure_write import (
    atomic_write_text_confined,
    read_text_confined,
    append_text_confined,
    confined_file_lock,
)


def test_binary_publication_retains_exact_bytes_and_private_mode(tmp_path: Path) -> None:
    from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined

    content = bytes(range(256)) * 2048
    target = tmp_path / "artifacts" / "package.whl"
    atomic_write_bytes_confined(tmp_path, target, content, mode=0o600)
    assert read_bytes_confined(tmp_path, target) == content
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert {path.name for path in target.parent.iterdir()} == {target.name}


@pytest.mark.parametrize("filename", ["a" * 248 + ".md", "章" * 80 + ".md"])
def test_confined_publication_supports_long_destination_components(tmp_path: Path, filename: str) -> None:
    """Temporary allocation must not extend a valid destination's name."""
    from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined

    target = tmp_path / filename
    content = b"exact publication bytes\x00\xff"
    atomic_write_bytes_confined(tmp_path, target, content, mode=0o600)
    assert read_bytes_confined(tmp_path, target) == content
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    atomic_write_bytes_confined(tmp_path, target, content + b" replacement", mode=0o600)
    assert read_bytes_confined(tmp_path, target) == content + b" replacement"
    assert set(tmp_path.iterdir()) == {target}


@pytest.mark.parametrize("component", ["target", "parent"])
def test_binary_publication_refuses_symlink_without_overwriting_sentinel(tmp_path: Path, component: str) -> None:
    from infrastructure.core.files.secure_write import atomic_write_bytes_confined

    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "package.whl"
    sentinel.write_bytes(b"private sentinel\x00\xff")
    root = tmp_path / "public"
    root.mkdir()
    if component == "target":
        target = root / "package.whl"
        target.symlink_to(sentinel)
    else:
        (root / "linked").symlink_to(outside, target_is_directory=True)
        target = root / "linked/package.whl"
    with pytest.raises((OSError, ValueError)):
        atomic_write_bytes_confined(root, target, b"unapproved")
    assert sentinel.read_bytes() == b"private sentinel\x00\xff"


def test_confined_write_retains_default_publication_permissions(tmp_path: Path) -> None:
    target = tmp_path / "evidence.json"

    atomic_write_text_confined(tmp_path, target, '{"verified": true}')

    assert target.read_text(encoding="utf-8") == '{"verified": true}'
    assert stat.S_IMODE(target.stat().st_mode) == 0o644
    assert set(tmp_path.iterdir()) == {target}


@pytest.mark.parametrize("mode", [0o600, 0o640, 0o644])
def test_confined_write_applies_requested_permissions(tmp_path: Path, mode: int) -> None:
    target = tmp_path / "publication.html"
    target.write_text("old", encoding="utf-8")

    atomic_write_text_confined(tmp_path, target, "new", mode=mode)

    assert target.read_text(encoding="utf-8") == "new"
    assert stat.S_IMODE(target.stat().st_mode) == mode
    assert set(tmp_path.iterdir()) == {target}


def test_confined_reads_and_appends_reject_symlink_targets_and_parents(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    secret = outside / "private.txt"
    secret.write_text("private sentinel")
    root = tmp_path / "root"
    root.mkdir()
    (root / "link").symlink_to(outside, target_is_directory=True)
    (root / "target").symlink_to(secret)
    for path in (root / "link/private.txt", root / "target"):
        for operation in (
            lambda: read_text_confined(root, path),
            lambda: append_text_confined(root, path, "unapproved"),
        ):
            with pytest.raises((OSError, ValueError)):
                operation()
    assert secret.read_text() == "private sentinel"


def test_bounded_read_budget(tmp_path: Path) -> None:
    target = tmp_path / "large.txt"
    target.write_text("abcdefghij")
    with pytest.raises(ValueError, match="read budget"):
        read_text_confined(tmp_path, target, max_bytes=5)


def test_concurrent_confined_append_has_no_lost_records(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor

    target = tmp_path / "decisions.jsonl"
    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(lambda number: append_text_confined(tmp_path, target, f"{number}\n"), range(60)))
    assert sorted(int(line) for line in read_text_confined(tmp_path, target).splitlines()) == list(range(60))


@pytest.mark.timeout(45)
def test_simultaneous_fresh_lock_creation_preserves_every_record(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    # A single successful round did not reveal the macOS first-creation race.
    # Every round starts without a lock file and synchronizes its first writers.
    for round_number in range(20):
        root = tmp_path / str(round_number)
        root.mkdir()
        target = root / "decisions.jsonl"
        start = Barrier(6, timeout=5)

        def append(number: int) -> None:
            if number < 6:
                start.wait()
            append_text_confined(root, target, f"{number}\n")

        with ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(append, range(60)))
        assert sorted(int(line) for line in read_text_confined(root, target).splitlines()) == list(range(60))
        assert stat.S_IMODE(target.stat().st_mode) == 0o600
        assert {path.name for path in root.iterdir()} == {"decisions.jsonl", "decisions.jsonl.append.lock"}


def test_lock_replacement_is_reported_instead_of_silent_success(tmp_path: Path) -> None:
    target = tmp_path / "state.lock"
    replacement = tmp_path / "replacement.lock"
    replacement.write_text("replacement")
    with pytest.raises(ValueError, match="lock target changed"):
        with confined_file_lock(tmp_path, target):
            replacement.replace(target)
    assert target.read_text() == "replacement"


def test_lock_symlink_cannot_authorize_external_state(tmp_path: Path) -> None:
    external = tmp_path / "external.lock"
    external.write_text("private fixture")
    target = tmp_path / "state.lock"
    target.symlink_to(external)
    with pytest.raises((OSError, ValueError)):
        with confined_file_lock(tmp_path, target):
            raise AssertionError("A symlink lock authorized mutation")
    assert external.read_text() == "private fixture"


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan"), True])
def test_invalid_lock_deadlines_are_refused(tmp_path: Path, timeout: float) -> None:
    with pytest.raises(ValueError, match="finite and positive"):
        with confined_file_lock(tmp_path, tmp_path / "state.lock", timeout=timeout):
            raise AssertionError("An invalid deadline authorized mutation")
    assert list(tmp_path.iterdir()) == []


def test_confined_lock_wait_is_finite(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor

    target = tmp_path / "state.lock"
    with confined_file_lock(tmp_path, target):

        def contender() -> None:
            with confined_file_lock(tmp_path, target, timeout=0.1):
                raise AssertionError("Contender acquired held lock")

        with ThreadPoolExecutor(max_workers=1) as pool:
            with pytest.raises(TimeoutError):
                pool.submit(contender).result(timeout=2)


@pytest.mark.parametrize("operation", ["text", "binary", "read", "append", "lock", "unlink"])
def test_ancestor_of_nominated_root_cannot_admit_external_state(tmp_path: Path, operation: str) -> None:
    from infrastructure.core.files.secure_write import atomic_write_bytes_confined, unlink_confined

    outside = tmp_path / "external" / "nested"
    outside.mkdir(parents=True)
    sentinel = outside / "private.txt"
    sentinel.write_text("private sentinel")
    link = tmp_path / "redirect"
    link.symlink_to(outside.parent, target_is_directory=True)
    root = link / "nested"
    target = root / sentinel.name
    with pytest.raises((OSError, ValueError)):
        if operation == "text":
            atomic_write_text_confined(root, target, "unapproved")
        elif operation == "binary":
            atomic_write_bytes_confined(root, target, b"unapproved")
        elif operation == "read":
            read_text_confined(root, target)
        elif operation == "append":
            append_text_confined(root, target, "unapproved")
        elif operation == "unlink":
            unlink_confined(root, target)
        else:
            with confined_file_lock(root, target):
                raise AssertionError("root-ancestor link admitted a lock")
    assert sentinel.read_text() == "private sentinel"
    assert {path.name for path in outside.iterdir()} == {sentinel.name}


def test_held_lock_refuses_replaced_ancestor_of_nominated_root(tmp_path: Path) -> None:
    ancestor = tmp_path / "public"
    root = ancestor / "nested"
    root.mkdir(parents=True)
    external = tmp_path / "external" / "nested"
    external.mkdir(parents=True)
    sentinel = external / "state.lock"
    sentinel.write_text("private sentinel")
    with pytest.raises(ValueError, match="directory changed"):
        with confined_file_lock(root, root / "state.lock"):
            ancestor.rename(tmp_path / "held-public")
            ancestor.symlink_to(external.parent, target_is_directory=True)
    assert sentinel.read_text() == "private sentinel"
    assert {path.name for path in external.iterdir()} == {sentinel.name}


@pytest.mark.skipif(os.name != "posix" or os.geteuid() == 0, reason="requires real nonroot POSIX permission checks")
@pytest.mark.parametrize("operation", ["text", "binary", "read", "append", "lock", "unlink"])
def test_confined_operations_traverse_search_only_ancestors_without_listing(tmp_path: Path, operation: str) -> None:
    from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined, unlink_confined

    ancestor = tmp_path.resolve() / "search-only"
    root = ancestor / "selected"
    parent = root / "data"
    parent.mkdir(parents=True)
    root.chmod(0o755)
    parent.chmod(0o750)
    target = parent / "state"
    target.write_bytes(b"original")
    target.chmod(0o640)
    identity = root.stat().st_dev, root.stat().st_ino

    def perform() -> None:
        if operation == "text":
            atomic_write_text_confined(root, target, "updated", mode=0o600, expected_root_identity=identity)
        elif operation == "binary":
            atomic_write_bytes_confined(root, target, b"updated\x00", mode=0o600, expected_root_identity=identity)
        elif operation == "read":
            assert read_bytes_confined(root, target, expected_root_identity=identity) == b"original"
        elif operation == "append":
            append_text_confined(root, target, "updated", expected_root_identity=identity)
        elif operation == "unlink":
            unlink_confined(root, target)
        else:
            with confined_file_lock(root, target, expected_root_identity=identity):
                assert target.read_bytes() == b"original"

    ancestor.chmod(0o111)
    try:
        with pytest.raises(PermissionError):
            list(ancestor.iterdir())
        if hasattr(os, "O_PATH"):
            perform()
        else:
            with pytest.raises((OSError, ValueError)):
                perform()
        assert stat.S_IMODE(ancestor.stat().st_mode) == 0o111
        assert stat.S_IMODE(root.stat().st_mode) == 0o755
        assert stat.S_IMODE(parent.stat().st_mode) == 0o750
    finally:
        ancestor.chmod(0o700)
    assert set(ancestor.iterdir()) == {root}
    expected = {"data"}
    if not hasattr(os, "O_PATH") or operation != "unlink":
        expected.add("data/state")
        content = (
            {
                "text": b"updated",
                "binary": b"updated\x00",
                "append": b"originalupdated",
            }.get(operation, b"original")
            if hasattr(os, "O_PATH")
            else b"original"
        )
        assert target.read_bytes() == content
        mode = 0o600 if hasattr(os, "O_PATH") and operation in {"text", "binary", "append"} else 0o640
        assert stat.S_IMODE(target.stat().st_mode) == mode
    if hasattr(os, "O_PATH") and operation == "append":
        expected.add("data/state.append.lock")
        assert stat.S_IMODE((parent / "state.append.lock").stat().st_mode) == 0o600
    assert {path.relative_to(root).as_posix() for path in root.rglob("*")} == expected
    if operation == "read":
        # Search-only handles must never replace readable handles at/below the
        # selected confinement root, even on platforms with O_PATH.
        for required_readable in (root, parent):
            mode = stat.S_IMODE(required_readable.stat().st_mode)
            required_readable.chmod(0o111)
            try:
                with pytest.raises((OSError, ValueError)):
                    read_bytes_confined(root, target)
            finally:
                required_readable.chmod(mode)
