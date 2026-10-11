"""Exact admitted-root identity controls for mature confined IO."""

from pathlib import Path

import pytest

from infrastructure.core.files.secure_write import (
    append_text_confined,
    atomic_write_bytes_confined,
    atomic_write_text_confined,
    confined_file_lock,
    read_bytes_confined,
    read_text_confined,
)

_OPERATIONS = ("append", "write_text", "write_bytes", "read_text", "read_bytes", "lock")


def _operate(kind: str, root: Path, target: Path, identity: tuple[int, int]) -> None:
    if kind == "append":
        append_text_confined(root, target, "more\n", expected_root_identity=identity)
    elif kind == "write_text":
        atomic_write_text_confined(root, target, "replaced\n", expected_root_identity=identity)
    elif kind == "write_bytes":
        atomic_write_bytes_confined(root, target, b"replaced\n", expected_root_identity=identity)
    elif kind == "read_text":
        assert read_text_confined(root, target, expected_root_identity=identity) == "original\n"
    elif kind == "read_bytes":
        assert read_bytes_confined(root, target, expected_root_identity=identity) == b"original\n"
    else:
        with confined_file_lock(root, target, expected_root_identity=identity):
            assert target.is_file()


@pytest.mark.parametrize("kind", _OPERATIONS)
def test_confined_operations_accept_actual_held_root_identity(tmp_path: Path, kind: str) -> None:
    root = tmp_path / "root"
    target = root / "output/evidence.txt"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"original\n")
    admitted = root.stat()
    _operate(kind, root, target, (admitted.st_dev, admitted.st_ino))
    if kind == "append":
        assert target.read_bytes() == b"original\nmore\n"
        assert target.stat().st_mode & 0o777 == 0o600
    elif kind.startswith("write"):
        assert target.read_bytes() == b"replaced\n"


@pytest.mark.parametrize("kind", _OPERATIONS)
def test_replaced_admitted_root_is_refused_before_any_child_creation(tmp_path: Path, kind: str) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "sentinel").write_bytes(b"original\n")
    admitted = root.stat()
    retired = tmp_path / "retired"
    root.rename(retired)
    root.mkdir()
    (root / "sentinel").write_bytes(b"replacement\n")
    with pytest.raises(ValueError, match="root changed after admission"):
        _operate(kind, root, root / "output/deep/evidence.txt", (admitted.st_dev, admitted.st_ino))
    assert sorted(path.name for path in root.iterdir()) == ["sentinel"]
    assert sorted(path.name for path in retired.iterdir()) == ["sentinel"]
    assert (root / "sentinel").read_bytes() == b"replacement\n"
    assert (retired / "sentinel").read_bytes() == b"original\n"


@pytest.mark.parametrize("identity", [(True, 1), (1, False), (1.0, 2), (-1, 2), (1,), (1, 2, 3), [1, 2], "1,2"])
def test_root_identity_requires_exact_nonnegative_integer_pair(tmp_path: Path, identity: object) -> None:
    root = tmp_path / "root"
    root.mkdir()
    with pytest.raises(ValueError, match="exact nonnegative integer pair"):
        append_text_confined(root, root / "output/logs/evidence.txt", "Refused", expected_root_identity=identity)  # type: ignore[arg-type]
    assert list(root.iterdir()) == []
