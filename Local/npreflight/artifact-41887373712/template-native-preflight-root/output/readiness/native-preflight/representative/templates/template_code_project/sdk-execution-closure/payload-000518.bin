"""Bounded installed decoder file observations; hashes alone do not attest origin.

No library binaries are archived. Authenticated source SDK/hosted custody binds
producer origin separately; this does not attest process memory or loaded code.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import importlib.metadata as metadata
import io
import os
import re
import sys
import stat
import tomllib
from pathlib import Path
from typing import Any

SCHEMA = "template-native-library-custody-v1"
DISTRIBUTIONS = (
    "pypdfium2",
    "Pillow",
    "ReportLab",
    "pdfplumber",
    "pdfminer.six",
    "pypdf",
    "lxml",
    "defusedxml",
    "fonttools",
    "NumPy",
    "Matplotlib",
    "PyYAML",
)
FORMATS = frozenset({"pdf", "html", "docx", "epub", "slides", "pptx"})
MODULES = {
    "pypdfium2": "pypdfium2",
    "pypdfium2_raw": "pypdfium2",
    "PIL": "pillow",
    "reportlab": "reportlab",
    "pdfplumber": "pdfplumber",
    "pdfminer": "pdfminer-six",
    "pypdf": "pypdf",
    "lxml": "lxml",
    "defusedxml": "defusedxml",
    "fontTools": "fonttools",
    "numpy": "numpy",
    "matplotlib": "matplotlib",
    "yaml": "pyyaml",
    "pptx": "python-pptx",
}
MAX_FILE = 512 * 1024 * 1024
MAX_TOTAL = 2 * 1024 * 1024 * 1024


def _name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _selected(formats: Any) -> tuple[str, ...]:
    selected = set(formats)
    if not selected or not selected <= FORMATS:
        raise ValueError("unknown or empty native decoder format selection")
    return DISTRIBUTIONS + (("python-pptx",) if selected & {"slides", "pptx"} else ())


def _lock(content: bytes) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for package in tomllib.loads(content.decode())["package"]:
        if "version" in package:
            result.setdefault(_name(package["name"]), set()).add(package["version"])
    return result


def _read(prefix: Path, relative: str) -> tuple[bytes, dict[str, int]]:
    """Hold every provider directory with no-follow handles before reading."""
    parts = Path(relative).parts
    if not parts or Path(relative).is_absolute() or any(p in {".", ".."} for p in parts):
        raise ValueError("decoder file escapes nominated provider prefix")
    fd = os.open(prefix, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
        try:
            before = os.fstat(file_fd)
            if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_FILE:
                raise ValueError("decoder RECORD entry is not a bounded regular file")
            chunks = []
            count = 0
            while chunk := os.read(file_fd, 1024 * 1024):
                count += len(chunk)
                if count > MAX_FILE:
                    raise ValueError("decoder file exceeded observation ceiling")
                chunks.append(chunk)
            after = os.fstat(file_fd)
            stable_fields = ("st_size", "st_mode", "st_ino", "st_dev", "st_mtime_ns", "st_ctime_ns")
            if (
                any(getattr(before, field) != getattr(after, field) for field in stable_fields)
                or count != before.st_size
            ):
                raise ValueError("decoder file changed during held observation")
            return b"".join(chunks), {
                "size": before.st_size,
                "mode": before.st_mode,
                "inode": before.st_ino,
                "device": before.st_dev,
                "mtime_ns": before.st_mtime_ns,
                "ctime_ns": before.st_ctime_ns,
            }
        finally:
            os.close(file_fd)
    finally:
        os.close(fd)


def _relative(prefix: Path, site: Path, label: str) -> str:
    # Normalize legitimate RECORD ../../../bin entries lexically; never follow
    # provider symlinks to determine custody.
    candidate = Path(os.path.normpath(str(site / label)))
    try:
        return candidate.relative_to(prefix).as_posix()
    except ValueError as error:
        raise ValueError("decoder RECORD path escapes original provider prefix") from error


def _installer_console_script_path(relative: str) -> bool:
    """Whether a normalized provider path is a ``<prefix>/bin/<name>`` entry."""
    parts = Path(relative).parts
    return len(parts) == 2 and parts[0] == "bin"


def _installer_console_script(relative: str, content: bytes) -> bool:
    """Whether a RECORD entry is an installer-written console-script shim.

    The installer writes these shims itself and chooses the interpreter line, so
    a wheel's recorded size and hash describe the wheel's own script rather than
    the installed bytes; ``uv`` in particular rewrites the shebang. Only a
    ``<prefix>/bin/<name>`` entry that really begins with a shebang qualifies,
    so a genuine library file, a non-script file under ``bin``, or a corrupted
    shim still falls through to the exact RECORD comparison below.
    """
    if not _installer_console_script_path(relative):
        return False
    first = content.partition(b"\n")[0]
    return first.startswith(b"#!") and len(first.strip()) > 2


def _assert_recorded_provider_file(relative: str, content: bytes, declared_hash: str, declared_size: str) -> None:
    """Compare one provider file against its original RECORD row, naming the file."""
    if declared_size and int(declared_size) != len(content):
        raise ValueError(f"native decoder file {relative} differs from RECORD size")
    if declared_hash:
        algorithm, encoded = declared_hash.split("=", 1)
        if algorithm != "sha256":
            raise ValueError("native decoder RECORD requires source-supported SHA256 hashes")
        actual = base64.urlsafe_b64encode(hashlib.new(algorithm, content).digest()).decode().rstrip("=")
        if actual != encoded:
            raise ValueError(f"native decoder file {relative} differs from RECORD hash")


def observe_native_library_custody(formats: Any, *, repo_root: Path | None = None) -> dict[str, Any]:
    selected = _selected(formats)
    root = (repo_root or Path(__file__).resolve().parents[2]).resolve()
    lock_bytes = (root / "uv.lock").read_bytes()
    lock = _lock(lock_bytes)
    prefix = Path(sys.prefix).resolve()
    distributions: list[dict[str, Any]] = []
    total = 0
    for requested in selected:
        try:
            dist = metadata.distribution(requested)
        except metadata.PackageNotFoundError as error:
            raise ValueError(f"required native decoder distribution missing: {requested}") from error
        name = _name(dist.metadata["Name"])
        if name != _name(requested) or dist.version not in lock.get(name, set()):
            raise ValueError(f"native decoder distribution differs from source lock: {requested}")
        site = Path(str(dist.locate_file(""))).absolute()
        record_paths = [str(item) for item in (dist.files or ()) if str(item).endswith(".dist-info/RECORD")]
        if len(record_paths) != 1:
            raise ValueError("native decoder requires exactly one original RECORD")
        record_relative = _relative(prefix, site, record_paths[0])
        record, _ = _read(prefix, record_relative)
        rows = list(csv.reader(io.StringIO(record.decode())))
        inventory = []
        seen = set()
        for row in rows:
            if len(row) != 3:
                raise ValueError("native decoder RECORD row is malformed")
            label, declared_hash, declared_size = row
            relative = _relative(prefix, site, label)
            if relative in seen:
                raise ValueError("native decoder RECORD repeats normalized provider file")
            seen.add(relative)
            content, facts = _read(prefix, relative)
            total += len(content)
            if total > MAX_TOTAL:
                raise ValueError("native decoder inventory exceeds observation ceiling")
            digest = hashlib.sha256(content).hexdigest()
            if _installer_console_script(relative, content):
                # Console-script shims are installer products, not provider
                # content, so their bytes cannot be certified from the wheel
                # RECORD. Retain the observed file and digest without claiming
                # the recorded size or hash, and keep the strict comparison for
                # every provider library file.
                inventory.append(
                    {
                        "record_label": label,
                        "relative": relative,
                        "sha256": digest,
                        "metadata": facts,
                        "installer_console_script": True,
                    }
                )
                continue
            _assert_recorded_provider_file(relative, content, declared_hash, declared_size)
            inventory.append({"record_label": label, "relative": relative, "sha256": digest, "metadata": facts})
        if record_relative not in seen:
            raise ValueError("native decoder RECORD omits itself")
        distributions.append(
            {
                "name": name,
                "version": dist.version,
                "site": str(site),
                "record_relative": record_relative,
                "record_base64": base64.b64encode(record).decode(),
                "files": inventory,
            }
        )
    loaded = []
    by_name = {d["name"]: {r["relative"] for r in d["files"]} for d in distributions}
    for module_name, module in tuple(sys.modules.items()):
        distribution = MODULES.get(module_name.split(".", 1)[0])
        location = getattr(module, "__file__", None)
        if distribution not in by_name or not location:
            continue
        relative = _relative(prefix, prefix, str(location))
        if relative not in by_name[distribution]:
            raise ValueError("loaded native decoder module is foreign to observed RECORD")
        loaded.append({"module": module_name, "distribution": distribution, "relative": relative})
    return {
        "schema_version": SCHEMA,
        "formats": sorted(set(formats)),
        "provider_prefix": str(prefix),
        "source_lock_sha256": hashlib.sha256(lock_bytes).hexdigest(),
        "distributions": distributions,
        "loaded_modules": sorted(loaded, key=lambda r: r["module"]),
        "observed_bytes": total,
    }


def validate_native_library_custody(
    before: dict[str, Any], after: dict[str, Any], *, formats: Any, reader: Any, runtime: Any = None
) -> None:
    selected = {_name(name) for name in _selected(formats)}
    if before != after:
        # Modules can load between observations; file custody must remain exact.
        a, b = dict(before), dict(after)
        a.pop("loaded_modules", None)
        b.pop("loaded_modules", None)
        if a != b:
            raise ValueError("native decoder provider file custody changed")
    lock_bytes = reader.read("uv.lock").content
    lock = _lock(lock_bytes)
    for observation in (before, after):
        if (
            observation.get("schema_version") != SCHEMA
            or observation.get("formats") != sorted(set(formats))
            or observation.get("source_lock_sha256") != hashlib.sha256(lock_bytes).hexdigest()
        ):
            raise ValueError("native decoder custody schema/source selection differs")
        rows = observation["distributions"]
        if len(rows) != len(selected) or {row["name"] for row in rows} != selected:
            raise ValueError("native decoder distribution roster omitted or repeated")
        total = 0
        by_name = {}
        for distribution in rows:
            if distribution["version"] not in lock.get(distribution["name"], set()):
                raise ValueError("native decoder version differs from source lock")
            prefix, site = Path(observation["provider_prefix"]), Path(distribution["site"])
            if not prefix.is_absolute() or not site.is_absolute():
                raise ValueError("native decoder original provider labels must be absolute")
            _relative(prefix, prefix, str(site))
            record = base64.b64decode(distribution["record_base64"], validate=True)
            declared = list(csv.reader(io.StringIO(record.decode())))
            files = distribution["files"]
            expected = [_relative(prefix, site, row[0]) for row in declared if len(row) == 3]
            if (
                len(declared) != len(files)
                or len(set(expected)) != len(expected)
                or [f["relative"] for f in files] != expected
                or [f["record_label"] for f in files] != [r[0] for r in declared]
            ):
                raise ValueError("native decoder RECORD complete file census differs")
            if distribution["record_relative"] not in expected:
                raise ValueError("native decoder RECORD self custody missing")
            for file, declaration in zip(files, declared, strict=True):
                facts = file["metadata"]
                if (
                    set(facts) != {"size", "mode", "inode", "device", "mtime_ns", "ctime_ns"}
                    or any(type(value) is not int for value in facts.values())
                    or not stat.S_ISREG(facts["mode"])
                ):
                    raise ValueError("native decoder regular file metadata is malformed")
                size = facts["size"]
                total += size
                if (
                    not isinstance(size, int)
                    or size < 0
                    or size > MAX_FILE
                    or not re.fullmatch(r"[0-9a-f]{64}", file["sha256"])
                ):
                    raise ValueError("native decoder file observation malformed")
                exempt = file.get("installer_console_script") is True
                if exempt and not _installer_console_script_path(file["relative"]):
                    raise ValueError("native decoder installer shim exemption is not a provider bin entry")
                if not exempt:
                    if declaration[2] and int(declaration[2]) != size:
                        raise ValueError("native decoder retained size differs from RECORD")
                    if (
                        declaration[1].startswith("sha256=")
                        and base64.urlsafe_b64encode(bytes.fromhex(file["sha256"])).decode().rstrip("=")
                        != declaration[1][7:]
                    ):
                        raise ValueError("native decoder retained hash differs from RECORD")
                if file["relative"] == distribution["record_relative"] and (
                    file["sha256"] != hashlib.sha256(record).hexdigest() or size != len(record)
                ):
                    raise ValueError("native decoder original RECORD bytes differ")
            by_name[distribution["name"]] = set(expected)
        if total != observation["observed_bytes"] or total > MAX_TOTAL:
            raise ValueError("native decoder full byte observation census differs")
        modules = observation["loaded_modules"]
        if len({r["module"] for r in modules}) != len(modules):
            raise ValueError("native decoder module association repeats")
        for module in modules:
            if MODULES.get(module["module"].split(".", 1)[0]) != module["distribution"] or module[
                "relative"
            ] not in by_name.get(module["distribution"], set()):
                raise ValueError("native decoder loaded module association is foreign")
