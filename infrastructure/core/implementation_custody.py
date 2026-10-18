"""Actual public implementation and installed-distribution custody.

Checkout source, installed wheel source, and bytecode launch conditions are
different evidence planes. This module never acquires dependencies or creates
fictional checkout files inside an installed distribution.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import math
import os
import re
import sys
import sysconfig
import time
import tomllib
from email.parser import BytesParser
from importlib.metadata import distributions
from pathlib import Path, PurePosixPath
from typing import Any

from infrastructure.core.bytecode_audit import verify_executed_source_code
from infrastructure.core.pipeline.fingerprints import verify_loaded_implementation
from infrastructure.core.pipeline.fingerprint_files import anchored_parent, open_directory, observation

PACKAGE = "research-project-template"
SCHEMA = "template/implementation-custody/1"


def _package_identity(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _regular_bytes(path: Path, *, max_bytes: int = 64 * 1024 * 1024) -> bytes:
    """Read a bounded regular file without accepting symlink ancestry/replacement."""
    import stat

    path = path.absolute()
    with anchored_parent(path) as parent:
        if parent is None:
            raise ValueError("implementation custody requires an existing regular file")
        descriptor = os.open(path.name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | os.O_NONBLOCK, dir_fd=parent)
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode) or before.st_size > max_bytes:
                raise ValueError("implementation custody requires a bounded regular file")
            chunks = []
            size = 0
            while chunk := os.read(descriptor, min(1024 * 1024, max_bytes + 1)):
                chunks.append(chunk)
                size += len(chunk)
                if size > max_bytes:
                    raise ValueError("implementation file grew beyond its byte ceiling")
            after = os.fstat(descriptor)
            current = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            if observation(before) != observation(after) or observation(after) != observation(current):
                raise ValueError("implementation file changed while consumed")
            return b"".join(chunks)
        finally:
            os.close(descriptor)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def source_file_manifest(
    root: Path,
    suffixes: frozenset[str],
    *,
    deadline: float | None = None,
    max_entries: int | None = None,
    max_depth: int | None = None,
) -> dict[str, str]:
    """Inventory no-follow public source with optional admission-work limits.

    Entries include directories and files outside the selected suffixes. Root
    depth is zero. Omitted limits preserve existing behavior. The monotonic
    deadline is soft between filesystem calls; hard time bounds require the
    caller's process guardian.
    """
    import stat

    if deadline is not None and (type(deadline) not in (int, float) or not math.isfinite(deadline)):
        raise ValueError("source manifest deadline must be a finite monotonic number")
    for name, value, minimum, maximum in (
        ("max_entries", max_entries, 1, 1_000_000),
        ("max_depth", max_depth, 0, 256),
    ):
        if value is not None and (type(value) is not int or not minimum <= value <= maximum):
            raise ValueError(f"source manifest {name} must be an exact integer in [{minimum}, {maximum}]")
    root = root.absolute()
    result: dict[str, str] = {}
    bounded = any(value is not None for value in (deadline, max_entries, max_depth))
    admitted_entries = 0

    def check_deadline() -> None:
        if deadline is not None and time.monotonic() >= deadline:
            raise ValueError("source manifest admission deadline exhausted")

    def names_in(descriptor: int, *, expected_count: int | None = None) -> list[str]:
        nonlocal admitted_entries
        if not bounded:
            return sorted(os.listdir(descriptor))
        names: list[str] = []
        with os.scandir(descriptor) as entries:
            for entry in entries:
                check_deadline()
                if expected_count is None:
                    admitted_entries += 1
                    if max_entries is not None and admitted_entries > max_entries:
                        raise ValueError("source manifest entry ceiling exceeded")
                elif len(names) >= expected_count:
                    raise ValueError("implementation directory changed during traversal")
                names.append(entry.name)
        check_deadline()
        return sorted(names)

    def visit(directory: Path, descriptor: int, depth: int) -> None:
        check_deadline()
        names = names_in(descriptor)
        for name in names:
            check_deadline()
            path = directory / name
            metadata = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            if stat.S_ISLNK(metadata.st_mode):
                raise ValueError("implementation source cannot contain symlinks")
            if stat.S_ISDIR(metadata.st_mode):
                if max_depth is not None and depth >= max_depth:
                    raise ValueError("source manifest depth ceiling exceeded")
                with open_directory(descriptor, name) as child:
                    opened = os.fstat(child)
                    if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
                        raise ValueError("implementation directory changed before traversal")
                    visit(path, child, depth + 1)
            elif path.suffix in suffixes:
                result[path.relative_to(root).as_posix()] = _sha(_regular_bytes(path))
            check_deadline()
        if names != names_in(descriptor, expected_count=len(names)):
            raise ValueError("implementation directory changed during traversal")
        check_deadline()

    check_deadline()
    with anchored_parent(root) as parent:
        if parent is not None:
            try:
                metadata = os.stat(root.name, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                metadata = None
            if metadata is not None:
                if not stat.S_ISDIR(metadata.st_mode):
                    raise ValueError("implementation source root must be a real directory")
                with open_directory(parent, root.name) as descriptor:
                    visit(root, descriptor, 0)
    check_deadline()
    return result


def _python_files(root: Path) -> dict[str, str]:
    return source_file_manifest(root, frozenset({".py"}))


def source_file_digest(path: Path) -> str:
    """Bind one public source file with the same no-follow read contract."""
    return _sha(_regular_bytes(path))


def source_file_bytes(path: Path) -> bytes:
    """Consume bounded source bytes under the same held no-follow read contract."""
    return _regular_bytes(path)


def runtime_identity() -> dict[str, Any]:
    """Bind the actual interpreter and only its installed site-package metadata."""
    binary = Path(sys.executable).resolve()
    packages = sorted(
        [str(item.metadata.get("Name", "")), item.version]
        for item in distributions(path=sorted({sysconfig.get_path("purelib"), sysconfig.get_path("platlib")}))
    )
    return {
        "python_executable": str(binary),
        "python_sha256": _sha(_regular_bytes(binary)),
        "python_version": sys.version,
        "implementation": sys.implementation.name,
        "packages": packages,
    }


def _distribution_custody(
    package_root: Path,
    *,
    installed: bool,
    package: str = PACKAGE,
    entrypoints: frozenset[str] = frozenset(
        {"research-template", "research-template.exe", "research-template-script.py"}
    ),
    public_modules: frozenset[str] = frozenset(),
    checkout_root: Path | None = None,
) -> dict[str, Any] | None:
    # A checkout's generated src/*.egg-info may precede its installed editable
    # metadata on sys.path. Only the actual runtime's installation sites may
    # nominate that supplementary distribution. Installed/custom-target source
    # instead nominates its own real provider parent, never another sys.path
    # provider with the same name.
    roots = (
        sorted({sysconfig.get_path("purelib"), sysconfig.get_path("platlib")})
        if checkout_root is not None
        else [str(package_root.parent)]
    )
    candidates = tuple(distributions(name=package, path=roots))
    if not candidates:
        if installed:
            raise ValueError("installed implementation lacks selected distribution metadata") from None
        return None
    if len(candidates) != 1:
        raise ValueError("selected platform distribution metadata is ambiguous")
    selected = candidates[0]
    files = selected.files
    if files is None:
        raise ValueError("selected platform distribution lacks its declared file set")
    records = [str(path) for path in files if str(path).endswith(".dist-info/RECORD")]
    if len(records) != 1:
        raise ValueError("selected platform distribution must declare exactly one RECORD")
    record_name = records[0]
    record_relative = PurePosixPath(record_name)
    if len(record_relative.parts) != 2 or ".." in record_relative.parts or record_relative.parts[1] != "RECORD":
        raise ValueError("selected platform RECORD must stay in one direct metadata directory")
    metadata_name = str(PurePosixPath(record_name).parent / "METADATA")
    record = _regular_bytes(Path(str(selected.locate_file(record_name))))
    metadata = _regular_bytes(Path(str(selected.locate_file(metadata_name))))
    headers = BytesParser().parsebytes(metadata)
    names = headers.get_all("Name") or []
    if (
        len(names) != 1
        or _package_identity(names[0]) != _package_identity(package)
        or headers.get_all("Version") != [selected.version]
    ):
        raise ValueError("selected platform METADATA identity is ambiguous or inconsistent")
    entries: dict[str, list[str]] = {}
    actual_files: dict[str, str] = {}
    source_files: dict[str, str] = {}
    companion_files: dict[str, str] = {}
    metadata_directory = PurePosixPath(record_name).parent
    site_root = Path(str(selected.locate_file(""))).absolute()
    scripts_root = Path(sysconfig.get_path("scripts")).absolute()
    module_files = frozenset(name + ".py" for name in public_modules)
    for row in csv.reader(io.StringIO(record.decode("utf-8"))):
        if (
            len(row) != 3
            or not row[0]
            or row[0] in entries
            or any(value in row[0] for value in ("\\", "\x00", "\n", "\r"))
        ):
            raise ValueError("selected platform RECORD has an invalid or duplicate row")
        name, declared_hash, declared_size = row
        relative = PurePosixPath(name)
        if relative.is_absolute():
            raise ValueError("selected platform RECORD cannot use absolute paths")
        location = Path(os.path.abspath(str(selected.locate_file(name))))
        in_package = location.is_relative_to(package_root)
        in_metadata = location.is_relative_to(site_root / metadata_directory)
        entrypoint = location.parent == scripts_root and location.name in entrypoints
        public_module = location.parent == site_root and location.name in module_files
        editable = (
            not installed
            and location.parent == site_root
            and package.replace("-", "_") in location.name
            and location.suffix in {".pth", ".py"}
        )
        if not (in_package or in_metadata or entrypoint or editable or public_module):
            raise ValueError("selected platform RECORD escapes its public package/metadata/entrypoint scope")
        entries[name] = [declared_hash, declared_size]
        # Installers may append cache files with empty hash/size. Fresh owned
        # bytecode prefixes ensure those caches cannot substitute for source.
        if "__pycache__" in relative.parts and location.suffix == ".pyc":
            continue
        raw = _regular_bytes(location)
        actual_files[name] = _sha(raw)
        if name != record_name and (not declared_hash or not declared_size):
            raise ValueError("selected distribution file lacks exact RECORD hash/size custody")
        if declared_size and (not declared_size.isdecimal() or int(declared_size) != len(raw)):
            raise ValueError("installed platform file differs from its declared RECORD size")
        if declared_hash:
            algorithm, separator, expected = declared_hash.partition("=")
            if algorithm != "sha256" or not separator:
                raise ValueError("selected platform RECORD requires SHA-256 file hashes")
            actual = base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).decode().rstrip("=")
            if actual != expected:
                raise ValueError("installed platform file differs from its declared RECORD hash")
        if in_package and location.suffix == ".py":
            if not declared_hash or not declared_size:
                raise ValueError("installed public Python source lacks exact RECORD custody")
            source_files[location.relative_to(package_root).as_posix()] = _sha(raw)
        if public_module:
            companion_files[location.name] = _sha(raw)
    if set(entries) != {str(path) for path in files}:
        raise ValueError("selected distribution file set differs from its RECORD")
    if installed:
        if not module_files.issubset(entries):
            raise ValueError("installed dependency omitted a declared companion module")
        actual_source = _python_files(package_root)
        if source_files != actual_source:
            raise ValueError("installed public Python differs from the declared distribution source file set")
    return {
        "name": package,
        "version": selected.version,
        "metadata_sha256": _sha(metadata),
        "record_sha256": _sha(record),
        "declared_files": entries,
        "file_sha256": actual_files,
        "public_python": source_files,
        # Keep package-relative names stable: a top-level companion may have
        # the same basename as the package's own __init__.py.
        "companion_python": companion_files,
    }


def capture_dependency_custody(
    package: str,
    source_root: Path,
    *,
    checkout_root: Path | None = None,
    fresh_pycache_prefix: Path | None = None,
    public_modules: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    """Bind an explicitly selected real dependency without inventing checkout files.

    The caller supplies the actual imported package directory. A checkout root
    is admitted only with its matching package metadata and lock; installed
    providers require their exact selected distribution RECORD and file set.
    """
    if not isinstance(package, str) or not package or any(value in package for value in ("/", "\\", "\x00")):
        raise ValueError("dependency custody requires an explicit package identity")
    if type(public_modules) is not frozenset or any(
        not isinstance(name, str) or not name.isidentifier() for name in public_modules
    ):
        raise ValueError("dependency companion modules require exact top-level Python identifiers")
    source_root = source_root.absolute()
    files = _python_files(source_root)
    if not files:
        raise ValueError("dependency custody requires actual public Python source")
    if checkout_root is not None:
        root = checkout_root.absolute()
        if not source_root.is_relative_to(root):
            raise ValueError("dependency source must stay inside its declared checkout")
        declared = tomllib.loads(_regular_bytes(root / "pyproject.toml").decode("utf-8"))["project"]
        if not isinstance(declared.get("name"), str) or _package_identity(declared["name"]) != _package_identity(
            package
        ):
            raise ValueError("dependency checkout package identity is inconsistent")
        for name in ("pyproject.toml", "uv.lock"):
            files["checkout/" + name] = source_file_digest(root / name)
    metadata = _distribution_custody(
        source_root,
        installed=checkout_root is None,
        package=package,
        entrypoints=frozenset(),
        public_modules=public_modules,
        checkout_root=checkout_root,
    )
    if checkout_root is not None and metadata is not None and declared.get("version") != metadata["version"]:
        raise ValueError("dependency checkout version differs from selected installed metadata")
    if fresh_pycache_prefix is not None:
        prefix = fresh_pycache_prefix.absolute()
        if sys.pycache_prefix is None or Path(sys.pycache_prefix).absolute() != prefix:
            raise ValueError("dependency did not use its launcher's fresh bytecode prefix")
        if prefix.is_symlink() or any(parent.is_symlink() for parent in prefix.parents):
            raise ValueError("dependency bytecode prefix cannot traverse symlinks")
        verify_fresh_module_bytecode(source_root, prefix)
    binding = "source-checkout" if checkout_root is not None else "installed-distribution"
    return {
        "name": package,
        "binding_kind": binding,
        "files": files,
        "distribution": metadata,
        "bytecode_binding": "fresh-owned-prefix" if fresh_pycache_prefix is not None else "loaded-baseline",
    }


def capture_implementation_custody(*, fresh_pycache_prefix: Path | None = None) -> dict[str, Any]:
    """Capture actual loaded public source and distinguish checkout from wheel custody.

    A provided prefix must have been created empty by the trusted launcher before
    importing infrastructure. This verifies its use; launch freshness remains an
    explicit launcher obligation rather than a claim inferred from source hashes.
    """
    import infrastructure

    verify_loaded_implementation()
    if infrastructure.__file__ is None:
        raise ValueError("actual platform source location is unavailable")
    package_root = Path(infrastructure.__file__).absolute().parent
    root = package_root.parent
    checkout = all((root / name).is_file() for name in ("pyproject.toml", "uv.lock", ".python-version"))
    files = {"infrastructure/" + key: value for key, value in _python_files(package_root).items()}
    if checkout:
        files.update({"scripts/" + key: value for key, value in _python_files(root / "scripts").items()})
        files.update(
            {name: _sha(_regular_bytes(root / name)) for name in ("pyproject.toml", "uv.lock", ".python-version")}
        )
    if fresh_pycache_prefix is not None:
        prefix = fresh_pycache_prefix.absolute()
        if sys.pycache_prefix is None or Path(sys.pycache_prefix).absolute() != prefix:
            raise ValueError("worker did not use its launcher's fresh bytecode prefix")
        if prefix.is_symlink() or any(parent.is_symlink() for parent in prefix.parents):
            raise ValueError("fresh bytecode prefix cannot traverse symlinks")
        verify_fresh_module_bytecode(package_root, prefix)
    metadata = _distribution_custody(package_root, installed=not checkout, checkout_root=root if checkout else None)
    if checkout:
        declared = tomllib.loads(_regular_bytes(root / "pyproject.toml").decode("utf-8"))["project"]
        if declared.get("name") != PACKAGE or declared.get("version") != infrastructure.__version__:
            raise ValueError("checkout package identity disagrees with loaded platform identity")
        if metadata is not None and declared.get("version") != metadata["version"]:
            raise ValueError("checkout package identity disagrees with selected installed metadata")
    if metadata is not None and infrastructure.__version__ != metadata["version"]:
        raise ValueError("loaded platform version differs from selected installed distribution")
    return {
        "schema_version": SCHEMA,
        "binding_kind": "source-checkout" if checkout else "installed-distribution",
        "files": files,
        "distribution": metadata,
        "runtime_environment": runtime_identity(),
        "bytecode_binding": "fresh-owned-prefix" if fresh_pycache_prefix is not None else "loaded-baseline",
    }


def verify_implementation_custody(expected: dict[str, Any], *, fresh_pycache_prefix: Path | None = None) -> None:
    """Reject changed source/distribution/runtime or stale loaded implementation."""
    actual = capture_implementation_custody(fresh_pycache_prefix=fresh_pycache_prefix)
    # Controller and fresh worker have separate explicit bytecode evidence.
    # Their source/distribution/runtime planes must agree exactly.
    if fresh_pycache_prefix is not None:
        expected = dict(expected, bytecode_binding="fresh-owned-prefix")
    if actual != expected:
        raise ValueError("public implementation, distribution, bytecode binding or runtime changed")


def verify_fresh_module_bytecode(source_root: Path, prefix: Path) -> None:
    """Verify actual pre-import-audited code and execution-time cache custody."""
    verify_executed_source_code(source_root, prefix)


def bytecode_audit_bootstrap(
    source_roots: tuple[Path, ...], prefix: Path | None, *, audit_path: Path | None = None, seed_main: bool = False
) -> str:
    """Freeze the trusted stdlib hook into a parent-owned worker bootstrap."""
    # Loaded module locations can retain import-path aliases. Canonicalize only
    # our implementation origin; explicit source paths retain strict admission.
    path = audit_path.absolute() if audit_path is not None else Path(__file__).resolve().with_name("bytecode_audit.py")
    raw = _regular_bytes(path)
    return _format_bytecode_audit_bootstrap(raw, path, source_roots, prefix, seed_main=seed_main)


def _format_bytecode_audit_bootstrap(
    raw: bytes, path: Path, source_roots: tuple[Path, ...], prefix: Path | None, *, seed_main: bool = False
) -> str:
    """Reconstruct the exact launcher from already admitted hook bytes and paths.

    This pure formatter does not admit or read paths. Execution launchers must
    first consume the hook through the confined reader above; receipt readers
    use the original admitted source snapshot to check the identical command.
    """
    prefix_expression = repr(str(prefix.absolute())) if prefix is not None else "sys.pycache_prefix"
    startup_expression = ",startup_code=sys._getframe().f_code" if seed_main else ""
    return (
        "import base64,sys\n"
        f"_audit_bytes=base64.b64decode({base64.b64encode(raw).decode('ascii')!r})\n"
        f"_audit_scope={{'__name__':'_template_bytecode_audit','__file__':{str(path)!r}}}\n"
        f"exec(compile(_audit_bytes,{str(path)!r},'exec',dont_inherit=True),_audit_scope)\n"
        f"_audit_scope['install_bytecode_audit']({tuple(str(root.absolute()) for root in source_roots)!r},"
        f"fresh_pycache_prefix={prefix_expression},source_sha256={_sha(raw)!r}{startup_expression})\n"
    )


__all__ = [
    "capture_implementation_custody",
    "capture_dependency_custody",
    "runtime_identity",
    "bytecode_audit_bootstrap",
    "verify_fresh_module_bytecode",
    "verify_implementation_custody",
    "source_file_manifest",
    "source_file_digest",
    "source_file_bytes",
]
