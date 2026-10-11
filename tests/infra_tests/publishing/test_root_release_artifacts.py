"""Real source/archive controls for exact root release distributions."""

from __future__ import annotations

import gzip
import tarfile
from io import BytesIO
from pathlib import Path

import pytest

from infrastructure.publishing.root_release_artifacts import admit_root_release_artifacts, admit_sdist_bytes
from infrastructure.publishing.root_release_contract import RUNTIME_VERSION_PROVIDER_SOURCE


def _authored(root: Path) -> dict[str, bytes]:
    files = {
        "pyproject.toml": b'[project]\nname="research-project-template"\nversion="4.0.1"\nrequires-python=">=3.12"\n',
        "README.md": b"Public authored SDK\n",
        "LICENSE": b"MIT\n",
        ".gitignore": b"__pycache__/\n",
        "infrastructure/__init__.py": b"from .domain import answer\n",
        "infrastructure/domain.py": b"def answer():\n    return 7\n",
        "infrastructure/py.typed": b"",
        "infrastructure/_version.py": RUNTIME_VERSION_PROVIDER_SOURCE.encode(),
        "infrastructure/steganography/kmyth/src/main/seal.c": b"int main(void) { return 0; }\n",
    }
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    (root / "CHANGELOG.md").write_text("## [4.0.1] - 2026-10-07\n")
    return files


def _archive(files: dict[str, bytes], *, duplicate: bool = False, symlink: bool = False) -> bytes:
    data = BytesIO()
    with tarfile.open(fileobj=data, mode="w:gz") as archive:
        rows = list(files.items())
        rows.append(
            (
                "PKG-INFO",
                b"Metadata-Version: 2.4\nName: research-project-template\nVersion: 4.0.1\nRequires-Python: >=3.12\n",
            )
        )
        if duplicate:
            rows.append(rows[0])
        for name, content in rows:
            member = tarfile.TarInfo("research_project_template-4.0.1/" + name)
            member.size = len(content)
            archive.addfile(member, BytesIO(content))
        if symlink:
            member = tarfile.TarInfo("research_project_template-4.0.1/linked")
            member.type = tarfile.SYMTYPE
            member.linkname = "/outside-source"
            archive.addfile(member)
    return data.getvalue()


def test_complete_real_sdist_retains_typing_and_native_source(tmp_path: Path) -> None:
    files = _authored(tmp_path)
    admit_sdist_bytes(tmp_path, _archive(files))
    assert files["infrastructure/py.typed"] == b""


@pytest.mark.parametrize("change", ["missing-native", "extra-product", "changed-code"])
def test_actual_archive_source_drift_is_refused(tmp_path: Path, change: str) -> None:
    files = _authored(tmp_path)
    if change == "missing-native":
        files.pop("infrastructure/steganography/kmyth/src/main/seal.c")
    elif change == "extra-product":
        files["infrastructure/steganography/kmyth/obj/unadmitted.o"] = b"actual owned archive control"
    else:
        files["infrastructure/domain.py"] = b"def answer():\n    return 9\n"
    with pytest.raises(ValueError, match="omitted, changed or invented"):
        admit_sdist_bytes(tmp_path, _archive(files))


@pytest.mark.parametrize("kind", ["duplicate", "link"])
def test_actual_unsafe_archive_structure_is_refused(tmp_path: Path, kind: str) -> None:
    files = _authored(tmp_path)
    with pytest.raises(ValueError, match="duplicated|unsafe"):
        admit_sdist_bytes(tmp_path, _archive(files, duplicate=kind == "duplicate", symlink=kind == "link"))


@pytest.mark.timeout(30)
def test_actual_compressed_oversize_refused_before_tar_metadata(tmp_path: Path) -> None:
    _authored(tmp_path)
    payload = gzip.compress(bytes(64 * 1024 * 1024 + 1))
    assert len(payload) < 1024 * 1024
    with pytest.raises(ValueError, match="decompressed byte ceiling"):
        admit_sdist_bytes(tmp_path, payload)


def test_missing_original_installed_matrix_cannot_create_release_assets(tmp_path: Path) -> None:
    files = _authored(tmp_path)
    directory = tmp_path / "dist"
    directory.mkdir()
    sdist = directory / "research_project_template-4.0.1.tar.gz"
    original = _archive(files)
    sdist.write_bytes(original)
    with pytest.raises(FileNotFoundError):
        admit_root_release_artifacts(tmp_path, "v4.0.1", tmp_path / "output/readiness/missing/receipt.json")
    assert list(directory.iterdir()) == [sdist]
    assert sdist.read_bytes() == original


@pytest.mark.parametrize("change", ["none", "local-wheel", "local-manifest", "retrieved-sdist", "symlink"])
def test_actual_separately_held_asset_file_custody(tmp_path: Path, change: str) -> None:
    import hashlib
    import json
    import shutil

    from infrastructure.publishing.root_release_artifacts import _verify_asset_files

    files = _authored(tmp_path)
    directory = tmp_path / "dist"
    directory.mkdir()
    images = tmp_path / "docs/releases"
    images.mkdir(parents=True)
    # This file-custody leaf has no installed/source acceptance authority.
    # The actual source archive below is admitted by the independent oracle.
    contents = [b"held wheel-file control bytes", _archive(files), b"held PNG-file control bytes"]
    names = [
        "research_project_template-4.0.1-py3-none-any.whl",
        "research_project_template-4.0.1.tar.gz",
        "template-v4.0.1-overview.png",
    ]
    admit_sdist_bytes(tmp_path, contents[1])
    expected = [
        {"name": name, "bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()}
        for name, value in zip(names, contents, strict=True)
    ]
    manifest_name = "template-v4.0.1-artifacts.json"
    manifest_bytes = json.dumps({"assets": expected}).encode()
    (directory / manifest_name).write_bytes(manifest_bytes)
    for index, (name, value) in enumerate(zip(names, contents, strict=True)):
        (images / name if index == 2 else directory / name).write_bytes(value)
    retrieved = tmp_path / "retrieved"
    retrieved.mkdir()
    for index, name in enumerate(names):
        shutil.copy2(images / name if index == 2 else directory / name, retrieved / name)
    shutil.copy2(directory / manifest_name, retrieved / manifest_name)
    if change == "local-wheel":
        (directory / names[0]).write_bytes(b"changed local asset")
    elif change == "local-manifest":
        (directory / manifest_name).write_bytes(b'{"assets":[]}')
    elif change == "retrieved-sdist":
        (retrieved / names[1]).write_bytes(b"changed retrieved asset")
    elif change == "symlink":
        (directory / names[0]).unlink()
        (directory / names[0]).symlink_to(retrieved / names[0])
    if change == "none":
        _verify_asset_files(tmp_path, manifest_name, manifest_bytes, expected, contents, retrieved=retrieved)
    else:
        with pytest.raises((ValueError, OSError)):
            _verify_asset_files(tmp_path, manifest_name, manifest_bytes, expected, contents, retrieved=retrieved)
