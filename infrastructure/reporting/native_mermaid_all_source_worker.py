"""Thin installed-SDK entry point for the original complete28 Source component."""

from __future__ import annotations

import argparse
import hashlib
import math
import os
import re
import sys
import time
from pathlib import Path

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.reporting.native_format_acceptance_contracts import (
    native_deadline_guard,
    native_environment,
)
from infrastructure.reporting.native_format_joint_source import (
    NativeSDKSelection,
    admit_native_source_operation,
)
from infrastructure.reporting.native_mermaid_batch_all_sources import (
    SOURCE_PHASE_SECONDS,
    _storage,
    observe_all_current_mermaid_batch_sources,
)
from infrastructure.reporting.native_mermaid_runtime_selection import (
    NativeMermaidSelection,
)
from infrastructure.reporting.native_tool_producer import native_producer_operation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "sdk-package-root", "implementation-custody", "directory"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--implementation-sha256", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--deadline-monotonic", type=float, required=True)
    parser.add_argument("--expected-census-digest")
    for prefix in ("original", "reader"):
        for member in (
            "package-root",
            "dependency-root",
            "node-executable",
            "chrome-executable",
        ):
            parser.add_argument(f"--{prefix}-mermaid-{member}-path", type=Path, required=True)
        parser.add_argument(f"--{prefix}-font-path", type=Path, action="append", required=True)
    args = parser.parse_args(argv)
    if getattr(sys, "_template_executed_bytecode_audit", None) is None:
        raise ValueError("complete28 component requires its genuine preimport selected-SDK execution audit")
    deadline = args.deadline_monotonic
    if not math.isfinite(deadline) or not 0 < deadline - time.monotonic() <= SOURCE_PHASE_SECONDS:
        raise ValueError(
            "complete28 component requires the original externally supplied remaining60-second phase clock"
        )
    if re.fullmatch(r"[0-9a-f]{32}", args.run_id) is None:
        raise ValueError("complete28 Source component requires its genuine fresh original run identity")
    implementation = read_bytes_confined(
        args.implementation_custody.parent,
        args.implementation_custody,
        max_bytes=64 * 1024 * 1024,
    )
    if hashlib.sha256(implementation).hexdigest() != args.implementation_sha256:
        raise ValueError("complete28 independently nominated selected-SDK custody bytes changed")
    original = NativeMermaidSelection(
        args.original_mermaid_package_root_path,
        args.original_mermaid_dependency_root_path,
        args.original_mermaid_node_executable_path,
        args.original_mermaid_chrome_executable_path,
    )
    reader = NativeMermaidSelection(
        args.reader_mermaid_package_root_path,
        args.reader_mermaid_dependency_root_path,
        args.reader_mermaid_node_executable_path,
        args.reader_mermaid_chrome_executable_path,
    )
    with native_deadline_guard(deadline):
        source = admit_native_source_operation(
            args.root,
            NativeSDKSelection(args.sdk_package_root, implementation),
            run_id=args.run_id,
            deadline=deadline,
            environment=os.environ,
        )
        env = native_environment(args.root, Path(sys.executable), args.directory)
        with native_producer_operation(source, run_id=args.run_id, deadline=deadline):
            observed = observe_all_current_mermaid_batch_sources(
                source,
                args.directory,
                original_selection=original,
                reader_selection=reader,
                font_files=tuple(args.original_font_path),
                reader_font_files=tuple(args.reader_font_path),
                env=env,
                deadline=deadline,
                expected_census_digest=args.expected_census_digest,
            )
            write_json(
                args.root,
                args.directory / "all-original-source-and-reader.json",
                observed,
            )
            _storage(args.directory, deadline)
    # The bootstrap retains the genuine executed-Code closure before original
    # exit. This zero is a component result and cannot replace any full gate.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
