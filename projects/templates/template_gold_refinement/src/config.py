"""Mega-madlib configuration schema for the gold-refinement exemplar.

Validates ``manuscript/config.yaml`` → ``gold_refinement:`` block.
Provides a frozen dataclass with lexicon, slots, section conditions,
and refinement-stage metadata for deterministic token injection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REQUIRED_LEXICON_CATEGORIES: tuple[str, ...] = (
    "metallurgical_terms",
    "manuscript_terms",
    "purity_adjectives",
    "refinement_verbs",
)

SECTION_KEYS: tuple[str, ...] = (
    "abstract",
    "introduction",
    "methodology",
    "results",
    "discussion",
    "conclusion",
    "reproducibility",
    "scope",
    "evaluation",
    "authoring_contract",
)

DEFAULT_SECTION_TITLES: dict[str, str] = {
    "abstract": "Abstract",
    "introduction": "Introduction: Ore to Nine-Nines",
    "methodology": "Methodology: The Refinery Pipeline",
    "results": "Results: Purity Progression and Karat Grading",
    "discussion": "Discussion: Load-Bearing vs Rhetorical Analogy",
    "conclusion": "Conclusion: Certification and Forking",
    "reproducibility": "Reproducibility: Seeded Regeneration",
    "scope": "Scope: Related Work and Limitations",
    "evaluation": "Evaluation: QA Probes and Audit Rules",
    "authoring_contract": "Authoring Contract: Human Review and Forking Obligations",
}

COMPOSITION_DEPTHS: frozenset[str] = frozenset({"compact", "standard", "deep"})

GOLD_REFINEMENT_SCHEMA_FIELDS: tuple[str, ...] = (
    "seed",
    "composition_depth",
    "hypothesis",
    "section_conditions",
    "section_titles",
    "narrative_moves",
    "lexicon",
    "slots",
    "refinement_stages",
    "visualizations",
    "design_principles",
    "quality_probes",
    "failure_modes",
    "authoring_obligations",
    "contribution_claims",
    "pipeline_phases",
    "audit_rules",
)

DEFAULT_NARRATIVE_MOVES: dict[str, tuple[str, ...]] = {
    "abstract": (
        "state the refinement problem",
        "name the metallurgical analogy",
        "summarize the purity targets",
    ),
    "introduction": (
        "frame gold refining as a load-bearing pipeline",
        "distinguish analogy from mere rhetoric",
        "introduce the mega-madlib token engine",
    ),
    "methodology": (
        "declare the five refinery stages",
        "explain deterministic token selection",
        "connect purity to manuscript operations",
    ),
    "results": (
        "report purity progression across stages",
        "show karat grading for each stage",
        "bind every token to provenance",
    ),
    "discussion": (
        "bound the claim",
        "describe useful adaptation cases",
        "name misuse modes",
    ),
    "conclusion": (
        "summarize certification",
        "state fork responsibilities",
    ),
    "reproducibility": (
        "fix seed and config hash",
        "write machine-readable artifacts",
        "rerender through the pipeline",
    ),
    "scope": (
        "distinguish analogy from truth",
        "limit publication claims",
        "explain responsible forking",
    ),
    "evaluation": (
        "name readiness criteria",
        "connect criteria to artifacts",
        "make failure probes visible",
    ),
    "authoring_contract": (
        "state human responsibilities",
        "name fork obligations",
        "require domain validators before domain claims",
    ),
}


@dataclass(frozen=True)
class SlotSpec:
    """A slot declaration: name, category, count, target section."""

    name: str
    category: str
    count: int = 1
    section: str = "methodology"

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("slot name must not be empty")
        if not self.category:
            raise ValueError(f"slot '{self.name}' category must not be empty")
        if self.count < 1:
            raise ValueError(f"slot '{self.name}' count must be >= 1, got {self.count}")
        if self.section not in SECTION_KEYS:
            raise ValueError(f"slot '{self.name}' section must be one of {SECTION_KEYS}, got '{self.section}'")


@dataclass
class GoldRefinementConfig:
    """Parsed and validated ``gold_refinement:`` block from config.yaml."""

    seed: int = 431
    composition_depth: str = "deep"
    hypothesis: str = ""
    section_conditions: dict[str, bool] = field(default_factory=dict)
    section_titles: dict[str, str] = field(default_factory=dict)
    narrative_moves: dict[str, tuple[str, ...]] = field(default_factory=dict)
    lexicon: dict[str, tuple[str, ...]] = field(default_factory=dict)
    slots: tuple[SlotSpec, ...] = ()
    refinement_stages: list[dict[str, Any]] = field(default_factory=list)
    visualizations: dict[str, bool] = field(default_factory=dict)
    design_principles: list[dict[str, str]] = field(default_factory=list)
    quality_probes: list[dict[str, str]] = field(default_factory=list)
    failure_modes: list[dict[str, str]] = field(default_factory=list)
    authoring_obligations: list[dict[str, str]] = field(default_factory=list)
    contribution_claims: list[dict[str, str]] = field(default_factory=list)
    pipeline_phases: list[dict[str, str]] = field(default_factory=list)
    audit_rules: list[dict[str, str]] = field(default_factory=list)

    @property
    def enabled_sections(self) -> tuple[str, ...]:
        return tuple(k for k, v in self.section_conditions.items() if v)

    @property
    def disabled_sections(self) -> tuple[str, ...]:
        return tuple(k for k, v in self.section_conditions.items() if not v)

    @property
    def total_token_count(self) -> int:
        return sum(s.count for s in self.slots)


class GoldRefinementConfigError(ValueError):
    """Raised when the gold_refinement config block is invalid."""


def load_gold_refinement_config(
    project_root: Path | None = None,
) -> GoldRefinementConfig:
    """Load and validate the ``gold_refinement:`` block from config.yaml.

    Returns defaults when the file or block is missing.
    """
    root = project_root or Path(__file__).resolve().parent.parent
    config_path = root / "manuscript" / "config.yaml"
    if not config_path.exists():
        return _default_config()
    with config_path.open("r") as f:
        data = yaml.safe_load(f) or {}
    gr_block = data.get("gold_refinement", {})
    if not gr_block:
        return _default_config()
    return _parse_config(gr_block)


def _default_config() -> GoldRefinementConfig:
    cfg = GoldRefinementConfig()
    cfg.section_conditions = dict.fromkeys(SECTION_KEYS, True)
    cfg.section_titles = dict(DEFAULT_SECTION_TITLES)
    cfg.narrative_moves = dict(DEFAULT_NARRATIVE_MOVES)
    cfg.lexicon = _default_lexicon()
    cfg.slots = _default_slots()
    return cfg


def _default_lexicon() -> dict[str, tuple[str, ...]]:
    return {
        "metallurgical_terms": (
            "cupellation",
            "assaying",
            "smelting",
            "cupellation",
            "hallmark",
        ),
        "manuscript_terms": (
            "draft",
            "claim",
            "citation",
            "cross-reference",
            "evidence",
        ),
        "purity_adjectives": (
            "unrefined",
            "purified",
            "certified",
            "immaculate",
            "nine-nines",
        ),
        "refinement_verbs": (
            "assaying",
            "certifying",
            "refining",
            "smelting",
            "cupellating",
        ),
    }


def _default_slots() -> tuple[SlotSpec, ...]:
    return (
        SlotSpec(name="METHOD_METAL_TERM", category="metallurgical_terms", count=3, section="methodology"),
        SlotSpec(name="METHOD_MANUSCRIPT_TERM", category="manuscript_terms", count=2, section="methodology"),
        SlotSpec(name="RESULTS_PURITY_ADJ", category="purity_adjectives", count=2, section="results"),
        SlotSpec(name="DISCUSSION_REFINEMENT_VERB", category="refinement_verbs", count=1, section="discussion"),
    )


def _parse_config(gr: dict[str, Any]) -> GoldRefinementConfig:
    seed = int(gr.get("seed", 431))
    depth = str(gr.get("composition_depth", "deep"))
    if depth not in COMPOSITION_DEPTHS:
        raise GoldRefinementConfigError(f"composition_depth must be one of {COMPOSITION_DEPTHS}, got '{depth}'")

    lexicon_raw = gr.get("lexicon", {})
    if not isinstance(lexicon_raw, dict):
        raise GoldRefinementConfigError("lexicon must be a mapping")
    lexicon: dict[str, tuple[str, ...]] = {}
    for cat in REQUIRED_LEXICON_CATEGORIES:
        vals = lexicon_raw.get(cat)
        if not vals or not isinstance(vals, (list, tuple)):
            raise GoldRefinementConfigError(f"lexicon category '{cat}' must be a non-empty list")
        lexicon[cat] = tuple(str(v) for v in vals)
    # Allow optional categories
    for cat, vals in lexicon_raw.items():
        if cat in REQUIRED_LEXICON_CATEGORIES:
            continue
        if isinstance(vals, (list, tuple)) and vals:
            lexicon[cat] = tuple(str(v) for v in vals)

    slots_raw = gr.get("slots", [])
    slots: list[SlotSpec] = []
    for s in slots_raw:
        if not isinstance(s, dict):
            raise GoldRefinementConfigError(f"slot must be a mapping, got {type(s)}")
        category = str(s.get("category", ""))
        if category and category not in lexicon:
            raise GoldRefinementConfigError(f"slot category '{category}' not found in lexicon")
        slots.append(
            SlotSpec(
                name=str(s.get("name", "")),
                category=category,
                count=int(s.get("count", 1)),
                section=str(s.get("section", "methodology")),
            )
        )
    slots_tuple = tuple(slots)

    section_conditions = dict.fromkeys(SECTION_KEYS, True)
    sc_raw = gr.get("section_conditions", {})
    if isinstance(sc_raw, dict):
        for k, v in sc_raw.items():
            if k in section_conditions:
                section_conditions[k] = bool(v)

    section_titles = dict(DEFAULT_SECTION_TITLES)
    st_raw = gr.get("section_titles", {})
    if isinstance(st_raw, dict):
        for k, v in st_raw.items():
            if k in section_titles:
                section_titles[k] = str(v)

    narrative_moves = dict(DEFAULT_NARRATIVE_MOVES)
    nm_raw = gr.get("narrative_moves", {})
    if isinstance(nm_raw, dict):
        for k, v in nm_raw.items():
            if k in narrative_moves and isinstance(v, (list, tuple)):
                narrative_moves[k] = tuple(str(m) for m in v)

    return GoldRefinementConfig(
        seed=seed,
        composition_depth=depth,
        hypothesis=str(gr.get("hypothesis", "")),
        section_conditions=section_conditions,
        section_titles=section_titles,
        narrative_moves=narrative_moves,
        lexicon=lexicon,
        slots=slots_tuple,
        refinement_stages=gr.get("refinement_stages", []),
        visualizations=gr.get("visualizations", {}),
        design_principles=gr.get("design_principles", []),
        quality_probes=gr.get("quality_probes", []),
        failure_modes=gr.get("failure_modes", []),
        authoring_obligations=gr.get("authoring_obligations", []),
        contribution_claims=gr.get("contribution_claims", []),
        pipeline_phases=gr.get("pipeline_phases", []),
        audit_rules=gr.get("audit_rules", []),
    )


__all__ = [
    "COMPOSITION_DEPTHS",
    "DEFAULT_NARRATIVE_MOVES",
    "DEFAULT_SECTION_TITLES",
    "GOLD_REFINEMENT_SCHEMA_FIELDS",
    "GoldRefinementConfig",
    "GoldRefinementConfigError",
    "REQUIRED_LEXICON_CATEGORIES",
    "SECTION_KEYS",
    "SlotSpec",
    "load_gold_refinement_config",
]
