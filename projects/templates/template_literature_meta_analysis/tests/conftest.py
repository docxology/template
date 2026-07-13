"""Pytest configuration for template_literature_meta_analysis tests."""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Add src/ AND the repo root to path so the documented per-project pytest command
# works from a clean environment. The repo root is required because some
# exemplar modules (e.g. deep_research.deep_research_adapter) import the
# top-level ``infrastructure`` package, which only resolves when the repo root
# is on sys.path (see sibling conftest.py files across projects/templates/*
# for the same pattern).
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
REPO_ROOT = os.path.abspath(os.path.join(ROOT, "..", "..", ".."))
for _path in (REPO_ROOT, SRC):
    if _path not in sys.path:
        sys.path.insert(0, _path)


# --- Required dependency verification ---
# These packages are listed in pyproject.toml [project.dependencies] and must be present
# for the full test suite to run. Fail fast with a clear message if missing.
REQUIRED_DEPENDENCIES = [
    ("rdflib", "rdflib>=7.0.0"),
    ("wordcloud", "wordcloud>=1.9.0"),
    ("sklearn", "scikit-learn>=1.3.0"),  # imported as sklearn
]
missing_required = []
for module_name, pkg_spec in REQUIRED_DEPENDENCIES:
    try:
        __import__(module_name)
    except ImportError:
        missing_required.append(pkg_spec)

if missing_required:
    raise ImportError(
        f"Required dependencies not installed for the full test suite: {', '.join(missing_required)}. "
        "Run: uv sync --extra dev (in the project directory)."
    )
# --- End required dependency check ---


def _reset_configurable_globals() -> None:
    """Reset module-level configuration globals to their domain-neutral defaults.

    Several modules cache configured state at module level (``SUBFIELDS``,
    ``HYPOTHESES``, ``HYPOTHESIS_CATEGORIES``). Pipeline/script tests load the
    shipped ``manuscript/config.yaml`` (which defines a different number of
    subfields/hypotheses than the defaults), mutating those globals. Resetting
    around every test keeps unit tests isolated and order-independent.
    """
    try:
        from analysis.subfield_registry import configure_subfields

        configure_subfields(None)
    except Exception as exc:  # pragma: no cover - defensive
        del exc
    try:
        from knowledge_graph.hypothesis import configure_hypotheses

        configure_hypotheses(None)
    except Exception as exc:  # pragma: no cover - defensive
        del exc


@pytest.fixture(autouse=True)
def _isolate_configurable_globals():
    """Autouse: reset configurable module globals before and after each test."""
    _reset_configurable_globals()
    yield
    _reset_configurable_globals()


@pytest.fixture
def sample_papers():
    """Return a list of sample Paper objects for testing."""
    from literature.models import Paper

    return [
        Paper(
            title="Active Inference: A Process Theory",
            abstract="This paper presents active inference as a unified brain theory based on the free energy principle.",
            year=2017,
            doi="10.1162/NECO_a_00912",
            arxiv_id="1709.02341",
            citation_count=500,
            references=["ref_001", "ref_002"],
        ),
        Paper(
            title="Deep Active Inference Agents Using Monte-Carlo Methods",
            abstract="We present deep active inference agents that scale to complex environments using neural networks.",
            year=2020,
            doi="10.5555/deep_aif_2020",
            citation_count=120,
            references=["ref_001"],
        ),
        Paper(
            title="Computational Psychiatry and Active Inference",
            abstract="We model schizophrenia as aberrant precision weighting in clinical psychiatry settings.",
            year=2021,
            doi="10.5555/comp_psych_2021",
            citation_count=45,
            references=[],
        ),
    ]


@pytest.fixture
def sample_assertions():
    """Return a list of sample Assertion objects for testing."""
    from knowledge_graph.nanopublication import Assertion

    return [
        Assertion(
            assertion_id="assert_000001",
            paper_id="paper_001",
            claim="Active inference provides a unified framework.",
            assertion_type="supports",
            hypothesis_id="PRIMARY_EFFICACY",
            confidence=0.9,
            citation_count=500,
        ),
        Assertion(
            assertion_id="assert_000002",
            paper_id="paper_002",
            claim="Deep AIF matches RL performance in discrete tasks.",
            assertion_type="supports",
            hypothesis_id="SCALABILITY",
            confidence=0.7,
            citation_count=120,
        ),
        Assertion(
            assertion_id="assert_000003",
            paper_id="paper_003",
            claim="Markov blanket boundaries are statistical constructs only.",
            assertion_type="contradicts",
            hypothesis_id="MECHANISTIC_BASIS",
            confidence=0.8,
            citation_count=200,
        ),
    ]


@pytest.fixture
def tmp_output_dir():
    """Return a temporary directory for test outputs, cleaned up after test."""
    with tempfile.TemporaryDirectory(prefix="aif_test_") as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_corpus_path(sample_papers, tmp_output_dir):
    """Write sample papers to a temporary JSONL corpus file.

    Returns the path to the created corpus.jsonl file.
    """
    from literature.corpus import Corpus

    corpus = Corpus()
    for paper in sample_papers:
        corpus.add(paper)
    corpus_path = Path(tmp_output_dir) / "corpus.jsonl"
    corpus.save(corpus_path)
    return str(corpus_path)
