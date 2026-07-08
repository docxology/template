from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

try:
    from .parsing import (
        as_bool as _as_bool,
        as_float as _as_float,
        as_str_tuple as _as_str_tuple,
        load_yaml_dict,
    )
except ImportError:
    from parsing import (  # type: ignore[no-redef]
        as_bool as _as_bool,
        as_float as _as_float,
        as_str_tuple as _as_str_tuple,
        load_yaml_dict,
    )


def _load_domain_profile_data(project_root: Path) -> dict[str, Any]:
    return load_yaml_dict(project_root / "domain_profile.yaml")


@dataclass(frozen=True)
class DomainStageMapping:
    """Data container for DomainStageMapping."""

    refinery_stage: str
    domain_operation: str
    purity_target: float
    evidence_surface: str
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        """Process as dict."""
        return {
            "refinery_stage": self.refinery_stage,
            "domain_operation": self.domain_operation,
            "purity_target": self.purity_target,
            "evidence_surface": self.evidence_surface,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class DomainMetricSpec:
    """Data container for DomainMetricSpec."""

    name: str
    weight: float = 1.0
    minimum: float = 0.0
    maximum: float = 1.0
    higher_is_better: bool = True
    description: str = ""

    def normalized(self, value: float) -> float:
        """Process normalized."""
        if self.maximum <= self.minimum:
            raise ValueError(f"Metric '{self.name}' must have maximum greater than minimum")
        score = (value - self.minimum) / (self.maximum - self.minimum)
        score = max(0.0, min(1.0, score))
        if not self.higher_is_better:
            score = 1.0 - score
        return score

    def as_dict(self) -> dict[str, Any]:
        """Process as dict."""
        return {
            "name": self.name,
            "weight": self.weight,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "higher_is_better": self.higher_is_better,
            "description": self.description,
        }


@dataclass(frozen=True)
class DomainAdapterProfile:
    """Data container for DomainAdapterProfile."""

    domain: str
    display_name: str
    required_packages: tuple[str, ...] = ()
    preferred_outputs: tuple[str, ...] = ()
    validation_gates: tuple[str, ...] = ()
    figure_types: tuple[str, ...] = ()
    citation_policy: str = ""
    review_gates: tuple[str, ...] = ()
    source_policy: str = ""
    artifact_expectations: tuple[str, ...] = ()
    benchmark_name: str = ""
    metrics: tuple[DomainMetricSpec, ...] = ()
    stage_mappings: tuple[DomainStageMapping, ...] = ()
    analogy_boundary_thesis: str = ""
    analogy_boundary_limits: tuple[str, ...] = ()
    analogy_boundary_non_claims: tuple[str, ...] = ()
    llm_prompt_guidance: str = ""

    @property
    def stage_count(self) -> int:
        """Process stage count."""
        return len(self.stage_mappings)

    @property
    def metric_count(self) -> int:
        """Process metric count."""
        return len(self.metrics)

    def purity_from_metrics(self, measurements: Mapping[str, float]) -> float:
        """Process purity from metrics."""
        if not self.metrics:
            return 0.0
        weighted_total = 0.0
        weight_sum = 0.0
        for spec in self.metrics:
            if spec.name not in measurements:
                raise KeyError(f"Missing metric '{spec.name}' for {self.display_name}")
            weighted_total += spec.normalized(float(measurements[spec.name])) * spec.weight
            weight_sum += spec.weight
        if weight_sum <= 0:
            return 0.0
        return max(0.0, min(1.0, weighted_total / weight_sum))

    def stage_rows(self) -> str:
        """Process stage rows."""
        return "\n".join(
            f"| {stage.refinery_stage} | {stage.domain_operation} | {stage.purity_target:.3f} | {stage.evidence_surface} |"
            for stage in self.stage_mappings
        )

    def metric_rows(self) -> str:
        """Process metric rows."""
        return "\n".join(
            f"| {metric.name} | {metric.weight:g} | {metric.minimum:g} | {metric.maximum:g} | "
            f"{'yes' if metric.higher_is_better else 'no'} | {metric.description} |"
            for metric in self.metrics
        )

    def boundary_lines(self) -> tuple[str, ...]:
        """Process boundary lines."""
        lines: list[str] = []
        if self.analogy_boundary_thesis:
            lines.append(self.analogy_boundary_thesis)
        lines.extend(self.analogy_boundary_limits)
        lines.extend(self.analogy_boundary_non_claims)
        return tuple(lines)

    def boundary_summary(self) -> str:
        """Process boundary summary."""
        return "\n".join(f"- {line}" for line in self.boundary_lines())

    def review_gate_summary(self) -> str:
        """Process review gate summary."""
        return ", ".join(self.review_gates)


def _metric_specs(benchmark: Any) -> tuple[DomainMetricSpec, ...]:
    if not isinstance(benchmark, dict):
        return ()
    specs: list[DomainMetricSpec] = []
    dimensions = benchmark.get("dimensions", [])
    if not isinstance(dimensions, list):
        return ()
    for item in dimensions:
        if not isinstance(item, dict):
            continue
        specs.append(
            DomainMetricSpec(
                name=str(item.get("name", "")),
                weight=float(item.get("weight", 1.0) or 1.0),
                minimum=_as_float(item.get("minimum"), 0.0),
                maximum=_as_float(item.get("maximum"), 1.0),
                higher_is_better=_as_bool(
                    item.get("higher_is_better"),
                    True,
                    field_name=f"benchmark_rubric.dimensions[{len(specs) + 1}].higher_is_better",
                ),
                description=str(item.get("description", "")),
            )
        )
    return tuple(spec for spec in specs if spec.name)


def _stage_mappings(data: Any) -> tuple[DomainStageMapping, ...]:
    if not isinstance(data, list):
        return ()
    mappings: list[DomainStageMapping] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        mappings.append(
            DomainStageMapping(
                refinery_stage=str(item.get("refinery_stage", "")),
                domain_operation=str(item.get("domain_operation", "")),
                purity_target=_as_float(item.get("purity_target"), 0.0),
                evidence_surface=str(item.get("evidence_surface", "")),
                notes=str(item.get("notes", "")),
            )
        )
    return tuple(mapping for mapping in mappings if mapping.refinery_stage)


def _boundary_parts(data: Any) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    if isinstance(data, dict):
        return (
            str(data.get("thesis", "")),
            _as_str_tuple(data.get("limits")),
            _as_str_tuple(data.get("non_claims")),
        )
    if isinstance(data, list):
        return "", _as_str_tuple(data), ()
    return "", (), ()


def load_domain_profile(project_root: Path | None = None) -> DomainAdapterProfile:
    """Load domain profile from a file."""
    root = project_root or Path(__file__).resolve().parent.parent
    data = _load_domain_profile_data(root)
    boundary_thesis, boundary_limits, boundary_non_claims = _boundary_parts(data.get("analogy_boundary", {}))
    return DomainAdapterProfile(
        domain=str(data.get("domain", "metallurgical_manuscript_composition")),
        display_name=str(data.get("display_name", "Gold Refinement")),
        required_packages=_as_str_tuple(data.get("required_packages")),
        preferred_outputs=_as_str_tuple(data.get("preferred_outputs")),
        validation_gates=_as_str_tuple(data.get("validation_gates")),
        figure_types=_as_str_tuple(data.get("figure_types")),
        citation_policy=str(data.get("citation_policy", "")),
        review_gates=_as_str_tuple(data.get("review_gates")),
        source_policy=str(data.get("source_policy", "")),
        artifact_expectations=_as_str_tuple(data.get("artifact_expectations")),
        benchmark_name=str((data.get("benchmark_rubric") or {}).get("name", "")),
        metrics=_metric_specs(data.get("benchmark_rubric", {})),
        stage_mappings=_stage_mappings(data.get("stage_mappings", [])),
        analogy_boundary_thesis=boundary_thesis,
        analogy_boundary_limits=boundary_limits,
        analogy_boundary_non_claims=boundary_non_claims,
        llm_prompt_guidance=str(data.get("llm_prompt_guidance", "")),
    )


__all__ = [
    "DomainAdapterProfile",
    "DomainMetricSpec",
    "DomainStageMapping",
    "load_domain_profile",
]
