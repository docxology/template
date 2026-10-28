"""Actual source-bound Mermaid producer adapter; diagram ink admission is separate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from defusedxml.ElementTree import fromstring

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
from infrastructure.reporting.native_format_browser_runtime import observe_runtime, validate_runtime
from infrastructure.reporting.native_office_mermaid_semantics import (
    inspect_mermaid_svg_source,
    mermaid_source_semantics,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.rendering._pdf_mermaid import _MERMAID_BLOCK_RE, _normalise_mermaid_source, _source_hash


def _svg_observation(data: bytes) -> dict[str, Any]:
    """Read actual bounded SVG structure and label text without executing it."""
    if len(data) > 8 * 1024 * 1024:
        raise ValueError("native Mermaid SVG exceeds its finite source budget")
    tree = fromstring(data)
    nodes = list(tree.iter())
    if len(nodes) > 100_000 or tree.tag != "{http://www.w3.org/2000/svg}svg":
        raise ValueError("native Mermaid SVG has invalid bounded root/structure")
    if any(node.tag.rsplit("}", 1)[-1] in {"script", "iframe", "object", "embed"} for node in nodes):
        raise ValueError("native Mermaid SVG contains an active external element")
    labels = [
        " ".join("".join(node.itertext()).split())
        for node in nodes
        if node.tag.rsplit("}", 1)[-1] in {"text", "foreignObject"}
    ]
    geometry = sum(
        node.tag.rsplit("}", 1)[-1] in {"path", "rect", "polygon", "line", "circle", "ellipse"} for node in nodes
    )
    if not geometry or not labels:
        raise ValueError("actual native Mermaid SVG omitted graphic geometry or label text")
    return {
        "svg_sha256": hashlib.sha256(data).hexdigest(),
        "view_box": tree.get("viewBox"),
        "labels": labels,
        "geometry_nodes": geometry,
    }


def observe_office_mermaid_source(
    root: Path,
    directory: Path,
    source: bytes,
    *,
    chrome_executable: Path,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> dict[str, Any]:
    """Render each original source fence with the genuine configured mmdc/Chrome.

    Call only in the parent's original supervised native phase. The dedicated
    private Puppeteer config is source-owned; no global configuration changes.
    SVG and PNG are separate actual mmdc outputs with original zero exits.
    The caller must additionally bind the original source fence inventory,
    independent SVG/vector/source semantics and native PNG ink before clearing
    the combined Mermaid obligation. This adapter never grants that gate.
    """
    if len(source) > 32 * 1024 * 1024:
        raise ValueError("Office Mermaid combined source exceeds finite AST/source budget")
    matches = tuple(_MERMAID_BLOCK_RE.finditer(source.decode()))
    if not matches or len(matches) > 100:
        raise ValueError("Office Mermaid source requires a bounded nonempty source fence set")
    create_private_native_directory(root, directory)
    consumed = directory / "combined-source.md"
    atomic_write_bytes_confined(root, consumed, source, mode=0o600)
    chrome = chrome_executable.resolve(strict=True)
    runtime_before = observe_runtime(chrome, deadline=deadline)
    config = directory / "puppeteer.json"
    # Preserve the actual existing PDF Mermaid adapter's configuration and
    # process flags, isolated to this fresh attempt directory.
    config_data = json.dumps({"executablePath": str(chrome), "args": ["--no-sandbox"]}).encode() + b"\n"
    atomic_write_bytes_confined(root, config, config_data, mode=0o600)
    reader = SnapshotReader(root)
    rows: list[dict[str, Any]] = []
    for ordinal, match in enumerate(matches):
        leaf = directory / f"diagram-{ordinal:04d}"
        create_private_native_directory(root, leaf)
        original = match.group("source").strip()
        normal = _normalise_mermaid_source(original)
        if not normal:
            raise ValueError("Office Mermaid source contains an empty diagram")
        source_path = leaf / "source.mmd"
        atomic_write_bytes_confined(root, source_path, normal.encode(), mode=0o600)
        outputs, processes = {}, {}
        for kind in ("svg", "png"):
            output = leaf / f"diagram.{kind}"
            arguments = [
                "--input",
                str(source_path),
                "--output",
                str(output),
                "--width",
                "1400",
                "--height",
                "900",
                "--backgroundColor",
                "white",
                "--quiet",
                "--puppeteerConfigFile",
                str(config),
            ]
            process = native_tool_record(
                root,
                leaf,
                "mmdc",
                arguments,
                env=env,
                deadline=deadline,
                run_id=run_id,
                purpose=f"mermaid-source-{kind}",
            )
            if process["exit_code"] != 0 or process["original_exit_code"] != 0:
                raise ValueError("actual configured native Mermaid producer failed; fallback is not diagram evidence")
            snapshot = reader.read(output.relative_to(root).as_posix())
            outputs[kind] = {"path": snapshot.relative, "sha256": snapshot.sha256}
            processes[kind] = process
        svg = reader.read(outputs["svg"]["path"])
        from infrastructure.reporting.native_office_content_witness import _image_identity

        png = reader.read(outputs["png"]["path"])
        identity = _image_identity(png.content)
        if identity["kind"] != "decoded-raster":
            raise ValueError("actual native Mermaid producer did not emit an independently decodable PNG")
        rows.append(
            {
                "ordinal": ordinal,
                "source_range": [match.start(), match.end()],
                "original_source_sha256": hashlib.sha256(original.encode()).hexdigest(),
                "normal_source_sha256": hashlib.sha256(normal.encode()).hexdigest(),
                "production_stem": f"inline_mermaid_{ordinal + 1:04d}_{_source_hash(normal)}",
                "source": {
                    "path": source_path.relative_to(root).as_posix(),
                    "sha256": hashlib.sha256(normal.encode()).hexdigest(),
                },
                "outputs": outputs,
                "processes": processes,
                "svg": _svg_observation(svg.content),
                "source_semantics": mermaid_source_semantics(normal),
                "svg_source_projection": inspect_mermaid_svg_source(normal, svg.content),
                "png": identity,
            }
        )
    runtime_after = observe_runtime(chrome, deadline=deadline)
    if runtime_before != runtime_after or not reader.unchanged():
        raise ValueError("native Mermaid Chrome/source/config/output custody changed during original production")
    return {
        "schema_version": "template-native-office-mermaid-source-v1",
        "run_id": run_id,
        "source": {"path": consumed.relative_to(root).as_posix(), "sha256": hashlib.sha256(source).hexdigest()},
        "config": {"path": config.relative_to(root).as_posix(), "sha256": hashlib.sha256(config_data).hexdigest()},
        "runtime_before": runtime_before,
        "runtime_after": runtime_after,
        "diagrams": rows,
        "blockers": [
            "Mermaid independent SVG raster decode and actual native image ink require genuine controls",
            *dict.fromkeys(blocker for row in rows for blocker in row["svg_source_projection"]["blockers"]),
        ],
        "assurance": (
            "genuine source-bound configured mmdc/Chrome production with actual SVG and PNG bytes; "
            "no diagram gate claimed"
        ),
    }


def replay_office_mermaid_source(
    root: Path,
    directory: Path,
    source: bytes,
    raw: dict[str, Any],
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
) -> None:
    """Bind original producer outputs/runtime labels without opening producer tools."""
    from infrastructure.reporting.native_format_acceptance_evidence import _file, _tool
    from infrastructure.reporting.native_format_portable_custody import producer_path
    from infrastructure.reporting.native_office_content_witness import _image_identity

    if raw.get("schema_version") != "template-native-office-mermaid-source-v1" or raw.get("run_id") != run_id:
        raise ValueError("portable Office Mermaid original source schema/run differs")
    frozen = _file(raw["source"], reader)
    config = _file(raw["config"], reader)
    if (
        frozen.path != directory / "combined-source.md"
        or frozen.content != source
        or config.path != directory / "puppeteer.json"
    ):
        raise ValueError("portable Office Mermaid original combined source/config differs")
    configuration = json.loads(config.content)
    chrome = configuration.get("executablePath")
    if (
        set(configuration) != {"executablePath", "args"}
        or configuration["args"] != ["--no-sandbox"]
        or not isinstance(chrome, str)
    ):
        raise ValueError("portable Office Mermaid source-owned Puppeteer configuration differs")
    runtime = raw["runtime_before"]
    executable = Path(chrome).relative_to(Path(runtime["root"])).as_posix()
    digest = next(
        (row["sha256"] for row in runtime["files"] if row["path"] == executable and row["kind"] == "file"), None
    )
    if not isinstance(digest, str):
        raise ValueError("portable Office Mermaid original Chrome runtime has no executable file hash")
    validate_runtime(runtime, chrome, digest)
    if runtime != raw["runtime_after"]:
        raise ValueError("portable Office Mermaid original Chrome runtime changed")
    matches = tuple(_MERMAID_BLOCK_RE.finditer(source.decode()))
    if not matches or len(matches) != len(raw["diagrams"]):
        raise ValueError("portable Office Mermaid original source fence inventory differs")
    for ordinal, (match, row) in enumerate(zip(matches, raw["diagrams"], strict=True)):
        leaf = directory / f"diagram-{ordinal:04d}"
        original = match.group("source").strip()
        normal = _normalise_mermaid_source(original)
        consumed = _file(row["source"], reader)
        if (
            row["ordinal"] != ordinal
            or row["source_range"] != [match.start(), match.end()]
            or row["original_source_sha256"] != hashlib.sha256(original.encode()).hexdigest()
            or row["normal_source_sha256"] != hashlib.sha256(normal.encode()).hexdigest()
            or consumed.path != leaf / "source.mmd"
            or consumed.content != normal.encode()
            or row["production_stem"] != f"inline_mermaid_{ordinal + 1:04d}_{_source_hash(normal)}"
        ):
            raise ValueError("portable Office Mermaid actual normalized source/source range differs")
        outputs = {}
        for kind in ("svg", "png"):
            output = _file(row["outputs"][kind], reader)
            if output.path != leaf / f"diagram.{kind}":
                raise ValueError("portable Office Mermaid output belongs to another original attempt")
            arguments = [
                "--input",
                str(producer_path(custody, root, consumed.path)),
                "--output",
                str(producer_path(custody, root, output.path)),
                "--width",
                "1400",
                "--height",
                "900",
                "--backgroundColor",
                "white",
                "--quiet",
                "--puppeteerConfigFile",
                str(producer_path(custody, root, config.path)),
            ]
            _tool(row["processes"][kind]["artifact"], reader, run_id, "mmdc", f"mermaid-source-{kind}", arguments)
            outputs[kind] = output.content
        if (
            _svg_observation(outputs["svg"]) != row["svg"]
            or _image_identity(outputs["png"]) != row["png"]
            or mermaid_source_semantics(normal) != row["source_semantics"]
            or inspect_mermaid_svg_source(normal, outputs["svg"]) != row["svg_source_projection"]
        ):
            raise ValueError("portable Office Mermaid independent SVG/PNG interpretation differs")
    if not reader.unchanged():
        raise ValueError("portable Office Mermaid admitted original custody changed")
