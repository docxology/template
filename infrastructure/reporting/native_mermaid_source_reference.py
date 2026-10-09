"""Actual source-only Mermaid producer, independent SVG paint, portable replay.

The root/source occurrence census and SDK/process admission are explicit caller
obligations. This module never executes SourceDATA project helpers, accepts a
candidate's image as source authority, or promotes whole-document coverage.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import shutil
from pathlib import Path
from typing import Any, Callable

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_pdf_mermaid_source import compile_original_mermaid_source
from infrastructure.reporting.native_format_pdf_source_decode_bounds import SourceImageDecodeBudget
from infrastructure.reporting.native_mermaid_runtime_custody import (
    admit_reader_mermaid_runtime,
    admit_reader_platform_fonts,
    observe_mermaid_runtime,
    validate_mermaid_runtime,
    validate_platform_font_files,
)
from infrastructure.reporting.native_mermaid_svg_paint import (
    inspect_original_svg_native_pixels,
    observe_original_svg_paint,
    preflight_original_mermaid_svg,
    validate_original_svg_paint,
)
from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime
from infrastructure.reporting.native_citation_process_custody import OriginalCitationToolObserver
from infrastructure.reporting.native_format_acceptance_contracts import CITATION_TOOL_FIELDS, TOOL_FIELDS, TOOL_SCHEMA
from infrastructure.reporting.release_readiness_snapshot import json_object_from_bytes
from infrastructure.rendering._pdf_mermaid import _normalise_mermaid_source
from infrastructure.rendering._mermaid_native_profile import (
    adapter_bytes,
    adapter_filename,
    adapter_sha256,
    policy,
    rendering_profile,
    request_bytes,
    validate_rendering_profile,
)
from infrastructure.reporting.native_mermaid_runtime_selection import NativeMermaidRuntimeAdmission

SCHEMA = "template-native-mermaid-original-source-reference-source11-runtime-v3"
TopologyInspector = Callable[[bytes, bytes], dict[str, Any]]
ArtifactReader = Callable[[dict[str, Any]], bytes]
ProcessAdmitter = Callable[[dict[str, Any]], None]


DISPLAY_POLICY = "template-native-mermaid-current-sdk-label-punctuation-display-v1"
REMAINING_ADMISSION = (
    "enclosing frozen SourceDATA/hydration and SDK/original process admission",
    "original Node/Chrome loaded operating-system library custody",
    "independent unclipped source glyph/stroke/marker ink and SVG clip/mask/filter semantics",
    "native occurrence position/visibility and complete source-authenticated document page admission",
)


def independent_mermaid_display_graph(source: bytes) -> dict[str, Any]:
    """Retain raw labels and independently derive the current SDK's display.

    State descriptions/transitions replace prose colons with ' -' and semicolons
    with commas; sequence message labels replace semicolons with commas. These
    finite display rules are explicit, not inferred from writer output. Raw
    source identities/labels are preserved separately. Unrecognised escaping or
    other SDK transformations still fail the exact graph comparison below.
    """
    graph = copy.deepcopy(compile_original_mermaid_source(source))
    if graph["family"] == "stateDiagram-v2":
        for row in [*graph["nodes"], *graph["edges"]]:
            row["label"] = row["label"].replace(":", " -").replace(";", ",")
    elif graph["family"] == "sequenceDiagram":
        for row in graph["edges"]:
            row["label"] = row["label"].replace(";", ",")
    return graph


def _normal(source: bytes) -> bytes:
    expected = independent_mermaid_display_graph(source)
    normal = _normalise_mermaid_source(source.decode("utf-8").strip()).encode("utf-8")
    normalized = compile_original_mermaid_source(normal)
    for key in ("family", "direction", "nodes", "edges", "class_styles"):
        if expected[key] != normalized[key]:
            raise ValueError(
                "original SDK normalization changes independently interpreted Mermaid source/display semantics"
            )
    return normal


def _binding(root: Path, path: Path, data: bytes) -> dict[str, Any]:
    return {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def _read(binding: dict[str, Any], reader: ArtifactReader) -> bytes:
    if (
        set(binding) != {"path", "sha256", "bytes"}
        or type(binding["bytes"]) is not int
        or not 0 <= binding["bytes"] <= 64 * 1024 * 1024
    ):
        raise ValueError("portable original Mermaid artifact binding is invalid/unbounded")
    data = reader(binding)
    if len(data) != binding["bytes"] or hashlib.sha256(data).hexdigest() != binding["sha256"]:
        raise ValueError("portable original Mermaid consumed artifact bytes differ")
    return data


def _topology(source: bytes, svg: bytes, inspector: TopologyInspector) -> dict[str, Any]:
    preflight_original_mermaid_svg(svg)
    result = inspector(source, svg)
    if result.get("schema_version") != "template-native-mermaid-independent-svg-topology-v1" or result.get(
        "source_graph"
    ) != compile_original_mermaid_source(source):
        raise ValueError("independent Mermaid SVG interpretation omits original exact source graph")
    return result


def _process_clock(process: dict[str, Any], name: str) -> float:
    value = process.get(name)
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError("portable original Mermaid omits actual parent process clock observations")
    return float(value)


def _runtime_version(runtime: dict[str, Any]) -> str:
    version = runtime["package"]["version"] if "package" in runtime else runtime["version"]
    if version not in {"11.16.0", "12.0.0"}:
        raise ValueError("original Mermaid runtime lacks its exact Source-owned finite profile")
    return str(version)


def _source11_live_node_reports(process: dict[str, Any]) -> None:
    stdout = process.get("stdout")
    if not isinstance(stdout, str) or len(stdout.encode("utf-8")) > 8 * 1024 * 1024:
        raise ValueError("Source11 original Node stdout is absent/unbounded")
    lines = stdout.splitlines()
    if len(lines) != 2:
        raise ValueError("Source11 original Node lacks both actual live loaded-library API observations")
    expected_fields = {
        "schema_version",
        "api",
        "phase",
        "pid",
        "owner_pid",
        "node_version",
        "platform",
        "architecture",
        "shared_objects",
        "loaded_library_bodies",
        "remaining_admission",
    }
    earlier: dict[str, dict[str, Any]] = {}
    for phase, line in zip(("before-import", "after-run"), lines, strict=True):
        report = json_object_from_bytes(line.encode("utf-8"))
        if (
            set(report) != expected_fields
            or report.get("schema_version") != "template-native-source11-node-live-loaded-report-v1"
            or report.get("api") != "process.report.getReport"
            or report.get("phase") != phase
            or type(report.get("pid")) is not int
            or report["pid"] != process["pid"]
            or type(report.get("owner_pid")) is not int
            or report["owner_pid"] != process["owner_pid"]
            or not isinstance(report.get("node_version"), str)
            or not re.fullmatch(r"v20\.[0-9]+\.[0-9]+", report["node_version"])
            or report.get("platform") not in {"linux", "darwin"}
            or report.get("architecture") not in {"arm64", "x64"}
            or report.get("remaining_admission")
            != ["source-required loaded library bodies and shared-cache/kernel closure"]
        ):
            raise ValueError("Source11 original Node live self/API/PID observation differs")
        libraries = report.get("shared_objects")
        if (
            not isinstance(libraries, list)
            or len(libraries) > 4096
            or any(
                not isinstance(name, str) or not Path(name).is_absolute() or len(name) > 4096 or "\0" in name
                for name in libraries
            )
        ):
            raise ValueError("Source11 original Node live loaded-library name census is absent/unbounded")
        bodies = report.get("loaded_library_bodies")
        if not isinstance(bodies, list) or len(bodies) != len(libraries):
            raise ValueError("Source11 original live loaded-library body observation census differs")
        total = 0
        for name, body in zip(libraries, bodies, strict=True):
            if not isinstance(body, dict) or body.get("path") != name:
                raise ValueError("Source11 original live loaded-library body path differs from actual loaded API")
            if body.get("status") == "observed-regular-body":
                if (
                    set(body) != {"path", "status", "bytes", "sha256", "identity_before", "identity_after"}
                    or type(body["bytes"]) is not int
                    or not 0 <= body["bytes"] <= 512 * 1024 * 1024
                    or not isinstance(body["sha256"], str)
                    or not re.fullmatch(r"[0-9a-f]{64}", body["sha256"])
                    or not isinstance(body["identity_before"], dict)
                    or set(body["identity_before"]) != {"dev", "ino", "nlink", "mode", "size", "mtimeNs", "ctimeNs"}
                    or body["identity_before"] != body["identity_after"]
                    or any(
                        not isinstance(value, str) or not re.fullmatch(r"[0-9]+", value)
                        for value in body["identity_before"].values()
                    )
                    or int(body["identity_before"]["size"]) != body["bytes"]
                ):
                    raise ValueError("Source11 original live library regular-body/physical custody differs")
                if name in earlier and earlier[name].get("status") == "observed-regular-body" and body != earlier[name]:
                    raise ValueError(
                        "Source11 actual live loaded-library body/physical identity changed during import/render"
                    )
                total += body["bytes"]
            elif body.get("status") == "unsupported-loaded-provider":
                if set(body) != {"path", "status", "reason"} or not isinstance(body["reason"], str):
                    raise ValueError("Source11 unavailable live loaded provider reason is not retained")
            else:
                raise ValueError("Source11 original live loaded-library provider status differs")
        earlier = {body["path"]: body for body in bodies}
        if total > 1024 * 1024 * 1024:
            raise ValueError("Source11 original live loaded-library observed body closure exceeds its finite bound")


def _original_process_closure(row: dict[str, Any], original_runtime: dict[str, Any]) -> None:
    version = _runtime_version(original_runtime)
    if row.get("producer_invocation_policy") != policy(version):
        raise ValueError("portable Mermaid producer lacks its admitted exact rectangular viewport API policy")
    validate_rendering_profile(version, row.get("producer_render_profile"))
    processes = row["processes"]
    if not isinstance(processes, dict) or set(processes) != {"svg", "png"}:
        raise ValueError("portable original Mermaid requires both genuine SVG/PNG process records")
    for kind, process in processes.items():
        if (
            set(process) != CITATION_TOOL_FIELDS
            or process.get("schema_version") != TOOL_SCHEMA
            or process.get("tool") != "node"
            or process.get("purpose") != f"original-mermaid-{kind}"
            or process.get("executable") != original_runtime["node_executable_label"]
            or process.get("executable_sha256") != original_runtime["node"]["sha256"]
            or type(process.get("exit_code")) is not int
            or process.get("exit_code") != 0
            or type(process.get("original_exit_code")) is not int
            or process.get("original_exit_code") != 0
            or process.get("timed_out") is not False
            or process.get("custody_refused") is not False
            or process.get("diagnostic")
            or type(process.get("pid")) is not int
            or process["pid"] <= 0
        ):
            raise ValueError("portable original Mermaid process execution/runtime closure differs")
        if version == "11.16.0":
            _source11_live_node_reports(process)
        started, duration, deadline = (
            _process_clock(process, name)
            for name in ("started_at_monotonic", "duration_seconds", "original_deadline_monotonic")
        )
        if started < 0 or duration < 0 or started + duration > deadline:
            raise ValueError("portable original Mermaid actual process exceeds its original enclosing clock")
        cwd = Path(process["cwd"])
        if not cwd.is_absolute() or ".." in cwd.parts:
            raise ValueError("portable original Mermaid process origin cwd is not confined")
        command = [
            original_runtime["node_executable_label"],
            str(cwd / adapter_filename(version)),
            str(cwd / f"mermaid-{kind}-request.json"),
        ]
        if process.get("command") != command:
            raise ValueError("portable original Mermaid source/CLI/viewport process command differs")
        before, after = process.get("input_observations_before"), process.get("input_observations_after")
        if not isinstance(before, list) or before != after:
            raise ValueError("portable original Mermaid consumed source/config changed")
        normal = next((value for value in before if value.get("path") == str(cwd / "normalized.mmd")), None)
        if normal is None or normal.get("sha256") != row["normalized_source"]["sha256"]:
            raise ValueError("portable original Mermaid process omits exact original consumed source bytes")
        for name, digest in (
            (adapter_filename(version), adapter_sha256(version)),
            (f"mermaid-{kind}-request.json", row["producer_requests"][kind]["sha256"]),
        ):
            if not any(value.get("path") == str(cwd / name) and value.get("sha256") == digest for value in before):
                raise ValueError("portable original Mermaid process omits actual SDK adapter/request input bytes")
        for phase in ("before", "after"):
            observed = process.get("executable_observation_" + phase, {})
            if observed.get("path") != command[0] or observed.get("sha256") != original_runtime["node"]["sha256"]:
                raise ValueError("portable original Mermaid executable changed before/after execution")


def observe_original_mermaid_sources(
    root: Path,
    directory: Path,
    sources: tuple[tuple[str, bytes], ...],
    *,
    package_root: Path,
    node_executable: Path,
    chrome_executable: Path,
    font_files: tuple[Path, ...],
    decoded_pixel_budget: SourceImageDecodeBudget,
    inspect_svg: TopologyInspector,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    on_original_tool: OriginalCitationToolObserver | None = None,
    runtime_admission: NativeMermaidRuntimeAdmission | None = None,
) -> dict[str, Any]:
    """Execute genuine source-only CLI and separately paint every original SVG.

    This API must be scheduled by the parent inside its original native phase.
    The selected Node must be the actual environment tool, and the whole installed
    CLI/package and Chrome bundles are held around all actual producer processes.
    """
    if not 0 < len(sources) <= 100 or len({identity for identity, _ in sources}) != len(sources):
        raise ValueError("original Mermaid occurrence census is absent/duplicate/unbounded")
    if any(not isinstance(identity, str) or not 0 < len(identity) <= 1024 for identity, _ in sources):
        raise ValueError("original Mermaid source occurrence identity is not bounded literal data")
    selected = shutil.which("node", path=env.get("PATH"))
    if selected is None or Path(selected).resolve(strict=True) != node_executable.resolve(strict=True):
        raise ValueError("selected original Node differs from actual admitted native environment")
    if env.get("NODE_OPTIONS") or env.get("NODE_PATH"):
        raise ValueError("original Mermaid profile cannot admit environment-supplied JavaScript/module overrides")
    before = observe_mermaid_runtime(
        package_root, node_executable, chrome_executable, deadline=deadline, runtime_admission=runtime_admission
    )
    version = _runtime_version(before)
    runtime_process = runtime_admission.node_version_proof() if runtime_admission is not None else None
    runtime = CitationRuntime(
        root, directory, env=env, deadline=deadline, run_id=run_id, on_original_tool=on_original_tool
    )
    rows, blockers = [], []
    for ordinal, (identity, source) in enumerate(sources):
        normal = _normal(source)
        leaf = CitationRuntime(
            root,
            directory / f"source-{ordinal:04d}",
            env=env,
            deadline=deadline,
            run_id=run_id,
            on_original_tool=on_original_tool,
        )
        raw_path = leaf.freeze("original.mmd", source)
        normal_path = leaf.freeze("normalized.mmd", normal)
        adapter = leaf.freeze(adapter_filename(version), adapter_bytes(version))
        processes, process_artifacts, artifacts, configs, requests = {}, {}, {}, {}, {}
        for kind in ("svg", "png"):
            profile = leaf.directory / f"producer-profile-{kind}"
            config_path = leaf.freeze(
                f"puppeteer-{kind}.json",
                (
                    json.dumps(
                        {
                            "executablePath": str(chrome_executable.resolve(strict=True)),
                            "userDataDir": str(profile),
                            "args": [
                                "--no-first-run",
                                "--disable-background-networking",
                                "--disable-extensions",
                                "--disable-sync",
                                "--proxy-server=http://127.0.0.1:9",
                                "--proxy-bypass-list=127.0.0.1",
                            ],
                        },
                        sort_keys=True,
                    )
                    + "\n"
                ).encode(),
            )
            configs[kind] = _binding(root, config_path, leaf.read(config_path))
            output = leaf.directory / f"original.{kind}"
            request = leaf.freeze(
                f"mermaid-{kind}-request.json",
                request_bytes(version, package_root.resolve(strict=True), normal_path, output, kind, config_path),
            )
            requests[kind] = _binding(root, request, leaf.read(request))
            process = leaf.tool(
                "node",
                [str(adapter), str(request)],
                f"original-mermaid-{kind}",
            )
            if version == "11.16.0":
                _source11_live_node_reports(process)
            data = leaf.read(output)
            artifacts[kind] = _binding(root, output, data)
            processes[kind] = process
            process_artifacts[kind] = dict(leaf.tools[-1])
            if profile.exists():
                shutil.rmtree(profile)
        svg, native_png = (
            _read(artifacts["svg"], lambda binding: leaf.read(root / binding["path"])),
            leaf.read(root / artifacts["png"]["path"]),
        )
        topology = _topology(normal, svg, inspect_svg)
        paint = observe_original_svg_paint(
            chrome_executable,
            svg,
            leaf.directory / "independent-svg-paint",
            deadline=deadline,
            font_files=font_files,
            decoded_pixel_budget=decoded_pixel_budget,
        )
        paint_path = leaf.directory / "independent-svg-paint/paint.png"
        pixel_binding = _binding(root, paint_path, paint_path.read_bytes())
        parity = inspect_original_svg_native_pixels(paint, native_png, decoded_pixel_budget=decoded_pixel_budget)
        if topology.get("status") != "pass" or topology.get("blockers") or topology.get("findings"):
            blockers.append(
                {
                    "identity": identity,
                    "reason": "independent original Mermaid SVG source/topology interpretation is incomplete",
                }
            )
        leaf.unchanged()
        rows.append(
            {
                "identity": identity,
                "source": _binding(root, raw_path, source),
                "normalized_source": _binding(root, normal_path, normal),
                "source_graph": compile_original_mermaid_source(source),
                "display_graph": independent_mermaid_display_graph(source),
                "source_display_policy": DISPLAY_POLICY,
                "artifacts": artifacts,
                "processes": processes,
                "process_artifacts": process_artifacts,
                "producer_configs": configs,
                "producer_adapter": _binding(root, adapter, leaf.read(adapter)),
                "producer_requests": requests,
                "producer_invocation_policy": policy(version),
                "producer_render_profile": rendering_profile(version),
                "topology": topology,
                "paint": paint,
                "paint_artifact": pixel_binding,
                "pixel_parity": parity,
            }
        )
    runtime.unchanged()
    after = observe_mermaid_runtime(
        package_root, node_executable, chrome_executable, deadline=deadline, runtime_admission=runtime_admission
    )
    if before != after:
        raise ValueError("complete original Mermaid/Node/Chrome runtime changed during actual source-only execution")
    result = {
        "schema_version": SCHEMA,
        "run_id": run_id,
        "runtime_before": before,
        "runtime_after": after,
        "runtime_process": runtime_process,
        "occurrences": rows,
        "blockers": blockers,
        "remaining_admission": list(REMAINING_ADMISSION),
    }
    return {**result, "content_digest": canonical_digest(result)}


def _admit_source11_version_proof(
    proof: object,
    runtime: dict[str, Any],
    artifact_reader: ArtifactReader,
    admit_original_process: ProcessAdmitter,
) -> None:
    if not isinstance(proof, dict) or set(proof) != {"artifact", "process"}:
        raise ValueError("Source11 reference lacks its actual original Node20 process proof")
    binding, process = proof["artifact"], proof["process"]
    if not isinstance(binding, dict) or set(binding) != {"path", "sha256"} or not isinstance(process, dict):
        raise ValueError("Source11 Node20 ToolAPI process binding differs")
    content = artifact_reader(binding)
    if (
        len(content) > 64 * 1024 * 1024
        or hashlib.sha256(content).hexdigest() != binding["sha256"]
        or json_object_from_bytes(content) != process
        or set(process) != TOOL_FIELDS
        or process.get("schema_version") != TOOL_SCHEMA
        or process.get("purpose") != "source-mermaid-node-version"
        or process.get("executable") != runtime["node_executable_label"]
        or process.get("executable_sha256") != runtime["node"]["sha256"]
        or process.get("command") != [runtime["node_executable_label"], "--version"]
        or type(process.get("original_exit_code")) is not int
        or process["original_exit_code"] != 0
        or type(process.get("exit_code")) is not int
        or process["exit_code"] != 0
        or process.get("timed_out") is not False
        or process.get("custody_refused") is not False
        or not isinstance(process.get("stdout"), str)
        or not re.fullmatch(r"v20\.[0-9]+\.[0-9]+\n?", process["stdout"])
        or process.get("stderr")
        or process.get("diagnostic")
    ):
        raise ValueError("Source11 Node20 exact original successful native invocation differs")
    admit_original_process(process)


def validate_original_mermaid_sources(
    original: dict[str, Any],
    sources: tuple[tuple[str, bytes], ...],
    *,
    artifact_reader: ArtifactReader,
    admit_original_process: ProcessAdmitter,
    inspect_svg: TopologyInspector,
    decoded_pixel_budget: SourceImageDecodeBudget,
) -> None:
    """Recompute exact retained source/process/topology/native paint obligations.

    This pure retained-artifact admission reopens no producer paths or installed
    runtimes. Its process callback must be the enclosing genuine custody verifier.
    Fresh reader-local runtime/font/process reproduction is a separate obligation.
    """
    if original.get("schema_version") != SCHEMA or original.get("content_digest") != canonical_digest(
        {key: value for key, value in original.items() if key != "content_digest"}
    ):
        raise ValueError("portable original Mermaid reference schema/digest differs")
    if original.get("remaining_admission") != list(REMAINING_ADMISSION):
        raise ValueError("portable Mermaid reference omitted unresolved original-source/native obligations")
    validate_mermaid_runtime(original["runtime_before"])
    if original["runtime_before"] != original["runtime_after"]:
        raise ValueError("portable original Mermaid complete runtime before/after differs")
    version = _runtime_version(original["runtime_before"])
    proof = original.get("runtime_process")
    if version == "11.16.0":
        _admit_source11_version_proof(proof, original["runtime_before"], artifact_reader, admit_original_process)
    elif proof is not None:
        raise ValueError("historical Mermaid12 record cannot borrow a Source11 Node20 runtime proof")
    rows = original["occurrences"]
    if not isinstance(rows, list) or len(rows) != len(sources) or original["blockers"]:
        raise ValueError("portable original Mermaid source census retains unresolved diagrams")
    for (identity, source), row in zip(sources, rows, strict=True):
        if row["identity"] != identity or _read(row["source"], artifact_reader) != source:
            raise ValueError("portable original Mermaid occurrence identity/source changed")
        normal = _normal(source)
        if _read(row["normalized_source"], artifact_reader) != normal or row[
            "source_graph"
        ] != compile_original_mermaid_source(source):
            raise ValueError("portable original Mermaid normalized source/independent graph changed")
        if row.get("source_display_policy") != DISPLAY_POLICY or row.get(
            "display_graph"
        ) != independent_mermaid_display_graph(source):
            raise ValueError("portable original Mermaid independent raw-to-display source policy differs")
        _original_process_closure(row, original["runtime_before"])
        if _read(row["producer_adapter"], artifact_reader) != adapter_bytes(version):
            raise ValueError("portable original Mermaid adapter differs from exact packaged SDK source bytes")
        if set(row["producer_requests"]) != {"svg", "png"}:
            raise ValueError("portable original Mermaid lacks both exact original API requests")
        if set(row["producer_configs"]) != {"svg", "png"}:
            raise ValueError("portable original Mermaid producer config closure differs")
        for kind in ("svg", "png"):
            config = json.loads(_read(row["producer_configs"][kind], artifact_reader))
            cwd = Path(row["processes"][kind]["cwd"])
            if _read(row["producer_requests"][kind], artifact_reader) != request_bytes(
                version,
                Path(original["runtime_before"]["package_root_label"]),
                cwd / "normalized.mmd",
                cwd / f"original.{kind}",
                kind,
                cwd / f"puppeteer-{kind}.json",
            ):
                raise ValueError("portable original Mermaid API request/source/config/runtime identities differ")
            expected = {
                "executablePath": original["runtime_before"]["chrome"]["executable"],
                "userDataDir": str(cwd / f"producer-profile-{kind}"),
                "args": [
                    "--no-first-run",
                    "--disable-background-networking",
                    "--disable-extensions",
                    "--disable-sync",
                    "--proxy-server=http://127.0.0.1:9",
                    "--proxy-bypass-list=127.0.0.1",
                ],
            }
            if config != expected:
                raise ValueError("portable original Mermaid native Chrome/private network config differs")
            before = row["processes"][kind]["input_observations_before"]
            if not any(
                value.get("path") == str(cwd / f"puppeteer-{kind}.json")
                and value.get("sha256") == row["producer_configs"][kind]["sha256"]
                for value in before
            ):
                raise ValueError("portable original Mermaid process omitted consumed exact original config")
        process_artifacts = row.get("process_artifacts")
        if not isinstance(process_artifacts, dict) or set(process_artifacts) != {"svg", "png"}:
            raise ValueError("portable original Mermaid lacks both exact original ToolAPI artifact bindings")
        for kind, process in row["processes"].items():
            binding = process_artifacts[kind]
            if not isinstance(binding, dict) or set(binding) != {"path", "sha256"}:
                raise ValueError("portable original Mermaid ToolAPI artifact binding differs")
            content = artifact_reader(binding)
            if (
                len(content) > 64 * 1024 * 1024
                or hashlib.sha256(content).hexdigest() != binding["sha256"]
                or json_object_from_bytes(content) != process
            ):
                raise ValueError("portable original Mermaid ToolAPI bytes differ from the original process")
            admit_original_process(process)
        svg = _read(row["artifacts"]["svg"], artifact_reader)
        png = _read(row["artifacts"]["png"], artifact_reader)
        if (
            _topology(normal, svg, inspect_svg) != row["topology"]
            or row["topology"].get("status") != "pass"
            or row["topology"].get("blockers")
            or row["topology"].get("findings")
        ):
            raise ValueError("portable independently interpreted original Mermaid graph/topology differs")
        paint = row["paint"]
        if paint.get("content_digest") != canonical_digest(
            {key: value for key, value in paint.items() if key != "content_digest"}
        ):
            raise ValueError("portable original SVG paint digest differs")
        validate_platform_font_files(paint["fonts"])
        painted_png = _read(row["paint_artifact"], artifact_reader)
        validate_original_svg_paint(
            paint, svg, painted_png, original["runtime_before"], decoded_pixel_budget=decoded_pixel_budget
        )
        if (
            inspect_original_svg_native_pixels(paint, png, decoded_pixel_budget=decoded_pixel_budget)
            != row["pixel_parity"]
        ):
            raise ValueError("portable original native/source SVG complete pixels differ")


def replay_original_mermaid_sources(
    original: dict[str, Any],
    sources: tuple[tuple[str, bytes], ...],
    *,
    artifact_reader: ArtifactReader,
    admit_original_process: ProcessAdmitter,
    root: Path,
    directory: Path,
    package_root: Path,
    node_executable: Path,
    chrome_executable: Path,
    font_files: tuple[Path, ...],
    decoded_pixel_budget: SourceImageDecodeBudget,
    inspect_svg: TopologyInspector,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    on_original_tool: OriginalCitationToolObserver | None = None,
    runtime_admission: NativeMermaidRuntimeAdmission | None = None,
) -> dict[str, Any]:
    """Validate original bytes then independently reproduce using reader roots.

    The caller supplies its actual admitted original process/custody verifier;
    original record booleans cannot authorize a native process. Reader tool/font
    roots are explicit and never derived from retained producer path labels.
    """
    validate_original_mermaid_sources(
        original,
        sources,
        artifact_reader=artifact_reader,
        admit_original_process=admit_original_process,
        inspect_svg=inspect_svg,
        decoded_pixel_budget=decoded_pixel_budget,
    )
    admit_reader_mermaid_runtime(
        original["runtime_before"],
        package_root,
        node_executable,
        chrome_executable,
        deadline=deadline,
        runtime_admission=runtime_admission,
    )
    rows = original["occurrences"]
    for row in rows:
        admit_reader_platform_fonts(row["paint"]["fonts"], font_files, deadline=deadline)
    reproduced = observe_original_mermaid_sources(
        root,
        directory,
        sources,
        package_root=package_root,
        node_executable=node_executable,
        chrome_executable=chrome_executable,
        font_files=font_files,
        decoded_pixel_budget=decoded_pixel_budget,
        inspect_svg=inspect_svg,
        env=env,
        deadline=deadline,
        run_id=run_id,
        on_original_tool=on_original_tool,
        runtime_admission=runtime_admission,
    )
    for prior, current in zip(rows, reproduced["occurrences"], strict=True):
        if (
            prior["source_graph"] != current["source_graph"]
            or prior["paint"]["fonts"] != current["paint"]["fonts"]
            or prior["paint"]["text_owners"] != current["paint"]["text_owners"]
            or prior["paint"]["original_dom"] != current["paint"]["original_dom"]
            or prior["paint"]["painted_dom"] != current["paint"]["painted_dom"]
            or any(
                prior["paint"]["paint"][key] != current["paint"]["paint"][key]
                for key in ("width", "height", "rgb_sha256")
            )
        ):
            raise ValueError("fresh reader-local Mermaid semantic/font/complete source paint reproduction differs")
    return reproduced
