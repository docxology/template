"""HTML source witnesses subordinate to original immutable source admission.

No receipt, AST JSON or membership tuple constructs a PublicReference here.
The controller supplies the actual factory-admitted reference and verifier.
Hydration retains its existing complete execution-provenance obligation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference import PublicReference
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_format_html_fidelity_components import (
    compile_html_fidelity_source,
)
from infrastructure.reporting.native_format_html_source_adapter import (
    observe_html_source_witness,
    replay_html_source_witness,
)
from infrastructure.reporting.native_format_html_source_metadata import (
    remaining_seconds,
)
from infrastructure.reporting.native_format_html_source_styles import (
    compile_source_html_styles,
)
from infrastructure.reporting.native_format_content_contracts import (
    NativeContentContract,
)
from infrastructure.reporting.native_format_semantic_source import semantic_source_plan
from infrastructure.reporting.native_pitch_source_admission import SourceCorrespondence
from infrastructure.reporting.native_projection_contracts import (
    ProjectionSourceUnsupported,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.validation.publication.rendered_provenance import (
    build_rendered_provenance_receipt,
)


@dataclass(frozen=True)
class AdmittedHTMLSource:
    """In-memory operation input; receipt decoding cannot construct admission."""

    fidelity: dict[str, Any]
    metadata: dict[str, Any] | None
    reference: PublicReference
    verify_correspondence: SourceCorrespondence

    def close(self, root: Path, reader: SnapshotReader, *, deadline: float) -> None:
        remaining_seconds(deadline)
        self.reference.verify_unchanged(deadline=deadline)
        self.verify_correspondence(self.reference, root, reader, deadline)
        remaining_seconds(deadline)


def require_html_source_context(
    root: Path,
    reader: SnapshotReader,
    source_reference: PublicReference | None,
    verify_source_correspondence: SourceCorrespondence | None,
    *,
    deadline: float,
) -> tuple[PublicReference, SourceCorrespondence]:
    remaining_seconds(deadline)
    if source_reference is None or verify_source_correspondence is None:
        raise ProjectionSourceUnsupported(
            "HTML requires independently admitted immutable source and current-mirror correspondence"
        )
    if reader.root != root.resolve():
        raise ValueError("HTML current reader differs from its admitted mirror locator")
    source_reference.verify_unchanged(deadline=deadline)
    verify_source_correspondence(source_reference, root, reader, deadline)
    remaining_seconds(deadline)
    return source_reference, verify_source_correspondence


def _compile(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    reader: SnapshotReader,
    semantic: dict[str, Any],
    metadata: dict[str, Any] | None,
    reference: PublicReference,
    verify: SourceCorrespondence,
    *,
    deadline: float,
) -> AdmittedHTMLSource:
    """Bind retained actual parser ASTs after their genuine source replay."""
    from infrastructure.reporting.native_format_acceptance_validation import _file

    remaining_seconds(deadline)
    body = semantic["body"]
    original = _file(body["original_source"]["ast"], reader)
    projected = _file(body["ast"], reader)
    if original.path != directory / "semantic-original-ast.json" or projected.path != directory / "semantic-ast.json":
        raise ValueError("HTML original/projected AST belongs to another source attempt")
    _, sources, bibliographies = semantic_source_plan(root, scope, artifact, reader)
    # Pure-source correspondence authenticates the original templates. Current
    # hydration binds their actual consumed bytes, without declaring generated
    # values approved merely because a receipt or parser reports equality.
    hydration: Any = build_rendered_provenance_receipt(root, scope).to_dict()
    originals = []
    for row in hydration["consumed_manuscript"]:
        remaining_seconds(deadline)
        if row["source_path"] is None:
            continue
        relative = (Path("projects") / scope / row["source_path"]).as_posix()
        current = reader.read(relative)
        if current.content != reference.read(relative) or current.sha256 != row["source_sha256"]:
            raise ValueError("HTML original hydration source differs from factory-admitted immutable bytes")
        originals.append({"path": relative, "sha256": current.sha256})
    config_relative = f"projects/{scope}/manuscript/config.yaml"
    config = reader.read(config_relative)
    if config.content != reference.read(config_relative):
        raise ValueError("HTML source config differs from factory-admitted immutable bytes")
    for name, content in bibliographies:
        current = reader.read(name)
        if current.content != content:
            raise ValueError("HTML current bibliography changed after actual source parse")
    stylesheet = reader.read("infrastructure/rendering/ide_style.css")
    if stylesheet.content != reference.read(stylesheet.relative):
        raise ValueError("HTML actual renderer stylesheet differs from admitted immutable Source")
    source_styles = compile_source_html_styles(stylesheet.content, config.content)
    from infrastructure.rendering._web_font_assets import FONT_BODIES, LICENSE_SHA256

    assets = []
    for name, nominated in FONT_BODIES.items():
        relative = "infrastructure/rendering/assets/fonts/liberation/" + nominated["filename"]
        current = reader.read(relative)
        if current.content != reference.read(relative) or current.sha256 != nominated["sha256"]:
            raise ValueError("actual Source renderer font body differs from factory-admitted immutable bytes")
        assets.append(
            {
                "postscript_name": name,
                **{key: nominated[key] for key in ("family", "weight", "style", "sha256", "bytes")},
            }
        )
    license_relative = "infrastructure/rendering/assets/fonts/liberation/OFL.txt"
    license_snapshot = reader.read(license_relative)
    if license_snapshot.content != reference.read(license_relative) or license_snapshot.sha256 != LICENSE_SHA256:
        raise ValueError("actual Source renderer font license differs from its immutable distribution")
    source_styles.pop("digest")
    source_styles["physical_font_assets"] = assets
    source_styles["font_provider"] = "source-web-font-assets-v1"
    source_styles["digest"] = canonical_digest(source_styles)
    fidelity = compile_html_fidelity_source(
        (*sources, *bibliographies),
        original.content,
        projected.content,
        metadata_source=metadata,
        source_styles=source_styles,
        deadline=deadline,
    )
    fidelity.pop("digest")
    fidelity["source_admission"] = {
        "commit": reference.commit,
        "source_identity": reference.source_identity,
        "originals": originals,
        "source_config": {"path": config.relative, "sha256": config.sha256},
    }
    fidelity["blockers"].append(
        "HTML consumed hydration/data/figure values require independently admitted "
        "original complete-source execution provenance"
    )
    parser = _file(body["tool"]["artifact"], reader).json_object()
    if "--filter" in parser.get("command", []):
        from infrastructure.reporting.native_format_current_pandoc import CROSSREF_CUSTODY_BLOCKER

        fidelity["blockers"].append(CROSSREF_CUSTODY_BLOCKER)
    fidelity["digest"] = canonical_digest(fidelity)
    result = AdmittedHTMLSource(fidelity, metadata, reference, verify)
    result.close(root, reader, deadline=deadline)
    return result


def observe_admitted_html_source(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    source_reference: PublicReference | None,
    verify_source_correspondence: SourceCorrespondence | None,
) -> tuple[NativeContentContract, dict[str, Any], AdmittedHTMLSource]:
    reference, verify = require_html_source_context(
        root, reader, source_reference, verify_source_correspondence, deadline=deadline
    )
    contract, semantic, metadata = observe_html_source_witness(
        root,
        directory,
        scope,
        artifact,
        reader,
        env=env,
        deadline=deadline,
        run_id=run_id,
    )
    admitted = _compile(
        root,
        directory,
        scope,
        artifact,
        reader,
        semantic,
        metadata,
        reference,
        verify,
        deadline=deadline,
    )
    remaining_seconds(deadline)
    return contract, semantic, admitted


def replay_admitted_html_source(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    raw: dict[str, Any],
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
    deadline: float,
    env: dict[str, str],
    source_reference: PublicReference | None,
    verify_source_correspondence: SourceCorrespondence | None,
) -> tuple[NativeContentContract, AdmittedHTMLSource]:
    reference, verify = require_html_source_context(
        root, reader, source_reference, verify_source_correspondence, deadline=deadline
    )
    contract, metadata = replay_html_source_witness(
        root,
        directory,
        scope,
        artifact,
        raw,
        reader,
        run_id=run_id,
        custody=custody,
        deadline=deadline,
        env=env,
    )
    admitted = _compile(
        root,
        directory,
        scope,
        artifact,
        reader,
        raw,
        metadata,
        reference,
        verify,
        deadline=deadline,
    )
    remaining_seconds(deadline)
    return contract, admitted
