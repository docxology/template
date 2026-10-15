"""Real ZIP/lock and installed-filesystem DATA controls; no native authority.

Invented provider bytes test parsers and exact RECORD/negative membership only.
No Source, executed PDFium library or successful native capability is fabricated.
The genuine installed/Source batch positive path remains a separate bounded probe.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import stat
import time
import zipfile
from pathlib import Path

import pytest

from infrastructure.reporting.native_full_worker_pdfium import (
    NativePDFiumSelection,
    admit_full_worker_pdfium_providers,
)
from infrastructure.reporting.native_office_diagram_runtime import admit_pdfium_runtimes
from infrastructure.reporting.native_office_pdfium_provider import _installed
from infrastructure.reporting.native_pdfium_source_wheel import (
    _validate_pdfium_batch_selections,
    inspect_pdfium_locked_wheel,
)

NAME = "pypdfium2-0.0.0-py3-none-any.whl"
SCOPE = "templates/template_code_project"


def _members() -> dict[str, bytes]:
    members = {
        "pypdfium2/__init__.py": b"VALUE = 1\n",
        "pypdfium2_raw/__init__.py": b"VALUE = 2\n",
        "pypdfium2_raw/libpdfium.dylib": b"Owned invented DATA; never loaded as a library.\n",
        "pypdfium2-0.0.0.dist-info/METADATA": b"Metadata-Version: 2.1\nName: pypdfium2\nVersion: 0.0.0\n",
    }
    record = io.StringIO()
    writer = csv.writer(record)
    for name, body in members.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(body).digest()).decode().rstrip("=")
        writer.writerow([name, "sha256=" + digest, len(body)])
    writer.writerow(["pypdfium2-0.0.0.dist-info/RECORD", "", ""])
    members["pypdfium2-0.0.0.dist-info/RECORD"] = record.getvalue().encode()
    return members


def _archive(members: dict[str, bytes], *, alias: bool = False) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, body in members.items():
            info = zipfile.ZipInfo(name)
            info.external_attr = ((stat.S_IFLNK if alias else stat.S_IFREG) | 0o644) << 16
            archive.writestr(info, body)
    return stream.getvalue()


def _lock(raw: bytes, *, version: str = "0.0.0", digest: str | None = None, size: int | None = None) -> bytes:
    return (
        '[[package]]\nname = "pypdfium2"\n'
        f'version = "{version}"\n'
        f'wheels = [{{url = "https://example.invalid/{NAME}", hash = "sha256:{digest or hashlib.sha256(raw).hexdigest()}", size = {len(raw) if size is None else size}}}]\n'
    ).encode()


def test_pdfium_held_lock_parser_binds_exact_zip_bytes_and_member_version() -> None:
    members = _members()
    raw = _archive(members)
    lock = _lock(raw)
    observed, declaration = inspect_pdfium_locked_wheel(NAME, raw, lock, deadline=time.monotonic() + 10)
    assert observed == members
    assert declaration == {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "source_lock_sha256": hashlib.sha256(lock).hexdigest(),
        "version": "0.0.0",
    }


@pytest.mark.parametrize("change", ["hash", "size", "version", "filename", "outside", "alias", "metadata"])
def test_pdfium_held_lock_parser_rejects_changed_declarations_and_members(change: str) -> None:
    members = _members()
    if change == "outside":
        members["unrelated/secret.py"] = b"VALUE = 99\n"
    if change == "metadata":
        members.pop("pypdfium2-0.0.0.dist-info/METADATA")
    raw = _archive(members, alias=change == "alias")
    lock = _lock(
        raw,
        digest="0" * 64 if change == "hash" else None,
        size=len(raw) + 1 if change == "size" else None,
        version="1.0.0" if change == "version" else "0.0.0",
    )
    with pytest.raises(ValueError):
        inspect_pdfium_locked_wheel(
            "../" + NAME if change == "filename" else NAME, raw, lock, deadline=time.monotonic() + 10
        )


def test_pdfium_held_lock_parser_preserves_original_deadline() -> None:
    raw = _archive(_members())
    with pytest.raises(TimeoutError):
        inspect_pdfium_locked_wheel(NAME, raw, _lock(raw), deadline=time.monotonic() - 1)


@pytest.mark.parametrize("change", ["body", "extra", "alias", "record"])
def test_pdfium_batch_closing_inventory_rejects_real_installed_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    site = tmp_path / "site"
    members = _members()
    for name, body in members.items():
        target = site / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
    monkeypatch.syspath_prepend(str(site))
    before = _installed(site, members, time.monotonic() + 10)
    assert _installed(site, members, time.monotonic() + 10) == before
    target = site / "pypdfium2/__init__.py"
    if change == "body":
        target.write_bytes(b"VALUE = 999\n")
    elif change == "extra":
        (site / "pypdfium2/hidden.txt").write_bytes(b"undeclared\n")
    elif change == "record":
        record = site / "pypdfium2-0.0.0.dist-info/RECORD"
        record.write_text(record.read_text() + "undeclared.txt,,\n")
    else:
        target.unlink()
        target.symlink_to(site / "pypdfium2_raw/__init__.py")
    with pytest.raises((ValueError, OSError)):
        _installed(site, members, time.monotonic() + 10)


@pytest.mark.parametrize("kind", ["empty", "list", "private", "duplicate", "untyped", "short"])
def test_pdfium_batch_refuses_invalid_fixed_selection_data(tmp_path: Path, kind: str) -> None:
    selection = NativePDFiumSelection(tmp_path, tmp_path / NAME)
    row = (SCOPE, selection)
    invalid = {
        "empty": (),
        "list": [row],
        "private": (("working/private", selection),),
        "duplicate": (row, row),
        "untyped": ((SCOPE, str(tmp_path)),),
        "short": ((SCOPE,),),
    }[kind]
    with pytest.raises(ValueError):
        _validate_pdfium_batch_selections(invalid)  # type: ignore[arg-type]
    _validate_pdfium_batch_selections((row,))


@pytest.mark.parametrize("factory", [admit_full_worker_pdfium_providers, admit_pdfium_runtimes])
def test_pdfium_batches_refuse_data_without_genuine_source(tmp_path: Path, factory) -> None:
    selection = NativePDFiumSelection(tmp_path, tmp_path / NAME)
    with pytest.raises(ValueError, match="genuine Source"):
        factory(None, ((SCOPE, selection),), deadline=time.monotonic() + 10)
