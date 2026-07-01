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

Import isolation: every public exemplar ships a top-level ``src``
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
PROJECT_ROOT = REPO_ROOT / "projects" / "templates" / "template_search_project"
_SRC = PROJECT_ROOT / "src"
_FIXTURE_CORPUS = PROJECT_ROOT / "data" / "corpus.json"

_PKG_ALIAS = "_search_project_src"

# The only top-level module name this exemplar's own code imports
# *absolutely* is ``src`` itself (``from src.config import
# DeepSearchConfig`` in ``manuscript_variables.py``). The scoped finder
# below resolves exactly that -- and only that -- from this project's
# own directory.
_TOP_LEVEL = frozenset({"src"})


class _SrcScopedFinder(MetaPathFinder):
    """Resolve this exemplar's bare ``src`` name from its own directory only.

    Installed on ``sys.meta_path`` so the exemplar's absolute
    ``from src.config import ...`` resolves to *this* project's ``src/``
    tree without a global ``sys.path`` entry that would collide with
    another exemplar's top-level packages once both regression tests run
    in the same pytest session. Scoping to ``_TOP_LEVEL`` (just ``src``)
    means an already-cached ``sys.modules['src']`` wins before
    ``sys.meta_path`` is consulted; conversely this finder only ever
    points at *this* project's directory.
    """

    def find_spec(
        self,
        fullname: str,
        path: Any = None,
        target: ModuleType | None = None,
    ) -> ModuleSpec | None:
        if fullname.split(".")[0] not in _TOP_LEVEL:
            return None
        # ``src`` lives directly under PROJECT_ROOT, so search there.
        return PathFinder.find_spec(fullname, [str(PROJECT_ROOT)], target)


def _load_absolute_submodules(*dotted_names: str) -> tuple[ModuleType, ...]:
    """Load this exemplar's ``src`` package (plus the named submodules) under a project-unique alias.

    Installs the project-scoped meta-path finder for the duration of this
    call only, so every absolute ``from src.config import ...`` the package
    init *or* its submodules (``manuscript_variables.py`` does this) perform
    resolves to this project's own ``src/`` tree, then removes the finder and
    pops every ``sys.modules`` entry it caused to be added under the bare
    ``src`` name. An earlier version installed the finder permanently and
    never removed it -- since it matches the single most generic name every
    exemplar uses (``src``), that leak silently redirected any *other*
    exemplar's later absolute ``from src.X import Y`` to *this* project's
    directory instead of its own once both regression tests collected in the
    same pytest session (it broke ``template_sia``'s unrelated
    ``from src.artifact_manifest import ...``, which needs its own ``src``).
    """

    if _PKG_ALIAS in sys.modules:
        package = sys.modules[_PKG_ALIAS]
        return tuple(importlib.import_module(f"{_PKG_ALIAS}.{dotted}") for dotted in dotted_names)

    pre_existing_src = {key: mod for key, mod in sys.modules.items() if key == "src" or key.startswith("src.")}
    finder = _SrcScopedFinder()
    sys.meta_path.insert(0, finder)
    try:
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
        return tuple(importlib.import_module(f"{_PKG_ALIAS}.{dotted}") for dotted in dotted_names)
    finally:
        sys.meta_path.remove(finder)
        for key in [k for k in sys.modules if (k == "src" or k.startswith("src.")) and k not in pre_existing_src]:
            del sys.modules[key]
        sys.modules.update(pre_existing_src)


_pipeline_mod, _manuscript_variables_mod = _load_absolute_submodules("pipeline", "manuscript_variables")
_build_citation_keys = _pipeline_mod._build_citation_keys
compute_variables = _manuscript_variables_mod.compute_variables

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
