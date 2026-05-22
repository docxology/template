"""Project-local research domain profile overlays."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class DomainProfile:
    """Declarative domain preferences for a project."""

    domain: str = "generic"
    display_name: str = "Generic Research Project"
    required_packages: tuple[str, ...] = ()
    preferred_outputs: tuple[str, ...] = ()
    validation_gates: tuple[str, ...] = ()
    figure_types: tuple[str, ...] = ()
    citation_policy: str = ""
    llm_prompt_guidance: str = ""
    review_gates: tuple[str, ...] = ()
    source_policy: str = ""
    artifact_expectations: tuple[str, ...] = ()
    benchmark_rubric: dict[str, Any] | None = None


_BUILTIN_PROFILES: dict[str, DomainProfile] = {
    "generic": DomainProfile(),
    "code_research": DomainProfile(
        domain="code_research",
        display_name="Code Research Project",
        required_packages=("pytest",),
        preferred_outputs=("pdf", "html"),
        validation_gates=("experiment_method_design", "publication_readiness"),
        figure_types=("line_plot", "comparison_table"),
        citation_policy="official_or_scholarly",
    ),
    "prose_research": DomainProfile(
        domain="prose_research",
        display_name="Prose Research Project",
        preferred_outputs=("pdf", "docx"),
        validation_gates=("source_quality", "publication_readiness"),
        figure_types=("conceptual_diagram",),
        citation_policy="official_or_scholarly",
    ),
    "literature_review": DomainProfile(
        domain="literature_review",
        display_name="Literature Review",
        preferred_outputs=("pdf", "html"),
        validation_gates=("source_quality", "citation_integrity", "publication_readiness"),
        figure_types=("evidence_map", "flow_diagram"),
        citation_policy="official_or_scholarly",
    ),
}


def load_domain_profile(project_root: Path, *, default_profile: str = "generic") -> DomainProfile:
    """Load ``domain_profile.yaml`` from a project, or return a generic profile."""
    profile_path = project_root / "domain_profile.yaml"
    if not profile_path.exists():
        return _BUILTIN_PROFILES.get(default_profile, _BUILTIN_PROFILES["generic"])

    payload = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"domain_profile.yaml must be a mapping: {profile_path}")

    unknown = set(payload) - _SUPPORTED_KEYS
    if unknown:
        keys = ", ".join(sorted(str(key) for key in unknown))
        raise ValueError(f"unsupported domain_profile key(s): {keys}")

    profile = DomainProfile(
        domain=str(payload.get("domain", "generic") or "generic"),
        display_name=str(payload.get("display_name", "Generic Research Project") or ""),
        required_packages=_tuple_of_strings(payload.get("required_packages")),
        preferred_outputs=_tuple_of_strings(payload.get("preferred_outputs")),
        validation_gates=_tuple_of_strings(payload.get("validation_gates")),
        figure_types=_tuple_of_strings(payload.get("figure_types")),
        citation_policy=str(payload.get("citation_policy", "") or ""),
        llm_prompt_guidance=str(payload.get("llm_prompt_guidance", "") or ""),
        review_gates=_tuple_of_strings(payload.get("review_gates")),
        source_policy=str(payload.get("source_policy", "") or ""),
        artifact_expectations=_tuple_of_strings(payload.get("artifact_expectations")),
        benchmark_rubric=_dict_or_none(payload.get("benchmark_rubric")),
    )
    if not profile.display_name:
        raise ValueError("domain_profile display_name must not be empty")
    return profile


_SUPPORTED_KEYS = frozenset(
    {
        "domain",
        "display_name",
        "required_packages",
        "preferred_outputs",
        "validation_gates",
        "figure_types",
        "citation_policy",
        "llm_prompt_guidance",
        "review_gates",
        "source_policy",
        "artifact_expectations",
        "benchmark_rubric",
    }
)


def _tuple_of_strings(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list | tuple):
        if not all(isinstance(item, str) for item in value):
            raise ValueError("domain_profile list values must be strings")
        return tuple(value)
    raise ValueError("domain_profile sequence values must be strings or lists of strings")


def _dict_or_none(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("domain_profile benchmark_rubric must be a mapping")
    return value
