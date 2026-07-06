from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


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


class MadlibConfigError(ValueError):
    pass


@dataclass(frozen=True)
class SlotSpec:
    name: str
    category: str
    section: str
    count: int = 1


@dataclass(frozen=True)
class MethodStep:
    name: str
    action: str
    evidence: str
    output: str


@dataclass(frozen=True)
class EvaluationCriterion:
    name: str
    target: str
    evidence: str
    gate: str


@dataclass(frozen=True)
class FailureMode:
    name: str
    risk: str
    detection: str
    mitigation: str


@dataclass(frozen=True)
class DesignPrinciple:
    name: str
    rationale: str
    manuscript_effect: str


@dataclass(frozen=True)
class PipelinePhase:
    name: str
    input_artifact: str
    transformation: str
    output_artifact: str
    guard: str


@dataclass(frozen=True)
class QualityProbe:
    name: str
    question: str
    passing_signal: str
    artifact: str


@dataclass(frozen=True)
class AuthoringObligation:
    name: str
    obligation: str
    review_surface: str


@dataclass(frozen=True)
class VisualizationConfig:
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
        if not self.enabled:
            return ()
        return tuple(field for field in VISUALIZATION_FIELDS if field != "enabled" and bool(getattr(self, field)))


@dataclass(frozen=True)
class MadlibConfig:
    title: str
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
        return tuple(section for section in SECTION_KEYS if self.section_conditions.get(section, True))


def load_madlib_config(project_root: Path | str) -> MadlibConfig:
    root = Path(project_root)
    config_path = root / "manuscript" / "config.yaml"
    if not config_path.is_file():
        raise MadlibConfigError(f"Missing manuscript config: {config_path}")

    loaded = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise MadlibConfigError(f"Config must be a YAML mapping: {config_path}")

    paper = _mapping(loaded.get("paper"), "paper")
    madlib = _mapping(loaded.get("madlib"), "madlib")
    title = str(paper.get("title") or "Template Madlib").strip()
    seed = int(madlib.get("seed", 0))
    composition_depth = str(madlib.get("composition_depth", "standard")).strip().lower()
    if composition_depth not in COMPOSITION_DEPTHS:
        allowed = ", ".join(sorted(COMPOSITION_DEPTHS))
        raise MadlibConfigError(f"madlib.composition_depth must be one of: {allowed}")

    lexicon = _load_lexicon(madlib.get("lexicon"))
    slots = _load_slots(madlib.get("slots"))
    _validate_required_categories(lexicon)
    _validate_slot_categories(slots, lexicon)
    visualizations = _load_visualizations(madlib.get("visualizations"))
    explicit_paths, defaulted_paths = _configured_path_sets(madlib, lexicon, slots)

    conditions = {section: True for section in SECTION_KEYS}
    conditions.update(_load_section_conditions(madlib.get("section_conditions")))

    return MadlibConfig(
        title=title,
        seed=seed,
        composition_depth=composition_depth,
        hypothesis=str(
            madlib.get(
                "hypothesis",
                "Deterministic token injection can produce a complete manuscript without hidden prose edits.",
            )
        ).strip(),
        lexicon=lexicon,
        slots=slots,
        section_conditions=conditions,
        section_titles=_load_section_titles(madlib.get("section_titles")),
        narrative_moves=_load_narrative_moves(madlib.get("narrative_moves")),
        method_protocol=_load_method_protocol(madlib.get("method_protocol")),
        evaluation_criteria=_load_evaluation_criteria(madlib.get("evaluation_criteria")),
        failure_modes=_load_failure_modes(madlib.get("failure_modes")),
        design_principles=_load_design_principles(madlib.get("design_principles")),
        pipeline_phases=_load_pipeline_phases(madlib.get("pipeline_phases")),
        quality_probes=_load_quality_probes(madlib.get("quality_probes")),
        authoring_obligations=_load_authoring_obligations(madlib.get("authoring_obligations")),
        visualizations=visualizations,
        explicit_paths=explicit_paths,
        defaulted_paths=defaulted_paths,
        audit_rules=_load_optional_strings(
            madlib.get("audit_rules"),
            "madlib.audit_rules",
            (
                "Every manuscript placeholder must be generated by source code.",
                "Every generated token choice must carry category and config-key provenance.",
                "Every disabled section must resolve to an explicit disabled-section body.",
            ),
        ),
        contribution_claims=_load_optional_strings(
            madlib.get("contribution_claims"),
            "madlib.contribution_claims",
            (
                "A Mad Lib manuscript can remain reproducible when the lexicon is treated as data.",
                "Conditional IMRAD section bodies can be rendered without shared renderer changes.",
            ),
        ),
        config_path=config_path,
    )


def _mapping(value: Any, key: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise MadlibConfigError(f"{key} must be a mapping")
    return value


def _load_lexicon(value: Any) -> dict[str, tuple[str, ...]]:
    raw = _mapping(value, "madlib.lexicon")
    lexicon: dict[str, tuple[str, ...]] = {}
    for category, values in raw.items():
        name = str(category).strip()
        entries = _string_tuple(values, f"madlib.lexicon.{name}")
        if not entries:
            raise MadlibConfigError(f"madlib.lexicon.{name} must contain at least one token")
        lexicon[name] = entries
    return lexicon


def _load_slots(value: Any) -> tuple[SlotSpec, ...]:
    if not isinstance(value, list) or not value:
        raise MadlibConfigError("madlib.slots must be a non-empty list")
    slots: list[SlotSpec] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise MadlibConfigError(f"madlib.slots[{index}] must be a mapping")
        name = str(item.get("name", "")).strip()
        category = str(item.get("category", "")).strip()
        section = str(item.get("section", "methods")).strip()
        count = int(item.get("count", 1))
        if not name:
            raise MadlibConfigError(f"madlib.slots[{index}].name is required")
        if not category:
            raise MadlibConfigError(f"madlib.slots[{index}].category is required")
        if count < 1:
            raise MadlibConfigError(f"madlib.slots[{index}].count must be >= 1")
        if section not in SECTION_KEYS:
            raise MadlibConfigError(f"madlib.slots[{index}].section is unknown: {section}")
        slots.append(SlotSpec(name=name, category=category, section=section, count=count))
    return tuple(slots)


def _load_section_conditions(value: Any) -> dict[str, bool]:
    if value is None:
        return {}
    raw = _mapping(value, "madlib.section_conditions")
    conditions: dict[str, bool] = {}
    for section, enabled in raw.items():
        key = str(section).strip()
        if key not in SECTION_KEYS:
            raise MadlibConfigError(f"madlib.section_conditions contains unknown section: {key}")
        conditions[key] = bool(enabled)
    return conditions


def _load_section_titles(value: Any) -> dict[str, str]:
    titles = dict(DEFAULT_SECTION_TITLES)
    raw = _mapping(value, "madlib.section_titles")
    for section, title in raw.items():
        key = str(section).strip()
        if key not in SECTION_KEYS:
            raise MadlibConfigError(f"madlib.section_titles contains unknown section: {key}")
        clean = str(title).strip()
        if not clean:
            raise MadlibConfigError(f"madlib.section_titles.{key} must not be empty")
        titles[key] = clean
    return titles


def _load_narrative_moves(value: Any) -> dict[str, tuple[str, ...]]:
    moves = dict(DEFAULT_NARRATIVE_MOVES)
    raw = _mapping(value, "madlib.narrative_moves")
    for section, entries in raw.items():
        key = str(section).strip()
        if key not in SECTION_KEYS:
            raise MadlibConfigError(f"madlib.narrative_moves contains unknown section: {key}")
        parsed = _string_tuple(entries, f"madlib.narrative_moves.{key}")
        if not parsed:
            raise MadlibConfigError(f"madlib.narrative_moves.{key} must contain at least one move")
        moves[key] = parsed
    return moves


def _load_method_protocol(value: Any) -> tuple[MethodStep, ...]:
    if value is None:
        return (
            MethodStep(
                name="Load config",
                action="Parse manuscript/config.yaml and validate madlib schema blocks.",
                evidence="Config validation tests",
                output="MadlibConfig",
            ),
            MethodStep(
                name="Plan tokens",
                action="Use seeded digest selection over each slot and category list.",
                evidence="Token determinism tests",
                output="TokenPlan",
            ),
            MethodStep(
                name="Hydrate manuscript",
                action="Build section bodies and write output/manuscript from generated variables.",
                evidence="Unresolved-token tests",
                output="output/manuscript/*.md",
            ),
        )
    if not isinstance(value, list) or not value:
        raise MadlibConfigError("madlib.method_protocol must be a non-empty list")
    steps: list[MethodStep] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise MadlibConfigError(f"madlib.method_protocol[{index}] must be a mapping")
        step = MethodStep(
            name=str(item.get("name", "")).strip(),
            action=str(item.get("action", "")).strip(),
            evidence=str(item.get("evidence", "")).strip(),
            output=str(item.get("output", "")).strip(),
        )
        if not all((step.name, step.action, step.evidence, step.output)):
            raise MadlibConfigError(f"madlib.method_protocol[{index}] requires name, action, evidence, and output")
        steps.append(step)
    return tuple(steps)


def _load_evaluation_criteria(value: Any) -> tuple[EvaluationCriterion, ...]:
    if value is None:
        return (
            EvaluationCriterion(
                name="Placeholder resolution",
                target="No unresolved uppercase manuscript placeholders in output/manuscript.",
                evidence="tests/test_manuscript_variables.py",
                gate="pytest",
            ),
            EvaluationCriterion(
                name="Render readiness",
                target="PDF, HTML, slides, figure registry, evidence registry, and design overlays pass.",
                evidence="scripts/pipeline/stage_04_validate.py",
                gate="validation",
            ),
        )
    if not isinstance(value, list) or not value:
        raise MadlibConfigError("madlib.evaluation_criteria must be a non-empty list")
    criteria: list[EvaluationCriterion] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise MadlibConfigError(f"madlib.evaluation_criteria[{index}] must be a mapping")
        criterion = EvaluationCriterion(
            name=str(item.get("name", "")).strip(),
            target=str(item.get("target", "")).strip(),
            evidence=str(item.get("evidence", "")).strip(),
            gate=str(item.get("gate", "")).strip(),
        )
        if not all((criterion.name, criterion.target, criterion.evidence, criterion.gate)):
            raise MadlibConfigError(f"madlib.evaluation_criteria[{index}] requires name, target, evidence, and gate")
        criteria.append(criterion)
    return tuple(criteria)


def _load_failure_modes(value: Any) -> tuple[FailureMode, ...]:
    if value is None:
        return (
            FailureMode(
                name="Unresolved placeholder",
                risk="A source manuscript token is added without a generated variable.",
                detection="Hydrated manuscript scan for uppercase placeholders.",
                mitigation="Add variable generation and tests before rendering.",
            ),
            FailureMode(
                name="Overclaimed generated prose",
                risk="A generated sentence implies external validation or publication status.",
                detection="Claim ledger and validation review.",
                mitigation="Keep publication metadata blank until a real record exists.",
            ),
        )
    if not isinstance(value, list) or not value:
        raise MadlibConfigError("madlib.failure_modes must be a non-empty list")
    modes: list[FailureMode] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise MadlibConfigError(f"madlib.failure_modes[{index}] must be a mapping")
        mode = FailureMode(
            name=str(item.get("name", "")).strip(),
            risk=str(item.get("risk", "")).strip(),
            detection=str(item.get("detection", "")).strip(),
            mitigation=str(item.get("mitigation", "")).strip(),
        )
        if not all((mode.name, mode.risk, mode.detection, mode.mitigation)):
            raise MadlibConfigError(f"madlib.failure_modes[{index}] requires name, risk, detection, and mitigation")
        modes.append(mode)
    return tuple(modes)


def _load_design_principles(value: Any) -> tuple[DesignPrinciple, ...]:
    if value is None:
        return (
            DesignPrinciple(
                name="Configuration owns prose choices",
                rationale="Reviewers can inspect the declared language surface before generation.",
                manuscript_effect="Large-grain manuscript variables are generated from YAML and source code.",
            ),
            DesignPrinciple(
                name="Generated output is disposable",
                rationale="The durable artifact is the regeneration contract, not hand-edited output files.",
                manuscript_effect="Output Markdown, PDF, HTML, and slides are rebuilt from source inputs.",
            ),
        )
    if not isinstance(value, list) or not value:
        raise MadlibConfigError("madlib.design_principles must be a non-empty list")
    principles: list[DesignPrinciple] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise MadlibConfigError(f"madlib.design_principles[{index}] must be a mapping")
        principle = DesignPrinciple(
            name=str(item.get("name", "")).strip(),
            rationale=str(item.get("rationale", "")).strip(),
            manuscript_effect=str(item.get("manuscript_effect", "")).strip(),
        )
        if not all((principle.name, principle.rationale, principle.manuscript_effect)):
            raise MadlibConfigError(
                f"madlib.design_principles[{index}] requires name, rationale, and manuscript_effect"
            )
        principles.append(principle)
    return tuple(principles)


def _load_pipeline_phases(value: Any) -> tuple[PipelinePhase, ...]:
    if value is None:
        return (
            PipelinePhase(
                name="Schema parse",
                input_artifact="manuscript/config.yaml",
                transformation="Load and validate the madlib schema.",
                output_artifact="MadlibConfig",
                guard="config tests",
            ),
            PipelinePhase(
                name="Manuscript hydration",
                input_artifact="MadlibConfig and TokenPlan",
                transformation="Compose section variables and resolve Markdown shells.",
                output_artifact="output/manuscript",
                guard="placeholder scan",
            ),
        )
    if not isinstance(value, list) or not value:
        raise MadlibConfigError("madlib.pipeline_phases must be a non-empty list")
    phases: list[PipelinePhase] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise MadlibConfigError(f"madlib.pipeline_phases[{index}] must be a mapping")
        phase = PipelinePhase(
            name=str(item.get("name", "")).strip(),
            input_artifact=str(item.get("input_artifact", "")).strip(),
            transformation=str(item.get("transformation", "")).strip(),
            output_artifact=str(item.get("output_artifact", "")).strip(),
            guard=str(item.get("guard", "")).strip(),
        )
        if not all((phase.name, phase.input_artifact, phase.transformation, phase.output_artifact, phase.guard)):
            raise MadlibConfigError(
                "madlib.pipeline_phases"
                f"[{index}] requires name, input_artifact, transformation, output_artifact, and guard"
            )
        phases.append(phase)
    return tuple(phases)


def _load_quality_probes(value: Any) -> tuple[QualityProbe, ...]:
    if value is None:
        return (
            QualityProbe(
                name="Placeholder survival",
                question="Did any source token survive hydration?",
                passing_signal="No uppercase placeholders are found in generated manuscript files.",
                artifact="output/manuscript",
            ),
            QualityProbe(
                name="Evidence cleanliness",
                question="Do rendered claims stay supported by local artifacts?",
                passing_signal="The evidence registry validation passes.",
                artifact="output/reports/evidence_registry.json",
            ),
        )
    if not isinstance(value, list) or not value:
        raise MadlibConfigError("madlib.quality_probes must be a non-empty list")
    probes: list[QualityProbe] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise MadlibConfigError(f"madlib.quality_probes[{index}] must be a mapping")
        probe = QualityProbe(
            name=str(item.get("name", "")).strip(),
            question=str(item.get("question", "")).strip(),
            passing_signal=str(item.get("passing_signal", "")).strip(),
            artifact=str(item.get("artifact", "")).strip(),
        )
        if not all((probe.name, probe.question, probe.passing_signal, probe.artifact)):
            raise MadlibConfigError(
                f"madlib.quality_probes[{index}] requires name, question, passing_signal, and artifact"
            )
        probes.append(probe)
    return tuple(probes)


def _load_authoring_obligations(value: Any) -> tuple[AuthoringObligation, ...]:
    if value is None:
        return (
            AuthoringObligation(
                name="Review generated claims",
                obligation="Inspect hydrated manuscript bodies before copying outputs.",
                review_surface="output/manuscript and output/web",
            ),
            AuthoringObligation(
                name="Extend domain evidence",
                obligation="Add domain validators before making domain-specific claims.",
                review_surface="tests and data/claim_ledger.yaml",
            ),
        )
    if not isinstance(value, list) or not value:
        raise MadlibConfigError("madlib.authoring_obligations must be a non-empty list")
    obligations: list[AuthoringObligation] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise MadlibConfigError(f"madlib.authoring_obligations[{index}] must be a mapping")
        obligation = AuthoringObligation(
            name=str(item.get("name", "")).strip(),
            obligation=str(item.get("obligation", "")).strip(),
            review_surface=str(item.get("review_surface", "")).strip(),
        )
        if not all((obligation.name, obligation.obligation, obligation.review_surface)):
            raise MadlibConfigError(
                f"madlib.authoring_obligations[{index}] requires name, obligation, and review_surface"
            )
        obligations.append(obligation)
    return tuple(obligations)


def _load_visualizations(value: Any) -> VisualizationConfig:
    if value is None:
        return VisualizationConfig()
    raw = _mapping(value, "madlib.visualizations")
    unknown = sorted(str(key) for key in raw if str(key) not in VISUALIZATION_FIELDS)
    if unknown:
        raise MadlibConfigError(f"madlib.visualizations contains unknown field(s): {', '.join(unknown)}")
    kwargs: dict[str, bool] = {}
    for field in VISUALIZATION_FIELDS:
        raw_value = raw.get(field, True)
        if not isinstance(raw_value, bool):
            raise MadlibConfigError(f"madlib.visualizations.{field} must be a boolean")
        kwargs[field] = raw_value
    return VisualizationConfig(**kwargs)


def _load_optional_strings(value: Any, key: str, default: tuple[str, ...]) -> tuple[str, ...]:
    if value is None:
        return default
    entries = _string_tuple(value, key)
    if not entries:
        raise MadlibConfigError(f"{key} must contain at least one entry")
    return entries


def _validate_required_categories(lexicon: dict[str, tuple[str, ...]]) -> None:
    missing = [category for category in REQUIRED_LEXICON_CATEGORIES if category not in lexicon]
    if missing:
        raise MadlibConfigError(f"madlib.lexicon missing required categories: {', '.join(missing)}")


def _validate_slot_categories(slots: tuple[SlotSpec, ...], lexicon: dict[str, tuple[str, ...]]) -> None:
    missing = sorted({slot.category for slot in slots if slot.category not in lexicon})
    if missing:
        raise MadlibConfigError(f"madlib.slots reference missing lexicon categories: {', '.join(missing)}")


def _configured_path_sets(
    madlib: dict[str, Any],
    lexicon: dict[str, tuple[str, ...]],
    slots: tuple[SlotSpec, ...],
) -> tuple[frozenset[str], frozenset[str]]:
    explicit: set[str] = {"madlib"}
    defaulted: set[str] = set()

    for field in MADLIB_SCHEMA_FIELDS:
        _mark_path(madlib, field, explicit, defaulted)

    raw_conditions = _mapping(madlib.get("section_conditions"), "madlib.section_conditions")
    raw_titles = _mapping(madlib.get("section_titles"), "madlib.section_titles")
    raw_moves = _mapping(madlib.get("narrative_moves"), "madlib.narrative_moves")
    for section in SECTION_KEYS:
        _mark_nested_path(raw_conditions, section, f"madlib.section_conditions.{section}", explicit, defaulted)
        _mark_nested_path(raw_titles, section, f"madlib.section_titles.{section}", explicit, defaulted)
        _mark_nested_path(raw_moves, section, f"madlib.narrative_moves.{section}", explicit, defaulted)

    for category in sorted(lexicon):
        explicit.add(f"madlib.lexicon.{category}")

    raw_slot_value = madlib.get("slots")
    raw_slots: list[Any] = raw_slot_value if isinstance(raw_slot_value, list) else []
    raw_slots_by_name = {
        str(item.get("name", "")).strip(): item
        for item in raw_slots
        if isinstance(item, dict) and str(item.get("name", "")).strip()
    }
    for slot in slots:
        slot_path = f"madlib.slots.{slot.name}"
        explicit.add(slot_path)
        raw_slot = raw_slots_by_name.get(slot.name, {})
        for optional_field in ("section", "count"):
            _mark_nested_path(raw_slot, optional_field, f"{slot_path}.{optional_field}", explicit, defaulted)

    raw_visualizations = _mapping(madlib.get("visualizations"), "madlib.visualizations")
    for field in VISUALIZATION_FIELDS:
        _mark_nested_path(
            raw_visualizations,
            field,
            f"madlib.visualizations.{field}",
            explicit,
            defaulted,
        )

    return frozenset(sorted(explicit)), frozenset(sorted(defaulted))


def _mark_path(
    mapping: dict[str, Any],
    key: str,
    explicit: set[str],
    defaulted: set[str],
) -> None:
    path = f"madlib.{key}"
    if key in mapping:
        explicit.add(path)
    else:
        defaulted.add(path)


def _mark_nested_path(
    mapping: dict[str, Any],
    key: str,
    path: str,
    explicit: set[str],
    defaulted: set[str],
) -> None:
    if key in mapping:
        explicit.add(path)
    else:
        defaulted.add(path)


def _string_tuple(value: Any, key: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise MadlibConfigError(f"{key} must be a list")
    return tuple(str(item).strip() for item in value if str(item).strip())
