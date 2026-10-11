"""Admit audited source before delegating finite notebook execution."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import hashlib
import importlib.util
import os
import stat
from typing import Any

# Establish an empty private cache namespace before importing platform or domain code.
if getattr(sys, "_template_executed_bytecode_audit", None) is None:
    _CACHE = tempfile.TemporaryDirectory(prefix="template-eda-launch-")
    sys.pycache_prefix = str(Path(_CACHE.name).resolve())
    sys.dont_write_bytecode = False

PROJECT = Path(__file__).resolve().parents[1]

_audit_spec = importlib.util.find_spec("infrastructure")
if _audit_spec is None or _audit_spec.origin is None:
    raise SystemExit("the declared platform distribution is unavailable")
_platform_source = Path(_audit_spec.origin).absolute().parent

if getattr(sys, "_template_executed_bytecode_audit", None) is None:
    # Startup I/O admits the selected platform's stdlib-only hook before public imports.
    _audit_path = _platform_source / "core/bytecode_audit.py"
    _audit_directory = os.open(_audit_path.anchor, os.O_RDONLY | os.O_DIRECTORY)
    _audit_directories = [_audit_directory]
    _audit_bindings = []
    try:
        for _name in _audit_path.parts[1:-1]:
            _child = os.open(_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=_audit_directory)
            _audit_bindings.append((_audit_directory, _name, os.fstat(_child)))
            _audit_directories.append(_child)
            _audit_directory = _child
        _audit_descriptor = os.open(
            _audit_path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=_audit_directory
        )
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
                    getattr(_before, field) != getattr(_after, field)
                    or getattr(_after, field) != getattr(_current, field)
                    for field in _fields
                )
            ):
                raise SystemExit("the selected audit source changed or is not bounded regular bytes")
            for _parent, _name, _metadata in _audit_bindings:
                _current_directory = os.stat(_name, dir_fd=_parent, follow_symlinks=False)
                if not stat.S_ISDIR(_current_directory.st_mode) or (
                    _current_directory.st_dev,
                    _current_directory.st_ino,
                ) != (_metadata.st_dev, _metadata.st_ino):
                    raise SystemExit("the selected audit source ancestor changed during admission")
        finally:
            os.close(_audit_descriptor)
    finally:
        for _directory in reversed(_audit_directories):
            os.close(_directory)
    _audit_scope: dict[str, Any] = {"__name__": "_template_bytecode_audit", "__file__": str(_audit_path)}
    # Execute the selected local hook only after bounded, no-follow source admission.
    exec(compile(_audit_bytes, str(_audit_path), "exec", dont_inherit=True), _audit_scope)  # nosec B102
    _audit_scope["install_bytecode_audit"](
        tuple(
            str(root.absolute())
            for root in (
                PROJECT / "src",
                PROJECT / "scripts",
                _platform_source,
                _platform_source.parent / "scripts",
            )
        ),
        fresh_pycache_prefix=sys.pycache_prefix,
        source_sha256=hashlib.sha256(_audit_bytes).hexdigest(),
        startup_code=sys._getframe().f_code,
    )

# Bind the admitted provider package before own source becomes importable.
# Its fixed package path prevents an own-src infrastructure shadow from winning.
import infrastructure

if infrastructure.__file__ is None or Path(infrastructure.__file__).absolute() != Path(_audit_spec.origin).absolute():
    raise SystemExit("the admitted platform provider changed during startup")
sys.path.insert(0, str(PROJECT / "src"))

from template_eda_notebook.notebook_execution import cli_main
from infrastructure.core.bytecode_audit import verify_executed_source_code

if __name__ == "__main__":
    try:
        _result = cli_main()
        assert sys.pycache_prefix is not None
        _verified_roots: tuple[Path, ...] = (PROJECT / "src", PROJECT / "scripts", _platform_source)
        if (_platform_source.parent / "scripts").is_dir():
            _verified_roots += (_platform_source.parent / "scripts",)
        for _root in _verified_roots:
            verify_executed_source_code(_root, Path(sys.pycache_prefix))
        raise SystemExit(_result)
    finally:
        if "_CACHE" in globals():
            _CACHE.cleanup()
