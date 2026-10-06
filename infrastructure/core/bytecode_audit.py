"""Stdlib-only pre-import audit of executed public code and its cache bytes.

Trusted launchers execute frozen, source-bound bytes of this module before any
public imports, then install the hook. The immutable public registry exposes
snapshots; its mutable state stays in the hook closure. This binds module exec
and later cache changes, not containment of arbitrary malicious Python code.
"""

from __future__ import annotations

import hashlib
import importlib.util
import marshal
import os
import stat
import sys
import types
from pathlib import Path
from typing import Any

SCHEMA = "template/executed-bytecode-audit/1"
REGISTRY_ATTRIBUTE = "_template_executed_bytecode_audit"
MAX_CACHE_BYTES = 64 * 1024 * 1024
MAX_EXECUTIONS = 10000


def _read_cache(path: Path) -> bytes:
    """Read bounded regular bytes through held, no-follow ancestor descriptors."""
    path = path.absolute()
    if ".." in path.parts:
        raise ValueError("audit paths cannot contain parent traversal")
    descriptors = [os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY)]
    bindings = []
    directory = descriptors[0]
    try:
        for name in path.parts[1:-1]:
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            descriptors.append(child)
            bindings.append((directory, name, child))
            directory = child
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_CACHE_BYTES:
                raise ValueError("audit cache requires a bounded regular file")
            blocks = []
            size = 0
            while block := os.read(descriptor, 1024 * 1024):
                blocks.append(block)
                size += len(block)
                if size > MAX_CACHE_BYTES:
                    raise ValueError("audit cache exceeds its byte ceiling")
            after = os.fstat(descriptor)
            current = os.stat(path.name, dir_fd=directory, follow_symlinks=False)
            fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
            if any(
                getattr(before, field) != getattr(after, field) or getattr(after, field) != getattr(current, field)
                for field in fields
            ):
                raise ValueError("audit cache changed while consumed")
            return b"".join(blocks)
        finally:
            os.close(descriptor)
    finally:
        try:
            for parent, name, child in reversed(bindings):
                held = os.fstat(child)
                named = os.stat(name, dir_fd=parent, follow_symlinks=False)
                if not stat.S_ISDIR(named.st_mode) or (held.st_dev, held.st_ino) != (named.st_dev, named.st_ino):
                    raise ValueError("audit source or cache ancestor changed during consumption")
        finally:
            for descriptor in reversed(descriptors):
                os.close(descriptor)


def install_bytecode_audit(
    source_roots: tuple[str, ...],
    *,
    fresh_pycache_prefix: str,
    source_sha256: str,
    startup_code: types.CodeType | None = None,
) -> None:
    """Install once before public imports using launcher-admitted hook bytes.

    The launcher creates the private prefix empty before interpreter startup.
    Python's early stdlib imports may already have populated it when this hook
    is installed. Every later selected public exec must match held current
    source before its payload runs; its actual code and selected cache digest
    also remain bound for post-execution verification.
    """
    if getattr(sys, REGISTRY_ATTRIBUTE, None) is not None:
        raise ValueError("executed-bytecode audit was already installed")
    roots = tuple(Path(root).absolute() for root in source_roots)
    prefix = Path(fresh_pycache_prefix).absolute()
    if not roots or any(".." in root.parts for root in roots):
        raise ValueError("audit needs explicit public source roots")
    if sys.pycache_prefix is None or Path(sys.pycache_prefix).absolute() != prefix:
        raise ValueError("audit prefix differs from interpreter startup prefix")
    if prefix.is_symlink() or any(parent.is_symlink() for parent in prefix.parents):
        raise ValueError("audit prefix cannot traverse symlinks")
    if len(source_sha256) != 64 or any(character not in "0123456789abcdef" for character in source_sha256):
        raise ValueError("audit source digest must be SHA-256")
    startup_path: Path | None = None
    main_module = sys.modules.get("__main__")
    if startup_code is not None:
        # This exception admits only the trusted standalone caller's actual
        # already-running module frame, never other previously imported code.
        filename = getattr(main_module, "__file__", None)
        if (
            type(startup_code) is not types.CodeType
            or startup_code is not sys._getframe(1).f_code
            or startup_code.co_name != "<module>"
            or not isinstance(filename, str)
            or not filename.endswith(".py")
        ):
            raise ValueError("audit startup seed requires its actual module-level main frame")
        startup_path = Path(startup_code.co_filename).absolute()
        if startup_path != Path(filename).absolute() or not any(startup_path.is_relative_to(root) for root in roots):
            raise ValueError("audit startup seed must match the admitted main source path")
        expected = compile(
            _read_cache(startup_path), startup_code.co_filename, "exec", dont_inherit=True, optimize=sys.flags.optimize
        )
        if canonical_code(startup_code) != canonical_code(expected):
            raise ValueError("executed main startup code differs from current source bytes")
        if isinstance(getattr(main_module, "__cached__", None), str):
            raise ValueError("an already-running cached main needs a pre-import execution audit")
    for module in tuple(sys.modules.values()):
        filename = getattr(module, "__file__", None)
        if (
            isinstance(filename, str)
            and filename.endswith(".py")
            and any(Path(filename).absolute().is_relative_to(root) for root in roots)
        ):
            if startup_path is not None and module is main_module and Path(filename).absolute() == startup_path:
                continue
            raise ValueError("executed-bytecode audit must precede public imports")
    records: dict[str, tuple[tuple[types.CodeType, str | None, str | None], ...]] = {}
    if startup_path is not None and startup_code is not None:
        records[str(startup_path)] = ((startup_code, None, None),)
    execution_count = int(startup_path is not None)

    def audit(event: str, arguments: tuple[Any, ...]) -> None:
        nonlocal execution_count
        if event != "exec" or not arguments or type(arguments[0]) is not types.CodeType:
            return
        code = arguments[0]
        filename = code.co_filename
        if not filename.endswith(".py") or not any(Path(filename).absolute().is_relative_to(root) for root in roots):
            return
        execution_count += 1
        if execution_count > MAX_EXECUTIONS:
            raise ValueError("public module executions exceed the audit ceiling")
        path = Path(filename).absolute()
        expected = compile(_read_cache(path), code.co_filename, "exec", dont_inherit=True, optimize=sys.flags.optimize)
        if canonical_code(code) != canonical_code(expected):
            relative = next(path.relative_to(root).as_posix() for root in roots if path.is_relative_to(root))
            raise ValueError(f"executed public module differs from current source bytes: {relative}")
        cached = Path(importlib.util.cache_from_source(str(path))).absolute()
        if not cached.is_relative_to(prefix):
            raise ValueError("public module cache is outside the fresh prefix")
        try:
            raw = _read_cache(cached)
        except FileNotFoundError:
            # Direct compile/exec has no importer cache. Actual executed code
            # remains bound and must match current source during verification.
            cache_path = cache_sha256 = None
        else:
            cache_path = str(cached)
            cache_sha256 = hashlib.sha256(raw).hexdigest()
        records[str(path)] = (*records.get(str(path), ()), (code, cache_path, cache_sha256))

    def snapshot() -> types.MappingProxyType:
        return types.MappingProxyType(dict(records))

    registry = types.MappingProxyType(
        {
            "schema_version": SCHEMA,
            "prefix": str(prefix),
            "source_roots": tuple(str(root) for root in roots),
            "hook_source_path": str(Path(__file__).absolute()),
            "hook_source_sha256": source_sha256,
            "snapshot": snapshot,
        }
    )
    sys.addaudithook(audit)
    setattr(sys, REGISTRY_ATTRIBUTE, registry)


def verify_executed_source_code(source_root: Path, prefix: Path) -> None:
    """Bind actual pre-import-audited execution and reject later cache changes.

    Serialized reference flags depend on runtime refcounts and interning. We
    compare every actual code field using version-2 serialization of trusted
    code objects with typed constants, never decoding any cache payload.
    """
    registry = getattr(sys, "_template_executed_bytecode_audit", None)
    if (
        not isinstance(registry, types.MappingProxyType)
        or registry.get("schema_version") != "template/executed-bytecode-audit/1"
    ):
        raise ValueError("fresh bytecode requires a pre-import executed-code audit")
    if registry.get("prefix") != str(prefix.absolute()):
        raise ValueError("executed-code audit differs from the fresh prefix")
    hook_path = Path(registry["hook_source_path"])
    if hashlib.sha256(_read_cache(hook_path)).hexdigest() != registry.get("hook_source_sha256"):
        raise ValueError("executed-code audit implementation changed")
    if not any(source_root.absolute().is_relative_to(Path(root)) for root in registry["source_roots"]):
        raise ValueError("public source is outside the pre-import audit roots")
    records = registry["snapshot"]()
    admitted = {path: runs for path, runs in records.items() if Path(path).is_relative_to(source_root.absolute())}
    for filename, actual_executions in admitted.items():
        path = Path(filename)
        relative = path.relative_to(source_root.absolute()).as_posix()
        raw_source = _read_cache(path)
        for actual_code, cache_path, cache_sha256 in actual_executions:
            expected = compile(
                raw_source, actual_code.co_filename, "exec", dont_inherit=True, optimize=sys.flags.optimize
            )
            if canonical_code(actual_code) != canonical_code(expected):
                raise ValueError(f"executed public module differs from current source bytes: {relative}")
            if cache_path is not None:
                raw = _read_cache(Path(cache_path))
                if len(raw) < 16 or raw[:4] != importlib.util.MAGIC_NUMBER:
                    raise ValueError("loaded public module cache has invalid Python bytecode identity")
                if hashlib.sha256(raw).hexdigest() != cache_sha256:
                    raise ValueError(f"loaded public module cache differs from execution-time bytes: {relative}")
    for module in tuple(sys.modules.values()):
        filename = getattr(module, "__file__", None)
        if not isinstance(filename, str) or not filename.endswith(".py"):
            continue
        path = Path(filename).absolute()
        if not path.is_relative_to(source_root.absolute()):
            continue
        relative = path.relative_to(source_root.absolute()).as_posix()
        actual_executions = admitted.get(str(path), ())
        if not actual_executions:
            raise ValueError(f"public module has no pre-import execution audit: {relative}")
        cached = getattr(module, "__cached__", None)
        for _, cache_path, _ in actual_executions:
            if cache_path is None:
                if isinstance(cached, str):
                    raise ValueError(f"imported public module lacks an audited cache: {relative}")
                continue
            if not isinstance(cached, str) or Path(cached).absolute() != Path(cache_path).absolute():
                raise ValueError("loaded public module did not use the audited fresh bytecode cache")


def canonical_code(code: types.CodeType) -> bytes:
    remaining = MAX_CACHE_BYTES

    def constant(value: Any, depth: int = 0) -> Any:
        nonlocal remaining
        remaining -= 256
        if type(value) in (str, bytes):
            remaining -= len(value.encode("utf-8", "surrogatepass") if type(value) is str else value)
        elif type(value) is int:
            remaining -= (value.bit_length() + 7) // 8
        elif type(value) is types.CodeType:
            remaining -= len(value.co_code) + len(value.co_linetable) + len(value.co_exceptiontable)
            remaining -= sum(
                len(name.encode("utf-8", "surrogatepass")) + 64
                for name in (
                    *value.co_names,
                    *value.co_varnames,
                    *value.co_freevars,
                    *value.co_cellvars,
                    value.co_filename,
                    value.co_name,
                    value.co_qualname,
                )
            )
        if remaining < 0:
            raise ValueError("public code canonicalization exceeds its byte-work ceiling")
        if depth > 128:
            raise ValueError("public code constants exceed the audit depth ceiling")
        if type(value) is types.CodeType:
            return ("code", value.replace(co_consts=tuple(constant(item, depth + 1) for item in value.co_consts)))
        if type(value) is tuple:
            return ("tuple", tuple(constant(item, depth + 1) for item in value))
        if type(value) is frozenset:
            return ("frozenset", frozenset(constant(item, depth + 1) for item in value))
        if type(value) is slice:
            return (
                "slice",
                constant(value.start, depth + 1),
                constant(value.stop, depth + 1),
                constant(value.step, depth + 1),
            )
        if value is Ellipsis:
            return ("ellipsis", None)
        if value is None or type(value) in (bool, int, float, complex, str, bytes):
            return (type(value).__name__, value)
        raise ValueError("public code contains an unsupported constant type")

    payload = marshal.dumps(constant(code), 2)
    if len(payload) > MAX_CACHE_BYTES:
        raise ValueError("public code canonicalization exceeds its byte ceiling")
    return payload


__all__ = ["install_bytecode_audit", "canonical_code", "verify_executed_source_code"]
