"""Source-only standalone TeX compilation with genuine every-page references.

An unrecorded writer and a fresh recorder reference must agree on every page.
This does not confer semantic/domain truth or native loaded-library admission.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.rendering.latex_utils import latex_compile_command
from infrastructure.reporting.native_format_acceptance_checks import audit_pdf_raster, parse_native_bytes
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact, create_private_native_directory
from infrastructure.reporting.native_format_acceptance_evidence import _tool
from infrastructure.reporting.native_format_pdf_reference_parity import inspect_pdf_reference_parity
from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime, dependency_identity, file_observation
from infrastructure.reporting.native_pdf_stream_bounds import preflight_pdf_streams
from infrastructure.reporting.native_tex_section_source import TexSectionInputs, freeze_tex_section_inputs
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

SCHEMA = "template-native-tex-section-reference-v1"
RESIDUALS = (
    "complete-independent-TeX-section-source-semantic-table-image-math-citation-and-scientific-control-predicates",
    "TeX-engine-and-native-backend-consuming-loaded-library-and-font-use-admission",
)


def _binding(snapshot: ArtifactSnapshot) -> dict[str, str]:
    return {"path": snapshot.relative, "sha256": snapshot.sha256}


def section_dependency_census(
    runtime: CitationRuntime, inputs: TexSectionInputs, output: Path
) -> tuple[dict[str, Any], ...]:
    """Read actual recorder INPUTs, refusing outside-source project references."""
    fls = runtime.read(output / (inputs.tex.stem + ".fls")).decode("utf-8")
    selected = {frozen.path: original for original, frozen, _ in inputs.files}
    external: dict[str, dict[str, Any]] = {}
    source = set()
    total = 0
    count = 0
    generated_suffixes = {".aux", ".out", ".toc", ".lof", ".lot", ".nav", ".snm", ".vrb"}
    for line in fls.splitlines():
        remaining(runtime.deadline)
        if not line.startswith("INPUT "):
            continue
        count += 1
        if count > 100000:
            raise ValueError("section recorder exceeds its finite input occurrence budget")
        path = Path(line[6:])
        path = (path if path.is_absolute() else inputs.tex.parent / path).resolve(strict=True)
        if path in selected:
            observed = file_observation(path)
            if observed["sha256"] != selected[path].sha256 or observed["bytes"] != len(selected[path].content):
                raise ValueError("section actual TeX input differs from held Source-selected bytes")
            source.add(path)
            continue
        if path.is_relative_to(output) and path.stem == inputs.tex.stem and path.suffix in generated_suffixes:
            continue
        if path.is_relative_to(runtime.root):
            raise ValueError("section TeX consumed an unheld project/generated reference input")
        if str(path) in external:
            continue
        row = file_observation(path)
        total += row["bytes"]
        if len(external) >= 10000 or total > 2 * 1024 * 1024 * 1024:
            raise ValueError("section actual dependency/font inventory exceeds native custody bounds")
        external[str(path)] = row
    if inputs.tex not in source or not external:
        raise ValueError("section actual recorder omitted selected TeX or external dependencies")
    return tuple(external[key] for key in sorted(external))


def _compile(runtime: CitationRuntime, inputs: TexSectionInputs, label: str, *, recorder: bool) -> Path:
    output = runtime.directory / label
    create_private_native_directory(runtime.root, output)
    command = latex_compile_command(inputs.tex, output, inputs.compiler, recorder=recorder)
    for ordinal in (1, 2):
        runtime.tool(
            command[0],
            command[1:],
            f"section-{label}-{ordinal:02d}",
            input_paths=(inputs.tex,),
            cwd=inputs.tex.parent,
            preserve_nominated_launcher=True,
        )
    log = runtime.read(output / (inputs.tex.stem + ".log")).decode("utf-8", errors="replace")
    if any(marker in log.lower() for marker in ("undefined", "missing character", "rerun to get")):
        raise ValueError("section independent two-pass writer retains unresolved native text/references")
    pdf = runtime.read(output / (inputs.tex.stem + ".pdf"))
    preflight_pdf_streams(pdf, deadline=runtime.deadline, max_objects=4_000_000)
    parse_native_bytes("pdf", pdf)
    return output


def _raster(
    root: Path, directory: Path, pdf: ArtifactSnapshot, *, env: dict[str, str], deadline: float, run_id: str
) -> dict[str, Any]:
    raster = audit_pdf_raster(
        root,
        directory,
        pdf,
        parse_native_bytes("pdf", pdf.content),
        env=env,
        deadline=deadline,
        run_id=run_id,
        ordinal=0,
    )
    return {
        "pdf": _binding(pdf),
        "rasters": [{"path": row["path"], "sha256": row["sha256"]} for row in raster["rasters"]],
        "raster": raster,
    }


def observe_tex_section_reference(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
) -> dict[str, str]:
    """Execute exact Source-selected section writer and independent native reference."""
    owner = current_native_producer_operation()
    if (
        owner is None
        or owner.source.bindings.current_root != root
        or reader.native_producer_operation is not owner
        or owner.deadline != deadline
        or not directory.is_relative_to(owner.stage_scope_directory(scope))
    ):
        raise ValueError("section reference needs its actual paired Source owner/scope/original clock")
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    create_private_native_directory(root, directory)
    runtime = CitationRuntime(root, directory / "compile", env=env, deadline=deadline, run_id=owner.run_id)
    inputs = freeze_tex_section_inputs(root, runtime.directory, scope, artifact, reader, env=env, deadline=deadline)
    discovery = _compile(runtime, inputs, "discovery", recorder=True)
    before = section_dependency_census(runtime, inputs, discovery)
    retained = []
    for ordinal, row in enumerate(before):
        remaining(deadline)
        path = Path(row["path"])
        content = read_bytes_confined(path.parent, path, max_bytes=512 * 1024 * 1024)
        if hashlib.sha256(content).hexdigest() != row["sha256"] or file_observation(path) != row:
            raise ValueError("section dependency changed before fresh reference compilation")
        frozen = runtime.freeze(f"section-dependency-{ordinal:06d}.input", content)
        retained.append({**row, "artifact": _binding(reader.read(frozen.relative_to(root).as_posix()))})
    baseline = _compile(runtime, inputs, "writer", recorder=False)
    reference = _compile(runtime, inputs, "reference", recorder=True)
    after = section_dependency_census(runtime, inputs, reference)
    if before != after or any(file_observation(Path(row["path"])) != row for row in before):
        raise ValueError("section dependency body or fresh recorder input census changed")
    references = {}
    for label, output in (("writer", baseline), ("reference", reference)):
        snapshot = reader.read((output / (inputs.tex.stem + ".pdf")).relative_to(root).as_posix())
        references[label] = _raster(root, output, snapshot, env=env, deadline=deadline, run_id=owner.run_id)
        references[label]["tex"] = _binding(reader.read(inputs.tex.relative_to(root).as_posix()))
        references[label]["aux"] = _binding(
            reader.read((output / (inputs.tex.stem + ".aux")).relative_to(root).as_posix())
        )
    parity = inspect_pdf_reference_parity(
        reader.read(references["writer"]["pdf"]["path"]).content,
        reader.read(references["reference"]["pdf"]["path"]).content,
        tuple(reader.read(row["path"]).content for row in references["writer"]["rasters"]),
        tuple(reader.read(row["path"]).content for row in references["reference"]["rasters"]),
        deadline=deadline,
    )
    for binding in runtime.tools:
        raw = reader.read(binding["path"]).json_object()
        _tool(binding, reader, owner.run_id, raw["tool"], raw["purpose"], raw["command"][1:])
    inputs.unchanged(reader, deadline=deadline)
    packet = {
        "schema_version": SCHEMA,
        "scope": scope,
        "artifact_id": artifact.id,
        "artifact_path": artifact.path,
        "run_id": owner.run_id,
        "sdk_context": json.loads(owner.source.descriptor(scope, deadline=deadline)),
        "compiler": inputs.compiler,
        "tex_input": _binding(reader.read(inputs.tex.relative_to(root).as_posix())),
        "inputs": inputs.manifest(),
        "tool_artifacts": runtime.tools,
        "dependency_custody": {
            "before": list(before),
            "after": list(after),
            "dependency_identity": dependency_identity(before),
            "retained": retained,
            "discovery_fls": _binding(
                reader.read((discovery / (inputs.tex.stem + ".fls")).relative_to(root).as_posix())
            ),
            "reference_fls": _binding(
                reader.read((reference / (inputs.tex.stem + ".fls")).relative_to(root).as_posix())
            ),
        },
        "references": references,
        "recorder_noninterference": parity,
        "blockers": list(RESIDUALS),
        "component_status": "fail" if parity["findings"] else "passed",
        "admission_status": "blocked",
    }
    binding = write_json(root, directory / "reference.json", packet)
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    remaining(deadline)
    return binding
