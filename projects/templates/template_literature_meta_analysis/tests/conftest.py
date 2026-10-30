"""Pytest configuration for template_literature_meta_analysis tests."""

import importlib.util
import os
import sys
import sysconfig
import tempfile
from pathlib import Path

import pytest

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Select the actual environment-provided SDK before registering own source.
# Pytest may prepend this checkout's tests/root to its import paths. Those own
# paths are not SDK providers, and a guessed ancestor is not a dependency.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
_own_root = Path(ROOT).resolve()
_runtime_paths = sysconfig.get_paths()
_runtime_sites = {Path(_runtime_paths[key]).resolve(strict=True) for key in ("purelib", "platlib")}
_original_import_paths = sys.path[:]
try:
    sys.path[:] = [
        entry
        for entry in sys.path
        if Path(entry or os.getcwd()).resolve() in _runtime_sites
        or not Path(entry or os.getcwd()).resolve().is_relative_to(_own_root)
    ]
    _sdk_spec = importlib.util.find_spec("infrastructure")
    if _sdk_spec is None or _sdk_spec.origin is None:
        raise ImportError("the declared research-project-template dependency is unavailable")
    _sdk_origin = Path(_sdk_spec.origin).resolve(strict=True)
    if _sdk_origin.is_relative_to(_own_root) and not any(
        _sdk_origin.is_relative_to(site_root) for site_root in _runtime_sites
    ):
        raise ImportError("own project source cannot provide the platform SDK")
    import infrastructure  # noqa: E402
finally:
    sys.path[:] = _original_import_paths

if infrastructure.__file__ is None or Path(infrastructure.__file__).resolve(strict=True) != _sdk_origin:
    raise ImportError("the selected platform SDK changed during project startup")

import tomllib  # noqa: E402

_platform_version = tomllib.loads((Path(ROOT) / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["template"][
    "platform_version"
]
if infrastructure.__version__ != _platform_version:
    raise ImportError(f"this project requires platform {_platform_version}; selected {infrastructure.__version__}")

# Register the canonical own source namespace after binding the SDK package.

_package_spec = importlib.util.spec_from_file_location(
    "template_literature_meta_analysis", Path(SRC) / "__init__.py", submodule_search_locations=[SRC]
)
assert _package_spec is not None and _package_spec.loader is not None
_package = importlib.util.module_from_spec(_package_spec)
sys.modules["template_literature_meta_analysis"] = _package
_package_spec.loader.exec_module(_package)

# The repo root's tests/ package (tests/__init__.py) shadows any namespace
# merge with this exemplar's tests/ tree, so ``from tests.knowledge_graph...``
# imports cannot resolve now that the exemplar tests shim is deleted. Register
# the shared LLM-extraction fixtures module directly instead.
_FIXTURES_PATH = os.path.join(ROOT, "tests", "knowledge_graph", "llm_extraction_fixtures.py")
_fixtures_spec = importlib.util.spec_from_file_location("llm_extraction_fixtures", _FIXTURES_PATH)
_llm_extraction_fixtures = importlib.util.module_from_spec(_fixtures_spec)
sys.modules["llm_extraction_fixtures"] = _llm_extraction_fixtures
_fixtures_spec.loader.exec_module(_llm_extraction_fixtures)


# --- Required dependency verification ---
# These packages are listed in pyproject.toml [project.dependencies] and must be present
# for the full test suite to run. Fail fast with a clear message if missing.
REQUIRED_DEPENDENCIES = [
    ("rdflib", "rdflib>=7.0.0"),
    # Marker-aware: the exemplar declares wordcloud only below 3.15 because no
    # cp315 distribution exists, so this frame must not require it there.
    *([("wordcloud", "wordcloud>=1.9.0")] if sys.version_info < (3, 15) else []),
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
        "Install the project's dev extra in its prepared environment (STANDALONE.md), "
        "or use the monorepo Stage-01 project-only gate."
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
        from template_literature_meta_analysis.analysis.subfield_registry import configure_subfields

        configure_subfields(None)
    except Exception as exc:  # pragma: no cover - defensive
        del exc
    try:
        from template_literature_meta_analysis.knowledge_graph.hypothesis import configure_hypotheses

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
    from template_literature_meta_analysis.literature.models import Paper

    return [
        Paper(
            title="Active Inference: A Process Theory",
            abstract=(
                "This paper presents active inference as a unified brain theory based on the free energy principle."
            ),
            year=2017,
            doi="10.1162/NECO_a_00912",
            arxiv_id="1709.02341",
            citation_count=500,
            references=["ref_001", "ref_002"],
        ),
        Paper(
            title="Deep Active Inference Agents Using Monte-Carlo Methods",
            abstract=(
                "We present deep active inference agents that scale to complex environments using neural networks."
            ),
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
    from template_literature_meta_analysis.knowledge_graph.nanopublication import Assertion

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
    from template_literature_meta_analysis.literature.corpus import Corpus

    corpus = Corpus()
    for paper in sample_papers:
        corpus.add(paper)
    corpus_path = Path(tmp_output_dir) / "corpus.jsonl"
    corpus.save(corpus_path)
    return str(corpus_path)
