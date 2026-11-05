"""Source-locked PDFium wheel and exact actual installed provider admission."""

from __future__ import annotations

import base64
import csv
import configparser
import hashlib
import importlib.machinery
import importlib.metadata
import stat
import sys
from io import StringIO
from pathlib import Path, PurePosixPath
from typing import Any

from infrastructure.core.implementation_custody import source_file_bytes
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_source_external_admission import (
    NativeSourceContext,
)

SCHEMA = "template-office-live-installed-pdfium-provider-v1"
MAX_FILES = 20_000
MAX_BYTES = 1024 * 1024 * 1024
PROVIDERS = ("pypdfium2", "pypdfium2_raw")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _identity(path: Path) -> dict[str, int]:
    value = path.lstat()
    if not stat.S_ISREG(value.st_mode):
        raise ValueError("PDFium selected member is not a regular original file")
    return {
        "device": value.st_dev,
        "inode": value.st_ino,
        "mode": value.st_mode,
        "size": value.st_size,
        "mtime_ns": value.st_mtime_ns,
        "ctime_ns": value.st_ctime_ns,
        "links": value.st_nlink,
    }


def _file(path: Path, deadline: float) -> tuple[bytes, dict[str, int]]:
    remaining(deadline)
    before = _identity(path)
    data = source_file_bytes(path)
    after = _identity(path)
    if before != after or len(data) != before["size"]:
        raise ValueError("PDFium original file identity changed while admitted")
    remaining(deadline)
    return data, before


def _label(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if not value or value == "." or path.is_absolute() or ".." in path.parts or "\\" in value or str(path) != value:
        raise ValueError("PDFium original member label escapes its nominated installed site")
    return path


def _wheel(source: NativeSourceContext, wheel: Path, deadline: float) -> tuple[dict[str, bytes], dict[str, Any]]:
    from infrastructure.reporting.native_pdfium_source_wheel import (
        inspect_pdfium_source_wheel,
    )

    raw, identity = _file(wheel, deadline)
    members, declared = inspect_pdfium_source_wheel(source, wheel.name, raw, deadline=deadline)
    return members, {"path": str(wheel), **declared, "identity": identity}


def _selected_site(site: Path, deadline: float) -> tuple[dict[str, Any], str]:
    remaining(deadline)
    selected = importlib.metadata.distribution("pypdfium2")
    if Path(str(selected.locate_file(""))).absolute() != site:
        raise ValueError("actual selected PDFium distribution differs from nominated installed site")
    origins = {}
    for name in PROVIDERS:
        spec = importlib.machinery.PathFinder.find_spec(name, sys.path)
        if spec is None or spec.origin != str(site / name / "__init__.py"):
            raise ValueError("actual selected PDFium import provider differs from admitted installed files")
        if spec.submodule_search_locations is None or tuple(spec.submodule_search_locations) != (str(site / name),):
            raise ValueError("PDFium selected package has an unadmitted additional import root")
        origins[name] = spec.origin
    records = [str(item) for item in (selected.files or ()) if str(item).endswith(".dist-info/RECORD")]
    if len(records) != 1 or len(_label(records[0]).parts) != 2:
        raise ValueError("PDFium installed provider requires one direct exact RECORD")
    remaining(deadline)
    return {
        "site": str(site),
        "version": selected.version,
        "origins": origins,
    }, records[0]


def _installed(site: Path, members: dict[str, bytes], deadline: float) -> dict[str, Any]:
    selection, record_name = _selected_site(site, deadline)
    record, record_identity = _file(site / record_name, deadline)
    entry_labels = [name for name in members if name.endswith(".dist-info/entry_points.txt")]
    scripts: dict[str, Path] = {}
    if entry_labels:
        if len(entry_labels) != 1 or site.parents[2] != Path(sys.prefix).absolute():
            raise ValueError("PDFium generated console metadata has no exact selected installed environment")
        entry_points = configparser.ConfigParser(interpolation=None)
        entry_points.read_string(members[entry_labels[0]].decode())
        if entry_points.sections() != ["console_scripts"]:
            raise ValueError("PDFium original wheel has an unsupported entry-point group")
        for name, target in entry_points.items("console_scripts"):
            _label(name)
            if "/" in name or not target.startswith("pypdfium2."):
                raise ValueError("PDFium original wheel console target differs from admitted provider")
            scripts[f"../../../bin/{name}"] = site.parents[2] / "bin" / name
    rows = {}
    for row in csv.reader(StringIO(record.decode())):
        if len(row) != 3 or row[0] in rows:
            raise ValueError("PDFium installed RECORD contains repeated or malformed members")
        if row[0] not in scripts:
            _label(row[0])
        rows[row[0]] = row[1:]
    if len(rows) > MAX_FILES:
        raise ValueError("PDFium installed RECORD exceeds its original finite member bound")
    metadata_root = record_name.rsplit("/", 1)[0]
    generated = {metadata_root + "/" + name for name in ("INSTALLER", "REQUESTED", "direct_url.json", "uv_cache.json")}
    caches = {name for name in rows if "__pycache__" in PurePosixPath(name).parts and name.endswith(".pyc")}
    if (
        not set(members) <= set(rows)
        or set(rows) - set(members) - generated - caches - set(scripts)
        or rows.get(record_name) != ["", ""]
    ):
        raise ValueError("PDFium installed complete file set differs from the original Source wheel")
    files: dict[str, dict[str, Any]] = {}
    cache_files: dict[str, dict[str, Any]] = {}
    unselected_scripts: dict[str, dict[str, Any]] = {}
    total = 0
    for name, (encoded, size) in rows.items():
        remaining(deadline)
        if name in scripts:
            content, identity = _file(scripts[name], deadline)
            digest = _sha(content)
            expected = "sha256=" + base64.urlsafe_b64encode(bytes.fromhex(digest)).decode().rstrip("=")
            if encoded != expected or size != str(len(content)):
                raise ValueError("PDFium unselected generated console script differs from its actual RECORD")
            total += len(content)
            if total > MAX_BYTES:
                raise ValueError("PDFium installed package exceeds its original finite byte bound")
            unselected_scripts[name] = {
                "path": str(scripts[name]),
                "sha256": digest,
                "bytes": len(content),
                "identity": identity,
            }
            continue
        if name in caches:
            if [encoded, size] != ["", ""]:
                raise ValueError("PDFium generated cache row has unsupported RECORD semantics")
            content, identity = _file(site / name, deadline)
            total += len(content)
            if total > MAX_BYTES:
                raise ValueError("PDFium installed package exceeds its original finite byte bound")
            cache_files[name] = {
                "sha256": _sha(content),
                "bytes": len(content),
                "identity": identity,
            }
            continue
        content, identity = _file(site / name, deadline)
        total += len(content)
        if len(files) >= MAX_FILES or total > MAX_BYTES:
            raise ValueError("PDFium installed package exceeds its original finite runtime bounds")
        digest = _sha(content)
        if name != record_name:
            expected = "sha256=" + base64.urlsafe_b64encode(bytes.fromhex(digest)).decode().rstrip("=")
            if encoded != expected or size != str(len(content)):
                raise ValueError("PDFium actual installed file differs from its exact RECORD hash/size")
        if name in members and name != record_name and content != members[name]:
            raise ValueError("PDFium actual installed body differs from original Source-declared wheel")
        files[name] = {"sha256": digest, "bytes": len(content), "identity": identity}
    # Independently account negative package membership, including non-Python
    # members; installation caches may never become selected public code.
    actual = set()
    directories = 0
    for name in (*PROVIDERS, metadata_root):
        pending = [site / name]
        while pending:
            directory = pending.pop()
            directories += 1
            if directories > MAX_FILES:
                raise ValueError("PDFium installed directory inventory exceeds its original finite bound")
            remaining(deadline)
            if directory.is_symlink():
                raise ValueError("PDFium installed provider contains a directory alias")
            for child in directory.iterdir():
                remaining(deadline)
                observed = child.lstat()
                if stat.S_ISDIR(observed.st_mode):
                    pending.append(child)
                elif stat.S_ISREG(observed.st_mode):
                    actual.add(child.relative_to(site).as_posix())
                else:
                    raise ValueError("PDFium installed provider has an unadmitted alias/type")
                if len(actual) > MAX_FILES:
                    raise ValueError("PDFium installed negative membership exceeds its original finite bound")
    if actual != set(files) | set(cache_files):
        raise ValueError("PDFium installed package/metadata has an undeclared member")
    return {
        "schema_version": SCHEMA,
        "selection": selection,
        "record_sha256": _sha(record),
        "record_identity": record_identity,
        "files": files,
        "unselected_installation_caches": cache_files,
        "unselected_generated_console_scripts": unselected_scripts,
        "bytes": total,
    }
