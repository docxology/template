"""Regression pins for the literature meta-analysis field-overview claims.

Manuscript: projects/templates/template_literature_meta_analysis/manuscript/
03a_results_field_overview.md.

This exemplar's live pipeline retrieves records from multiple engines over the
network. The regression tier must NOT hit the network, so every value here is
re-derived OFFLINE from the committed deterministic seed corpus
``data/fixtures/modafinil_corpus.jsonl`` (80 synthetic records, reserved
``10.5555/`` test DOIs, RNG seed 42) -- the same corpus the offline default run
uses -- by calling the real source functions ``Corpus.load`` /
``descriptive_stats`` / ``citation_distribution`` / ``compute_temporal_metrics``.
Those are exactly the functions whose outputs ``src/manuscript/variables.py``
injects into the ``{{CORPUS_SIZE}}`` / ``{{UNIQUE_AUTHORS}}`` / ``{{CITATION_MAX}}``
/ ``{{CITATION_TOTAL}}`` / ``{{GINI_COEFFICIENT}}`` / ``{{PEAK_YEAR}}`` /
``{{PCT_WITH_DOI}}`` manuscript tokens -- never by hand-copying a number from
the manuscript.

No mocks, no network: real deterministic objects loaded from a committed
artifact only, in line with the repo no-mock / no-network-in-CI policy (mirrors
``template_search_project``'s offline ``corpus.json`` convention).

Import isolation: every public exemplar ships a top-level ``src`` package, so a
bare ``sys.path.insert`` + ``from src...`` collides on ``sys.modules['src']``
once a second project's regression test joins the same pytest session. This
file loads the exemplar's ``src`` package under a project-unique alias
(``_literature_meta_analysis_src``). Because this exemplar's own modules use
*absolute* imports (``from literature.models import Paper``, ``from
analysis.subfield_defaults import ...``), the loader also installs a
project-scoped ``sys.meta_path`` finder that resolves this exemplar's top-level
``src`` names from its own ``src/`` directory only -- so those absolute imports
resolve without a global ``sys.path`` entry, and it never shadows another
exemplar that also ships a top-level ``analysis`` package (e.g.
``template_code_project``).
"""

from __future__ import annotations

import importlib
import importlib.util
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec, PathFinder
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
PROJECT_ROOT = REPO_ROOT / "projects" / "templates" / "template_literature_meta_analysis"
_SRC = PROJECT_ROOT / "src"
_FIXTURE_CORPUS = PROJECT_ROOT / "data" / "fixtures" / "modafinil_corpus.jsonl"

_PKG_ALIAS = "_literature_meta_analysis_src"

# Top-level module names this exemplar's own code imports *absolutely*
# (``from analysis.subfield_defaults import ...``, ``from literature.models
# import Paper``). The scoped finder below resolves exactly these -- and only
# these -- from this project's own ``src/`` directory.
_TOP_LEVEL = frozenset(
    {
        "literature",
        "analysis",
        "manuscript",
        "knowledge_graph",
        "visualization",
        "config",
        "config_loader",
        "deep_research",
    }
)


class _SrcScopedFinder(MetaPathFinder):
    """Resolve this exemplar's top-level ``src`` names from its own ``src/`` only.

    Installed on ``sys.meta_path`` so the exemplar's absolute intra-package
    imports resolve to the project's own tree without a global ``sys.path``
    entry. Scoping to ``_TOP_LEVEL`` means another exemplar that also ships a
    top-level package of the same name (e.g. ``template_code_project``'s
    ``analysis``) is unaffected once *it* is imported first, because the
    already-cached ``sys.modules`` entry wins before ``sys.meta_path`` is
    consulted; conversely this finder only ever points at *this* project's
    ``src/``.
    """

    def find_spec(
        self,
        fullname: str,
        path: Any = None,
        target: ModuleType | None = None,
    ) -> ModuleSpec | None:
        if fullname.split(".")[0] not in _TOP_LEVEL:
            return None
        return PathFinder.find_spec(fullname, [str(_SRC)], target)


def _load_src_package() -> ModuleType:
    """Load this exemplar's ``src`` package under a project-unique alias.

    Registers the package under the ``_literature_meta_analysis_src`` alias so
    the loaded object is collision-free across projects.
    """

    if _PKG_ALIAS in sys.modules:
        return sys.modules[_PKG_ALIAS]
    src_init = _SRC / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        _PKG_ALIAS,
        src_init,
        submodule_search_locations=[str(_SRC)],
    )
    assert spec is not None and spec.loader is not None, f"cannot load {src_init}"
    package = importlib.util.module_from_spec(spec)
    sys.modules[_PKG_ALIAS] = package
    spec.loader.exec_module(package)
    return package


def _load_absolute_submodules(*dotted_names: str) -> tuple[ModuleType, ...]:
    """Import top-level ``src`` submodules (e.g. ``analysis.descriptive_stats``).

    ``_SrcScopedFinder`` is installed on ``sys.meta_path`` only for the
    duration of this call, and every ``sys.modules`` entry it causes to be
    added under one of ``_TOP_LEVEL`` is popped again afterward (restoring
    whatever was cached there before, if anything). An earlier version left
    the finder and the cached modules in place permanently, which silently
    hijacked *any* later ``import config`` (etc.) system-wide for the rest of
    the pytest session -- it broke ``template_madlib``'s unrelated top-level
    ``config`` module once both exemplars' regression tests were collected
    together, because a bare ``import config`` always checks ``sys.modules``
    (and now ``sys.meta_path``) before consulting the caller's own
    ``sys.path`` manipulation.
    """

    _load_src_package()
    pre_existing = {name: sys.modules.get(name) for name in _TOP_LEVEL}
    finder = _SrcScopedFinder()
    sys.meta_path.insert(0, finder)
    try:
        return tuple(importlib.import_module(dotted) for dotted in dotted_names)
    finally:
        sys.meta_path.remove(finder)
        for name, existing in pre_existing.items():
            found_new = {key: mod for key, mod in sys.modules.items() if key == name or key.startswith(f"{name}.")}
            for key in found_new:
                del sys.modules[key]
            if existing is not None:
                sys.modules[name] = existing


_literature_corpus, _literature_models, _analysis_descriptive, _analysis_temporal = _load_absolute_submodules(
    "literature.corpus", "literature.models", "analysis.descriptive_stats", "analysis.temporal_analysis"
)
Corpus = _literature_corpus.Corpus
Paper = _literature_models.Paper
descriptive_stats = _analysis_descriptive.descriptive_stats
citation_distribution = _analysis_descriptive.citation_distribution
compute_temporal_metrics = _analysis_temporal.compute_temporal_metrics


def _pin(pinned: dict[str, Any], key: str) -> dict[str, Any]:
    entry = pinned[key]
    assert isinstance(entry, dict), f"{key} must be an object"
    assert "value" in entry, f"{key} must include a pinned value"
    return entry


def _assert_pin_matches(entry: dict[str, Any], observed: float | int) -> None:
    tolerance = entry.get("abs_tolerance", 0)
    assert observed == pytest.approx(entry["value"], abs=tolerance)


@pytest.fixture(scope="module")
def corpus_papers() -> list[Any]:
    """Load the committed deterministic seed corpus once (offline, no network)."""

    assert _FIXTURE_CORPUS.exists(), f"missing committed fixture corpus {_FIXTURE_CORPUS}"
    papers = Corpus.load(_FIXTURE_CORPUS).papers
    # Guard: these are the real Paper objects, not stand-ins (no-mock policy).
    assert papers and all(isinstance(paper, Paper) for paper in papers)
    return papers


@pytest.fixture(scope="module")
def stats(corpus_papers: list[Any]) -> dict[str, Any]:
    """Re-derive descriptive bibliometrics exactly as variables.py reads them."""

    return descriptive_stats(corpus_papers)


def test_field_overview_size_and_identifier_claims_rederive_from_source(
    load_pinned_values: Any,
    corpus_papers: list[Any],
    stats: dict[str, Any],
) -> None:
    """Bind the corpus-size, unique-author, and DOI-coverage claims to source.

    03a_results_field_overview.md / Field Overview + Descriptive Bibliometrics
    + Identifier and Full-Text Coverage. These are the {{CORPUS_SIZE}},
    {{UNIQUE_AUTHORS}}, and {{PCT_WITH_DOI}} tokens.
    """

    pinned = load_pinned_values("template_literature_meta_analysis")

    # {{CORPUS_SIZE}} == len(papers) (what variables.compute_variables uses).
    _assert_pin_matches(_pin(pinned, "field_overview_corpus_size"), len(corpus_papers))

    # {{UNIQUE_AUTHORS}} == descriptive_stats(papers)['unique_authors'].
    _assert_pin_matches(_pin(pinned, "field_overview_unique_authors"), stats["unique_authors"])

    # {{PCT_WITH_DOI}}: every synthetic record carries a reserved 10.5555/ DOI,
    # so this is exactly 100.0. Cross-check the raw DOI count matches the corpus
    # size the percentage is computed against.
    doi_count = sum(1 for paper in corpus_papers if paper.doi)
    assert doi_count == len(corpus_papers)
    _assert_pin_matches(_pin(pinned, "field_overview_pct_with_doi"), stats["pct_with_doi"])


def test_descriptive_bibliometrics_citation_claims_rederive_from_source(
    load_pinned_values: Any,
    corpus_papers: list[Any],
    stats: dict[str, Any],
) -> None:
    """Bind the citation max/total and Gini-coefficient claims to source.

    03a_results_field_overview.md / Descriptive Bibliometrics. These are the
    {{CITATION_MAX}}, {{CITATION_TOTAL}}, and {{GINI_COEFFICIENT}} tokens. The
    Gini is pinned at full float precision (manuscript renders 0.398 via
    variables.py's ``f'{gini:.3f}'``) to catch sub-display drift.
    """

    pinned = load_pinned_values("template_literature_meta_analysis")
    dist = citation_distribution(corpus_papers)

    _assert_pin_matches(_pin(pinned, "bibliometrics_citation_count_max"), stats["citation_count_max"])

    # descriptive_stats and citation_distribution must agree on the total; pin
    # the descriptive_stats value and assert the independent path matches it.
    total_pin = _pin(pinned, "bibliometrics_citation_count_total")
    _assert_pin_matches(total_pin, stats["citation_count_total"])
    assert dist["total_citations"] == stats["citation_count_total"]

    _assert_pin_matches(_pin(pinned, "bibliometrics_gini_coefficient"), dist["gini"])


def test_field_overview_peak_year_claim_rederives_from_source(
    load_pinned_values: Any,
    corpus_papers: list[Any],
) -> None:
    """Bind the peak-publication-year claim to source.

    03a_results_field_overview.md / Field Overview + RQ1. The {{PEAK_YEAR}}
    token is compute_temporal_metrics(papers)['peak_year'].
    """

    pinned = load_pinned_values("template_literature_meta_analysis")
    temporal = compute_temporal_metrics(corpus_papers)
    _assert_pin_matches(_pin(pinned, "field_overview_peak_year"), temporal["peak_year"])


def test_pin_mutation_negative_control_fails(load_pinned_values: Any) -> None:
    """Changing a committed pin must fail the comparison predicate.

    Non-vacuity control (feedback-verify-not-trust-machine-proof): proves the
    assertions above can actually fail, so a green run means the re-derivation
    genuinely matched the pin -- not that the comparison is a no-op.
    """

    pinned = load_pinned_values("template_literature_meta_analysis")
    entry = dict(_pin(pinned, "field_overview_corpus_size"))
    observed = entry["value"]
    entry["value"] = observed + 1  # perturb the pinned ground truth

    with pytest.raises(AssertionError):
        _assert_pin_matches(entry, observed)
