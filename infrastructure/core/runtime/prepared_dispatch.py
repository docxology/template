"""Finite prepared-runtime dispatch through the existing process guardian."""

from __future__ import annotations

import math
import os
import sys
import tempfile
import time
from pathlib import Path

from infrastructure.core.bytecode_audit import verify_executed_source_code
from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess
from infrastructure.core.implementation_custody import bytecode_audit_bootstrap
from infrastructure.core.runtime.prepared_runtime import PreparedRuntimeUnavailable, check_prepared_root_runtime


def dispatch_prepared_cli(repo: Path, arguments: list[str], *, started: float, budget: float) -> int:
    """Use existing packages and preserve observed child/interruption outcomes."""
    try:
        if not math.isfinite(budget) or budget <= 0:
            raise ValueError("Prepared dispatch budget must be positive and finite")
        secure = bool(arguments and arguments[0] == "secure") and not any(
            argument in {"--help", "-h", "--validate-kmyth"} for argument in arguments
        )
        check_prepared_root_runtime(repo, secure=secure)
        remaining = started + budget - time.monotonic()
        if remaining <= 0:
            return 124
        with tempfile.TemporaryDirectory(prefix="template-prepared-worker-") as temporary:
            prefix = Path(temporary).resolve() / "bytecode"
            prefix.mkdir(mode=0o700)
            bootstrap = bytecode_audit_bootstrap((repo / "infrastructure", repo / "scripts"), prefix) + (
                "import sys;sys.path.insert(0,sys.argv.pop(1));"
                "from infrastructure.core.runtime.prepared_dispatch import worker_main;"
                "raise SystemExit(worker_main())"
            )
            remaining = started + budget - time.monotonic()
            if remaining <= 0:
                return 124
            selected_env = build_bounded_env(dict(os.environ))
            # The admission clock belongs to this outer supervisor, not the
            # scientific child's environment/cache identity.
            selected_env.pop("TEMPLATE_PREPARED_DISPATCH_STARTED", None)
            selected_env.pop("TEMPLATE_PREPARED_STARTUP_DEADLINE", None)
            child = run_bounded_subprocess(
                [sys.executable, "-I", "-X", f"pycache_prefix={prefix}", "-c", bootstrap, str(repo), *arguments],
                cwd=repo,
                env=selected_env,
                timeout=remaining,
                capture_output=False,
            )
        if child.original_returncode in {130, -2} or child.returncode in {130, -2}:
            return 130
        if child.timed_out or child.returncode == 124 or time.monotonic() >= started + budget:
            return 124
        if child.custody_refused:
            print(f"Prepared CLI custody refusal: {child.command_error}", file=sys.stderr)
            original = child.original_returncode
            return original if original is not None and original > 0 and original != 75 else 75
        return child.returncode if child.returncode >= 0 else 1
    except PreparedRuntimeUnavailable as exc:
        print(
            f"BLOCKED: {exc}. Prepare dependencies explicitly with uv sync --locked before execution.", file=sys.stderr
        )
        return 75


def worker_main() -> int:
    """Invoke the real CLI and recheck every admitted root after cleanup."""
    from infrastructure.orchestration.cli import main

    repo = Path(__file__).absolute().parents[3]
    try:
        original = main()
    except SystemExit as exc:
        original = 0 if exc.code is None else (exc.code if type(exc.code) is int else 1)
    except KeyboardInterrupt:
        original = 130
    try:
        assert sys.pycache_prefix is not None
        for root in (repo / "infrastructure", repo / "scripts"):
            verify_executed_source_code(root, Path(sys.pycache_prefix))
    except (OSError, ValueError) as exc:
        print(f"Prepared CLI source custody changed after original exit {original}: {exc}", file=sys.stderr)
        return original if original not in {0, 75} else 75
    return original


__all__ = ["dispatch_prepared_cli", "worker_main"]
