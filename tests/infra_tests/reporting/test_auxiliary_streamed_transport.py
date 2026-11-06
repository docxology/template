"""Real ZIP/graph component behavior; these DATA fixtures grant no live acceptance."""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import stat
import struct
import time
import zipfile
from pathlib import Path
from contextlib import nullcontext

import pytest

from infrastructure.project.public_acceptance_literature_readback import ORIGINAL_DIRECTORY, import_originals
from infrastructure.reporting.native_hosted_transport_archive import (
    MAX_ARCHIVE,
    MAX_MEMBERS,
    MAX_TOTAL,
    _archive,
    _auxiliary_capacity,
    import_auxiliary_archive,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.required_acceptance_aggregate import _evidence_closure
from infrastructure.reporting.required_candidate_transport import _graph_paths


def _zip(files: dict[str, bytes], *, compression: int = zipfile.ZIP_DEFLATED) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=compression) as archive:
        for name, body in files.items():
            archive.writestr(name, body)
    return stream.getvalue()


def _packet(body: bytes) -> dict[str, bytes]:
    names = ("retained/.pipeline/first.bin", "retained/second.bin")
    bindings = [
        {"path": ORIGINAL_DIRECTORY + "/" + name, "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}
        for name in names
    ]
    return {
        "receipt.json": json.dumps({"component_only": True, "originals": bindings}).encode(),
        **dict.fromkeys(names, body),
    }


@pytest.fixture
def mutable_disposable_root(tmp_path: Path):
    yield tmp_path
    for directory, _, files in os.walk(tmp_path):
        Path(directory).chmod(0o700)
        for name in files:
            path = Path(directory) / name
            if not path.is_symlink():
                path.chmod(0o600)


def test_real_expanded_zip_and_exact_closure_exceed_one_archive_without_relaxing_old_decoder(
    mutable_disposable_root: Path,
) -> None:
    body = bytes(range(256)) * (35 * 1024 * 1024 // 256)
    files = _packet(body)
    raw = _zip(files)
    assert len(raw) < MAX_ARCHIVE < sum(map(len, files.values())) < MAX_TOTAL
    with pytest.raises(ValueError, match="membership/type/bytes"):
        _archive(raw, maximum=MAX_ARCHIVE, count=10000)
    observed = import_originals(mutable_disposable_root, raw, time.monotonic() + 60)
    assert observed == {"members": 3, "closure_files": 3, "closure_bytes": sum(map(len, files.values()))}
    for name, expected in files.items():
        copied = mutable_disposable_root / ORIGINAL_DIRECTORY / name
        assert copied.read_bytes() == expected
        assert stat.S_IMODE(copied.stat().st_mode) == 0o400


def test_shared_importer_preserves_identical_existing_data_and_refuses_changed_copy(tmp_path: Path) -> None:
    files = {"receipt.json": b"{}", "hidden/.pipeline/original.bin": b"actual retained bytes"}
    destination = tmp_path / ORIGINAL_DIRECTORY
    first, total = import_auxiliary_archive(
        tmp_path, destination, _zip(files), deadline=time.monotonic() + 30, mode=0o600, fresh=False
    )
    second, again = import_auxiliary_archive(
        tmp_path, destination, _zip(files), deadline=time.monotonic() + 30, mode=0o600, fresh=False
    )
    assert first == second and total == again == sum(map(len, files.values()))
    (destination / "hidden/.pipeline/original.bin").write_bytes(b"changed")
    with pytest.raises(ValueError, match="conflicts"):
        import_auxiliary_archive(
            tmp_path, destination, _zip(files), deadline=time.monotonic() + 30, mode=0o600, fresh=False
        )


@pytest.mark.parametrize(
    "defect", ["traversal", "absolute", "backslash", "directory", "symlink", "duplicate", "missing-receipt", "count"]
)
def test_shared_import_refuses_unsafe_or_incomplete_census_before_creating_destination(
    tmp_path: Path, defect: str
) -> None:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        if defect != "missing-receipt":
            archive.writestr("receipt.json", b"{}")
        if defect == "count":
            for number in range(10000):
                archive.writestr(f"member-{number}", b"")
        else:
            name = {
                "traversal": "../escape",
                "absolute": "/escape",
                "backslash": "bad\\escape",
                "directory": "directory/",
                "duplicate": "receipt.json",
            }.get(defect, "original.bin")
            info = zipfile.ZipInfo(name)
            if defect == "symlink":
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
            with pytest.warns(UserWarning, match="Duplicate") if defect == "duplicate" else nullcontext():
                archive.writestr(info, b"body")
    destination = tmp_path / ORIGINAL_DIRECTORY
    with pytest.raises(ValueError):
        import_auxiliary_archive(
            tmp_path, destination, stream.getvalue(), deadline=time.monotonic() + 30, mode=0o600, fresh=True
        )
    assert not destination.exists()


@pytest.mark.parametrize("kind", ["compressed", "per-file", "whole"])
def test_existing_raw_and_per_file_caps_and_native_whole_cap_remain_distinct(tmp_path: Path, kind: str) -> None:
    if kind == "compressed":
        raw = b"x" * (MAX_ARCHIVE + 1)
    elif kind == "per-file":
        raw = _zip({"receipt.json": b"{}", "oversize.bin": b"x" * (MAX_ARCHIVE + 1)})
    else:
        # The complete declared inventory is refused before decoding any
        # forged member. Separate real70MiB and CRC controls cover decoding.
        raw_array = bytearray(_zip({"receipt.json": b"{}", **{f"file-{number}": b"" for number in range(129)}}))
        position = 0
        while (position := raw_array.find(b"PK\x01\x02", position)) >= 0:
            struct.pack_into("<I", raw_array, position + 24, MAX_ARCHIVE)
            position += 46
        raw = bytes(raw_array)
    destination = tmp_path / ORIGINAL_DIRECTORY
    with pytest.raises(ValueError, match="compressed|per-file|whole-transport"):
        import_auxiliary_archive(tmp_path, destination, raw, deadline=time.monotonic() + 30, mode=0o600, fresh=True)
    assert not destination.exists()


def test_actual_small_device_filesystem_refuses_reserve_without_writing() -> None:
    device = Path("/dev")
    from infrastructure.core.testing._ci_execution_files import RESERVE

    if not device.is_dir() or shutil.disk_usage(device).free >= RESERVE:
        pytest.skip("host has no read-only observable small device filesystem")
    with pytest.raises(ValueError, match="reserve"):
        _auxiliary_capacity(device, 0)


def test_real_crc_corruption_and_expired_clock_refuse(tmp_path: Path) -> None:
    raw = bytearray(
        _zip({"receipt.json": b"{}", "original.bin": b"unique-retained-body"}, compression=zipfile.ZIP_STORED)
    )
    raw[raw.index(b"unique-retained-body")] ^= 1
    with pytest.raises(zipfile.BadZipFile, match="CRC"):
        import_auxiliary_archive(
            tmp_path, tmp_path / ORIGINAL_DIRECTORY, bytes(raw), deadline=time.monotonic() + 30, mode=0o600, fresh=True
        )
    with pytest.raises(TimeoutError):
        import_auxiliary_archive(
            tmp_path,
            tmp_path / "output/readiness/expired",
            _zip({"receipt.json": b"{}"}),
            deadline=time.monotonic() - 1,
            mode=0o600,
            fresh=True,
        )
    assert not (tmp_path / "output/readiness/expired").exists()


@pytest.mark.parametrize("size", [True, -1, "4", 999])
def test_candidate_and_public_graphs_refuse_malformed_or_changed_sized_bindings(tmp_path: Path, size: object) -> None:
    target = tmp_path / "output/readiness/original.bin"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"real")
    relative = "output/readiness/receipt.json"
    (tmp_path / relative).write_text(
        json.dumps(
            {
                "original": {
                    "path": "output/readiness/original.bin",
                    "sha256": hashlib.sha256(b"real").hexdigest(),
                    "bytes": size,
                }
            }
        )
    )
    for strict in (False, True):
        with pytest.raises(ValueError, match="sized artifact|original size"):
            _graph_paths(
                tmp_path, relative, SnapshotReader(tmp_path), deadline=time.monotonic() + 30, strict_bindings=strict
            )


def test_public_closure_preserves_source_exclusion_list_json_and_strict_absolute_refusal(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_bytes(b"[project]\n")
    output = tmp_path / "output/readiness"
    output.mkdir(parents=True)
    reference = {"path": "pyproject.toml", "sha256": hashlib.sha256(b"[project]\n").hexdigest(), "bytes": 10}
    (output / "receipt.json").write_text(json.dumps([reference]))
    closure = _evidence_closure(SnapshotReader(tmp_path), "output/readiness/receipt.json")
    assert set(closure) == {"output/readiness/receipt.json"}
    reference["path"] = str(tmp_path / "pyproject.toml")
    (output / "receipt.json").write_text(json.dumps([reference]))
    with pytest.raises(ValueError, match="absolute"):
        _evidence_closure(SnapshotReader(tmp_path), "output/readiness/receipt.json")


def test_public_closure_refuses_missing_retained_bytes_and_expired_reader(tmp_path: Path) -> None:
    output = tmp_path / "output/readiness"
    output.mkdir(parents=True)
    (output / "receipt.json").write_text(
        json.dumps({"original": {"path": "output/readiness/missing.bin", "sha256": "a" * 64}})
    )
    with pytest.raises((ValueError, FileNotFoundError)):
        _evidence_closure(SnapshotReader(tmp_path), "output/readiness/receipt.json")
    with pytest.raises(TimeoutError):
        _evidence_closure(
            SnapshotReader(tmp_path, operation_deadline=time.monotonic() - 1), "output/readiness/receipt.json"
        )


@pytest.mark.parametrize("prior", [True, -1, MAX_TOTAL + 1])
def test_shared_importer_refuses_invalid_prior_decoded_census(tmp_path: Path, prior: int) -> None:
    destination = tmp_path / ORIGINAL_DIRECTORY
    with pytest.raises(ValueError, match="prior decoded-byte census"):
        import_auxiliary_archive(
            tmp_path,
            destination,
            _zip({"receipt.json": b"{}"}),
            deadline=time.monotonic() + 30,
            mode=0o600,
            fresh=True,
            prior_decoded_bytes=prior,
        )
    assert not destination.exists()


def test_actual_successive_imports_advance_one_fixed_whole_transport_budget(tmp_path: Path) -> None:
    files = {"receipt.json": b"{}", "original.bin": bytes(range(256)) * 64}
    raw = _zip(files)
    first, first_bytes = import_auxiliary_archive(
        tmp_path, tmp_path / "output/readiness/first", raw, deadline=time.monotonic() + 30, mode=0o600, fresh=True
    )
    second, second_bytes = import_auxiliary_archive(
        tmp_path,
        tmp_path / "output/readiness/second",
        raw,
        deadline=time.monotonic() + 30,
        mode=0o600,
        fresh=True,
        prior_decoded_bytes=first_bytes,
    )
    assert len(first) == len(second) == 2 and first_bytes == second_bytes == sum(map(len, files.values()))
    refused = tmp_path / "output/readiness/over-whole-budget"
    # A Source-owned counter is a fixed-ceiling nomination, never an override;
    # the next complete declared import must fit before any bytes are decoded.
    with pytest.raises(ValueError, match="whole-transport"):
        import_auxiliary_archive(
            tmp_path,
            refused,
            raw,
            deadline=time.monotonic() + 30,
            mode=0o600,
            fresh=True,
            prior_decoded_bytes=MAX_TOTAL - second_bytes + 1,
        )
    assert not refused.exists()


@pytest.mark.parametrize("prior", [True, -1, MAX_MEMBERS + 1, MAX_MEMBERS])
def test_shared_importer_refuses_invalid_or_exhausted_whole_member_census(tmp_path: Path, prior: int) -> None:
    destination = tmp_path / ORIGINAL_DIRECTORY
    with pytest.raises(ValueError, match="member census"):
        import_auxiliary_archive(
            tmp_path,
            destination,
            _zip({"receipt.json": b"{}"}),
            deadline=time.monotonic() + 30,
            mode=0o600,
            fresh=True,
            prior_members=prior,
        )
    assert not destination.exists()
