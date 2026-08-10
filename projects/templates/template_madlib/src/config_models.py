"""Typed configuration values and default schema data for the Madlib exemplar."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SECTION_KEYS: tuple[str, ...] = (
    "abstract",
    "introduction",
    "methods",
    "results",
    "discussion",
    "configuration",
    "evaluation",
    "reproducibility",
    "limitations",
    "scope",
    "authoring_contract",
)
DEFAULT_SECTION_TITLES: dict[str, str] = {
    "abstract": "Abstract",
    "introduction": "Introduction: Lexicon as Data and Manuscript as Build Artifact",
    "methods": "Methods: Source-Owned Token Injection and Conditional IMRAD Assembly",
    "results": "Results: Provenance, Density, and Resolved Manuscript Surface",
    "discussion": "Discussion: Accountability Boundaries for Generated Prose",
    "configuration": "Configuration: Schema-Controlled Lexicon, Slots, and Narrative Moves",
    "evaluation": "Evaluation: Gate Criteria, QA Probes, and Failure Discovery",
    "reproducibility": "Reproducibility: Seeded Regeneration and Artifact Trace",
    "limitations": "Limitations: Non-Claims, Misuse Modes, and Human Review",
    "scope": "Scope: Related Generators and Responsible Forking",
    "authoring_contract": "Authoring Contract: Human Review and Forking Obligations",
}
REQUIRED_LEXICON_CATEGORIES: tuple[str, ...] = ("adjectives", "nouns", "verbs")
COMPOSITION_DEPTHS: frozenset[str] = frozenset({"compact", "standard", "deep"})
MADLIB_CONFIG_SCHEMA_VERSION = 2
LEGACY_MADLIB_CONFIG_SCHEMA_VERSION = 1
VISUALIZATION_FIELDS: tuple[str, ...] = (
    "enabled",
    "configured_field_matrix",
    "section_configuration_heatmap",
    "field_origin_summary",
    "token_injection_flow",
    "section_token_allocation",
    "provenance_trace_map",
    "quality_gate_matrix",
)
MADLIB_SCHEMA_FIELDS: tuple[str, ...] = (
    "schema_version",
    "seed",
    "composition_depth",
    "hypothesis",
    "section_conditions",
    "section_titles",
    "narrative_moves",
    "method_protocol",
    "evaluation_criteria",
    "failure_modes",
    "design_principles",
    "pipeline_phases",
    "quality_probes",
    "authoring_obligations",
    "audit_rules",
    "contribution_claims",
    "lexicon",
    "slots",
    "visualizations",
)
DEFAULT_NARRATIVE_MOVES: dict[str, tuple[str, ...]] = {
    "abstract": (
        "state the problem",
        "name the deterministic intervention",
        "summarize the audit surface",
    ),
    "introduction": (
        "separate playful Mad Lib syntax from research claims",
        "identify drift between prose and source data",
        "frame configuration as an inspectable dataset",
    ),
    "methods": (
        "load and validate config",
        "expand slots deterministically",
        "compose conditional sections",
        "emit artifacts before rendering",
    ),
    "results": (
        "report token density",
        "show resolved sections",
        "bind every manuscript token to provenance",
    ),
    "discussion": (
        "bound the claim",
        "describe useful cases",
        "name misuse modes",
    ),
    "configuration": (
        "document schema ownership",
        "show switch behavior",
        "record counts from code",
    ),
    "evaluation": (
        "name readiness criteria",
        "connect criteria to artifacts",
        "separate local checks from publication readiness",
    ),
    "reproducibility": (
        "fix seed and config hash",
        "write machine-readable artifacts",
        "verify no unresolved placeholders remain",
    ),
    "limitations": (
        "state non-claims",
        "identify misuse modes",
        "preserve human review",
    ),
    "scope": (
        "distinguish generation from truth",
        "limit publication claims",
        "point to local evidence",
    ),
    "authoring_contract": (
        "state human responsibilities",
        "name fork obligations",
        "connect review to generated evidence",
    ),
}


@dataclass(frozen=True)
class SlotSpec:
    """One deterministic token slot declared by the manuscript config."""

    name: str
    category: str
    section: str
    count: int = 1


@dataclass(frozen=True)
class MethodStep:
    """One declared method step and its evidence/output contract."""

    name: str
    action: str
    evidence: str
    output: str


@dataclass(frozen=True)
class EvaluationCriterion:
    """One release or quality criterion from the configuration."""

    name: str
    target: str
    evidence: str
    gate: str


@dataclass(frozen=True)
class FailureMode:
    """One named failure mode and its detection/mitigation contract."""

    name: str
    risk: str
    detection: str
    mitigation: str


@dataclass(frozen=True)
class DesignPrinciple:
    """One documented design principle for generated prose."""

    name: str
    rationale: str
    manuscript_effect: str


@dataclass(frozen=True)
class PipelinePhase:
    """One input/transformation/output phase in the declared pipeline."""

    name: str
    input_artifact: str
    transformation: str
    output_artifact: str
    guard: str


@dataclass(frozen=True)
class QualityProbe:
    """One question, passing signal, and artifact for a quality probe."""

    name: str
    question: str
    passing_signal: str
    artifact: str


@dataclass(frozen=True)
class AuthoringObligation:
    """One human review obligation and its review surface."""

    name: str
    obligation: str
    review_surface: str


@dataclass(frozen=True)
class VisualizationConfig:
    """Boolean switches for the generated configuration figures."""

    enabled: bool = True
    configured_field_matrix: bool = True
    section_configuration_heatmap: bool = True
    field_origin_summary: bool = True
    token_injection_flow: bool = True
    section_token_allocation: bool = True
    provenance_trace_map: bool = True
    quality_gate_matrix: bool = True

    @property
    def enabled_flags(self) -> tuple[str, ...]:
        """Return enabled visualization fields in their schema order."""
        if not self.enabled:
            return ()
        return tuple(field for field in VISUALIZATION_FIELDS if field != "enabled" and bool(getattr(self, field)))


@dataclass(frozen=True)
class MadlibConfig:
    """Validated, source-bound configuration consumed by the exemplar."""

    title: str
    schema_version: int
    source_schema_version: int
    seed: int
    composition_depth: str
    hypothesis: str
    lexicon: dict[str, tuple[str, ...]]
    slots: tuple[SlotSpec, ...]
    section_conditions: dict[str, bool]
    section_titles: dict[str, str]
    narrative_moves: dict[str, tuple[str, ...]]
    method_protocol: tuple[MethodStep, ...]
    evaluation_criteria: tuple[EvaluationCriterion, ...]
    failure_modes: tuple[FailureMode, ...]
    design_principles: tuple[DesignPrinciple, ...]
    pipeline_phases: tuple[PipelinePhase, ...]
    quality_probes: tuple[QualityProbe, ...]
    authoring_obligations: tuple[AuthoringObligation, ...]
    visualizations: VisualizationConfig
    explicit_paths: frozenset[str]
    defaulted_paths: frozenset[str]
    audit_rules: tuple[str, ...]
    contribution_claims: tuple[str, ...]
    config_path: Path

    @property
    def enabled_sections(self) -> tuple[str, ...]:
        """Return configured sections whose condition is enabled."""
        return tuple(section for section in SECTION_KEYS if self.section_conditions.get(section, True))
