"""Canonical audited auxiliary launches and independent portable DATA readback."""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.project.acceptance_payload import (
    format_acceptance_payload_loader,
    validate_acceptance_payload,
    write_acceptance_payload,
)
from infrastructure.project.public_acceptance_evidence import bootstrap_command
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

WORKER = "infrastructure.project.public_acceptance_auxiliary_worker"
PIPELINE = "infrastructure.project.public_acceptance_auxiliary_pipeline"
PAYLOAD = "audited-bootstrap.payload"


def _body(
    interpreter: Path,
    root: Path,
    module: str,
    arguments: tuple[str, ...],
    directory: Path,
    *,
    original_root: Path,
    print_nomination: dict[str, Any] | None = None,
) -> tuple[bytes, tuple[str, ...]]:
    if module not in {WORKER, PIPELINE}:
        raise ValueError("auxiliary bootstrap requires its exact source-owned entry module")
    command = bootstrap_command(
        interpreter,
        root,
        module,
        *arguments,
        command_root=original_root,
        implementation_root=original_root / "infrastructure",
        fresh_pycache_prefix=directory / "bytecode",
    )
    body = command[3]
    if print_nomination is not None:
        if (
            module != WORKER
            or set(print_nomination)
            != {"spec_path", "spec_sha256", "run_id", "deadline", "parent_pid", "producer_root"}
            or print_nomination["producer_root"] != str(original_root)
            or Path(print_nomination["spec_path"]).parent / "execution" != directory
        ):
            raise ValueError("auxiliary print custody only belongs to the fixed worker")
        # Portable process JSON sorts keys. Payload Source must not depend on
        # a caller dictionary's insertion order before that round trip.
        print_nomination = {key: print_nomination[key] for key in sorted(print_nomination)}
        original = " runpy.run_module(sys.argv.pop(1),run_name='__main__')\n"
        replacement = (
            " from infrastructure.project.auxiliary_print_code import audited_entry,retain_code\n"
            f" with audited_entry(Path({str(original_root)!r}),{print_nomination!r},"
            f"Path({str(directory / PAYLOAD)!r})):\n"
            "  _print_outcome={'kind':'not_started'}\n"
            "  try:\n"
            "   runpy.run_module(sys.argv.pop(1),run_name='__main__')\n"
            "   _print_outcome={'kind':'returned'}\n"
            "  except BaseException as _print_error:\n"
            "   _print_outcome=({'kind':'raised','system_exit_code':_print_error.code} "
            "if isinstance(_print_error,SystemExit) else {'kind':'failed','class':type(_print_error).__name__})\n"
            "   raise\n"
            "  finally:\n"
            "   try:\n"
            f"    retain_code(Path({str(original_root)!r}),Path({str(directory / 'print-code')!r}),"
            f"{print_nomination!r},_print_outcome)\n"
            "   except BaseException as _print_retention_error:\n"
            "    sys.stderr.write('actual auxiliary print Code retention refused: '"
            "+type(_print_retention_error).__name__+'\\n')\n"
            "    if _print_outcome in ({'kind':'returned'},{'kind':'raised','system_exit_code':0}): raise\n"
        )
        if body.count(original) != 1:
            raise ValueError("auxiliary print fixed bootstrap entry changed")
        body = body.replace(original, replacement)
    return body.encode(), command[4:]


def prepare_audited_auxiliary_command(
    interpreter: Path, root: Path, module: str, arguments: tuple[str, ...], directory: Path
) -> tuple[list[str], dict[str, Any]]:
    """Create a private empty prefix and exact readonly payload before Popen."""
    if directory.is_symlink() or directory.exists() and directory.resolve(strict=True) != directory:
        raise ValueError("auxiliary bootstrap directory is aliased")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    metadata = directory.lstat()
    if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) != 0o700:
        raise ValueError("auxiliary bootstrap directory must be privately owned")
    prefix = directory / "bytecode"
    prefix.mkdir(mode=0o700)  # Existing/aliased caches are never reused.
    selected_hook = Path(__file__).absolute().parents[1] / "core/bytecode_audit.py"
    if read_bytes_confined(root, root / "infrastructure/core/bytecode_audit.py") != read_bytes_confined(
        selected_hook.parent, selected_hook
    ):
        raise ValueError("auxiliary preimport audit hook differs from the nominated Source body")
    from infrastructure.project.auxiliary_print_code import nomination

    held = nomination(root, arguments) if module == WORKER else None
    body, tail = _body(interpreter, root, module, arguments, directory, original_root=root, print_nomination=held)
    forbidden = tuple(
        root / name for name in ("infrastructure", "scripts", "tests", "projects") if (root / name).exists()
    )
    payload = write_acceptance_payload(directory, directory / PAYLOAD, body, forbidden_roots=forbidden)
    return [str(interpreter), "-IB", "-c", format_acceptance_payload_loader(payload), *tail], payload


def validate_audited_auxiliary_command(
    reader: SnapshotReader,
    process: dict[str, Any],
    *,
    module: str,
    arguments: tuple[str, ...],
    execution_relative: str,
    retained_payload: dict[str, str] | None = None,
) -> None:
    """Regenerate Source hook/finder/roots/arguments; never reopen Original paths."""
    original = Path(process["producer_root"])
    directory = original / execution_relative
    interpreter = Path(process["selected_interpreter"])
    body, tail = _body(
        interpreter,
        reader.root,
        module,
        arguments,
        directory,
        original_root=original,
        print_nomination=process.get("auxiliary_print_launch"),
    )
    payload = validate_acceptance_payload(body, process.get("bootstrap_payload"), expected_path=directory / PAYLOAD)
    if retained_payload is None:
        observed = reader.read(execution_relative + "/" + PAYLOAD)
    else:
        observed = reader.read(retained_payload["path"])
        if observed.sha256 != retained_payload["sha256"]:
            raise ValueError("retained auxiliary bootstrap artifact changed")
    if observed.content != body:
        raise ValueError("auxiliary bootstrap differs from exact current Source hook/template/roots")
    expected = [str(interpreter), "-IB", "-c", format_acceptance_payload_loader(payload), *tail]
    if process.get("command") != expected:
        raise ValueError("auxiliary command differs from its exact Source-derived audited bootstrap")
