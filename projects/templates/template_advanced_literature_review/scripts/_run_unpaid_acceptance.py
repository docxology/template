#!/usr/bin/env python3
"""Explicit core or unpaid live phase acceptance entry point."""

from __future__ import annotations

import atexit
import hashlib
import importlib.util
import os
import stat
import sys
import tempfile
from pathlib import Path

_BYTECODE_CACHE = tempfile.TemporaryDirectory(prefix="template-literature-controller-cache-")
sys.pycache_prefix = str(Path(_BYTECODE_CACHE.name).resolve())
atexit.register(_BYTECODE_CACHE.cleanup)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(PROJECT_ROOT / "src"), str(PROJECT_ROOT.parents[2])]

# Admit the actual stdlib-only audit hook before importing public packages.
# This is startup I/O; the shared hook owns execution/cache custody logic.
_audit_spec = importlib.util.find_spec("infrastructure")
if _audit_spec is None or _audit_spec.origin is None:
    raise SystemExit("the declared platform distribution is unavailable")
_platform_source = Path(_audit_spec.origin).absolute().parent
_audit_path = _platform_source / "core/bytecode_audit.py"
_audit_descriptors = [os.open(_audit_path.anchor, getattr(os, "O_PATH", os.O_RDONLY) | os.O_DIRECTORY)]
_audit_bindings = []
_audit_directory = _audit_descriptors[0]
try:
    for _name in _audit_path.parts[1:-1]:
        _child = os.open(
            _name, getattr(os, "O_PATH", os.O_RDONLY) | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=_audit_directory
        )
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
_audit_scope["install_bytecode_audit"](
    tuple(str(root.absolute()) for root in _audit_roots),
    fresh_pycache_prefix=sys.pycache_prefix,
    source_sha256=hashlib.sha256(_audit_bytes).hexdigest(),
    startup_code=sys._getframe().f_code,
)

from _bootstrap import bootstrap_project

PROJECT_ROOT = bootstrap_project()

from multi_phase.live_acceptance import main

if __name__ == "__main__":
    raise SystemExit(main(PROJECT_ROOT))
