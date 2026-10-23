#!/usr/bin/env python3
"""Thin orchestrator: coordinated search vs single-thread baseline.

Runs the coordinated AutoScientists loop and the single-thread baseline on the
same deterministic objective under a *matched* experiment budget, then renders
their champion trajectories plus a machine-readable summary. Because coordinated
teams partition the same sequential budget (rather than adding parallel compute),
this is an honest robustness/efficiency comparison, not a speedup claim — the
summary reports both the reported metric and the noise-free clean metric. All
computation lives in ``src``; this script only orchestrates, plots, and writes.
"""

from __future__ import annotations

import argparse
import sys
import atexit
import tempfile
from pathlib import Path
import hashlib
import importlib.util
import importlib
import os
import stat
import sysconfig
from types import MappingProxyType

# The pipeline launcher already owns a pre-import audit and its private cache.
# Replacing that prefix would invalidate the launcher's actual execution records.
_active_audit = getattr(sys, "_template_executed_bytecode_audit", None)
if _active_audit is None:
    _BYTECODE_CACHE = tempfile.TemporaryDirectory(prefix="template-autoscientists-controller-cache-")
    sys.pycache_prefix = str(Path(_BYTECODE_CACHE.name).resolve())
    atexit.register(_BYTECODE_CACHE.cleanup)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_provider_roots = tuple(Path(sysconfig.get_path(kind)).resolve(strict=True) for kind in ("purelib", "platlib"))


_original_import_paths = sys.path[:]
# Capture provider lookup paths and their physical bindings before public code.
# Reuse that surface for lookup and import, refusing changed path bindings.
_provider_import_paths = []
for _entry in _original_import_paths:
    _candidate = Path(_entry or os.getcwd()).resolve()
    if not (
        _candidate.is_relative_to(PROJECT_ROOT)
        and not any(_candidate.is_relative_to(provider) for provider in _provider_roots)
    ):
        _provider_import_paths.append((_entry, _candidate))
try:
    sys.path[:] = [str(candidate) for _, candidate in _provider_import_paths]
    _audit_spec = importlib.util.find_spec("infrastructure")
finally:
    sys.path[:] = _original_import_paths

# Admit the actual stdlib-only audit hook before importing public packages.
# This is startup I/O; the shared hook owns execution/cache custody logic.
if _audit_spec is None or _audit_spec.origin is None:
    raise SystemExit("the declared platform distribution is unavailable")
_audit_origin = Path(_audit_spec.origin).resolve(strict=True)
if _audit_origin.is_relative_to(PROJECT_ROOT) and not any(
    _audit_origin.is_relative_to(provider) for provider in _provider_roots
):
    raise SystemExit("own project source cannot provide the declared platform SDK")
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
if _active_audit is None:
    # A fresh standalone controller owns its provider-root selection. An
    # existing launcher already fixed its pre-import scope; an optional,
    # unconsumed installed package cannot retroactively extend that scope.
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
    for _entry, _candidate in _provider_import_paths:
        if Path(_entry or os.getcwd()).resolve() != _candidate:
            raise SystemExit("the selected provider import path changed during startup")
    sys.path[:] = [str(candidate) for _, candidate in _provider_import_paths]
    _selected_sdk = importlib.import_module("infrastructure")
    if Path(_selected_sdk.__file__).resolve(strict=True) != _audit_origin:
        raise SystemExit("the selected platform source origin changed during startup")
finally:
    sys.path[:] = _original_import_paths
for path in (PROJECT_ROOT, PROJECT_ROOT / "src"):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from template_autoscientists.figures.figures import write_comparison_outputs  # noqa: E402
from template_autoscientists.agents.live_domain import LiveSettings  # noqa: E402
from template_autoscientists.search.live_comparison import live_exit_code, run_live_comparison  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("core", "live"), default="core")
    parser.add_argument("--model")
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--experiments-per-arm", type=int, default=6)
    parser.add_argument("--request-timeout-seconds", type=int, default=60)
    parser.add_argument("--run-timeout-seconds", type=int, default=600)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    if args.mode == "live":
        if not args.model or args.output_dir is None:
            parser.error("live mode requires --model and a fresh --output-dir")
        try:
            receipt = run_live_comparison(
                args.project_root,
                args.output_dir,
                LiveSettings(
                    model=args.model,
                    endpoint=args.endpoint,
                    experiments_per_arm=args.experiments_per_arm,
                    request_timeout_seconds=args.request_timeout_seconds,
                    run_timeout_seconds=args.run_timeout_seconds,
                ),
            )
        except ValueError as exc:
            parser.error(str(exc))
        print(receipt)
        return live_exit_code(receipt)
    for path in write_comparison_outputs(args.output_dir or args.project_root / "output"):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
