"""Source-owned native proof requirements; these types cannot grant admission."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest

from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact

OBLIGATION_IDS = (
    "pdf-visual-source-parity",
    "browser-layout",
    "native-docx-layout",
    "native-epub-reader",
    "projection-visual-oracle",
    "pitch-native-parity",
    "newspaper-print-oracle",
    "storybook-print-oracle",
)
SPEC_SCHEMA = "template-native-oracle-requirements-v1"


@dataclass(frozen=True)
class NativeControlTargetRequirement:
    """One exact Source-selected target and its required actual signed outcome.

    Target dictionaries retain the existing Office placement or Pitch page
    shapes. These are sealed requirement DATA, never runtime capabilities.
    """

    target: dict[str, Any]
    original_exit_code: int
    intended_diagnostic: str | None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.target, dict)
            or not self.target
            or not isinstance(self.target.get("artifact_id"), str)
            or not self.target["artifact_id"]
            or type(self.original_exit_code) is not int
            or self.original_exit_code != (0 if self.intended_diagnostic is None else 1)
            or self.intended_diagnostic is not None
            and (not isinstance(self.intended_diagnostic, str) or not self.intended_diagnostic)
        ):
            raise ValueError("Source target requirement lost its exact artifact/diagnostic/signed outcome")


@dataclass(frozen=True)
class OriginalControlRequirement:
    """A literal Source mutator and its required real original outcome."""

    name: str
    original_exit_code: int
    intended_diagnostic: str | None
    target_requirements: tuple[NativeControlTargetRequirement, ...] = ()


@dataclass(frozen=True)
class NativeOriginalRefusalRequirement:
    """The existing malformed-parser or invalid-tool original, kept separately."""

    name: str
    format: str
    original_input: bytes
    original_exit_code: int
    original_executor: str
    result_predicate: str


@dataclass(frozen=True)
class NativeControlSuiteRequirement:
    """The whole selector, never a caller-selected subset of control names."""

    id: str
    source_selector: str
    result_predicate: str | None
    controls: tuple[OriginalControlRequirement, ...]
    target_mode: str
    related_artifact_ids: tuple[str, ...]
    target_selector: str
    original_executor: str = "existing-Source-supervisor"

    def __post_init__(self) -> None:
        names = tuple(row.name for row in self.controls)
        if not names or names[0] != "baseline" or len(set(names)) != len(names):
            raise ValueError("native suite needs a well-formed unique baseline-first requirement roster")
        for row in self.controls:
            if type(row.original_exit_code) is not int:
                raise ValueError("native control requirements need an actual signed integer exit")
            if not row.target_requirements:
                if row.original_exit_code != (0 if row.intended_diagnostic is None else 1):
                    raise ValueError("native control requirements cannot relabel original exits")
            elif (
                any(target.original_exit_code != row.original_exit_code for target in row.target_requirements)
                or row.intended_diagnostic is not None
                and any(target.intended_diagnostic != row.intended_diagnostic for target in row.target_requirements)
                or len({canonical_digest(target.target) for target in row.target_requirements})
                != len(row.target_requirements)
                or any(
                    target.target["artifact_id"] not in self.related_artifact_ids for target in row.target_requirements
                )
            ):
                raise ValueError(
                    "native control target requirements changed signed exits/diagnostics or complete roles"
                )
        if not all((self.id, self.source_selector, self.target_mode, self.target_selector, self.original_executor)):
            raise ValueError("native suite omitted its Source selector or original execution role")
        if not self.related_artifact_ids or len(set(self.related_artifact_ids)) != len(self.related_artifact_ids):
            raise ValueError("native suite omitted or repeated its associated Source artifact roles")


@dataclass(frozen=True)
class NativeDiagramApplicability:
    """Scope projection of the genuine complete Source census, including absence.

    This data is a requirement binding. Only a fresh complete Source census can
    establish applicability; constructing or decoding it cannot prove absence.
    """

    scope: str
    complete_census_digest: str
    ordered_document_inputs: tuple[tuple[str, str], ...]
    occurrence_identities: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.scope or not self.complete_census_digest or not self.ordered_document_inputs:
            raise ValueError("diagram applicability omitted complete held Source census inputs")
        if len(set(self.occurrence_identities)) != len(self.occurrence_identities):
            raise ValueError("diagram applicability repeated an exact Source occurrence")


@dataclass(frozen=True)
class NativeWitnessRequirement:
    """Every current source-derived artifact needs complete actual witness axes."""

    artifact_id: str
    source_adapter: str
    coverage_axes: tuple[str, ...]


@dataclass(frozen=True)
class NativeOracleObligation:
    """One existing declaration with complete artifacts, controls and known gaps."""

    id: str
    artifact_ids: tuple[str, ...]
    witnesses: tuple[NativeWitnessRequirement, ...]
    control_suite_ids: tuple[str, ...]
    missing_implementations: tuple[str, ...]


@dataclass(frozen=True)
class NativeOracleSpecification:
    """Compiled requirements only; no pass, fulfilled or release-authority field."""

    schema: str
    scope: str
    declared_formats: tuple[str, ...]
    source_binding: tuple[str, str]
    artifact_contract_digest: str
    artifacts: tuple[NativeArtifact, ...]
    diagram_applicability: NativeDiagramApplicability | None
    original_refusals: tuple[NativeOriginalRefusalRequirement, ...]
    suites: tuple[NativeControlSuiteRequirement, ...]
    obligations: tuple[NativeOracleObligation, ...]
    replay_preconditions: tuple[str, ...]

    def data(self) -> dict[str, object]:
        """Seal every requirement byte; decoding DATA never creates authority.

        Exact malformed original inputs are hexadecimal to preserve their full
        bytes in JSON. No witness/control outcomes or fulfilled IDs exist here.
        The reader must freshly compile the entire genuine Source graph.
        """
        body = asdict(self)
        for refusal in body["original_refusals"]:
            refusal["original_input_hex"] = refusal.pop("original_input").hex()
        body = json.loads(json.dumps(body))
        return {**body, "content_digest": canonical_digest(body)}

    def __post_init__(self) -> None:
        artifact_ids = tuple(row.id for row in self.artifacts)
        suite_ids = tuple(row.id for row in self.suites)
        obligation_ids = tuple(row.id for row in self.obligations)
        artifact_paths = tuple(row.path for row in self.artifacts)
        if (
            self.schema != SPEC_SCHEMA
            or not artifact_ids
            or len(set(artifact_ids)) != len(artifact_ids)
            or len(set(artifact_paths)) != len(artifact_paths)
        ):
            raise ValueError("native requirements need a complete unique Source artifact contract")
        if len(set(suite_ids)) != len(suite_ids) or len(set(obligation_ids)) != len(obligation_ids):
            raise ValueError("native proof requirements repeat a suite or declaration")
        refusal_names = tuple(row.name for row in self.original_refusals)
        if not refusal_names or len(set(refusal_names)) != len(refusal_names):
            raise ValueError("native requirements omitted or repeated original conformance refusals")
        if any(
            row.original_exit_code != 1
            or not row.original_input
            or not row.original_executor
            or not row.result_predicate
            for row in self.original_refusals
        ):
            raise ValueError("native conformance refusal requirement lost its real original execution contract")
        if set(obligation_ids) - set(OBLIGATION_IDS):
            raise ValueError("native proof requirements invent a declaration identity")
        used: set[str] = set()
        for obligation in self.obligations:
            if not obligation.artifact_ids or len(set(obligation.artifact_ids)) != len(obligation.artifact_ids):
                raise ValueError("native declaration omitted or repeated Source artifact coverage")
            if tuple(row.artifact_id for row in obligation.witnesses) != obligation.artifact_ids:
                raise ValueError("native declaration omitted or reordered complete witness coverage")
            if not obligation.control_suite_ids or len(set(obligation.control_suite_ids)) != len(
                obligation.control_suite_ids
            ):
                raise ValueError("native declaration omitted or repeated required control suites")
            if any(
                not row.source_adapter or not row.coverage_axes or len(set(row.coverage_axes)) != len(row.coverage_axes)
                for row in obligation.witnesses
            ):
                raise ValueError("native witness omitted or repeated its Source adapter/coverage axes")
            if set(obligation.artifact_ids) - set(artifact_ids) or set(obligation.control_suite_ids) - set(suite_ids):
                raise ValueError("native declaration names foreign artifacts or control suites")
            used.update(obligation.artifact_ids)
        if used != set(artifact_ids):
            raise ValueError("native requirements leave a Source artifact without its declaration")
        for suite in self.suites:
            if set(suite.related_artifact_ids) - set(artifact_ids):
                raise ValueError("native control selector names a foreign artifact")
        required_suites = {item for obligation in self.obligations for item in obligation.control_suite_ids}
        if required_suites != set(suite_ids):
            raise ValueError("native requirement graph contains an unused or missing control suite")
