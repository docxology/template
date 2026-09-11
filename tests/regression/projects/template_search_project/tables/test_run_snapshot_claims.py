"""Regression pins for the template_search_project "Run snapshot" claims.

Manuscript: projects/templates/template_search_project/manuscript/
00_abstract.md and 03_results.md ("Run snapshot" paragraph) plus
02_methodology.md (auto-populated references.bib / collision-free
citation keys).

This exemplar is a literature-search → BibTeX → LLM-synthesis template
whose live pipeline can fan out to arXiv / Crossref over the network.
The regression tier must NOT hit the network, so every value here is
re-derived OFFLINE from the committed deterministic corpus
``data/corpus.json`` (6 curated papers, ``sources: [local]`` -- the
CI-safe default in ``manuscript/config.yaml``) by calling the real
source functions the manuscript pipeline uses:

- ``{{RESULT_NUM_PAPERS}}`` == ``len(result.papers)`` from
  ``infrastructure.search.literature.LiteratureClient.search`` over a
  ``LocalBackend`` reading the corpus (the search stage of
  ``src.pipeline.run_literature_pipeline``).
- ``{{RESULT_WITH_DOI}}`` / ``{{RESULT_WITH_ABSTRACT}}`` ==
  ``src.manuscript_variables.compute_variables(...).result_with_doi`` /
  ``.result_with_abstract`` -- exactly the pure token computer whose
  fields ``scripts/z_generate_manuscript_variables.py`` injects into
  the manuscript.
- BibTeX entry count + collision-free citation-key count ==
  ``len(bib_entries)`` / ``len(set(citation_keys.values()))`` from
  ``src.pipeline._build_citation_keys(result.papers)`` -- the stage
  that writes ``manuscript/references.bib``.

No mocks, no network: real deterministic objects loaded from a
committed artifact only. ``AbstractFetcher`` short-circuits with status
``skipped`` for every corpus paper (all six ship an abstract), so even
the standard pipeline is genuinely network-free for this corpus; these
pins bind to the pure functions directly rather than to the
regeneratable on-disk ``output/`` artefacts, in line with the repo
no-mock / no-network-in-CI policy.

Import isolation (historical): before SUBMODULAR-SEARCH-1 every public exemplar shipped a top-level ``src``
package, so a bare ``sys.path.insert`` + ``from src...`` collides on
``sys.modules['src']`` once a second project's regression test joins
the same pytest session. Unlike ``template_prose_project`` (whose
``manuscript_variables`` uses only *relative* imports and loads cleanly
under a plain project-unique alias), THIS exemplar's
``src/manuscript_variables.py`` does ``from src.config import
DeepSearchConfig`` -- an *absolute* ``src.`` import that
``src/__init__.py`` imports eagerly -- so the plain-alias pattern fails
at package load with ``ModuleNotFoundError: No module named 'src'``.
This file therefore loads the exemplar's ``src`` package under a
project-unique alias (``_search_project_src``) AND installs a
project-scoped ``sys.meta_path`` finder (like
``template_literature_meta_analysis``) that resolves the bare ``src``
name to *this* project's ``src/`` directory only -- never a global
``sys.path`` entry -- so the absolute import resolves without shadowing
another exemplar that also ships top-level packages of the same name.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
PROJECT_ROOT = REPO_ROOT / "projects" / "templates" / "template_search_project"
_SRC = PROJECT_ROOT / "src" / "template_search_project"
_FIXTURE_CORPUS = PROJECT_ROOT / "data" / "corpus.json"

# SUBMODULAR-SEARCH-1: the exemplar package is a regular nested package
# (``src/template_search_project/``) whose modules import via absolute
# ``template_search_project.*`` paths, so the exemplar imports directly --
# no project-unique alias or scoped meta-path finder is needed. The alias
# machinery existed only to resolve the pre-split flat layout's absolute
# ``from src.config import ...`` imports, which no longer exist.
from template_search_project.pipeline.pipeline import _build_citation_keys  # noqa: E402
from template_search_project.publish.manuscript_variables import (  # noqa: E402
    compute_variables,
)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))  # needed for ``infrastructure.*``; shared-safe, no top-level collision

assert _SRC.is_dir(), f"exemplar package missing: {_SRC}"
# Repo-wide infrastructure (shared safely -- only the project-local
# ``src`` package needs the alias / finder isolation above).
from infrastructure.search.literature import (  # noqa: E402
    LiteratureClient,
    LocalBackend,
    Paper,
    SearchQuery,
)


# The offline defaults from ``manuscript/config.yaml`` -- kept in sync
# with the ``verifier_args`` recorded in the pinned-values JSON.
_QUERY_TEXT = "reproducible research optimization"
_MAX_RESULTS = 100


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
    """Run the deterministic local search once (offline, no network).

    This is exactly the search stage of ``run_literature_pipeline``: a
    ``LiteratureClient`` over a single ``LocalBackend`` reading the
    committed ``data/corpus.json``. Returns the deduplicated
    ``result.papers`` list the manuscript's ``{{RESULT_*}}`` tokens are
    computed from.
    """

    assert _FIXTURE_CORPUS.exists(), f"missing committed fixture corpus {_FIXTURE_CORPUS}"
    client = LiteratureClient([LocalBackend(_FIXTURE_CORPUS)], cache=None)
    query = SearchQuery(text=_QUERY_TEXT, max_results=_MAX_RESULTS, year_min=None, year_max=None)
    papers = client.search(query, use_cache=False).papers
    # Guard: these are the real Paper objects, not stand-ins (no-mock policy).
    assert papers and all(isinstance(paper, Paper) for paper in papers)
    return papers


@pytest.fixture(scope="module")
def manuscript_vars(corpus_papers: list[Any]) -> Any:
    """Re-derive the run-snapshot tokens exactly as variables.py reads them."""

    payload = {
        "papers": [paper.to_dict() for paper in corpus_papers],
        "per_source_counts": {"local": len(corpus_papers)},
        "errors": {},
        "query": {},
    }
    return compute_variables(
        config_query=_QUERY_TEXT,
        config_max_results=_MAX_RESULTS,
        config_sources=["local"],
        search_result_payload=payload,
    )


def test_run_snapshot_paper_count_rederives_from_source(
    load_pinned_values: Any,
    corpus_papers: list[Any],
    manuscript_vars: Any,
) -> None:
    """Bind the {{RESULT_NUM_PAPERS}} claim to source.

    00_abstract.md + 03_results.md / Run snapshot. The paper count the
    search stage returns == compute_variables(...).result_num_papers ==
    len(result.papers); assert both paths agree and match the pin.
    """

    pinned = load_pinned_values("template_search_project")
    _assert_pin_matches(_pin(pinned, "run_num_papers"), len(corpus_papers))
    # The pure token computer must agree with the raw search-stage count.
    assert manuscript_vars.result_num_papers == len(corpus_papers)


def test_run_snapshot_enrichment_coverage_rederives_from_source(
    load_pinned_values: Any,
    corpus_papers: list[Any],
    manuscript_vars: Any,
) -> None:
    """Bind the {{RESULT_WITH_DOI}} and {{RESULT_WITH_ABSTRACT}} claims to source.

    00_abstract.md + 03_results.md / Run snapshot. These are the honest
    enrichment-coverage counts (03_results.md: "count fields the corpus
    or the AbstractFetcher actually populated, never values inferred").
    Cross-check the raw corpus-field counts against compute_variables.
    """

    pinned = load_pinned_values("template_search_project")

    _assert_pin_matches(_pin(pinned, "run_with_doi"), manuscript_vars.result_with_doi)
    _assert_pin_matches(_pin(pinned, "run_with_abstract"), manuscript_vars.result_with_abstract)

    # Independent path: recount the fields directly on the Paper objects
    # and assert compute_variables agrees (guards the token computer).
    raw_with_doi = sum(1 for paper in corpus_papers if paper.doi)
    raw_with_abstract = sum(1 for paper in corpus_papers if paper.abstract)
    assert manuscript_vars.result_with_doi == raw_with_doi
    assert manuscript_vars.result_with_abstract == raw_with_abstract


def test_bibtex_entry_and_citation_key_claims_rederive_from_source(
    load_pinned_values: Any,
    corpus_papers: list[Any],
) -> None:
    """Bind the auto-populated references.bib claims to source.

    02_methodology.md / stage 3 + 03_results.md output list. The BibTeX
    stage builds one collision-free citation key + BibEntry per
    deduplicated paper via _build_citation_keys. Pin both the entry
    count and that the keys are collision-free (unique-key count ==
    paper count).
    """

    pinned = load_pinned_values("template_search_project")
    citation_keys, bib_entries = _build_citation_keys(corpus_papers)

    _assert_pin_matches(_pin(pinned, "bibtex_entry_count"), len(bib_entries))
    _assert_pin_matches(_pin(pinned, "bibtex_unique_citation_keys"), len(set(citation_keys.values())))

    # The 'collision-free' claim: as many distinct keys as papers, and
    # one BibEntry per paper.
    assert len(bib_entries) == len(corpus_papers)
    assert len(set(citation_keys.values())) == len(corpus_papers)


def test_pin_mutation_negative_control_fails(load_pinned_values: Any) -> None:
    """Changing a committed pin must fail the comparison predicate.

    Non-vacuity control (feedback-verify-not-trust-machine-proof): proves
    the assertions above can actually fail, so a green run means the
    re-derivation genuinely matched the pin -- not that the comparison is
    a no-op.
    """

    pinned = load_pinned_values("template_search_project")
    entry = dict(_pin(pinned, "run_num_papers"))
    observed = entry["value"]
    entry["value"] = observed + 1  # perturb the pinned ground truth

    with pytest.raises(AssertionError):
        _assert_pin_matches(entry, observed)
