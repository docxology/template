"""Independent portable reconstruction of retained source-only TeX references.

The enclosing native reader must authenticate original source/parser/SDK custody.
This component never opens a producer compiler, distribution, or filesystem path.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
import hashlib
from io import BytesIO
import json
import math
from pathlib import PurePath, PurePosixPath
import re
import time
from typing import Any

from infrastructure.reporting.native_format_pdf_source import PDFSourceInputs
from infrastructure.reporting.native_format_tex_reference import (
    TEXMF_TREES_ARGUMENT,
    admitted_texmf_roots,
    validate_texmf_installation,
    texmf_dependency_admitted,
)
from infrastructure.reporting.native_format_portable_custody import validate_executable_observation
from infrastructure.reporting.native_format_scientific_math import (
    _math_body,
    reference_math_glyphs,
    scientific_math_from_ast,
)

from infrastructure.reporting.native_format_acceptance_contracts import (
    TOOL_FIELDS,
    TOOL_SCHEMA,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

POLICY = "actual successful Kpathsea file opens plus native fonts/metrics and every TeX FLS input"


def strict_json_object(content: bytes) -> dict[str, Any]:
    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in rows:
            if key in result:
                raise ValueError("original scientific JSON repeats a field")
            result[key] = value
        return result

    result = json.loads(content, object_pairs_hook=pairs)
    if not isinstance(result, dict):
        raise ValueError("original scientific JSON must be an object")
    return result


def _absolute(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if not path.is_absolute() or ".." in path.parts or str(path) != value or "\\" in value or "\0" in value:
        raise ValueError("original reference path is not canonical absolute")
    return path


def unsupported_source_blockers(ast_bytes: bytes) -> list[str]:
    """Retain unsupported raw/citation/table occurrences; never waive them."""
    blockers = []

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            if value.get("t") in {"Cite", "RawInline", "RawBlock", "Table"}:
                blockers.append(f"{path}: source {value['t']} requires independent full-source/citation/table replay")
            for key, child in value.items():
                visit(child, f"{path}/{key}")
        elif isinstance(value, list):
            for ordinal, child in enumerate(value):
                visit(child, f"{path}/{ordinal}")

    visit(json.loads(ast_bytes)["blocks"], "blocks")
    return blockers


def replay_scientific_math_reference(
    raw: dict[str, Any],
    ast_bytes: bytes,
    inputs: PDFSourceInputs,
    *,
    read_artifact: Callable[[dict[str, Any]], bytes],
    producer_path: Callable[[str], str],
    run_id: str,
    deadline: float,
    native_reader: SnapshotReader,
) -> dict[str, Any]:
    """Rebuild all source/reference predicates from original retained bytes."""

    def admitted(binding: dict[str, Any]) -> bytes:
        if set(binding) != {"path", "sha256"}:
            raise ValueError("reference artifact fieldset differs")
        content = read_artifact(binding)
        if hashlib.sha256(content).hexdigest() != binding["sha256"]:
            raise ValueError("reference artifact differs from bound original bytes")
        if time.monotonic() >= deadline:
            raise TimeoutError("independent reference replay deadline exhausted")
        return content

    fields = {
        "schema_version",
        "source",
        "pdf",
        "discovery_fls",
        "final_fls",
        "backend_inputs",
        "compiler_logs",
        "consumed_backend_path",
        "runtime_before",
        "runtime_after",
        "dependencies_before",
        "dependencies_after",
        "backend_input_policy",
        "tool_artifacts",
        "environment",
        "status",
        "source_ast_sha256",
        "source_ast",
        "nodes",
        "template_tool_artifact",
        "source_inputs",
        "blockers",
        "execution_budget_seconds",
        "elapsed_seconds",
        "implementation",
    }
    if set(raw) != fields or raw["status"] != "pass":
        raise ValueError("source reference original observation fieldset/outcome differs")
    budget, elapsed = raw["execution_budget_seconds"], raw["elapsed_seconds"]
    if (
        type(budget) not in {int, float}
        or type(elapsed) not in {int, float}
        or not math.isfinite(budget)
        or not math.isfinite(elapsed)
        or not 0 < elapsed < budget <= 3600
    ):
        raise ValueError("source reference lacks finite original execution budget/outcome")
    if admitted(raw["source_ast"]) != ast_bytes:
        raise ValueError("source reference original AST bytes differ")
    from pathlib import Path
    from infrastructure.reporting import native_format_scientific_math, native_format_tex_reference

    modules = (native_format_scientific_math, native_format_tex_reference)
    implementation = raw["implementation"]
    if len(implementation) != len(modules):
        raise ValueError("source reference actual implementation closure differs")
    for ordinal, (row, module) in enumerate(zip(implementation, modules, strict=True)):
        current = Path(str(module.__file__)).read_bytes()
        if (
            set(row) != {"original_path", "sha256", "artifact"}
            or _absolute(row["original_path"]).name != Path(str(module.__file__)).name
            or admitted(row["artifact"]) != current
            or hashlib.sha256(current).hexdigest() != row["sha256"]
            or PurePosixPath(row["artifact"]["path"]).name != f"{ordinal:02d}-{Path(str(module.__file__)).name}.bin"
        ):
            raise ValueError("source reference differs from current loaded implementation bytes")
    strict_json_object(ast_bytes)
    nodes = scientific_math_from_ast(ast_bytes)
    expected_sources = [
        {"path": path, "sha256": hashlib.sha256(content).hexdigest()}
        for path, content in (*inputs.sources, inputs.config, *((inputs.preamble,) if inputs.preamble else ()))
    ]
    if (
        raw["schema_version"] != "template-native-source-scientific-math-v1"
        or raw["source_ast_sha256"] != hashlib.sha256(ast_bytes).hexdigest()
        or raw["nodes"] != [asdict(node) for node in nodes]
        or raw["source_inputs"] != expected_sources
        or raw["blockers"] != list(inputs.blockers)
    ):
        raise ValueError("reference source/case identity differs from current reconstructed source")
    directory = str(PurePosixPath(raw["source"]["path"]).parent)
    original_directory = _absolute(producer_path(directory))
    original_root = _absolute(producer_path("."))

    def tool(binding: dict[str, Any], purpose: str, name: str, arguments: list[str]) -> dict[str, Any]:
        process = strict_json_object(admitted(binding))
        if set(process) != TOOL_FIELDS:
            raise ValueError("reference original tool fieldset differs")
        validate_executable_observation(
            process["executable_observation_before"], process["executable"], process["executable_sha256"]
        )
        validate_executable_observation(
            process["executable_observation_after"], process["executable"], process["executable_sha256"]
        )
        if (
            process["schema_version"] != TOOL_SCHEMA
            or process["run_id"] != run_id
            or process["purpose"] != purpose
            or process["tool"] != name
            or not isinstance(process["command"], list)
            or len(process["command"]) != len(arguments) + 1
            or process["command"][1:] != arguments
            or type(process["exit_code"]) is not int
            or process["exit_code"] != 0
            or type(process["original_exit_code"]) is not int
            or process["original_exit_code"] != 0
            or process["timed_out"] is not False
            or process["custody_refused"] is not False
            or process["diagnostic"] != ""
            or not isinstance(process["stdout"], str)
            or not isinstance(process["stderr"], str)
        ):
            raise ValueError("reference original command/outcome/custody differs")
        native = strict_json_object(admitted(process["native_process_artifact"]))
        nomination = native.get("nomination")
        preserve = name == "xelatex"
        if (
            not isinstance(nomination, dict)
            or set(nomination) != {"tool", "path", "resolved_path"}
            or nomination["tool"] != name
            or nomination["resolved_path"] != process["executable"]
            or not isinstance(nomination["path"], str)
            or str(_absolute(nomination["path"])) != nomination["path"]
            or native.get("launcher_preserved") is not preserve
            or native.get("command") != process["command"]
            or process["command"][0] != (nomination["path"] if preserve else process["executable"])
        ):
            raise ValueError("reference actual Source-nominated launcher differs from its original argv")
        if native_reader.native_producer_operation is not None:
            from infrastructure.reporting.native_tool_producer import validate_live_native_tool

            validate_live_native_tool(binding, process, native_reader, run_id=run_id)
        else:
            from infrastructure.reporting.native_tool_replay import validate_original_native_tool

            validate_original_native_tool(
                binding,
                process,
                native_reader,
                run_id=run_id,
                required_sdk_modules=(
                    "reporting/native_tool_process.py",
                    "reporting/native_format_acceptance_checks.py",
                ),
            )
        return process

    import yaml

    config = yaml.safe_load(inputs.config[1])
    metadata = config.get("metadata", {}) if isinstance(config, dict) else {}
    arguments = [producer_path(directory + "/template.ast.json"), "--from=json", "--to=latex", "--standalone"]
    for name in ("fontsize", "documentclass", "geometry"):
        if metadata.get(name):
            arguments.extend(["-V", f"{name}:{metadata[name]}"])
    template = tool(raw["template_tool_artifact"], "math-reference-template", "pandoc", arguments)["stdout"]
    if template.count(r"\begin{document}") != 1:
        raise ValueError("reference template lacks unique source-owned document boundary")
    from infrastructure.rendering._pdf_combined_latex import postprocess_latex

    declared = ""
    if inputs.preamble:
        # The source helper selects only its fenced LaTeX preamble. Reconstruct
        # without writing or reading a temporary producer path.
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from infrastructure.rendering._pdf_latex_helpers import extract_preamble

        with TemporaryDirectory(prefix="native-reference-reader-preamble-") as scratch:
            preamble_path = Path(scratch) / "preamble.md"
            preamble_path.write_bytes(inputs.preamble[1])
            declared = extract_preamble(preamble_path)
    tex = postprocess_latex(
        template.split(r"\begin{document}", 1)[0]
        + declared
        + "\n\\begin{document}\n\\pagestyle{empty}\n"
        + _math_body(nodes)
        + "\n\\end{document}\n"
    ).encode()
    if admitted(raw["source"]) != tex:
        raise ValueError("retained reference TeX differs from source-only reconstruction")
    if raw["environment"] != {
        **{name: str(original_directory / name.lower()) for name in ("TEXMFHOME", "TEXMFCONFIG", "TEXMFVAR")},
        "TEXMFOUTPUT": str(original_directory),
        "openin_any": "p",
        "openout_any": "p",
    }:
        raise ValueError("reference private source environment differs")
    if raw["runtime_before"] != raw["runtime_after"] or set(raw["runtime_before"]) != {
        "xelatex",
        "xdvipdfmx",
        "kpsewhich",
    }:
        raise ValueError("reference runtime changed")
    records = raw["tool_artifacts"]
    if len(records) != 10 or any(
        set(row) != {"artifact", "exit_code", "original_exit_code"}
        or type(row["exit_code"]) is not int
        or row["exit_code"] != 0
        or type(row["original_exit_code"]) is not int
        or row["original_exit_code"] != 0
        for row in records
    ):
        raise ValueError("reference requires every original version/discovery/final process")
    for index, name in enumerate(("xelatex", "xdvipdfmx", "kpsewhich")):
        process = tool(records[index]["artifact"], f"reference-{name}-version", name, ["--version"])
        if raw["runtime_before"][name] != {
            "path": process["executable"],
            "sha256": process["executable_sha256"],
            "version": process["stdout"],
        }:
            raise ValueError("reference runtime version differs from original custody")
    roots: list[PurePath] = []
    queries = (
        ("reference-texmfdist", ["--var-value=TEXMFDIST"]),
        ("reference-texmfroot", ["--var-value=TEXMFROOT"]),
        ("reference-texmf-trees", [TEXMF_TREES_ARGUMENT]),
    )
    for index, (purpose, query) in enumerate(queries, 3):
        process = tool(records[index]["artifact"], purpose, "kpsewhich", query)
        if (
            process["executable"] != raw["runtime_before"]["kpsewhich"]["path"]
            or process["executable_sha256"] != raw["runtime_before"]["kpsewhich"]["sha256"]
        ):
            raise ValueError("reference distribution query runtime changed")
        if query != [TEXMF_TREES_ARGUMENT]:
            roots.append(_absolute(process["stdout"].strip()))
            continue
        searched = tuple(_absolute(item) for item in process["stdout"].strip().split(":"))
        installation = roots[1]
        validate_texmf_installation(installation, _absolute(raw["runtime_before"]["kpsewhich"]["path"]))
        roots = list(admitted_texmf_roots(roots[0], roots[1], searched, original_directory))
    compiler_args = [
        "-fmt=xelatex",
        "-no-pdf",
        "-no-shell-escape",
        "-recorder",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-jobname=reference",
        f"-output-directory={original_directory}",
        producer_path(raw["source"]["path"]),
    ]
    backend_args = [
        "--kpathsea-debug=4",
        "-vv",
        "-o",
        producer_path(raw["pdf"]["path"]),
        producer_path(directory + "/reference.xdv"),
    ]
    if raw["consumed_backend_path"] != directory + "/reference.xdv" or raw["backend_input_policy"] != POLICY:
        raise ValueError("reference consumed backend input/policy differs")
    dependencies = raw["dependencies_before"]
    if dependencies != raw["dependencies_after"] or not 0 < len(dependencies) <= 2048:
        raise ValueError("reference original dependency closure changed")
    paths = [row["original_path"] for row in dependencies]
    if paths != sorted(set(paths)) or sum(row["size_bytes"] for row in dependencies) > 256 * 1024 * 1024:
        raise ValueError("reference dependency inventory is ambiguous or excessive")
    for index, row in enumerate(dependencies):
        if set(row) != {"original_path", "resolved_path", "size_bytes", "sha256", "artifact"}:
            raise ValueError("reference dependency fieldset differs")
        path, resolved = _absolute(row["original_path"]), _absolute(row["resolved_path"])
        if (
            not texmf_dependency_admitted(resolved, tuple(roots), installation)
            or type(row["size_bytes"]) is not int
            or not 0 < row["size_bytes"] <= 64 * 1024 * 1024
        ):
            raise ValueError("reference dependency escapes original public distribution")
        content = admitted(row["artifact"])
        if (
            len(content) != row["size_bytes"]
            or hashlib.sha256(content).hexdigest() != row["sha256"]
            or row["artifact"]["path"] != directory + f"/dependencies/{index:04d}-{resolved.name}.bin"
        ):
            raise ValueError("retained reference dependency differs from actual original observations")
    for offset, label in ((6, "discovery"), (8, "final")):
        compiler = tool(records[offset]["artifact"], f"reference-{label}-compiler", "xelatex", compiler_args)
        backend = tool(records[offset + 1]["artifact"], f"reference-{label}-backend", "xdvipdfmx", backend_args)
        for process, name in ((compiler, "xelatex"), (backend, "xdvipdfmx")):
            runtime = raw["runtime_before"][name]
            if process["executable"] != runtime["path"] or process["executable_sha256"] != runtime["sha256"]:
                raise ValueError("reference compiler/backend runtime identity changed")
        for role, filename in (("compiler_logs", f"{label}-compiler-log.bin"), ("backend_inputs", f"{label}-xdv.bin")):
            if raw[role][label]["path"] != directory + "/" + filename:
                raise ValueError("reference original log/XDV role binding differs")
        log = admitted(raw["compiler_logs"][label])
        if re.search(
            rb"Undefined control sequence|Missing character:|undefined references|undefined citations|LaTeX Error", log
        ) or not admitted(raw["backend_inputs"][label]):
            raise ValueError("reference compiler omitted complete final native inputs")
        if not log.startswith(b"This is XeTeX, Version") or b"Output written on " not in log:
            raise ValueError("reference original compiler log is incomplete")
        if raw[f"{label}_fls"]["path"] != directory + f"/{label}.fls":
            raise ValueError("reference original FLS role binding differs")
        fls = admitted(raw[f"{label}_fls"]).decode()
        if fls.splitlines()[0] != f"PWD {original_root}":
            raise ValueError("reference FLS original source working directory differs")
        opened = re.findall(
            r"kdebug:fopen\(([^,\n]+), r(?:b)?\) => (0x[0-9a-fA-F]+)", backend["stderr"] + backend["stdout"]
        )
        if not opened:
            raise ValueError("reference backend omitted actual file opens")
        external = set()
        observed = [line.removeprefix("INPUT ") for line in fls.splitlines() if line.startswith("INPUT ")]
        observed += [name for name, pointer in opened if int(pointer, 16)]
        for name in observed:
            path = PurePosixPath(name)
            path = path if path.is_absolute() else original_root / path
            if path.is_relative_to(original_directory):
                if path.suffix not in {".tex", ".aux", ".out", ".xdv"}:
                    raise ValueError("reference observed unsupported private input")
            else:
                external.add(str(path))
        if external != set(paths) or not any(
            PurePosixPath(path).suffix.lower() in {".otf", ".ttf", ".pfb", ".pk"} for path in external
        ):
            raise ValueError("reference FLS/backend actual dependency/font closure differs")
    pdf = admitted(raw["pdf"])
    rows = reference_math_glyphs(pdf, nodes)
    import pdfplumber

    vectors = []
    with pdfplumber.open(BytesIO(pdf)) as document:
        for number, page in enumerate(document.pages, 1):
            values = [
                {key: item[key] for key in ("x0", "x1", "top", "bottom", "linewidth") if key in item}
                for item in (*page.lines, *page.curves, *page.rects)
            ]
            if any(not math.isfinite(float(value)) for item in values for value in item.values()):
                raise ValueError("reference native vector geometry is not finite")
            vectors.append({"page": number, "objects": values})
    return {
        "schema_version": "template-native-scientific-reference-replay-v1",
        "source_nodes": [asdict(node) for node in nodes],
        "reference_glyphs": list(rows),
        "reference_vectors": vectors,
        "pdf_sha256": hashlib.sha256(pdf).hexdigest(),
        "blockers": list(inputs.blockers)
        + unsupported_source_blockers(ast_bytes)
        + [f"{node.identity}: source prose anchor placement requires independent full-source replay" for node in nodes]
        + [
            f"{node.identity}: table mathematical typography requires native cell geometry"
            for node in nodes
            if node.context == "table"
        ],
    }
