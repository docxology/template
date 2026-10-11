"""Complete literal control declarations from their existing Source owners."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_oracle_obligation_spec import (
    NativeControlSuiteRequirement,
    NativeControlTargetRequirement,
    NativeOriginalRefusalRequirement,
    OriginalControlRequirement,
)


def _suite(
    name: str,
    selector: str,
    predicate: str | None,
    codes: Mapping[str, str | None],
    targets: tuple[str, ...],
    *,
    mode: str = "invented-source-fixture",
    target_selector: str = "Source-literal-invented-control-fixture",
    original_executor: str = "existing-Source-supervisor",
) -> NativeControlSuiteRequirement:
    controls = tuple(OriginalControlRequirement(key, 0 if code is None else 1, code) for key, code in codes.items())
    return NativeControlSuiteRequirement(
        name, selector, predicate, controls, mode, targets, target_selector, original_executor
    )


def control_requirements(
    kinds: frozenset[str],
    artifacts: tuple[NativeArtifact, ...],
    *,
    declared_formats: tuple[str, ...],
    manuscript_slide_pdfs: tuple[str, ...],
    diagram_occurrences: tuple[str, ...],
    print_scope: str | None,
    pitch_plan: dict[str, Any] | None = None,
) -> tuple[NativeControlSuiteRequirement, ...]:
    """Declare whole suites for actual Source artifacts, including configured extras.

    This does not invoke a witness or make any control outcome observation.
    Literal selectors stay in their original modules; no names are caller inputs.
    """
    result = []

    def ids(*selected: str) -> tuple[str, ...]:
        return tuple(row.id for row in artifacts if row.format in selected)

    if "pdf" in kinds:
        from infrastructure.reporting.native_format_pdf_oracles import PDF_CONTROL_CODES

        result.append(
            _suite(
                "pdf",
                "native_format_pdf_oracles.PDF_CONTROL_CODES",
                "native_format_pdf_oracles.require_pdf_control_result",
                PDF_CONTROL_CODES,
                ids("pdf"),
            )
        )
    if "html" in kinds:
        from infrastructure.reporting.native_format_browser_oracles import BROWSER_CONTROL_CODES
        from infrastructure.reporting.native_format_browser_semantic_controls import SEMANTIC_CONTROL_CODES

        result.extend(
            (
                _suite(
                    "html",
                    "native_format_browser_oracles.BROWSER_CONTROL_CODES",
                    "native_format_browser_oracles.require_browser_control_result",
                    BROWSER_CONTROL_CODES,
                    ids("html"),
                ),
                _suite(
                    "html_semantic",
                    "native_format_browser_semantic_controls.SEMANTIC_CONTROL_CODES",
                    "native_format_browser_semantic_controls.require_semantic_control_result",
                    SEMANTIC_CONTROL_CODES,
                    ids("html"),
                ),
            )
        )
    for kind in ("docx", "epub"):
        if kind not in kinds:
            continue
        from infrastructure.reporting.native_office_scientific_controls import CONTROL_CODES

        if kind == "docx":
            from infrastructure.reporting.native_office_observer import OFFICE_CONTROL_CODES

            codes, selector = OFFICE_CONTROL_CODES, "native_office_observer.OFFICE_CONTROL_CODES"
        else:
            from infrastructure.reporting.native_epub_observer import EPUB_CONTROL_CODES

            codes, selector = EPUB_CONTROL_CODES, "native_epub_observer.EPUB_CONTROL_CODES"
        result.append(_suite(kind, selector, "native_format_control_replay.validate_format_controls", codes, ids(kind)))
        result.append(
            _suite(
                kind + "_scientific",
                "native_office_scientific_controls.CONTROL_CODES",
                "native_office_scientific_replay.replay_office_scientific_controls",
                CONTROL_CODES,
                ids(kind),
            )
        )
        if diagram_occurrences:
            from infrastructure.reporting.native_office_diagram_controls import CONTROL_CODES as DIAGRAM_CODES

            result.append(
                _suite(
                    kind + "_diagrams",
                    "native_office_diagram_controls.CONTROL_CODES+original-baseline",
                    "native_office_diagram_controls.replay_office_diagram_control",
                    {"baseline": None, **DIAGRAM_CODES},
                    ids(kind),
                    mode="complete-source-census-and-every-native-placement",
                    target_selector="native_office_diagram_census.select_diagram_control_targets",
                    original_executor="native_office_diagram_controls.run_office_diagram_control",
                )
            )
    if "slides" in declared_formats or "pptx" in kinds:
        from infrastructure.reporting.native_office_observer import PPTX_CONTROL_CODES
        from infrastructure.reporting.native_projection_checks import PROJECTION_CONTROL_CODES

        projection_roles = tuple(
            row.id
            for row in artifacts
            if row.format == "pptx"
            or row.id in manuscript_slide_pdfs
            or row.id.startswith("pitch:")
            and row.format == "pdf"
        )
        result.extend(
            (
                _suite(
                    "projection",
                    "native_projection_checks.PROJECTION_CONTROL_CODES",
                    "native_format_control_replay.validate_format_controls",
                    PROJECTION_CONTROL_CODES,
                    projection_roles,
                    mode="shared-invented-capability-fixture-for-projection-roles",
                ),
                _suite(
                    "pptx",
                    "native_office_observer.PPTX_CONTROL_CODES",
                    "native_format_control_replay.validate_format_controls",
                    PPTX_CONTROL_CODES,
                    projection_roles,
                    mode="shared-invented-capability-fixture-for-projection-roles",
                ),
            )
        )
    if manuscript_slide_pdfs:
        from infrastructure.reporting.native_slide_controls import SLIDE_CONTROL_CODES

        result.append(
            _suite(
                "manuscript_slides",
                "native_slide_controls.SLIDE_CONTROL_CODES",
                None,
                SLIDE_CONTROL_CODES,
                manuscript_slide_pdfs,
                mode="invented-two-page-pdf-source-fixture",
                target_selector="native_slide_controls.actual-source-fixture-pdf",
                original_executor="native_slide_controls.run_slide_source_control",
            )
        )
    if print_scope is not None:
        from infrastructure.reporting.native_print_artifact_controls import print_control_names
        from infrastructure.reporting.native_print_artifact_observer import FINDING

        names = print_control_names(print_scope)
        codes = {name: None if name == "baseline" else FINDING for name in names}
        result.append(
            _suite(
                "configured_print",
                "native_print_artifact_controls.print_control_names",
                "native_print_control_replay.validate_print_controls",
                codes,
                tuple(row.id for row in artifacts if row.id.startswith(("newspaper:", "storybook:"))),
                mode="configured-artifacts-source-selected-per-mutator",
                target_selector="native_print_artifact_controls.selected_control_artifacts",
            )
        )
    if pitch_plan is not None:
        from infrastructure.reporting.native_pitch_control_plan import CONTROL_NAMES, IDS, SCOPE

        pitch_ids = tuple(row.id for row in artifacts if row.id.startswith("pitch:"))
        if (
            pitch_plan["schema_version"] != "template-native-pitch-control-plan-v1"
            or pitch_plan["scope"] != SCOPE
            or pitch_ids != IDS
            or [row["artifact"]["id"] for row in pitch_plan["artifacts"]] != list(pitch_ids)
            or tuple(pitch_plan["targets"]) != CONTROL_NAMES
            or pitch_plan["active_controls"] != [name for name in CONTROL_NAMES if pitch_plan["targets"][name]]
        ):
            raise ValueError("configured Pitch requirement lost the entire Source pair/page selector")
        selected_controls = []
        for name in pitch_plan["active_controls"]:
            selected = tuple(
                NativeControlTargetRequirement(
                    target, 0 if target["intended_diagnostic"] is None else 1, target["intended_diagnostic"]
                )
                for target in pitch_plan["targets"][name]
            )
            target_diagnostics = {target.intended_diagnostic for target in selected}
            diagnostic = next(iter(target_diagnostics)) if len(target_diagnostics) == 1 else None
            selected_controls.append(
                OriginalControlRequirement(name, 0 if name == "baseline" else 1, diagnostic, selected)
            )
        result.append(
            NativeControlSuiteRequirement(
                "configured_pitch",
                "native_pitch_control_plan.CONTROL_NAMES+complete-Source-plan",
                "native_pitch_control_replay.replay_pitch_controls",
                tuple(selected_controls),
                "configured-source-pairs-and-every-applicable-page",
                pitch_ids,
                "native_pitch_control_plan.compile_pitch_source_control_plan",
                "native_pitch_control_supervisor.supervise_pitch_controls",
            )
        )
    return tuple(result)


def conformance_refusal_requirements(
    artifacts: tuple[NativeArtifact, ...],
) -> tuple[NativeOriginalRefusalRequirement, ...]:
    """Preserve the exact existing worker/reader parser and tool selection.

    Literal bytes and ordering mirror their existing Source-owned execution and
    validation branch. These requirements do not replace that actual branch.
    """
    predicate = "native_format_acceptance_validation._validate_native_conformance"
    parsers = tuple(
        NativeOriginalRefusalRequirement(
            "invalid-native-" + kind,
            kind,
            b"invented public malformed native artifact",
            1,
            "native_format_acceptance_worker.main(--control=" + kind + ")",
            predicate,
        )
        for kind in sorted({row.format for row in artifacts})
    )
    return parsers + (
        NativeOriginalRefusalRequirement(
            "invalid-pdf-tool",
            "pdf",
            b"invented public malformed PDF negative control\n",
            1,
            "native_tool_record(pdftoppm,purpose=invalid-pdf-tool)",
            predicate,
        ),
    )
