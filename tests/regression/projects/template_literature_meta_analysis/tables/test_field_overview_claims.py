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

Import isolation: register the real source package under its installed canonical
namespace, ``template_literature_meta_analysis``. Cached canonical modules must
originate in this exact owned source tree. Generic sibling packages remain
untouched; scientific imports never depend on a process-wide alias or finder.
"""

from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
PROJECT_ROOT = REPO_ROOT / "projects" / "templates" / "template_literature_meta_analysis"
_SRC = PROJECT_ROOT / "src"
_FIXTURE_CORPUS = PROJECT_ROOT / "data" / "fixtures" / "modafinil_corpus.jsonl"

_PACKAGE = "template_literature_meta_analysis"


def _load_source_package() -> ModuleType:
    """Admit only this tree's canonical source package and cached descendants."""
    expected_root = _SRC.resolve(strict=True)
    expected_init = expected_root / "__init__.py"
    for name, loaded in tuple(sys.modules.items()):
        if name != _PACKAGE and not name.startswith(_PACKAGE + "."):
            continue
        suffix = name.removeprefix(_PACKAGE).lstrip(".")
        parts = suffix.split(".") if suffix else []
        if any(not part.isidentifier() for part in parts):
            raise ValueError(f"canonical Literature module identity differs: {name}")
        location = expected_root.joinpath(*parts)
        package_init = location / "__init__.py"
        is_package = package_init.is_file()
        expected_origin = package_init if is_package else location.with_suffix(".py")
        origin = getattr(loaded, "__file__", None)
        spec = getattr(loaded, "__spec__", None)
        if (
            not isinstance(origin, str)
            or not expected_origin.is_file()
            or Path(origin).resolve(strict=True) != expected_origin
            or getattr(spec, "origin", None) != origin
        ):
            raise ValueError(f"canonical Literature source origin differs: {name}")
        if (
            getattr(loaded, "__name__", None) != name
            or getattr(spec, "name", None) != name
            or getattr(loaded, "__package__", None) != (name if is_package else name.rsplit(".", 1)[0])
        ):
            raise ValueError(f"canonical Literature module identity differs: {name}")
        paths = getattr(loaded, "__path__", None)
        spec_paths = getattr(spec, "submodule_search_locations", None)
        if is_package:
            if (
                paths is None
                or spec_paths is None
                or any(
                    [Path(path).resolve(strict=True) for path in actual] != [location] for actual in (paths, spec_paths)
                )
            ):
                raise ValueError(f"canonical Literature source search path differs: {name}")
        elif paths is not None or spec_paths is not None:
            raise ValueError(f"canonical Literature module search path differs: {name}")
    existing = sys.modules.get(_PACKAGE)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(_PACKAGE, expected_init, submodule_search_locations=[str(_SRC)])
    assert spec is not None and spec.loader is not None, f"cannot load {expected_init}"
    package = importlib.util.module_from_spec(spec)
    sys.modules[_PACKAGE] = package
    try:
        spec.loader.exec_module(package)
    except BaseException:
        sys.modules.pop(_PACKAGE, None)
        raise
    return package


_load_source_package()
_literature_corpus, _literature_models, _analysis_descriptive, _analysis_temporal = (
    importlib.import_module(f"{_PACKAGE}.{name}")
    for name in ("literature.corpus", "literature.models", "analysis.descriptive_stats", "analysis.temporal_analysis")
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
