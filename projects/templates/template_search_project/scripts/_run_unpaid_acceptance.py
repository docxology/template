#!/usr/bin/env python3
"""Run the explicitly selected core or unpaid live literature acceptance lane."""

from __future__ import annotations

import sys
import atexit
import tempfile
from pathlib import Path
import hashlib
import importlib.util
import os
import stat
import importlib
import sysconfig
from types import MappingProxyType

# The pipeline launcher already owns a pre-import audit and its private cache.
# Replacing that prefix would invalidate the launcher's actual execution records.
_active_audit = getattr(sys, "_template_executed_bytecode_audit", None)
if _active_audit is None:
    _BYTECODE_CACHE = tempfile.TemporaryDirectory(prefix="template-literature-controller-cache-")
    sys.pycache_prefix = str(Path(_BYTECODE_CACHE.name).resolve())
    atexit.register(_BYTECODE_CACHE.cleanup)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_provider_roots = tuple(Path(sysconfig.get_path(kind)).resolve(strict=True) for kind in ("purelib", "platlib"))


def _own_source(path: Path) -> bool:
    resolved = path.resolve()
    return resolved.is_relative_to(PROJECT_ROOT) and not any(
        resolved.is_relative_to(provider) for provider in _provider_roots
    )


_original_import_paths = sys.path[:]
try:
    sys.path[:] = [entry for entry in _original_import_paths if not _own_source(Path(entry or os.getcwd()))]
    _audit_spec = importlib.util.find_spec("infrastructure")
finally:
    sys.path[:] = _original_import_paths

# Admit the actual stdlib-only audit hook before importing public packages.
# This is startup I/O; the shared hook owns execution/cache custody logic.
if _audit_spec is None or _audit_spec.origin is None:
    raise SystemExit("the declared platform distribution is unavailable")
if _own_source(Path(_audit_spec.origin).resolve(strict=True)):
    raise SystemExit("own project source cannot provide the declared platform SDK")
_platform_source = Path(_audit_spec.origin).absolute().parent
_audit_path = _platform_source / "core/bytecode_audit.py"
_audit_descriptors = [os.open(_audit_path.anchor, os.O_RDONLY | os.O_DIRECTORY)]
_audit_bindings = []
_audit_directory = _audit_descriptors[0]
try:
    for _name in _audit_path.parts[1:-1]:
        _child = os.open(_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=_audit_directory)
        _audit_descriptors.append(_child)
        _audit_bindings.append((_audit_directory, _name, _child))
        _audit_directory = _child
    _audit_descriptor = os.open(_audit_path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=_audit_directory)
    try:
        _before = os.fstat(_audit_descriptor)
        _audit_bytes = os.read(_audit_descriptor, 65537)
        _after = os.fstat(_audit_descriptor)
        _current = os.stat(_audit_path.name, dir_fd=_audit_directory, follow_symlinks=False)
        _fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        if (
            not stat.S_ISREG(_before.st_mode)
            or len(_audit_bytes) > 65536
            or len(_audit_bytes) != _before.st_size
            or any(
                getattr(_before, field) != getattr(_after, field) or getattr(_after, field) != getattr(_current, field)
                for field in _fields
            )
        ):
            raise SystemExit("the selected audit source changed or is not bounded regular bytes")
    finally:
        os.close(_audit_descriptor)
finally:
    try:
        for _parent, _name, _child in reversed(_audit_bindings):
            _held = os.fstat(_child)
            _named = os.stat(_name, dir_fd=_parent, follow_symlinks=False)
            if not stat.S_ISDIR(_named.st_mode) or (_held.st_dev, _held.st_ino) != (_named.st_dev, _named.st_ino):
                raise SystemExit("the selected audit source ancestor changed during consumption")
    finally:
        for _descriptor in reversed(_audit_descriptors):
            os.close(_descriptor)
_audit_roots = [PROJECT_ROOT / "src", PROJECT_ROOT / "scripts", _platform_source, _platform_source.parent / "scripts"]
_provider_spec = importlib.util.find_spec("template_literature_meta_analysis")
if _provider_spec is not None and _provider_spec.origin is not None:
    _audit_roots.append(Path(_provider_spec.origin).absolute().parent)
_audit_scope = {"__name__": "_template_bytecode_audit", "__file__": str(_audit_path)}
# Execute only the trusted, bounded, no-follow startup source admitted above.
exec(compile(_audit_bytes, str(_audit_path), "exec", dont_inherit=True), _audit_scope)  # nosec B102
if _active_audit is None:
    _audit_scope["install_bytecode_audit"](
        tuple(str(root.absolute()) for root in _audit_roots),
        fresh_pycache_prefix=sys.pycache_prefix,
        source_sha256=hashlib.sha256(_audit_bytes).hexdigest(),
        startup_code=sys._getframe().f_code,
    )
else:
    if (
        not isinstance(_active_audit, MappingProxyType)
        or _active_audit.get("schema_version") != _audit_scope["SCHEMA"]
        or _active_audit.get("hook_source_path") != str(_audit_path)
        or _active_audit.get("hook_source_sha256") != hashlib.sha256(_audit_bytes).hexdigest()
        or sys.pycache_prefix is None
        or _active_audit.get("prefix") != str(Path(sys.pycache_prefix).absolute())
    ):
        raise SystemExit("the active audit differs from the selected platform or cache")
    for _root in _audit_roots:
        _audit_scope["verify_executed_source_code"](_root, Path(sys.pycache_prefix))

try:
    sys.path[:] = [entry for entry in _original_import_paths if not _own_source(Path(entry or os.getcwd()))]
    _selected_sdk = importlib.import_module("infrastructure")
    if Path(_selected_sdk.__file__).resolve(strict=True) != Path(_audit_spec.origin).resolve(strict=True):
        raise SystemExit("the selected platform source origin changed during startup")
finally:
    sys.path[:] = _original_import_paths
# Select the declared SDK before exposing domain source; no ancestor imports.
_original_import_paths = sys.path[:]
try:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from _search_sdk_bootstrap import select_platform_sdk

    select_platform_sdk(PROJECT_ROOT)
finally:
    sys.path[:] = _original_import_paths
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from template_search_project.pipeline.live_acceptance import main

if __name__ == "__main__":
    raise SystemExit(main(PROJECT_ROOT))
