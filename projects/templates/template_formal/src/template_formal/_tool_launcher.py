"""Optional platform-audited startup for the canonical Formal tool command.

The mathematical/domain package remains standalone. This tool-only adapter
requires the declared platform extra and reuses its mature execution custody.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
import time
from pathlib import Path


def _arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--acquire", action="store_true")
    parser.add_argument("--receipt", type=Path)
    arguments = parser.parse_args(argv)
    arguments.receipt_promoted = False
    if not math.isfinite(arguments.timeout) or not 0 < arguments.timeout <= 600:
        parser.error("formal tool timeout must be finite, positive and at most600 seconds")
    arguments.project_root = arguments.project_root.absolute()
    if arguments.receipt is not None:
        arguments.receipt = arguments.receipt.absolute()
        if arguments.receipt.is_relative_to(arguments.project_root) and not arguments.receipt.is_relative_to(
            arguments.project_root / "output"
        ):
            parser.error("tool receipts cannot overwrite admitted project sources")
    return arguments


def worker_main(prefix: Path, deadline: float, pending: Path) -> int:
    """Publish a tool receipt only after actual pre-import code verification."""
    from importlib.metadata import version

    from infrastructure.core.implementation_custody import verify_fresh_module_bytecode
    from infrastructure.core.files.secure_write import atomic_write_text_confined
    from template_formal.tool_acceptance import run_formal_tools

    arguments = _arguments()
    import infrastructure

    platform = Path(infrastructure.__file__).absolute().parent
    project_source = Path(__file__).absolute().parents[1]
    try:
        verify_fresh_module_bytecode(platform, prefix)
        verify_fresh_module_bytecode(project_source, prefix)
    except (OSError, ValueError) as error:
        print(f"Formal tool startup custody refused: {error}", file=sys.stderr)
        return 75
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return 124
    try:
        receipt = run_formal_tools(arguments.project_root, timeout=remaining, acquire=arguments.acquire)
    except TimeoutError as error:
        print(f"Formal tool total deadline exhausted: {error}", file=sys.stderr)
        return 124
    except (OSError, ValueError) as error:
        print(f"Invalid Formal tool declarations: {error}", file=sys.stderr)
        return 2
    try:
        verify_fresh_module_bytecode(platform, prefix)
        verify_fresh_module_bytecode(project_source, prefix)
    except (OSError, ValueError) as error:
        print(f"Formal tool final custody refused: {error}", file=sys.stderr)
        return 75
    if time.monotonic() >= deadline:
        return 124
    receipt["tool_launcher"] = {
        "execution_binding": "preimport-audited-fresh-prefix",
        "controller_execution_binding": "fresh-prefix",
        "platform_version": version("research-project-template"),
    }
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    atomic_write_text_confined(pending.parent, pending, text, mode=0o600)
    print(text, end="")
    if time.monotonic() >= deadline:
        pending.unlink(missing_ok=True)
        return 124
    return {"passed": 0, "failed": 1, "blocked": 75, "timed_out": 124}[str(receipt["status"])]


def _discard_promoted_receipt(arguments: argparse.Namespace) -> None:
    """Invalidate only an artifact actually promoted by this invocation."""
    if not arguments.receipt_promoted:
        return
    from infrastructure.core.files.secure_write import unlink_confined

    try:
        unlink_confined(Path(arguments.receipt.anchor), arguments.receipt)
    except FileNotFoundError:
        pass
    except (OSError, ValueError) as error:
        print(f"Expired Formal receipt cleanup refused: {error}", file=sys.stderr)
    arguments.receipt_promoted = False


def _launch(arguments: argparse.Namespace, deadline: float) -> int:
    """Reuse the platform supervisor and retain its final custody/exit result."""
    project_source = Path(__file__).absolute().parents[1]
    with tempfile.TemporaryDirectory(prefix="template-formal-launcher-") as directory:
        scratch = Path(directory).resolve()
        controller_prefix = scratch / "controller-bytecode"
        controller_prefix.mkdir(mode=0o700)
        # Under the platform's executed-bytecode audit the interpreter already
        # runs with a fresh audited private prefix; replacing it would place
        # later public caches outside the audited prefix.
        if getattr(sys, "_template_executed_bytecode_audit", None) is None:
            sys.pycache_prefix = str(controller_prefix)
            sys.dont_write_bytecode = False
        try:
            from importlib.metadata import PackageNotFoundError, version

            from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess
            from infrastructure.core.implementation_custody import bytecode_audit_bootstrap
            from infrastructure.core.files.secure_write import (
                atomic_write_text_confined,
                read_text_confined,
                unlink_confined,
            )
            import infrastructure
        except ImportError as error:
            print(f"Formal tool launcher blocked: install the formal-tools extra ({error})", file=sys.stderr)
            return 75
        try:
            platform_version = version("research-project-template")
        except PackageNotFoundError:
            platform_version = ""
        if platform_version != "4.1.0":
            print("Formal tool launcher blocked: exact platform4.1.0 is required", file=sys.stderr)
            return 75
        if arguments.receipt is not None:
            try:
                unlink_confined(Path(arguments.receipt.anchor), arguments.receipt)
            except FileNotFoundError:
                pass
            except (OSError, ValueError) as error:
                print(f"Invalid Formal receipt destination: {error}", file=sys.stderr)
                return 2
        prefix = scratch / "worker-bytecode"
        prefix.mkdir(mode=0o700)
        pending = scratch / "pending.json"
        platform = Path(infrastructure.__file__).resolve(strict=True).parent
        bootstrap = bytecode_audit_bootstrap((platform, project_source), prefix)
        # The isolated child uses the actual provider already selected above.
        # Inferring a checkout would contradict this provider's audit roots.
        bootstrap += f"sys.path.insert(0,{str(platform.parent)!r})\n"
        bootstrap += (
            f"sys.path.insert(0,{str(project_source)!r})\n"
            "from pathlib import Path\nfrom template_formal._tool_launcher import worker_main\n"
            f"raise SystemExit(worker_main(Path({str(prefix)!r}),{deadline!r},Path({str(pending)!r})))\n"
        )
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return 124
        selected_arguments = ["--project-root", str(arguments.project_root), "--timeout", str(arguments.timeout)]
        if arguments.acquire:
            selected_arguments.append("--acquire")
        result = run_bounded_subprocess(
            [sys.executable, "-I", "-X", f"pycache_prefix={prefix}", "-c", bootstrap, *selected_arguments],
            cwd=arguments.project_root,
            env=build_bounded_env(),
            timeout=remaining,
        )
        if not result.custody_refused and not result.timed_out and time.monotonic() < deadline:
            print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
        if (
            arguments.receipt is not None
            and not result.custody_refused
            and not result.timed_out
            and time.monotonic() < deadline
        ):
            try:
                text = read_text_confined(scratch, pending)
                recorded = json.loads(text)
                code = {"passed": 0, "failed": 1, "blocked": 75, "timed_out": 124}.get(recorded.get("status"))
                if code != result.returncode:
                    raise ValueError("tool receipt differs from supervised worker exit")
                atomic_write_text_confined(Path(arguments.receipt.anchor), arguments.receipt, text, mode=0o600)
                arguments.receipt_promoted = True
            except FileNotFoundError:
                if result.returncode == 0:
                    return 1
            except (OSError, ValueError, AttributeError) as error:
                print(f"Formal receipt promotion refused: {error}", file=sys.stderr)
                return 1
        if time.monotonic() >= deadline and result.returncode not in {130, 124}:
            _discard_promoted_receipt(arguments)
            return 124
        return result.returncode


def main(argv: list[str] | None = None) -> int:
    """Classify the finite program budget after private cache cleanup too."""
    arguments = _arguments(argv)
    deadline = time.monotonic() + arguments.timeout
    code = _launch(arguments, deadline)
    if time.monotonic() >= deadline and code not in {130, 124}:
        _discard_promoted_receipt(arguments)
        return 124
    return code


if __name__ == "__main__":
    raise SystemExit(main())
