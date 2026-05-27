"""Publication metadata and citation helpers."""

from __future__ import annotations

import json
from typing import Any

try:
    from ..optimizer import OptimizationResult
except ImportError:  # pragma: no cover
    from optimizer import OptimizationResult  # type: ignore[no-redef]

from ._infra import INFRASTRUCTURE_AVAILABLE, get_logger
from .experiments import _project_root

if INFRASTRUCTURE_AVAILABLE:
    from infrastructure.publishing import generate_citation_apa, generate_citation_bibtex, generate_citation_mla
    from infrastructure.publishing.models import PublicationMetadata


def extract_optimization_metadata(results: dict[float, OptimizationResult]) -> dict[str, Any] | None:
    """Extract publication metadata from optimization results."""
    try:
        best_step_size = min(results.keys(), key=lambda k: results[k].objective_value)
        best_result = results[best_step_size]
        objective_history: list[float] = best_result.objective_history or []
        iterations_to_convergence = len(objective_history)
        convergence_rate = (
            abs(objective_history[-1] - objective_history[0]) / len(objective_history)
            if len(objective_history) >= 2
            else 0.0
        )
        return {
            "title": "Optimization Algorithm Performance Analysis",
            "description": (
                f"Comparative analysis of gradient descent optimization with step sizes {list(results.keys())}"
            ),
            "algorithm": "Gradient Descent",
            "objective_function": "Quadratic Function f(x) = x²",
            "step_sizes_tested": list(results.keys()),
            "best_step_size": best_step_size,
            "final_objective": best_result.objective_value,
            "iterations_to_convergence": iterations_to_convergence,
            "convergence_rate": convergence_rate,
            "analysis_type": "Numerical Optimization",
            "methodology": "Gradient descent with fixed step sizes",
        }
    except (KeyError, ValueError, TypeError, AttributeError) as e:
        if INFRASTRUCTURE_AVAILABLE and get_logger is not None:
            get_logger(__name__).warning("Failed to extract optimization metadata: %s", e)
        return None


def generate_citations_from_metadata(metadata: dict[str, Any]) -> dict[str, str] | None:
    """Generate citations from optimization metadata."""
    if not INFRASTRUCTURE_AVAILABLE:
        return None
    try:
        pub_metadata = PublicationMetadata(
            title=metadata["title"],
            authors=["Optimization Analysis Pipeline"],
            abstract=metadata.get("description", "Optimization algorithm performance analysis"),
            keywords=["optimization", "gradient descent", "numerical analysis"],
            publication_date="2026-01-01",
            license="MIT",
        )
        return {
            "bibtex": generate_citation_bibtex(pub_metadata),
            "apa": generate_citation_apa(pub_metadata),
            "mla": generate_citation_mla(pub_metadata),
        }
    except (KeyError, ValueError, TypeError, ImportError, NameError) as e:
        if get_logger is not None:
            get_logger(__name__).warning("Failed to generate citations: %s", e)
        return None


def save_publishing_materials(metadata: dict[str, Any], citations: dict[str, str] | None = None) -> None:
    """Save publishing materials to output directory."""
    try:
        output_dir = _project_root() / "output" / "citations"
        output_dir.mkdir(parents=True, exist_ok=True)
        metadata_path = output_dir / "optimization_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)

        if citations:
            for format_name, citation_text in citations.items():
                citation_path = output_dir / f"citation_{format_name}.txt"
                with open(citation_path, "w") as f:
                    f.write(citation_text)

        summary_path = output_dir / "publication_summary.md"
        with open(summary_path, "w") as f:
            f.write("# Optimization Analysis Publication Summary\n\n")
            f.write(f"**Title:** {metadata['title']}\n\n")
            f.write(f"**Description:** {metadata['description']}\n\n")
            f.write(f"**Algorithm:** {metadata['algorithm']}\n\n")
            f.write(f"**Best Step Size:** {metadata['best_step_size']}\n\n")
            f.write(f"**Final Objective:** {metadata['final_objective']:.6f}\n\n")
            f.write(f"**Iterations:** {metadata['iterations_to_convergence']}\n\n")
            if citations:
                f.write("## Citations\n\n")
                for format_name, citation in citations.items():
                    f.write(f"### {format_name.upper()}\n\n{citation}\n\n")

        if INFRASTRUCTURE_AVAILABLE and get_logger is not None:
            get_logger(__name__).info("Publishing materials saved to: %s", output_dir)
    except (OSError, json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
        if INFRASTRUCTURE_AVAILABLE and get_logger is not None:
            get_logger(__name__).warning("Failed to save publishing materials: %s", e)


__all__ = [
    "extract_optimization_metadata",
    "generate_citations_from_metadata",
    "save_publishing_materials",
]
