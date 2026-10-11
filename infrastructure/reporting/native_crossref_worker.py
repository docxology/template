"""Actual Source-audited Pandoc filter child; stdout contains only filter JSON."""

from __future__ import annotations

import argparse
import json
import os
import platform
import select
import socket
import sys
from pathlib import Path
from typing import Any

from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_crossref_filter import BLOCKERS, SCHEMA
from infrastructure.reporting.native_crossref_protocol import (
    peer_pid,
    process_birth,
    receive,
    send,
)
from infrastructure.reporting.native_format_acceptance_contracts import (
    native_deadline_guard,
    native_environment,
)
from infrastructure.reporting.native_pdf_citation_runtime import (
    CitationRuntime,
    file_observation,
)
from infrastructure.reporting.native_source_external_admission import (
    admit_explicitly_bound_native_source,
)
from infrastructure.reporting.native_tool_process import MAX_STREAM_BYTES
from infrastructure.reporting.native_tool_producer import native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def filter_json(raw: bytes) -> dict[str, Any]:
    """Pandoc AST admission is structural only; it grants no semantic truth."""
    if not 0 < len(raw) <= MAX_STREAM_BYTES:
        raise ValueError("crossref filter JSON exceeds the existing native stream bound")

    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        value = {}
        for key, item in rows:
            if key in value:
                raise ValueError("crossref filter JSON repeats a field")
            value[key] = item
        return value

    value = json.loads(raw, object_pairs_hook=pairs)
    if (
        not isinstance(value, dict)
        or set(value) != {"pandoc-api-version", "meta", "blocks"}
        or (
            not isinstance(value["pandoc-api-version"], list)
            or not value["pandoc-api-version"]
            or any(type(number) is not int or number < 0 for number in value["pandoc-api-version"])
            or not isinstance(value["meta"], dict)
            or not isinstance(value["blocks"], list)
        )
    ):
        raise ValueError("crossref filter requires one complete actual Pandoc JSON document")
    return value


def read_filter_stdin(deadline: float) -> bytes:
    raw = bytearray()
    while True:
        if not select.select([0], [], [], remaining(deadline))[0]:
            raise TimeoutError("crossref filter stdin exhausted its original Pandoc operation clock")
        chunk = os.read(0, 65536)
        if not chunk:
            break
        raw.extend(chunk)
        if len(raw) > MAX_STREAM_BYTES:
            raise ValueError("crossref filter stdin exceeds the existing native stream ceiling")
    filter_json(bytes(raw))
    return bytes(raw)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--specification", required=True)
    parser.add_argument("--specification-sha256", required=True)
    parser.add_argument("--implementation-sha256", required=True)
    parser.add_argument("--deadline", type=float, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    import infrastructure

    with native_deadline_guard(args.deadline):
        root = args.root.resolve(strict=True)
        reader = SnapshotReader(root)
        declaration = reader.read(args.specification)
        spec = declaration.json_object()
        if (
            declaration.sha256 != args.specification_sha256
            or spec.get("schema_version") != SCHEMA
            or (
                spec.get("run_id") != args.run_id
                or spec.get("deadline_monotonic") != args.deadline
                or spec.get("expected_exit") != 0
            )
        ):
            raise ValueError("crossref child differs from the genuine parent's original Source/role/clock nomination")
        implementation = reader.read(spec["implementation"]["path"])
        if (
            implementation.sha256 != args.implementation_sha256
            or implementation.sha256 != spec["implementation"]["sha256"]
        ):
            raise ValueError("crossref actual SDK differs from the parent's exact prelaunch implementation")
        if infrastructure.__file__ is None:
            raise ValueError("crossref child actual loaded SDK origin is unavailable")
        held = root.stat()
        source = admit_explicitly_bound_native_source(
            root,
            environment=dict(os.environ),
            current_root_identity=(held.st_dev, held.st_ino),
            selected_sdk_package_root=Path(infrastructure.__file__).absolute().parent,
            expected_implementation_bytes=implementation.content,
            run_id=args.run_id,
            deadline=args.deadline,
            fresh_pycache_prefix=Path(sys.pycache_prefix) if sys.pycache_prefix else None,
        )
        if source is None or json.loads(source.descriptor(spec["scope"], deadline=args.deadline)) != spec["source"]:
            raise ValueError("crossref child requires fresh genuine Source/SDK/current-mirror correspondence")
        directory = root / spec["directory"]
        if declaration.path != directory / "specification.json":
            raise ValueError("crossref child specification belongs to another original attempt")
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(remaining(args.deadline))
            connection.connect(spec["socket_address"])
            if peer_pid(connection, deadline=args.deadline) != spec["parent_owner_pid"]:
                raise ValueError("crossref child side channel differs from the actual originating Source owner")
            send(
                connection,
                {"phase": "ready", "specification_sha256": declaration.sha256},
                deadline=args.deadline,
            )
            admission = receive(connection, deadline=args.deadline)
            child = process_birth(os.getpid(), deadline=args.deadline)
            parent = process_birth(os.getppid(), deadline=args.deadline)
            if admission != {"phase": "admitted", "parent": parent, "child": child}:
                raise ValueError("crossref child actual kernel birth/parent differs from live Pandoc admission")
            raw = read_filter_stdin(args.deadline)
            env = native_environment(root, Path(sys.executable), directory)
            selected = Path(spec["crossref"]["path"])
            env["PATH"] = str(selected.parent) + os.pathsep + env.get("PATH", "")
            if file_observation(selected) != spec["crossref"]:
                raise ValueError("crossref actual executable differs from the independently nominated original body")
            with native_producer_operation(source, run_id=args.run_id, deadline=args.deadline) as owner:
                live_reader = SnapshotReader(root, native_producer_operation=owner)
                runtime = CitationRuntime(
                    root,
                    directory / "crossref-native",
                    env=env,
                    deadline=args.deadline,
                    run_id=args.run_id,
                )
                stdin = runtime.freeze("pandoc-input.json", raw)
                qualifications = None
                compiler_tools = []
                if platform.system() == "Linux":
                    from infrastructure.reporting.native_loader_qualification import qualify_native_loader_tool

                    if spec["official_archive"] is None:
                        raise ValueError("Source Linux Crossref lacks its official archive/body admission")
                    version, version_qualification, compiled = qualify_native_loader_tool(
                        runtime,
                        "pandoc-crossref",
                        ["--version"],
                        "crossref-filter-version",
                    )
                    _, json_qualification, _ = qualify_native_loader_tool(
                        runtime,
                        "pandoc-crossref",
                        [spec["output_format"]],
                        "crossref-filter-json",
                        stdin_path=stdin,
                        compiled=compiled,
                    )
                    compiler_record = live_reader.read(compiled.binding["path"]).json_object()
                    compiler_tools = [compiler_record["compiler_header_selection"], compiler_record["compiler"]]
                    qualifications = [version_qualification, json_qualification]
                else:
                    version = runtime.tool("pandoc-crossref", ["--version"], "crossref-filter-version")
                    runtime.tool("pandoc-crossref", [spec["output_format"]], "crossref-filter-json", stdin_path=stdin)
                output = runtime.read(runtime.directory / "crossref-filter-json.stdout.bin")
                before, after = filter_json(raw), filter_json(output)
                if before["pandoc-api-version"] != after["pandoc-api-version"]:
                    raise ValueError("actual crossref binary changed the declared Pandoc JSON API identity")
                output_path = runtime.freeze("pandoc-output.json", output)
                result = {
                    "schema_version": SCHEMA,
                    "run_id": args.run_id,
                    "specification_sha256": declaration.sha256,
                    "parent": parent,
                    "child": child,
                    "input": {
                        "path": stdin.relative_to(root).as_posix(),
                        "sha256": live_reader.read(stdin.relative_to(root).as_posix()).sha256,
                    },
                    "output": {
                        "path": output_path.relative_to(root).as_posix(),
                        "sha256": live_reader.read(output_path.relative_to(root).as_posix()).sha256,
                    },
                    "tool_artifacts": [*compiler_tools, *runtime.tools],
                    "official_archive": spec["official_archive"],
                    "loader_qualifications": qualifications,
                    "source_exit_intent": 0,
                    "version": version["stdout"],
                    "output_format": spec["output_format"],
                    "blockers": [] if qualifications is not None else list(BLOCKERS),
                }
                observation = write_json(root, directory / "filter-observation.json", result)
                owner.verify(live_reader, run_id=args.run_id, deadline=args.deadline)
                source.verify_correspondence(source.reference, root, live_reader, args.deadline)
                if (
                    process_birth(os.getpid(), deadline=args.deadline) != child
                    or process_birth(os.getppid(), deadline=args.deadline) != parent
                ):
                    raise ValueError("actual crossref child/parent birth changed before final original output seal")
                send(
                    connection,
                    {
                        "phase": "sealed",
                        "specification_sha256": declaration.sha256,
                        "observation": observation,
                        "source_exit_intent": 0,
                    },
                    deadline=args.deadline,
                )
                if receive(connection, deadline=args.deadline) != {"phase": "release"}:
                    raise ValueError("crossref output release lacked the actual originating Source owner")
                sys.stdout.buffer.write(output)
                sys.stdout.buffer.flush()
                remaining(args.deadline)
                return 0


if __name__ == "__main__":
    raise SystemExit(main())
