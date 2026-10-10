"""Compile complete Source requirements without observing or granting a pass."""

from __future__ import annotations

from pathlib import Path

import yaml

from infrastructure.project.public_capabilities import RENDER_FORMAT_NAMES
from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.rendering.config import RenderingConfig
from infrastructure.reporting.native_format_acceptance_contracts import contract_digest, native_artifact_contract
from infrastructure.reporting.native_mermaid_source_census import (
    SourceMermaidCensus,
    collect_current_source_mermaid_fences,
)
from infrastructure.reporting.native_oracle_control_requirements import (
    conformance_refusal_requirements,
    control_requirements,
)
from infrastructure.reporting.native_oracle_obligation_spec import (
    SPEC_SCHEMA,
    NativeDiagramApplicability,
    NativeOracleObligation,
    NativeOracleSpecification,
    NativeWitnessRequirement,
)
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

# These are requirement axes, never producer observations or claimed successes.
COMMON = (
    "externally-admitted-original-source-and-installed-sdk",
    "complete-original-core-plan-stage-inputs-and-actual-zero-exit-attempts",
    "same-native-run-analysis-domain-hydration-registry-asset-lineage",
    "independently-reconstructed-complete-source-occurrence-census",
    "unchanged-opening-and-closing-source-policy-provider-custody",
)
AXES = {
    "pdf": (
        "all-source-semantic-nodes-metadata-annotations",
        "every-native-page-glyph-font-crop-and-ink",
        "independent-source-only-full-reference-and-current-reader-reproduction",
    ),
    "html": (
        "original-and-projected-pandoc-asts-all-typed-occurrences",
        "source-css-assets-fonts-math-citations",
        "dom-reflow-and-pixels-at-both390-and1280-viewports",
        "tables-footnotes-order-targets-images-alpha-and-metadata",
    ),
    "docx": (
        "all-office-source-occurrence-ordinals-locations-payloads",
        "source-citeproc-package-survival",
        "native-reference-candidate-every-page-projection-and-source-image-cover-ink",
        "applicable-authenticated-mermaid-occurrences-geometry-and-complete-controls",
    ),
    "epub": (
        "all-office-source-occurrence-ordinals-locations-payloads",
        "source-citeproc-package-survival",
        "actual-epubcheck-frozen-engine-ordered-source-spine-and-native-reader-layout",
        "native-reference-candidate-every-page-projection-source-images-covers-and-diagrams",
    ),
    "pptx": (
        "complete-source-deck-layout-theme-fonts-notes-images-citations-qr-targets",
        "actual-package-and-native-conversion-every-page-source-reference-parity",
    ),
    "png": (
        "configured-source-page-roster-and-actual-Source-rgba-alpha-background-caption-policy",
        "complete-page-contact-order-and-print-scale-source-font-reference",
    ),
}
SLIDE_AXES = (
    "complete-enabled-source-section-profile-resources-bibliography",
    "all-source-and-resolved-occurrence-markers",
    "source-marked-writer-reference-and-candidate-full-page-rasters",
    "source-paint-noninterference",
)
PITCH_AXES = (
    "all-short-medium-long-pdf-pptx-companions",
    "source-model-and-package-layout-theme-notes-qr-citation-parity",
)
REPLAY_PRECONDITIONS = (
    "actual-externally-supplied-NativeReaderOperation-verified-by-require_native_operation",
    "externally-held-per-scope-NativeOriginalLaunch-validated-by-validate_original_joint_launch",
    "original-scope-nonce-command-specification-closure-and-worker-zero-bound-to-held-original",
    "same-original-control-nonces-typed-original-processes-exits-and-intended-diagnostics",
    "current-reader-source-sdk-font-tool-provider-decoder-budget-and-already-live-deadline",
    "fresh-actual-current-reader-reproduction-of-every-declared-witness-and-control",
    "existing-native-conformance-parser-controls-and-invalid-pdf-tool-originals-retained",
    "exact-artifact-suite-control-occurrence-page-rosters-no-missing-extra-duplicate-or-reordered-member",
    "no-unresolved-source-node-generated-value-lineage-or-implementation-gap",
    "complete-closing-source-input-provider-and-no-active-process-custody-within-original-budgets",
)
LINEAGE_GAP = "original-analysis-domain-hydration-registry-to-consumed-native-byte-lineage-and-portable-replay"


def _required_formats(scope: str, reader: SnapshotReader) -> tuple[str, ...]:
    """Use the same source configuration rule as required_profile, without env overrides."""
    config = yaml.safe_load(reader.read(f"projects/{scope}/manuscript/config.yaml").content)
    if not isinstance(config, dict):
        raise ValueError("native format requirements need the held Source configuration mapping")
    rendering = RenderingConfig.from_project_config(config, env={})
    return tuple(name for name in RENDER_FORMAT_NAMES if getattr(rendering, f"enable_{name}"))


def _diagram_applicability(census: SourceMermaidCensus, scope: str) -> NativeDiagramApplicability:
    """Bind actual complete Source discovery, including an independently derived scope absence."""
    inputs = tuple(items for selected_scope, items in census.document_inputs if selected_scope == scope)
    if len(inputs) != 1:
        raise ValueError("complete admitted diagram source census omitted or repeated this scope")
    occurrences = tuple(row.identity for row in census.occurrences if row.scope == scope)
    return NativeDiagramApplicability(scope, census.data()["content_digest"], inputs[0], occurrences)


def _adapter(id_: str, kind: str) -> str:
    if id_.startswith(("storybook:", "newspaper:")):
        return "configured-print-source-font-artifact-observation-and-replay"
    if id_.startswith("pitch:"):
        return "admitted-pitch-package-native-pdf-reference-and-complete-pair-replay"
    if id_.endswith((":slides", ":reveal")):
        return "manuscript-source-occurrence-profile-reference-and-native-replay"
    return {
        "pdf": "whole-scientific-source-pdf-reference-and-semantic-replay",
        "html": "admitted-source-browser-dom-reflow-pixel-and-semantic-replay",
        "docx": "office-full-source-package-and-native-reference-replay",
        "epub": "office-full-source-spine-epubcheck-and-native-reader-replay",
    }[kind]


def compile_native_oracle_obligations(
    root: Path,
    scope: str,
    formats: tuple[str, ...],
    reader: SnapshotReader,
    *,
    source: NativeSourceContext,
    deadline: float,
    source_census: list[SourceMermaidCensus] | None = None,
) -> NativeOracleSpecification:
    """Derive declarations from held Source/config, never a supplied output list.

    The caller supplies the real Source context and existing finite clock.
    This function creates no operation, original launch, timeout or admission.
    Original and reader integrations must separately perform the complete proof.
    """
    if not isinstance(source, NativeSourceContext) or root != reader.root or scope not in PUBLIC_PROJECT_NAMES:
        raise ValueError("native requirement compilation needs the genuine held Source/current-reader binding")
    remaining(deadline)
    source.verify_correspondence(source.reference, root, reader, deadline)
    required_formats = _required_formats(scope, reader)
    if formats != required_formats:
        raise ValueError("asserted native formats differ from the complete ordered held Source profile")
    artifacts = native_artifact_contract(root, scope, formats, reader)
    kinds = frozenset(row.format for row in artifacts)
    if kinds - set(AXES):
        raise ValueError("Source native contract contains an undeclared native proof kind")
    ids = tuple(row.id for row in artifacts)
    slides = tuple(id_ for id_ in ids if id_.endswith((":slides", ":reveal")))
    slide_pdfs = tuple(row.id for row in artifacts if row.format == "pdf" and row.id.endswith(":slides"))
    reveals = tuple(row.id for row in artifacts if row.format == "html" and row.id.endswith(":reveal"))
    pitch = tuple(id_ for id_ in ids if id_.startswith("pitch:"))
    print_scope = scope if scope in {"templates/template_newspaper", "templates/template_storybook"} else None
    census = collect_current_source_mermaid_fences(source, deadline=deadline)
    if source_census is not None:
        if source_census:
            raise ValueError("native Source census must be retained exactly once per compilation phase")
        source_census.append(census)
    diagrams = _diagram_applicability(census, scope) if kinds & {"docx", "epub"} else None
    diagram_occurrences = () if diagrams is None else diagrams.occurrence_identities
    pitch_plan = None
    if scope == "templates/template_pitch_deck":
        from infrastructure.reporting.native_pitch_control_plan import compile_pitch_source_control_plan

        pitch_plan, _ = compile_pitch_source_control_plan(
            root, reader, source=source, formats=formats, deadline=deadline
        )
    suites = control_requirements(
        kinds,
        artifacts,
        declared_formats=required_formats,
        manuscript_slide_pdfs=slide_pdfs,
        diagram_occurrences=diagram_occurrences,
        print_scope=print_scope,
        pitch_plan=pitch_plan,
    )
    suite_ids = {row.id for row in suites}
    witnesses = {
        row.id: NativeWitnessRequirement(
            row.id,
            _adapter(row.id, row.format),
            COMMON
            + AXES[row.format]
            + (SLIDE_AXES if row.id in slides else ())
            + (PITCH_AXES if row.id in pitch else ()),
        )
        for row in artifacts
    }
    obligations = []

    def add(id_: str, selected: tuple[str, ...], controls: tuple[str, ...], gaps: tuple[str, ...] = ()) -> None:
        if not selected or set(controls) - suite_ids:
            raise ValueError("native declaration omitted its Source artifacts or complete selected controls")
        obligations.append(
            NativeOracleObligation(
                id_, selected, tuple(witnesses[item] for item in selected), controls, (LINEAGE_GAP,) + gaps
            )
        )

    pdf = tuple(row.id for row in artifacts if row.format == "pdf")
    if pdf:
        scientific = any(id_ == "manuscript:pdf" or id_.startswith("section:") and id_.endswith(":pdf") for id_ in pdf)
        add(
            "pdf-visual-source-parity",
            pdf,
            ("pdf",),
            ("complete-whole-scientific-pdf-source-semantic-original-control-selection-and-replay",)
            if scientific
            else (),
        )
    html = tuple(row.id for row in artifacts if row.format == "html")
    if html:
        add("browser-layout", html, ("html", "html_semantic"))
    for kind, id_ in (("docx", "native-docx-layout"), ("epub", "native-epub-reader")):
        selected = tuple(row.id for row in artifacts if row.format == kind)
        if selected:
            controls = (kind, kind + "_scientific") + ((kind + "_diagrams",) if diagram_occurrences else ())
            gaps: tuple[str, ...] = (
                "complete-scoped-original-diagram-suite-supervision-and-current-reader-replay",
                "all-authenticated-source-diagram-occurrence-controls-beyond-first-native-placement",
            )
            add(id_, selected, controls, gaps if diagram_occurrences else ())
    if slides:
        gaps = ("complete-original-manuscript-slide-control-supervision-and-current-reader-suite-replay",)
        if reveals:
            gaps += ("complete-source-profile-Reveal-projection-specific-original-controls-and-reader-replay",)
        add("projection-visual-oracle", slides, ("projection", "pptx", "manuscript_slides"), gaps)
    if scope == "templates/template_pitch_deck":
        expected = tuple(f"pitch:{length}:{kind}" for length in ("short", "medium", "long") for kind in ("pdf", "pptx"))
        if pitch != expected:
            raise ValueError("full Pitch declaration requires all configured three PDF/PPTX companions")
        add(
            "pitch-native-parity",
            pitch,
            ("projection", "pptx", "configured_pitch"),
            ("complete-configured-all-pair-source-layout-theme-notes-citation-qr-native-original-controls-and-replay",),
        )
    if print_scope is not None:
        prefix = "newspaper:" if print_scope.endswith("template_newspaper") else "storybook:"
        selected = tuple(id_ for id_ in ids if id_.startswith(prefix))
        add(
            "newspaper-print-oracle" if prefix == "newspaper:" else "storybook-print-oracle",
            selected,
            ("configured_print",),
        )
    source.verify_correspondence(source.reference, root, reader, deadline)
    remaining(deadline)
    return NativeOracleSpecification(
        SPEC_SCHEMA,
        scope,
        formats,
        (source.bindings.expected_commit, source.bindings.expected_source_identity),
        contract_digest(artifacts),
        artifacts,
        diagrams,
        conformance_refusal_requirements(artifacts),
        suites,
        tuple(obligations),
        REPLAY_PRECONDITIONS,
    )


def require_exact_native_oracle_specification(
    asserted: NativeOracleSpecification,
    root: Path,
    scope: str,
    formats: tuple[str, ...],
    reader: SnapshotReader,
    *,
    source: NativeSourceContext,
    deadline: float,
) -> None:
    """Freshly reconstruct and compare the exact entire requirement graph.

    Scope/formats must come from the externally held original launch at the
    eventual reader boundary. This validates declaration custody only. It does
    not validate originals, controls, witnesses or resolve any obligation.
    """
    expected = compile_native_oracle_obligations(root, scope, formats, reader, source=source, deadline=deadline)
    if not isinstance(asserted, NativeOracleSpecification) or asserted != expected:
        raise ValueError("native requirements differ from fresh complete Source declaration/artifact/control graph")


def require_exact_native_oracle_specification_data(
    asserted: object,
    root: Path,
    scope: str,
    formats: tuple[str, ...],
    reader: SnapshotReader,
    *,
    source: NativeSourceContext,
    deadline: float,
) -> None:
    """Freshly compile and compare all serialized declarations, never admit them.

    There is deliberately no DATA-to-specification or DATA-to-operation factory.
    A recomputed digest alone cannot hide a changed selector or omitted member.
    """
    expected = compile_native_oracle_obligations(root, scope, formats, reader, source=source, deadline=deadline)
    if asserted != expected.data():
        raise ValueError("native requirement DATA differs from the entire fresh Source-owned specification")
