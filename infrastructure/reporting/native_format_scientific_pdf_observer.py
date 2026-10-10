"""Admitted scientific PDF occurrences and real portable source witness replay.

These observations strengthen conformance. Complete reference, generated-value,
semantic control and SDK/process admission remain explicit obligations; a source
ledger or matching document never grants release acceptance here.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference import PublicReference
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_format_content_contracts import (
    semantic_content_contract_from_ast,
)
from infrastructure.reporting.native_format_pdf_semantic_plan import (
    PDFSemanticPlan,
    compile_pdf_semantic_plan,
)
from infrastructure.reporting.native_format_pdf_source import (
    PDFSourceInputs,
    observe_pdf_source,
    pdf_source_inputs,
)
from infrastructure.reporting.native_format_pdf_source_replay import (
    replay_pdf_source_witness,
)
from infrastructure.reporting.native_format_pdf_source_witness import (
    inspect_pdf_source_witness,
)
from infrastructure.reporting.native_pitch_source_admission import SourceCorrespondence
from infrastructure.reporting.native_projection_contracts import (
    ProjectionSourceUnsupported,
)
from infrastructure.reporting.release_readiness_snapshot import (
    ArtifactSnapshot,
    SnapshotReader,
)

SCHEMA = "template-native-scientific-pdf-conformance-v1"
ENCLOSING_BLOCKERS = (
    "PDF consumed hydration/data/figure values require independently admitted "
    "original complete-source execution provenance",
    "PDF complete original source-reference/layout and supervised scientific negative controls "
    "require enclosing admission",
)


def _budget(deadline: float) -> None:
    if type(deadline) not in {int, float} or not math.isfinite(deadline):
        raise ValueError("scientific PDF requires its original finite deadline")
    if time.monotonic() >= deadline:
        raise TimeoutError("scientific PDF source observation exhausted its original deadline")


def require_scientific_pdf_source_context(
    root: Path,
    reader: SnapshotReader,
    reference: PublicReference | None,
    verify: SourceCorrespondence | None,
    *,
    deadline: float,
) -> tuple[PublicReference, SourceCorrespondence]:
    """Require the live immutable source capability, never receipt-derived DATA."""
    _budget(deadline)
    if reference is None or verify is None:
        raise ProjectionSourceUnsupported(
            "scientific PDF requires original immutable source and current-mirror admission"
        )
    if reader.root != root.resolve():
        raise ValueError("scientific PDF reader differs from its admitted current mirror")
    reference.verify_unchanged(deadline=deadline)
    verify(reference, root, reader, deadline)
    return reference, verify


def _original_sources(
    root: Path,
    scope: str,
    reader: SnapshotReader,
    reference: PublicReference,
    *,
    deadline: float,
) -> list[dict[str, str]]:
    from infrastructure.validation.publication.rendered_provenance import (
        build_rendered_provenance_receipt,
    )

    hydration = build_rendered_provenance_receipt(root, scope)
    rows = []
    for row in hydration.consumed_manuscript:
        _budget(deadline)
        if row.source_path is None:
            continue
        relative = (Path("projects") / scope / row.source_path).as_posix()
        current = reader.read(relative)
        if current.content != reference.read(relative) or current.sha256 != row.source_sha256:
            raise ValueError("scientific PDF original hydration source differs from admitted immutable bytes")
        rows.append({"path": relative, "sha256": current.sha256})
    relative = f"projects/{scope}/manuscript/config.yaml"
    config = reader.read(relative)
    if config.content != reference.read(relative):
        raise ValueError("scientific PDF source config differs from admitted immutable bytes")
    rows.append({"path": relative, "sha256": config.sha256})
    return rows


def compile_scientific_pdf_assets(
    root: Path,
    scope: str,
    inputs: PDFSourceInputs,
    plan: PDFSemanticPlan,
    reader: SnapshotReader,
    *,
    deadline: float,
) -> dict[str, dict[str, str]]:
    """Retain each image occurrence using the actual PDF writer path policy.

    Repeated image occurrences stay distinct even when they consume one file.
    Source-generated values still require the enclosing execution provenance.
    No candidate PDF stream chooses an original source asset.
    """
    manuscript = root / Path(inputs.config[0]).parent
    project = root / "projects" / scope
    from infrastructure.rendering._pdf_figure_paths import fix_figure_paths

    native_directory = project / "output/pdf"
    assets: dict[str, dict[str, str]] = {}
    total = 0
    for row in plan.occurrences:
        _budget(deadline)
        if row["kind"] != "Image":
            continue
        value = row["content"]
        if not isinstance(value, list) or len(value) != 3 or not isinstance(value[2], list) or len(value[2]) != 2:
            raise ValueError("scientific PDF source image schema is malformed")
        target = value[2][0]
        if not isinstance(target, str) or not target or "\x00" in target:
            raise ValueError("scientific PDF source image target is malformed")
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or parsed.path.startswith("/"):
            raise ProjectionSourceUnsupported(
                f"{row['identity']}: source image requires explicit local resource admission"
            )
        if any(character in target for character in "{}\\"):
            raise ProjectionSourceUnsupported(f"{row['identity']}: source image needs explicit TeX path admission")
        rewritten = fix_figure_paths(
            r"\includegraphics{" + unquote(parsed.path) + "}",
            manuscript,
            native_directory,
        )
        match = re.fullmatch(r"\\includegraphics\{([^}]+)\}", rewritten)
        if match is None:
            raise ProjectionSourceUnsupported(
                f"{row['identity']}: source image writer path cannot be independently bound"
            )
        candidate = Path(os.path.normpath(str(native_directory / match[1])))
        try:
            relative = candidate.relative_to(root).as_posix()
        except ValueError as error:
            raise ProjectionSourceUnsupported(
                f"{row['identity']}: source image writer resource escapes admission"
            ) from error
        if not candidate.is_file():
            raise ProjectionSourceUnsupported(f"{row['identity']}: source image has no admitted writer resource")
        selected = reader.read(relative)
        total += len(selected.content)
        if len(assets) >= 20_000 or total > 64 * 1024 * 1024:
            raise ValueError("scientific PDF source image occurrence closure exceeds its finite byte budget")
        assets[row["identity"]] = {"path": selected.relative, "sha256": selected.sha256}
    return assets


def scientific_pdf_source_observation(
    witness: dict[str, Any], source_blockers: list[str] | tuple[str, ...]
) -> dict[str, Any]:
    """Retain unresolved complete acceptance after scoped native observations."""
    blockers = [*source_blockers, *witness["blockers"], *ENCLOSING_BLOCKERS]
    findings = witness["findings"]
    return {
        "findings": findings,
        "blockers": blockers,
        "status": "fail" if findings else "blocked",
    }


def verify_scientific_pdf_reader_input(snapshot: ArtifactSnapshot, reader: SnapshotReader) -> None:
    """Check held actual input bytes/identity; this grants no launch authority."""
    held = reader.read(snapshot.relative)
    if held.path != snapshot.path or held.content != snapshot.content or not reader.unchanged():
        raise ValueError("scientific PDF reader source input changed before/after current launch")


def replay_current_scientific_pdf_ast(
    root: Path,
    markdown: ArtifactSnapshot,
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
) -> bytes:
    """Keep original input membership separate from the fresh Source-owned run."""
    from infrastructure.reporting.native_format_current_pandoc import current_pandoc_reader

    _budget(deadline)
    verify_scientific_pdf_reader_input(markdown, reader)
    with current_pandoc_reader(root, reader, env=env, deadline=deadline, purpose="scientific-pdf-ast") as current:
        source = current.runtime.freeze("source-only.md", markdown.content)
        arguments = [str(source), "--from=markdown+tex_math_dollars+raw_tex+header_attributes", "--to=json"]
        observed = current.tool("pandoc", arguments, "current-scientific-pdf-ast")
    verify_scientific_pdf_reader_input(markdown, reader)
    _budget(deadline)
    stdout = observed["stdout"]
    if not isinstance(stdout, str):
        raise ValueError("current scientific source parser omitted its exact raw text output")
    return stdout.encode()


def observe_scientific_pdf_source(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    snapshot: ArtifactSnapshot,
    raster: dict[str, Any],
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    source_reference: PublicReference | None,
    verify_source_correspondence: SourceCorrespondence | None,
) -> dict[str, Any]:
    """Parse actual source before inspecting exact every-page native bytes."""
    reference, verify = require_scientific_pdf_source_context(
        root, reader, source_reference, verify_source_correspondence, deadline=deadline
    )
    originals = _original_sources(root, scope, reader, reference, deadline=deadline)
    _, source = observe_pdf_source(
        root,
        directory,
        scope,
        artifact,
        reader,
        env=env,
        deadline=deadline,
        run_id=run_id,
    )
    inputs = pdf_source_inputs(root, directory, scope, artifact, reader)
    ast = reader.read(source["ast"]["path"])
    plan = compile_pdf_semantic_plan(artifact.id, inputs.sources, ast.content)
    assets = None
    try:
        assets = compile_scientific_pdf_assets(root, scope, inputs, plan, reader, deadline=deadline)
    except ProjectionSourceUnsupported as error:
        witness = {"findings": [], "blockers": [str(error)], "status": "blocked"}
    else:
        witness = inspect_pdf_source_witness(
            snapshot.content,
            tuple(reader.read(row["path"]).content for row in raster["rasters"]),
            plan,
            assets={identity: (row["path"], reader.read(row["path"]).content) for identity, row in assets.items()},
            deadline=deadline,
        )
    reference.verify_unchanged(deadline=deadline)
    verify(reference, root, reader, deadline)
    _budget(deadline)
    return {
        "schema_version": SCHEMA,
        "source": source,
        "original_source_inputs": originals,
        "semantic_plan": plan.to_dict(),
        "assets": assets,
        "witness": witness,
        "observation": scientific_pdf_source_observation(witness, inputs.blockers),
    }


def replay_scientific_pdf_source(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    snapshot: ArtifactSnapshot,
    raster: dict[str, Any],
    raw: dict[str, Any],
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
    env: dict[str, str],
    deadline: float,
    source_reference: PublicReference | None,
    verify_source_correspondence: SourceCorrespondence | None,
) -> dict[str, Any]:
    """Reparse source independently and replay every retained scoped witness."""
    from infrastructure.reporting.native_format_acceptance_validation import (
        _file,
        _tool,
    )
    from infrastructure.reporting.native_format_portable_custody import producer_path

    reference, verify = require_scientific_pdf_source_context(
        root, reader, source_reference, verify_source_correspondence, deadline=deadline
    )
    if (
        set(raw)
        != {
            "schema_version",
            "source",
            "original_source_inputs",
            "semantic_plan",
            "assets",
            "witness",
            "observation",
        }
        or raw["schema_version"] != SCHEMA
    ):
        raise ValueError("scientific PDF conformance fieldset differs")
    originals = _original_sources(root, scope, reader, reference, deadline=deadline)
    if raw["original_source_inputs"] != originals:
        raise ValueError("scientific PDF original immutable source input census differs")
    inputs = pdf_source_inputs(root, directory / "independent-source", scope, artifact, reader)
    source = raw["source"]
    if (
        set(source)
        != {
            "schema_version",
            "source_inputs",
            "markdown",
            "ast",
            "parser_artifact",
            "citation_engine",
            "blockers",
            "contract",
        }
        or source["schema_version"] != "template-native-pdf-source-only-v1"
    ):
        raise ValueError("scientific PDF actual source parser receipt differs")
    markdown, ast = _file(source["markdown"], reader), _file(source["ast"], reader)
    if (
        markdown.path != directory / "source-only.md"
        or markdown.content != inputs.content
        or ast.path != directory / "source-only.ast.json"
    ):
        raise ValueError("scientific PDF parser consumed different source bytes or attempt")
    arguments = [
        str(producer_path(custody, root, markdown.path)),
        "--from=markdown+tex_math_dollars+raw_tex+header_attributes",
        "--to=json",
    ]
    process = _tool(
        source["parser_artifact"],
        reader,
        run_id,
        "pandoc",
        "pdf-source-original-ast",
        arguments,
    )
    if process["stdout"].encode() != ast.content:
        raise ValueError("scientific PDF retained AST differs from actual original parser stdout")
    expected_inputs = [
        {"role": role, "path": path, "sha256": hashlib.sha256(content).hexdigest()}
        for role, values in (
            ("manuscript", inputs.sources),
            ("config", (inputs.config,)),
            ("preamble", (inputs.preamble,) if inputs.preamble else ()),
            ("bibliography", inputs.bibliographies),
            ("auxiliary", inputs.auxiliary),
        )
        for path, content in values
    ]
    contract = semantic_content_contract_from_ast(artifact.id, inputs.sources, ast.content)
    if (
        source["source_inputs"] != expected_inputs
        or source["contract"] != contract.to_dict()
        or source["blockers"] != list(inputs.blockers)
        or source["citation_engine"] != "natbib/plainnat (original AST has no citeproc)"
    ):
        raise ValueError("scientific PDF original source plan differs from current admitted bytes")
    independent_ast = replay_current_scientific_pdf_ast(root, markdown, reader, env=env, deadline=deadline)
    if independent_ast != ast.content:
        raise ValueError("scientific PDF actual independent original source parse differs")
    plan = compile_pdf_semantic_plan(artifact.id, inputs.sources, ast.content)
    if canonical_digest(raw["semantic_plan"]) != plan.digest:
        raise ValueError("scientific PDF complete original occurrence ledger differs")
    assets: dict[str, dict[str, str]] | None
    try:
        asset_bindings = compile_scientific_pdf_assets(root, scope, inputs, plan, reader, deadline=deadline)
    except ProjectionSourceUnsupported as error:
        assets = None
        witness = {"findings": [], "blockers": [str(error)], "status": "blocked"}
        if raw["witness"] != witness:
            raise ValueError("scientific PDF unsupported source asset obligation differs")
    else:
        assets = asset_bindings
        witness = replay_pdf_source_witness(
            raw["witness"],
            artifact_id=artifact.id,
            sources=inputs.sources,
            ast_bytes=ast.content,
            pdf={"path": snapshot.relative, "sha256": snapshot.sha256},
            rasters=tuple({"path": row["path"], "sha256": row["sha256"]} for row in raster["rasters"]),
            assets=asset_bindings,
            read_artifact=lambda binding: _file(binding, reader).content,
            deadline=deadline,
        )
    if raw["assets"] != assets or raw["observation"] != scientific_pdf_source_observation(witness, inputs.blockers):
        raise ValueError("scientific PDF source/native observations conceal unsupported obligations")
    reference.verify_unchanged(deadline=deadline)
    verify(reference, root, reader, deadline)
    _budget(deadline)
    return {
        "observation": scientific_pdf_source_observation(witness, inputs.blockers),
        "source_blockers": list(inputs.blockers),
        "witness": witness,
    }
