"""Admit the local stdlib-only audit hook before prepared CLI imports."""

from __future__ import annotations

import hashlib
import math
import os
import signal
import stat
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


def _expired(_signal: int, _frame: object) -> None:
    raise TimeoutError("Prepared runtime startup exceeded its finite admission deadline")


if __name__ == "__main__":
    _entered = time.monotonic()
    _started = _entered
    signal.signal(signal.SIGINT, signal.default_int_handler)
    signal.signal(signal.SIGALRM, _expired)
    _repo = Path(__file__).absolute().parents[2]
    try:
        _started = float(os.environ.get("TEMPLATE_PREPARED_DISPATCH_STARTED", str(_entered)))
        if not math.isfinite(_started) or _started < 0 or _started > _entered:
            raise ValueError("Prepared dispatch admission clock is invalid")
        try:
            _budget = float(os.environ.get("TEMPLATE_DISPATCH_TIMEOUT_SECONDS", "14400"))
            if not math.isfinite(_budget) or _budget <= 0:
                raise ValueError("TEMPLATE_DISPATCH_TIMEOUT_SECONDS must be positive and finite")
        except ValueError as _error:
            print(f"Invalid dispatch configuration: {_error}", file=sys.stderr)
            raise SystemExit(2) from None
        _startup_deadline = float(
            os.environ.get("TEMPLATE_PREPARED_STARTUP_DEADLINE", str(_started + min(30, _budget)))
        )
        if not math.isfinite(_startup_deadline) or _startup_deadline > _started + min(30, _budget):
            raise ValueError("Prepared startup deadline exceeds the original admitted budget")
        _remaining = min(_started + _budget, _startup_deadline) - time.monotonic()
        if _remaining <= 0:
            raise TimeoutError("Whole-dispatch deadline expired during interpreter admission")
        signal.setitimer(signal.ITIMER_REAL, _remaining)
        with tempfile.TemporaryDirectory(prefix="template-prepared-startup-") as _temporary:
            sys.pycache_prefix = str(Path(_temporary).resolve())
            _path = _repo / "infrastructure/core/bytecode_audit.py"
            _descriptors = [os.open(_path.anchor, os.O_RDONLY | os.O_DIRECTORY)]
            _bindings: list[tuple[int, str, int]] = []
            _directory = _descriptors[0]
            try:
                for _name in _path.parts[1:-1]:
                    _child = os.open(_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=_directory)
                    _bindings.append((_directory, _name, _child))
                    _descriptors.append(_child)
                    _directory = _child
                _descriptor = os.open(_path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=_directory)
                try:
                    _before = os.fstat(_descriptor)
                    _source = os.read(_descriptor, 65537)
                    _after = os.fstat(_descriptor)
                    _current = os.stat(_path.name, dir_fd=_directory, follow_symlinks=False)
                    _fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_mode")
                    if (
                        not stat.S_ISREG(_before.st_mode)
                        or len(_source) > 65536
                        or len(_source) != _before.st_size
                        or any(
                            getattr(_before, field) != getattr(_after, field)
                            or getattr(_after, field) != getattr(_current, field)
                            for field in _fields
                        )
                    ):
                        raise ValueError("Prepared audit hook changed or is not bounded regular bytes")
                finally:
                    os.close(_descriptor)
            finally:
                try:
                    for _parent, _name, _child in reversed(_bindings):
                        _held, _named = os.fstat(_child), os.stat(_name, dir_fd=_parent, follow_symlinks=False)
                        if not stat.S_ISDIR(_named.st_mode) or (_held.st_dev, _held.st_ino) != (
                            _named.st_dev,
                            _named.st_ino,
                        ):
                            raise ValueError("Prepared audit hook ancestor changed")
                finally:
                    for _descriptor in reversed(_descriptors):
                        os.close(_descriptor)
            _scope: dict[str, Any] = {"__name__": "_template_prepared_audit", "__file__": str(_path)}
            exec(compile(_source, str(_path), "exec", dont_inherit=True), _scope)  # nosec B102
            _scope["install_bytecode_audit"](
                (str(_repo / "infrastructure"), str(_repo / "scripts")),
                fresh_pycache_prefix=sys.pycache_prefix,
                source_sha256=hashlib.sha256(_source).hexdigest(),
                startup_code=sys._getframe().f_code,
            )
            # -S prevents arbitrary .pth startup code before the guardian.
            # Establish the candidate prefix before any public sysconfig/metadata
            # imports; the stdlib-only admission module validates it below.
            _selected = Path(os.environ.get("TEMPLATE_ROOT_PYTHON", str(_repo / ".venv/bin/python")))
            _observed_prefix = sys.prefix
            sys.prefix = sys.exec_prefix = str(_selected.parent.parent)
            sys.path.insert(0, str(_repo))
            from infrastructure.core.runtime.prepared_runtime import (
                PreparedRuntimeUnavailable,
                check_prepared_root_runtime,
                configure_prepared_site,
            )

            configure_prepared_site(_selected, observed_prefix=_observed_prefix)
            from infrastructure.core.runtime.prepared_dispatch import dispatch_prepared_cli

            check_prepared_root_runtime(_repo)
            signal.setitimer(signal.ITIMER_REAL, 0)
            _result = dispatch_prepared_cli(_repo, sys.argv[1:], started=_started, budget=_budget)
            try:
                for _root in (_repo / "infrastructure", _repo / "scripts"):
                    _scope["verify_executed_source_code"](_root, Path(sys.pycache_prefix))
            except (OSError, ValueError) as _error:
                print(
                    f"Prepared dispatcher source custody changed after original exit {_result}: {_error}",
                    file=sys.stderr,
                )
                if _result in {0, 75}:
                    _result = 75
            if _result != 130 and time.monotonic() >= _started + _budget:
                _result = 124
        raise SystemExit(_result)
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except TimeoutError as _error:
        print(f"TIMED OUT: {_error}", file=sys.stderr)
        raise SystemExit(124) from None
    except ImportError as _error:
        print(
            f"BLOCKED: prepared runtime dependency unavailable: {_error}; run uv sync --locked explicitly.",
            file=sys.stderr,
        )
        raise SystemExit(75) from None
    except RuntimeError as _error:
        # The known preparation exception alone represents unavailable requirements.
        if "PreparedRuntimeUnavailable" in globals() and isinstance(_error, PreparedRuntimeUnavailable):
            print(f"BLOCKED: {_error}; run uv sync --locked explicitly.", file=sys.stderr)
            raise SystemExit(75) from None
        print(f"Prepared dispatch failed: {_error}", file=sys.stderr)
        raise SystemExit(1) from None
    except (OSError, ValueError) as _error:
        print(f"Prepared dispatch refused: {_error}", file=sys.stderr)
        raise SystemExit(1) from None
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
