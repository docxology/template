#!/usr/bin/env python3
"""Generate comprehensive research figures for the manuscript.

This script runs the full Ento-Linguistic analysis pipeline using real
src/ modules to produce publication-quality figures referenced in the
manuscript. It builds a synthetic entomological corpus, extracts terminology,
constructs concept maps and terminology networks, and generates all figures
from computed data.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ── Path setup ────────────────────────────────────────────────────────
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
repo_root = os.path.abspath(os.path.join(project_root, ".."))
src_path = os.path.join(project_root, "src")
for p in (project_root, src_path, repo_root):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ── Logging ───────────────────────────────────────────────────────────
try:
    from src.core.logging import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)

# ── Infrastructure validation (optional) ──────────────────────────────
try:
    from src.core.validation import validate_figure_registry, verify_output_integrity
    INFRASTRUCTURE_AVAILABLE = True
except ImportError:
    INFRASTRUCTURE_AVAILABLE = False
    validate_figure_registry = None
    verify_output_integrity = None


# ═══════════════════════════════════════════════════════════════════════
#  Synthetic Corpus Builder
# ═══════════════════════════════════════════════════════════════════════

SYNTHETIC_ABSTRACTS: List[str] = [
    # Unit of Individuality
    (
        "The colony as a superorganism: collective decision-making in ant societies. "
        "We examine how the concept of individuality applies when nestmates cooperate "
        "as a single organism. The superorganism framework treats the colony as the "
        "fundamental unit of selection, yet individual nestmates retain behavioural "
        "plasticity. Eusocial insect colonies blur the boundary between organism and "
        "collective, raising questions about how biological individuality should be "
        "defined. Our analysis of Atta cephalotes reveals symbiont integration at "
        "the holobiont level, complicating simple definitions of the individual ant."
    ),
    # Behavior and Identity
    (
        "Task specialization and behavioural plasticty in Camponotus floridanus. "
        "Workers termed 'foragers' exhibit flexible task switching, challenging "
        "categorical role assignments. We tracked 500 individually-marked workers "
        "over 60 days, finding that 38% of ants labelled as 'soldiers' engaged in "
        "foraging behaviour regularly. The division of labor is not fixed: role "
        "assignment reflects probabilistic response thresholds rather than stable "
        "identities. Behaviour labels like 'nurse' and 'forager' create the "
        "impression of permanent castes when the reality is fluid task allocation."
    ),
    # Power & Labor
    (
        "Caste determination and reproductive hierarchies in Solenopsis invicta. "
        "The terms 'queen' and 'worker' import human social hierarchies into ant "
        "biology. We analyze how 'caste' terminology, borrowed from human stratification "
        "systems, frames ant social organization as a rigid hierarchy. Dominance "
        "interactions between reproductive and non-reproductive nestmates are routinely "
        "described using 'slave' and 'master' metaphors. The power structure of the "
        "colony is better understood through resource allocation models than through "
        "analogies to human feudal systems. Terms like 'soldier caste' impose military "
        "hierarchy onto defensive specialization."
    ),
    # Sex & Reproduction
    (
        "Sex determination and reproductive biology in Hymenoptera. Haplodiploidy "
        "creates fundamentally different patterns of relatedness and sex allocation. "
        "The terms 'sex determination' and 'sex differentiation' carry implicit "
        "assumptions about binary sex systems derived from mammalian biology. "
        "In ants, reproductive females (queens) and males (drones) follow different "
        "developmental pathways controlled by ploidy and epigenetic regulation. "
        "Worker reproduction occurs in queenless colonies, complicating the "
        "strict queen/worker reproductive dichotomy."
    ),
    # Kin & Relatedness
    (
        "Kin recognition and nestmate discrimination in Linepithema humile. "
        "Chemical profiles mediate colony identity, with cuticular hydrocarbons "
        "functioning as recognition cues. Genetic relatedness under haplodiploidy "
        "creates asymmetric kin coefficients: sisters share 75% of genes while "
        "brothers share only 25%. Kin selection theory, originally developed for "
        "bilateral diploid organisms, requires modification when applied to "
        "haplodiploid social insect societies. Colony fusion events challenge "
        "the assumption that kin relatedness exclusively drives cooperative behaviour."
    ),
    # Economics
    (
        "Resource allocation and foraging optimization in Pogonomyrmex barbatus. "
        "Economic models of ant foraging describe colonies as efficient resource "
        "markets, with investment in trail infrastructure and trade-offs between "
        "exploration and exploitation. Seed harvesting involves collective decisions "
        "about resource allocation that parallel portfolio optimization in human "
        "economics. The metaphor of 'markets' and 'trade' applied to ant resource "
        "distribution imposes assumptions about rational agency that may not apply "
        "to stimulus-response foraging systems."
    ),
    # Cross-domain: Individuality + Power
    (
        "Superorganism theory and the dissolution of individual agency in leaf-cutter "
        "ant colonies. When colonies are treated as organisms, the agency of individual "
        "workers is dissolved into the collective. The superorganism concept conflates "
        "colony-level coordination with individual-level decision-making, while caste "
        "terminology imposes hierarchical structure on emergent self-organization. "
        "Division of labor among Acromyrmex workers arises from simple behavioral rules, "
        "not from top-down caste assignments by a 'ruling queen'."
    ),
    # Cross-domain: Behavior + Kinship
    (
        "Altruism, kin selection, and helper behaviour in social insect colonies. "
        "Hamilton's rule provides a framework for understanding cooperative behaviour "
        "among genetic relatives. Workers 'sacrifice' reproduction, described in "
        "anthropomorphic terms of 'altruism' and 'selflessness'. These kinship "
        "concepts, derived from human familial structures, frame helping behaviour "
        "as conscious moral choices rather than evolved strategies shaped by "
        "inclusive fitness. The 'selfish gene' framing further layers economic "
        "metaphor onto genetic processes."
    ),
    # Cross-domain: Economics + Power
    (
        "Colony investment strategies and worker allocation in army ants. "
        "The colony allocates workers to foraging, defense, and brood care through "
        "probabilistic mechanisms. Economic language of 'investment', 'returns', and "
        "'efficiency' structures analysis of colony resource decisions. Soldier "
        "production is framed as 'military expenditure', while forager allocation "
        "is described as 'labour market dynamics'. These economic framings treat "
        "colonies as rational utility-maximizing agents, obscuring the mechanistic "
        "basis of collective behaviour."
    ),
    # Additional domain coverage
    (
        "Communication networks and information transfer in Formica rufa. "
        "Pheromone trails create stigmergic communication channels that coordinate "
        "foraging. The colony processes information through distributed networks "
        "without central control. Terms like 'recruitment' and 'trail communication' "
        "borrow from human organizational language. The relationship between individual "
        "ant behaviour and colony-level patterns exemplifies how terminology at "
        "different scales of biological organization creates conceptual confusion "
        "about the unit of individuality and collective cognition."
    ),
]


def _setup_directories() -> Tuple[str, str, str]:
    """Set up output directories and return paths."""
    output_dir = os.path.join(project_root, "output")
    data_dir = os.path.join(output_dir, "data")
    figure_dir = os.path.join(output_dir, "figures")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(figure_dir, exist_ok=True)
    return output_dir, data_dir, figure_dir


# ═══════════════════════════════════════════════════════════════════════
#  Analysis Pipeline
# ═══════════════════════════════════════════════════════════════════════

def run_analysis_pipeline(texts: List[str]) -> Dict[str, Any]:
    """Run the complete Ento-Linguistic analysis pipeline on a text corpus.

    Uses real analysis modules from src/ to extract terms, build concept maps,
    analyze domains, and compute co-occurrence networks.

    Args:
        texts: List of text strings (abstracts) to analyze

    Returns:
        Dictionary with all analysis results
    """
    from src.analysis.text_analysis import TextProcessor
    from src.analysis.term_extraction import TerminologyExtractor
    from src.analysis.conceptual_mapping import ConceptualMapper
    from src.analysis.domain_analysis import DomainAnalyzer

    results: Dict[str, Any] = {}

    # ── Step 1: Text Processing ───────────────────────────────────────
    logger.info("Step 1/4: Processing text corpus...")
    processor = TextProcessor()
    results["corpus_stats"] = processor.get_vocabulary_stats(texts)
    logger.info(f"  Corpus: {len(texts)} documents, "
                f"{results['corpus_stats'].get('total_tokens', '?')} tokens")

    # ── Step 2: Terminology Extraction ────────────────────────────────
    logger.info("Step 2/4: Extracting terminology...")
    extractor = TerminologyExtractor(text_processor=processor)
    terms = extractor.extract_terms(texts, min_frequency=1)
    results["terms"] = terms
    results["domain_seed_stats"] = extractor.get_domain_statistics()
    logger.info(f"  Extracted {len(terms)} terms across "
                f"{len(results['domain_seed_stats'])} domains")

    # ── Step 3: Concept Mapping ───────────────────────────────────────
    logger.info("Step 3/4: Building concept map...")
    mapper = ConceptualMapper()
    concept_map = mapper.build_concept_map(terms)
    results["concept_map"] = concept_map
    logger.info(f"  {len(concept_map.concepts)} concepts, "
                f"{len(concept_map.concept_relationships)} relationships")

    # ── Step 4: Domain Analysis ───────────────────────────────────────
    logger.info("Step 4/4: Analyzing domains...")
    analyzer = DomainAnalyzer()
    domain_analyses = analyzer.analyze_all_domains(terms, texts)
    results["domain_analyses"] = domain_analyses

    # Build domain data summary for visualization
    domain_data: Dict[str, Dict[str, Any]] = {}
    for domain_name, analysis in domain_analyses.items():
        if domain_name.startswith("_"):
            continue  # Skip cross-domain meta-analysis
        domain_data[domain_name] = {
            "term_count": len(analysis.key_terms) if hasattr(analysis, "key_terms") else 0,
            "avg_confidence": (
                np.mean(list(analysis.confidence_scores.values()))
                if hasattr(analysis, "confidence_scores") and analysis.confidence_scores
                else 0.0
            ),
            "total_frequency": sum(
                t.frequency for t in terms.values()
                if domain_name in getattr(t, "domains", [])
            ),
            "bridging_terms": set(),  # Populated below
            "ambiguity_metrics": (
                analysis.ambiguity_metrics
                if hasattr(analysis, "ambiguity_metrics")
                else {}
            ),
            # Scalar ambiguity score for visualization
            "ambiguity_score": (
                analysis.ambiguity_metrics.get("domain_metrics", {}).get(
                    "average_ambiguity_score",
                    analysis.ambiguity_metrics.get("domain_metrics", {}).get(
                        "average_context_diversity", 0.0
                    ),
                )
                if hasattr(analysis, "ambiguity_metrics") and analysis.ambiguity_metrics
                else 0.0
            ),
        }

    # Find bridging terms (terms in multiple domains)
    for term_text, term_obj in terms.items():
        if len(term_obj.domains) > 1:
            for d in term_obj.domains:
                if d in domain_data:
                    domain_data[d]["bridging_terms"].add(term_text)

    results["domain_data"] = domain_data

    # Build co-occurrence relationships for the terminology network
    relationships: Dict[Tuple[str, str], float] = {}
    for (c1, c2), weight in concept_map.concept_relationships.items():
        relationships[(c1, c2)] = weight

    # Also build term-level co-occurrence from the extracted terms
    term_items = list(terms.items())
    for i, (t1_name, t1) in enumerate(term_items):
        for j in range(i + 1, min(i + 30, len(term_items))):
            t2_name, t2 = term_items[j]
            # Compute co-occurrence based on shared domains
            shared_domains = set(t1.domains) & set(t2.domains)
            if shared_domains:
                weight = len(shared_domains) / max(len(t1.domains), len(t2.domains), 1)
                if weight > 0.1:
                    relationships[(t1_name, t2_name)] = weight

    results["relationships"] = relationships

    return results


# ═══════════════════════════════════════════════════════════════════════
#  Figure Generation
# ═══════════════════════════════════════════════════════════════════════

def generate_concept_map(results: Dict[str, Any], figure_dir: str) -> str:
    """Generate concept_map.png using ConceptVisualizer.

    Args:
        results: Analysis pipeline results
        figure_dir: Output directory for figures

    Returns:
        Path to generated figure
    """
    from src.visualization.concept_visualization import ConceptVisualizer

    concept_map = results["concept_map"]
    filepath = Path(figure_dir) / "concept_map.png"

    viz = ConceptVisualizer(figsize=(14, 10))
    viz.visualize_concept_map(
        concept_map,
        filepath=filepath,
        title="Ento-Linguistic Concept Map:\nDomain Relationships and Terminology Networks",
    )

    logger.info(f"  ✅ concept_map.png ({filepath.stat().st_size / 1024:.1f} KB)")
    return str(filepath)


def generate_terminology_network(results: Dict[str, Any], figure_dir: str) -> str:
    """Generate terminology_network.png using ConceptVisualizer.

    Args:
        results: Analysis pipeline results
        figure_dir: Output directory for figures

    Returns:
        Path to generated figure
    """
    from src.visualization.concept_visualization import ConceptVisualizer

    terms = results["terms"]
    relationships = results["relationships"]
    filepath = Path(figure_dir) / "terminology_network.png"

    viz = ConceptVisualizer(figsize=(16, 12))
    viz.visualize_terminology_network(
        terms=list(terms.items()),
        relationships=relationships,
        filepath=filepath,
        title="Ento-Linguistic Terminology Network:\nCo-occurrence and Domain Clustering",
    )

    logger.info(f"  ✅ terminology_network.png ({filepath.stat().st_size / 1024:.1f} KB)")
    return str(filepath)


def generate_domain_comparison(results: Dict[str, Any], figure_dir: str) -> str:
    """Generate domain_comparison.png using ConceptVisualizer.

    Args:
        results: Analysis pipeline results
        figure_dir: Output directory for figures

    Returns:
        Path to generated figure
    """
    from src.visualization.concept_visualization import ConceptVisualizer

    domain_data = results["domain_data"]
    filepath = Path(figure_dir) / "domain_comparison.png"

    viz = ConceptVisualizer(figsize=(15, 12))
    viz.create_domain_comparison_plot(
        domain_data=domain_data,
        filepath=filepath,
    )

    logger.info(f"  ✅ domain_comparison.png ({filepath.stat().st_size / 1024:.1f} KB)")
    return str(filepath)


def generate_domain_overlap_heatmap(results: Dict[str, Any], figure_dir: str) -> str:
    """Generate domain_overlap_heatmap.png showing cross-domain term sharing.

    Args:
        results: Analysis pipeline results
        figure_dir: Output directory for figures

    Returns:
        Path to generated figure
    """
    from src.visualization.concept_visualization import ConceptVisualizer

    terms = results["terms"]
    filepath = Path(figure_dir) / "domain_overlap_heatmap.png"

    # Build overlap matrix from terms
    domain_names = sorted({d for t in terms.values() for d in t.domains})

    # Short names for key construction (avoid _ parsing issues)
    short = {d: d.replace("_and_", "&").replace("_", "") for d in domain_names}

    overlaps: Dict[str, Dict[str, Any]] = {}
    for d1 in domain_names:
        terms_d1 = {t for t, obj in terms.items() if d1 in obj.domains}
        for d2 in domain_names:
            terms_d2 = {t for t, obj in terms.items() if d2 in obj.domains}
            shared = terms_d1 & terms_d2
            total = len(terms_d1 | terms_d2) if terms_d1 | terms_d2 else 1
            key = f"{short[d1]}_and_{short[d2]}"
            overlaps[key] = {
                "overlap_percentage": (len(shared) / total) * 100 if d1 != d2 else 100,
                "overlap_count": len(shared),
                "shared_terms": list(shared)[:10],
            }

    viz = ConceptVisualizer(figsize=(12, 10))
    viz.create_domain_overlap_heatmap(
        domain_overlaps=overlaps,
        filepath=filepath,
        title="Cross-Domain Term Overlap in Ento-Linguistic Analysis",
    )

    logger.info(f"  ✅ domain_overlap_heatmap.png ({filepath.stat().st_size / 1024:.1f} KB)")
    return str(filepath)


def generate_anthropomorphic_analysis(results: Dict[str, Any], figure_dir: str) -> str:
    """Generate anthropomorphic_framing.png showing human-derived terminology.

    Args:
        results: Analysis pipeline results
        figure_dir: Output directory for figures

    Returns:
        Path to generated figure
    """
    from src.visualization.concept_visualization import ConceptVisualizer

    filepath = Path(figure_dir) / "anthropomorphic_framing.png"

    # Curated anthropomorphic concepts organized by category
    anthropomorphic_data: Dict[str, List[str]] = {
        "Hierarchical Terms": [
            "queen", "king", "worker", "soldier", "slave",
            "master", "caste", "rank", "dominance", "subordinate",
        ],
        "Economic Metaphors": [
            "investment", "trade", "market", "efficiency",
            "resource allocation", "returns", "expenditure",
        ],
        "Kinship Language": [
            "mother", "sister", "daughter", "family",
            "kin", "altruism", "selflessness",
        ],
        "Identity Labels": [
            "forager", "nurse", "guard", "scout",
            "recruit", "specialist", "generalist",
        ],
        "Agency Attribution": [
            "decides", "chooses", "communicates", "signals",
            "cooperates", "competes", "sacrifices",
        ],
    }

    viz = ConceptVisualizer(figsize=(14, 10))
    viz.create_anthropomorphic_analysis_plot(
        anthropomorphic_data=anthropomorphic_data,
        filepath=filepath,
    )

    logger.info(f"  ✅ anthropomorphic_framing.png ({filepath.stat().st_size / 1024:.1f} KB)")
    return str(filepath)


def save_analysis_data(results: Dict[str, Any], data_dir: str) -> List[str]:
    """Save analysis results as data files.

    Args:
        results: Analysis pipeline results
        data_dir: Output directory for data files

    Returns:
        List of saved file paths
    """
    saved = []

    # Save corpus statistics
    corpus_stats_path = os.path.join(data_dir, "corpus_statistics.json")
    with open(corpus_stats_path, "w") as f:
        json.dump(results["corpus_stats"], f, indent=2, default=str)
    saved.append(corpus_stats_path)

    # Save domain statistics
    domain_stats = {}
    for domain_name, data in results["domain_data"].items():
        domain_stats[domain_name] = {
            "term_count": data["term_count"],
            "avg_confidence": float(data["avg_confidence"]),
            "total_frequency": data["total_frequency"],
            "bridging_term_count": len(data["bridging_terms"]),
            "bridging_terms": list(data["bridging_terms"]),
        }
    domain_stats_path = os.path.join(data_dir, "domain_statistics.json")
    with open(domain_stats_path, "w") as f:
        json.dump(domain_stats, f, indent=2, default=str)
    saved.append(domain_stats_path)

    # Save extracted terms summary
    terms_summary = {}
    for term_text, term_obj in results["terms"].items():
        terms_summary[term_text] = {
            "lemma": term_obj.lemma,
            "domains": term_obj.domains,
            "frequency": term_obj.frequency,
            "confidence": term_obj.confidence,
            "n_contexts": len(term_obj.contexts),
        }
    terms_path = os.path.join(data_dir, "extracted_terms.json")
    with open(terms_path, "w") as f:
        json.dump(terms_summary, f, indent=2, default=str)
    saved.append(terms_path)

    # Save concept map summary
    concept_summary = {
        "n_concepts": len(results["concept_map"].concepts),
        "n_relationships": len(results["concept_map"].concept_relationships),
        "concepts": {
            name: {
                "description": c.description,
                "n_terms": len(c.terms),
                "domains": list(c.domains),
                "confidence": c.confidence,
            }
            for name, c in results["concept_map"].concepts.items()
        },
    }
    concept_path = os.path.join(data_dir, "concept_map_summary.json")
    with open(concept_path, "w") as f:
        json.dump(concept_summary, f, indent=2, default=str)
    saved.append(concept_path)

    logger.info(f"\n📊 Saved {len(saved)} data files to {data_dir}")
    for s in saved:
        logger.info(f"   - {os.path.basename(s)}")

    return saved


# ═══════════════════════════════════════════════════════════════════════
#  Figure Registry
# ═══════════════════════════════════════════════════════════════════════

def _register_figures_with_manager(figures: List[str], figure_dir: str) -> None:
    """Register generated figures with FigureManager for cross-referencing."""
    try:
        from src.visualization.figure_manager import FigureManager

        registry_file = os.path.join(figure_dir, "figure_registry.json")
        fm = FigureManager(registry_file=registry_file)

        figure_metadata = {
            "concept_map.png": {
                "label": "fig:concept_map",
                "caption": "Ento-Linguistic Concept Map",
                "section": "introduction",
            },
            "terminology_network.png": {
                "label": "fig:terminology_network",
                "caption": "Terminology Network with Domain Clustering",
                "section": "experimental_results",
            },
            "domain_comparison.png": {
                "label": "fig:domain_comparison",
                "caption": "Cross-Domain Terminology Comparison",
                "section": "experimental_results",
            },
            "domain_overlap_heatmap.png": {
                "label": "fig:domain_overlap",
                "caption": "Domain Term Overlap Heatmap",
                "section": "experimental_results",
            },
            "anthropomorphic_framing.png": {
                "label": "fig:anthropomorphic",
                "caption": "Anthropomorphic Framing Analysis",
                "section": "discussion",
            },
        }

        registered = 0
        for fig_path in figures:
            filename = os.path.basename(fig_path)
            if filename in figure_metadata:
                meta = figure_metadata[filename]
                fm.register_figure(
                    filename=filename,
                    caption=meta["caption"],
                    label=meta["label"],
                    section=meta["section"],
                )
                registered += 1

        logger.info(f"✅ Registered {registered} figures with FigureManager")

    except ImportError:
        logger.warning("⚠️  FigureManager not available, skipping registration")
    except Exception as e:
        logger.warning(f"⚠️  Could not register figures: {e}")


# ═══════════════════════════════════════════════════════════════════════
#  Main Entry Point
# ═══════════════════════════════════════════════════════════════════════

def main() -> None:
    """Generate all research figures and data using the real analysis pipeline."""
    output_dir, data_dir, figure_dir = _setup_directories()

    logger.info("=" * 70)
    logger.info("  Ento-Linguistic Research Figure Generation Pipeline")
    logger.info("=" * 70)
    logger.info(f"  Output: {output_dir}")
    logger.info(f"  Corpus: {len(SYNTHETIC_ABSTRACTS)} synthetic abstracts")
    logger.info("")

    # ── Run analysis pipeline ─────────────────────────────────────────
    logger.info("▶ Running analysis pipeline...")
    results = run_analysis_pipeline(SYNTHETIC_ABSTRACTS)
    logger.info("")

    # ── Generate figures ──────────────────────────────────────────────
    logger.info("▶ Generating figures...")
    figures = []

    fig_path = generate_concept_map(results, figure_dir)
    if fig_path:
        figures.append(fig_path)

    fig_path = generate_terminology_network(results, figure_dir)
    if fig_path:
        figures.append(fig_path)

    fig_path = generate_domain_comparison(results, figure_dir)
    if fig_path:
        figures.append(fig_path)

    fig_path = generate_domain_overlap_heatmap(results, figure_dir)
    if fig_path:
        figures.append(fig_path)

    fig_path = generate_anthropomorphic_analysis(results, figure_dir)
    if fig_path:
        figures.append(fig_path)

    logger.info("")

    # ── Save data ─────────────────────────────────────────────────────
    data_files = save_analysis_data(results, data_dir)

    # ── Register figures ──────────────────────────────────────────────
    _register_figures_with_manager(figures, figure_dir)

    # ── Summary ───────────────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 70)
    logger.info(f"  ✅ Generated {len(figures)} research figures")
    for fig in figures:
        logger.info(f"     - {os.path.basename(fig)}")
    logger.info(f"  ✅ Saved {len(data_files)} data files")
    logger.info(f"  📁 All outputs: {output_dir}")
    logger.info("=" * 70)

    # Also print for subprocess test capture
    print("Integration with src/ modules demonstrated")

    # ── Validation (if infrastructure available) ──────────────────────
    if INFRASTRUCTURE_AVAILABLE and validate_figure_registry:
        try:
            registry_path = Path(figure_dir) / "figure_registry.json"
            manuscript_dir = Path(project_root) / "manuscript"
            validate_figure_registry(registry_path, manuscript_dir)
            logger.info("✅ Figure registry validation passed")
        except Exception as exc:
            logger.warning(f"⚠️  Figure registry validation warning: {exc}")

    if INFRASTRUCTURE_AVAILABLE and verify_output_integrity:
        try:
            verify_output_integrity(Path(output_dir))
            logger.info("✅ Output integrity check passed")
        except Exception as exc:
            logger.warning(f"⚠️  Output integrity warning: {exc}")


if __name__ == "__main__":
    main()
