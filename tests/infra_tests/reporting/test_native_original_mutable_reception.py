"""Real-file reception controls; transport/Source admission remains separately required."""

from pathlib import Path

import pytest

from infrastructure.reporting.native_hosted_original_custody import _receive_native_original_file


DELIVERY = "projects/templates/template_code_project/output/pdf/manuscript.pdf"


def test_native_original_replaces_independently_pristine_delivery(tmp_path: Path) -> None:
    reference = tmp_path / "published"
    mirror = tmp_path / "mirror"
    published = reference / DELIVERY
    target = mirror / DELIVERY
    for path in (published, target):
        path.parent.mkdir(parents=True)
        path.write_bytes(b"published toolchain output\n")
    held = published.read_bytes()
    native = b"actual different native toolchain output\n"

    _receive_native_original_file(mirror, DELIVERY, native, published_snapshot=held)

    assert target.read_bytes() == native
    assert published.read_bytes() == held


@pytest.mark.parametrize("case", ["fresh", "identical", "conflict", "authored", "leaf-symlink", "parent-symlink"])
def test_native_original_reception_preserves_owned_files_and_confinement(tmp_path: Path, case: str) -> None:
    root = tmp_path / "mirror"
    root.mkdir()
    body = b"authenticated original bytes\n"
    label = DELIVERY
    if case == "authored":
        label = "projects/templates/template_code_project/src/producer.py"
    target = root / label
    target.parent.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / target.name
    sentinel.write_bytes(b"unique outside bytes\n")
    if case == "leaf-symlink":
        target.symlink_to(sentinel)
    elif case == "parent-symlink":
        target.parent.rmdir()
        target.parent.symlink_to(outside, target_is_directory=True)
    elif case != "fresh":
        target.write_bytes(body if case == "identical" else b"earlier owned bytes\n")
    before = target.read_bytes() if target.exists() else None
    identity = target.lstat().st_ino if target.exists() else None

    if case in {"fresh", "identical"}:
        _receive_native_original_file(root, label, body, published_snapshot=None)
        assert target.read_bytes() == body
        if case == "identical":
            assert target.lstat().st_ino == identity
    else:
        with pytest.raises((OSError, ValueError)):
            _receive_native_original_file(root, label, body, published_snapshot=b"published snapshot\n")
        assert target.read_bytes() == before
        assert target.lstat().st_ino == identity
    assert sentinel.read_bytes() == b"unique outside bytes\n"
