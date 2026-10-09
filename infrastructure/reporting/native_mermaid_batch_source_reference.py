"""Genuine ordered Source11 artifacts and independently owned batch readers.

Each native batch has one actual supervised Node process and one actual
Source-only Chrome process. Every ordered occurrence has its own inputs and
SVG/PNG/paint artifacts. This schema never pretends those are separate PIDs.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path, PurePosixPath
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_citation_process_custody import (
    OriginalCitationToolObserver,
)
from infrastructure.reporting.native_format_acceptance_contracts import (
    CITATION_TOOL_FIELDS,
    TOOL_SCHEMA,
)
from infrastructure.reporting.native_format_pdf_mermaid_source import (
    compile_original_mermaid_source,
)
from infrastructure.reporting.native_format_pdf_source_decode_bounds import (
    SourceImageDecodeBudget,
)
from infrastructure.reporting.native_mermaid_font_bodies import NativeMermaidFontBodies
from infrastructure.reporting.native_mermaid_runtime_custody import (
    admit_reader_mermaid_runtime,
    validate_mermaid_runtime,
)
from infrastructure.reporting.native_mermaid_runtime_selection import (
    NativeMermaidRuntimeAdmission,
)
from infrastructure.reporting.native_mermaid_source_reference import (
    ArtifactReader,
    ProcessAdmitter,
    TopologyInspector,
    _admit_source11_version_proof,
    _binding,
    _normal,
    _read,
    _source11_live_node_reports,
    _topology,
    independent_mermaid_display_graph,
)
from infrastructure.reporting.native_mermaid_svg_batch_paint import (
    observe_original_svg_batch_paint,
)
from infrastructure.reporting.native_mermaid_svg_paint import (
    inspect_original_svg_native_pixels,
    validate_original_svg_paint,
)
from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime
from infrastructure.reporting.release_readiness_snapshot import json_object_from_bytes
from infrastructure.rendering._mermaid_source_font_default import (
    PROFILE_NAME,
    SCRIPT_NAME,
    default_font_profile_bytes,
    default_font_script_bytes,
    validate_default_font_buffers,
)
from infrastructure.rendering._mermaid_native_profile import rendering_profile

SCHEMA = "template-native-mermaid-source11-actual-ordered-batch-reference-v1"
REQUEST_SCHEMA = "template-mermaid-source11-ordered-batch-request-licensed-font-v2"
REPORT_SCHEMA = "template-mermaid-source11-actual-ordered-batch-artifacts-licensed-font-v2"
REMAINING_ADMISSION = (
    "actual enclosing independently admitted Source/SDK/provider/terminal original custody",
    "source-required loaded-library/shared-cache/kernel and actual platform font selection/shaping custody",
    "independent complete unclipped glyph/stroke/marker/clip/mask/filter ink and whole-document native positions",
)


def _adapter() -> bytes:
    return (Path(__file__).absolute().parent.parent / "rendering/_mermaid_v11_batch_adapter.mjs").read_bytes()


def _record_binding(
    record: dict[str, Any],
    binding: dict[str, Any],
    reader: ArtifactReader,
    admit: ProcessAdmitter,
) -> None:
    if set(binding) != {"path", "sha256"}:
        raise ValueError("original batch process binding differs from exact actual Tool wrapper")
    content = reader(binding)
    if (
        len(content) > 64 * 1024 * 1024
        or hashlib.sha256(content).hexdigest() != binding["sha256"]
        or json_object_from_bytes(content) != record
    ):
        raise ValueError("retained actual batch process bytes changed before original custody admission")
    if (
        set(record) != CITATION_TOOL_FIELDS
        or record.get("schema_version") != TOOL_SCHEMA
        or type(record.get("original_exit_code")) is not int
        or record["original_exit_code"] != 0
        or type(record.get("exit_code")) is not int
        or record["exit_code"] != 0
        or record["timed_out"] is not False
        or record["custody_refused"] is not False
        or record["diagnostic"]
    ):
        raise ValueError("actual Source batch process lacks signed success/complete original Tool custody")
    # The external callable is held by the genuine original owner. The object
    # above is only DATA until that owner admits the exact actual invocation.
    admit(record)


def _consumed(record: dict[str, Any], name: str, data: bytes) -> None:
    expected = {
        "path": str(Path(record["cwd"]) / name),
        "name": name,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    if expected not in record["input_observations_before"] or expected not in record["input_observations_after"]:
        raise ValueError("original Source artifact was not the exact input consumed by its actual native batch")


def observe_original_mermaid_batch(
    root: Path,
    directory: Path,
    sources: tuple[tuple[str, bytes], ...],
    *,
    runtime_admission: NativeMermaidRuntimeAdmission,
    font_bodies: NativeMermaidFontBodies,
    decoded_pixel_budget: SourceImageDecodeBudget,
    inspect_svg: TopologyInspector,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    on_original_tool: OriginalCitationToolObserver,
) -> dict[str, Any]:
    remaining(deadline)
    if not 0 < len(sources) <= 100 or len({identity for identity, _ in sources}) != len(sources):
        raise ValueError("genuine ordered Source batch needs every distinct original occurrence")
    source = runtime_admission.source
    if source.bindings.current_root != root or source.bindings.run_id != run_id or font_bodies.source is not source:
        raise ValueError("genuine Source batch runtime/font/source/run owners differ")
    node = runtime_admission.selection.node_executable
    selected = shutil.which("node", path=env.get("PATH"))
    if (
        selected is None
        or Path(selected).resolve(strict=True) != node.resolve(strict=True)
        or env.get("NODE_OPTIONS")
        or env.get("NODE_PATH")
    ):
        raise ValueError("actual Source batch Node selection differs or permits external module overrides")
    before = runtime_admission.observe(deadline=deadline)
    font_bodies.verify_live(deadline=deadline)
    tool = CitationRuntime(
        root,
        directory / "node",
        env=env,
        deadline=deadline,
        run_id=run_id,
        on_original_tool=on_original_tool,
    )
    adapter = tool.freeze("source11-ordered-batch.mjs", _adapter())
    font_helper = tool.freeze(SCRIPT_NAME, default_font_script_bytes())
    font_profile_data = default_font_profile_bytes(deadline=deadline)
    font_profile = tool.freeze(PROFILE_NAME, font_profile_data)
    profile = tool.directory / "browser-profile"
    config_data = {
        "executablePath": str(runtime_admission.selection.chrome_executable.resolve(strict=True)),
        "userDataDir": str(profile),
        "args": [
            "--no-first-run",
            "--disable-background-networking",
            "--disable-extensions",
            "--disable-sync",
            "--proxy-server=http://127.0.0.1:9",
            "--proxy-bypass-list=127.0.0.1",
        ],
    }
    config = tool.freeze("puppeteer.json", (json.dumps(config_data, sort_keys=True) + "\n").encode())
    inputs = []
    request_rows: list[dict[str, Any]] = []
    for ordinal, (identity, raw) in enumerate(sources):
        remaining(deadline)
        if not isinstance(identity, str) or not 0 < len(identity) <= 1024 or not raw or len(raw) > 1024 * 1024:
            raise ValueError("genuine ordered Source occurrence identity/body is absent or unbounded")
        normal = _normal(raw)
        original = tool.freeze(f"source-{ordinal:04d}.mmd", raw)
        normalized = tool.freeze(f"normalized-{ordinal:04d}.mmd", normal)
        inputs.append((identity, original, normalized, normal))
        request_rows.append(
            {
                "ordinal": ordinal,
                "identity": identity,
                "input": str(normalized),
                "input_sha256": hashlib.sha256(normal).hexdigest(),
                "svg_output": str(tool.directory / f"native-{ordinal:04d}.svg"),
                "png_output": str(tool.directory / f"native-{ordinal:04d}.png"),
            }
        )
    report_path = tool.directory / "actual-native-batch.json"
    request_data = {
        "schema_version": REQUEST_SCHEMA,
        "font_profile": str(font_profile),
        "font_profile_sha256": hashlib.sha256(font_profile_data).hexdigest(),
        "package_root": str(runtime_admission.selection.package_root.resolve(strict=True)),
        "dependency_root": str(runtime_admission.selection.dependency_root.resolve(strict=True)),
        "puppeteer_config": str(config),
        "render_profile": rendering_profile("11.16.0"),
        "occurrences": request_rows,
        "result_output": str(report_path),
    }
    request = tool.freeze("batch-request.json", (json.dumps(request_data, sort_keys=True) + "\n").encode())
    process = tool.tool("node", [str(adapter), str(request)], "original-mermaid-ordered-batch")
    _source11_live_node_reports(process)
    report_bytes = tool.read(report_path)
    native_report = json_object_from_bytes(report_bytes)
    if (
        set(native_report) != {"schema_version", "pid", "owner_pid", "occurrences"}
        or native_report["schema_version"] != REPORT_SCHEMA
        or native_report["pid"] != process["pid"]
        or native_report["owner_pid"] != process["owner_pid"]
        or not isinstance(native_report["occurrences"], list)
        or len(native_report["occurrences"]) != len(sources)
    ):
        raise ValueError("actual Source batch report lacks its real process/complete original occurrence set")
    artifacts = []
    for ordinal, (actual, planned) in enumerate(zip(native_report["occurrences"], request_rows, strict=True)):
        if set(actual) != {"ordinal", "identity", "input_sha256", "svg", "png"} or any(
            actual[key] != planned[key] for key in ("ordinal", "identity", "input_sha256")
        ):
            raise ValueError("actual Source native artifact order/identity/body differs from genuine original inputs")
        retained = {}
        for kind in ("svg", "png"):
            observed = actual[kind]
            path = Path(planned[kind + "_output"])
            data = tool.read(path)
            validate_default_font_buffers(observed.get("source_fonts", {}).get("buffers"), deadline=deadline)
            expected_fonts = observed.get("source_fonts")
            if not isinstance(expected_fonts, dict) or set(expected_fonts) != {
                "buffers",
                "platform_fonts",
                "used_default_faces",
            }:
                raise ValueError("actual Source native font observation differs")
            if observed != {
                "output": str(path),
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
                "source_fonts": expected_fonts,
            }:
                raise ValueError("actual original batch artifact bytes differ from native producer observation")
            retained[kind] = _binding(root, path, data)
        artifacts.append(retained)
    if profile.exists():
        shutil.rmtree(profile)
    tool.unchanged()
    paints = observe_original_svg_batch_paint(
        root,
        directory / "paint",
        tuple(
            (identity, tool.read(root / artifact["svg"]["path"]))
            for (identity, _), artifact in zip(sources, artifacts, strict=True)
        ),
        runtime_admission=runtime_admission,
        font_bodies=font_bodies,
        decoded_pixel_budget=decoded_pixel_budget,
        env=env,
        deadline=deadline,
        run_id=run_id,
        on_original_tool=on_original_tool,
    )
    rows = []
    blockers = []
    for ordinal, (source_row, input_row, artifact, painted) in enumerate(
        zip(sources, inputs, artifacts, paints["occurrences"], strict=True)
    ):
        identity, raw = source_row
        _, raw_path, normalized_path, normalized_bytes = input_row
        svg, png = (
            tool.read(root / artifact["svg"]["path"]),
            tool.read(root / artifact["png"]["path"]),
        )
        topology = _topology(normalized_bytes, svg, inspect_svg)
        parity = inspect_original_svg_native_pixels(painted["paint"], png, decoded_pixel_budget=decoded_pixel_budget)
        if topology.get("status") != "pass" or topology.get("blockers") or topology.get("findings"):
            blockers.append(
                {
                    "identity": identity,
                    "reason": "independent complete source SVG topology is not admitted",
                }
            )
        rows.append(
            {
                "ordinal": ordinal,
                "identity": identity,
                "source": _binding(root, raw_path, raw),
                "normalized_source": _binding(root, normalized_path, normalized_bytes),
                "source_graph": compile_original_mermaid_source(raw),
                "display_graph": independent_mermaid_display_graph(raw),
                "artifacts": artifact,
                "topology": topology,
                "paint": painted["paint"],
                "paint_artifact": painted["paint_artifact"],
                "pixel_parity": parity,
            }
        )
    after = runtime_admission.observe(deadline=deadline)
    if before != after:
        raise ValueError("complete actually nominated Source batch runtime changed during original artifacts/paint")
    font_bodies.verify_terminal_bytes(deadline=deadline)
    result = {
        "schema_version": SCHEMA,
        "run_id": run_id,
        "runtime_before": before,
        "runtime_after": after,
        "runtime_process": runtime_admission.node_version_proof(),
        "native_process": process,
        "native_process_artifact": dict(tool.tools[-1]),
        "native_report": _binding(root, report_path, report_bytes),
        "producer_font_helper": _binding(root, font_helper, tool.read(font_helper)),
        "producer_font_profile": _binding(root, font_profile, font_profile_data),
        "producer_adapter": _binding(root, adapter, tool.read(adapter)),
        "producer_request": _binding(root, request, tool.read(request)),
        "producer_config": _binding(root, config, tool.read(config)),
        "paint_batch_process": paints["shared_process"],
        "paint_batch_process_artifact": paints["shared_process_artifact"],
        "occurrences": rows,
        "blockers": blockers,
        "remaining_admission": list(REMAINING_ADMISSION),
    }
    return {**result, "content_digest": canonical_digest(result)}


def validate_original_mermaid_batch(
    original: dict[str, Any],
    sources: tuple[tuple[str, bytes], ...],
    *,
    artifact_reader: ArtifactReader,
    admit_original_process: ProcessAdmitter,
    decoded_pixel_budget: SourceImageDecodeBudget,
    inspect_svg: TopologyInspector,
) -> None:
    if original.get("schema_version") != SCHEMA or original.get("content_digest") != canonical_digest(
        {key: value for key, value in original.items() if key != "content_digest"}
    ):
        raise ValueError("original Source ordered batch schema/content changed")
    before, after = original["runtime_before"], original["runtime_after"]
    validate_mermaid_runtime(before)
    if before != after or original.get("remaining_admission") != list(REMAINING_ADMISSION):
        raise ValueError("original Source ordered batch held runtime/remaining obligations differ")
    _admit_source11_version_proof(original["runtime_process"], before, artifact_reader, admit_original_process)
    for process, binding in (
        (original["native_process"], original["native_process_artifact"]),
        (original["paint_batch_process"], original["paint_batch_process_artifact"]),
    ):
        _record_binding(process, binding, artifact_reader, admit_original_process)
    process = original["native_process"]
    if (
        process["executable"] != before["node_executable_label"]
        or process["executable_sha256"] != before["node"]["sha256"]
        or process["purpose"] != "original-mermaid-ordered-batch"
    ):
        raise ValueError("original actual Source batch Node executable/purpose differs")
    chrome_process = original["paint_batch_process"]
    chrome_executable = (
        PurePosixPath(before["chrome"]["executable"]).relative_to(PurePosixPath(before["chrome"]["root"])).as_posix()
    )
    chrome_digest = next(
        row["sha256"] for row in before["chrome"]["files"] if row["path"] == chrome_executable and row["kind"] == "file"
    )
    if (
        chrome_process["executable"] != before["chrome"]["executable"]
        or chrome_process["executable_sha256"] != chrome_digest
        or chrome_process["purpose"] != "original-svg-ordered-batch-paint"
    ):
        raise ValueError("original actual Source paint browser executable/purpose differs")
    _source11_live_node_reports(process)
    adapter_data = _read(original["producer_adapter"], artifact_reader)
    if adapter_data != _adapter():
        raise ValueError("original actual Source batch adapter differs from independently selected SDK")
    _consumed(process, "source11-ordered-batch.mjs", adapter_data)
    request_data = _read(original["producer_request"], artifact_reader)
    config_data = _read(original["producer_config"], artifact_reader)
    _consumed(process, "batch-request.json", request_data)
    _consumed(process, "puppeteer.json", config_data)
    request = json_object_from_bytes(request_data)
    config = json_object_from_bytes(config_data)
    native = json_object_from_bytes(_read(original["native_report"], artifact_reader))
    rows = original["occurrences"]
    cwd = Path(process["cwd"])
    if (
        set(request)
        != {
            "schema_version",
            "package_root",
            "dependency_root",
            "puppeteer_config",
            "render_profile",
            "occurrences",
            "result_output",
            "font_profile",
            "font_profile_sha256",
        }
        or set(native) != {"schema_version", "pid", "owner_pid", "occurrences"}
        or process["command"]
        != [
            before["node_executable_label"],
            str(cwd / "source11-ordered-batch.mjs"),
            str(cwd / "batch-request.json"),
        ]
        or request["font_profile"] != str(cwd / PROFILE_NAME)
        or request["font_profile_sha256"] != hashlib.sha256(default_font_profile_bytes()).hexdigest()
        or request["puppeteer_config"] != str(cwd / "puppeteer.json")
        or request["result_output"] != str(cwd / "actual-native-batch.json")
        or not isinstance(rows, list)
        or len(rows) != len(sources)
        or len(request["occurrences"]) != len(sources)
        or len(native["occurrences"]) != len(sources)
        or request["schema_version"] != REQUEST_SCHEMA
        or request["package_root"] != before["package_root_label"]
        or request["dependency_root"] != before["dependency_root_label"]
        or request["render_profile"] != rendering_profile("11.16.0")
        or native["schema_version"] != REPORT_SCHEMA
        or native["pid"] != process["pid"]
        or native["owner_pid"] != process["owner_pid"]
    ):
        raise ValueError("original batch exact request/runtime/native occurrence report differs")
    _consumed(process, SCRIPT_NAME, default_font_script_bytes())
    _consumed(process, PROFILE_NAME, default_font_profile_bytes())
    expected_config = {
        "executablePath": before["chrome"]["executable"],
        "userDataDir": str(cwd / "browser-profile"),
        "args": [
            "--no-first-run",
            "--disable-background-networking",
            "--disable-extensions",
            "--disable-sync",
            "--proxy-server=http://127.0.0.1:9",
            "--proxy-bypass-list=127.0.0.1",
        ],
    }
    if config != expected_config:
        raise ValueError("original batch actual native browser configuration was not consumed by Node")
    for ordinal, ((identity, raw), row, requested, native_row) in enumerate(
        zip(sources, rows, request["occurrences"], native["occurrences"], strict=True)
    ):
        if (
            set(requested)
            != {
                "ordinal",
                "identity",
                "input",
                "input_sha256",
                "svg_output",
                "png_output",
            }
            or set(native_row) != {"ordinal", "identity", "input_sha256", "svg", "png"}
            or row["ordinal"] != ordinal
            or row["identity"] != identity
            or requested["ordinal"] != ordinal
            or requested["identity"] != identity
            or native_row["ordinal"] != ordinal
            or native_row["identity"] != identity
            or requested["input"] != str(cwd / f"normalized-{ordinal:04d}.mmd")
            or requested["svg_output"] != str(cwd / f"native-{ordinal:04d}.svg")
            or requested["png_output"] != str(cwd / f"native-{ordinal:04d}.png")
        ):
            raise ValueError("original batch Source order/identity changed or was deduplicated")
        normalized = _normal(raw)
        _consumed(process, f"source-{ordinal:04d}.mmd", raw)
        _consumed(process, f"normalized-{ordinal:04d}.mmd", normalized)
        if (
            _read(row["source"], artifact_reader) != raw
            or _read(row["normalized_source"], artifact_reader) != normalized
            or row["source_graph"] != compile_original_mermaid_source(raw)
            or row["display_graph"] != independent_mermaid_display_graph(raw)
        ):
            raise ValueError("original actual batch source/display bytes or independent semantics differ")
        if (
            requested["input_sha256"] != hashlib.sha256(normalized).hexdigest()
            or native_row["input_sha256"] != requested["input_sha256"]
        ):
            raise ValueError("original actual native batch substituted source input bytes")
        svg, png = (
            _read(row["artifacts"]["svg"], artifact_reader),
            _read(row["artifacts"]["png"], artifact_reader),
        )
        for kind, data in (("svg", svg), ("png", png)):
            validate_default_font_buffers(native_row[kind].get("source_fonts", {}).get("buffers"))
            if native_row[kind] != {
                "output": requested[kind + "_output"],
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "source_fonts": native_row[kind]["source_fonts"],
            }:
                raise ValueError("original actual native batch result body/ordered input assignment differs")
        if _topology(normalized, svg, inspect_svg) != row["topology"]:
            raise ValueError("independent Source batch SVG topology changed")
        paint = row["paint"]
        if (
            paint["browser_pid"] != chrome_process["pid"]
            or paint["browser_command"] != chrome_process["command"]
            or paint["browser_original_exit"] != chrome_process["original_exit_code"]
            or paint["stdout_sha256"] != chrome_process["raw_stdout"]["sha256"]
            or paint["stderr_sha256"] != chrome_process["raw_stderr"]["sha256"]
        ):
            raise ValueError("original Source occurrence paint is not bound to its genuine shared browser process")
        validate_original_svg_paint(
            paint,
            svg,
            _read(row["paint_artifact"], artifact_reader),
            before,
            decoded_pixel_budget=decoded_pixel_budget,
        )
        if (
            inspect_original_svg_native_pixels(paint, png, decoded_pixel_budget=decoded_pixel_budget)
            != row["pixel_parity"]
        ):
            raise ValueError("strict original Source batch native/independent pixel parity changed")


def replay_original_mermaid_batch(
    original: dict[str, Any],
    sources: tuple[tuple[str, bytes], ...],
    *,
    artifact_reader: ArtifactReader,
    admit_original_process: ProcessAdmitter,
    root: Path,
    directory: Path,
    runtime_admission: NativeMermaidRuntimeAdmission,
    font_bodies: NativeMermaidFontBodies,
    decoded_pixel_budget: SourceImageDecodeBudget,
    inspect_svg: TopologyInspector,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    on_original_tool: OriginalCitationToolObserver,
) -> dict[str, Any]:
    validate_original_mermaid_batch(
        original,
        sources,
        artifact_reader=artifact_reader,
        admit_original_process=admit_original_process,
        decoded_pixel_budget=decoded_pixel_budget,
        inspect_svg=inspect_svg,
    )
    selected = runtime_admission.selection
    admit_reader_mermaid_runtime(
        original["runtime_before"],
        selected.package_root,
        selected.node_executable,
        selected.chrome_executable,
        deadline=deadline,
        runtime_admission=runtime_admission,
    )
    for row in original["occurrences"]:
        font_bodies.authenticate_retained_fonts(row["paint"]["fonts"], deadline=deadline)
    current = observe_original_mermaid_batch(
        root,
        directory,
        sources,
        runtime_admission=runtime_admission,
        font_bodies=font_bodies,
        decoded_pixel_budget=decoded_pixel_budget,
        inspect_svg=inspect_svg,
        env=env,
        deadline=deadline,
        run_id=run_id,
        on_original_tool=on_original_tool,
    )
    if (
        current["native_process"]["pid"] == original["native_process"]["pid"]
        or current["paint_batch_process"]["pid"] == original["paint_batch_process"]["pid"]
    ):
        raise ValueError("fresh Source reader reused an actual original batch process")

    def shaped_references(paint: dict[str, Any]) -> list[dict[str, Any]]:
        # Physical provider addresses/path labels are retained observations,
        # not portable original authority or current provider nominations.
        # Each current reference below was produced by the fresh actual live
        # typed shaper with independently held current body/face bytes.
        return [
            {
                "owner_index": owner["owner_index"],
                "original_text": owner["original_text"],
                "references": [face["reference"] for face in owner["declared_face_shaping"]],
            }
            for owner in paint["font_shaped_bodies"]
        ]

    for prior, fresh in zip(original["occurrences"], current["occurrences"], strict=True):
        if (
            any(prior[key] != fresh[key] for key in ("ordinal", "identity", "source_graph", "display_graph"))
            or any(
                prior["paint"][key] != fresh["paint"][key]
                for key in (
                    "fonts",
                    "text_owners",
                    "original_dom",
                    "painted_dom",
                    "font_body_glyphs",
                    "source_glyph_layout",
                )
            )
            or shaped_references(prior["paint"]) != shaped_references(fresh["paint"])
            or any(
                prior["paint"]["paint"][key] != fresh["paint"]["paint"][key]
                for key in ("width", "height", "rgb_sha256")
            )
        ):
            raise ValueError("fresh actual Source batch semantic/font/glyph-body/full-pixel reproduction differs")
    return current
