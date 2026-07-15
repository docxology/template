"""Centralized configuration constants for the literature meta-analysis pipeline.

This module defines all file paths, default parameter values, and system-wide
settings used throughout the analysis scripts. Import from this module instead
of hardcoding literal values to ensure consistency and maintainability.

Project layout
--------------
# output/
# ├── data/           Analysis JSON results and intermediate artifacts
# │   ├── corpus.jsonl
# │   ├── subfield_classification.json
# │   ├── temporal_analysis.json
# │   ├── tfidf_data.json
# │   ├── topics.json
# │   ├── citation_network.json
# │   ├── citation_graph.gml
# │   ├── nanopublications.jsonl
# │   ├── hypothesis_scores.json
# │   ├── hypothesis_trends.json
# │   ├── fulltext_assessment.json
# │   ├── fulltext_extraction.json
# │   ├── workflow_graphs.jsonl
# │   ├── reproducibility_scores.json
# │   └── reproducibility_summary.json
# ├── fulltext/       Downloaded PDFs, extracted .txt, and figures/
# ├── figures/        Publication-ready PNG figures
# └── manuscript/     Rendered markdown with variables injected

Pipeline defaults
-----------------
These constants control the default behavior of the thin orchestrator
scripts in scripts/. Individual scripts may override them via CLI flags.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Project structure
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
PROJECT_NAME = "template_advanced_literature_review"

# Output directories
OUTPUT_DIR = PROJECT_ROOT / "output"
DATA_DIR = OUTPUT_DIR / "data"
FIGURES_DIR = OUTPUT_DIR / "figures"

# Key artifact paths
CORPUS_PATH = DATA_DIR / "corpus.jsonl"
MANUSCRIPT_DIR = PROJECT_ROOT / "manuscript"

# ---------------------------------------------------------------------------
# Analysis defaults (02_meta_analysis_pipeline.py)
# ---------------------------------------------------------------------------
DEFAULT_N_TOPICS = 5
DEFAULT_MAX_FEATURES = 500
DEFAULT_MIN_YEAR = 2000  # Pre-2000 papers excluded from text/temporal analysis
DEFAULT_SEED = 42  # RNG seed for NMF reproducibility

# ---------------------------------------------------------------------------
# Knowledge graph defaults (03_build_knowledge_graph.py)
# ---------------------------------------------------------------------------
KG_MIN_YEAR = 1960  # Pre-1960 papers excluded from KG construction
DEFAULT_LLM_MODEL = "gemma3:4b"
DEFAULT_LLM_URL = "http://localhost:11434"
DEFAULT_CHECKPOINT_INTERVAL = 50

# ---------------------------------------------------------------------------
# Reproducibility assessment defaults (10_reproducibility_assessment.py)
# ---------------------------------------------------------------------------
DEFAULT_REPRO_CHECKPOINT_INTERVAL = 50
# Matches manuscript/config.yaml's `project_config.fulltext.download_dir`
# ("output/fulltext") when no config file / no override is present.
FULLTEXT_DIR = OUTPUT_DIR / "fulltext"

# Literature search defaults (01_literature_search.py).
#
# This template is DOMAIN-AGNOSTIC: the live search term, per-engine queries, and
# relevance keywords are supplied by ``manuscript/config.yaml`` (bundled default:
# "modafinil"). These module-level fallbacks are intentionally EMPTY so that no
# domain term is hardcoded in source — the config file is the single source of
# truth for what to search. ``config_loader`` falls back to these only when no
# config file is present, in which case the caller must pass queries explicitly.
DEFAULT_ARXIV_QUERIES: list[str] = []
DEFAULT_RELEVANCE_KEYWORDS: list[str] = []

# ---------------------------------------------------------------------------
# Figure generation defaults (04_generate_figures.py)
# ---------------------------------------------------------------------------
# Default DPI when saving figures. Individual scripts may override via --dpi.
# See VIZ_CONFIG for full styling palette (font sizes, colors, etc.).
DEFAULT_DPI = 300

# ---------------------------------------------------------------------------
# Visualization styling (imported from visualization.style)
# ---------------------------------------------------------------------------
# Figure size in inches
FIGURE_SIZE = (12, 7)
# DPI used by VIZ_CONFIG (overridden by script --dpi flag)
DPI = 150
# Font sizes (enforced via apply_visual_style())
FONT_SIZE = 18
TICK_SIZE = 16
TITLE_SIZE = 22

__all__ = [
    # Paths
    "PROJECT_ROOT",
    "PROJECT_NAME",
    "OUTPUT_DIR",
    "DATA_DIR",
    "FIGURES_DIR",
    "CORPUS_PATH",
    "MANUSCRIPT_DIR",
    # Analysis defaults
    "DEFAULT_N_TOPICS",
    "DEFAULT_MAX_FEATURES",
    "DEFAULT_MIN_YEAR",
    "DEFAULT_SEED",
    # Knowledge graph defaults
    "KG_MIN_YEAR",
    "DEFAULT_LLM_MODEL",
    "DEFAULT_LLM_URL",
    "DEFAULT_CHECKPOINT_INTERVAL",
    "DEFAULT_REPRO_CHECKPOINT_INTERVAL",
    "FULLTEXT_DIR",
    "DEFAULT_ARXIV_QUERIES",
    "DEFAULT_RELEVANCE_KEYWORDS",
    # Figure defaults
    "DEFAULT_DPI",
    # Visualization styling
    "FIGURE_SIZE",
    "DPI",
    "FONT_SIZE",
    "TICK_SIZE",
    "TITLE_SIZE",
]
