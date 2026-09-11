"""Regression pins for the deterministic prose-review editorial claims.

Manuscript: projects/templates/template_prose_project/manuscript/.
These tests bind the quantitative claims in the abstract "Run snapshot"
paragraph (00_abstract.md) and the ``bibliography_consistency`` claim in the
Results section (03_results.md) to a *fresh* re-derivation from the committed
manuscript source — never to the on-disk ``output/`` artefacts, which are
regeneratable and can lag the committed source (see the ``_meta.note`` in
``pinned_values/template_prose_project.json`` for the concrete drift caught at
pin time).

No mocks: the values are recomputed by calling the same deterministic source
functions the pipeline uses — ``infrastructure.prose.analyze_manuscript`` and
``src.pipeline.prose_facade.parse_bib_keys`` — over the real manuscript directory.
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
PROJECT_ROOT = REPO_ROOT / "projects" / "templates" / "template_prose_project"
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.prose import analyze_manuscript  # noqa: E402


# SUBMODULAR-PROSE-1: the exemplar package is a regular nested package
# (``src/template_prose_project/``) whose modules import via absolute
# ``template_prose_project.*`` paths, so the exemplar imports directly --
# the project-unique alias machinery existed only to resolve the pre-split
# flat layout's ``from src.config import ...`` imports, which no longer
# exist (and a dotted alias import cannot address subpackages by path).
from template_prose_project.pipeline.config import load_project_config  # noqa: E402
from template_prose_project.manuscript.manuscript_variables import (  # noqa: E402
    ManuscriptVariables,
    compute_variables,
)
from template_prose_project.pipeline.prose_facade import parse_bib_keys  # noqa: E402


def _pin(pinned: dict[str, Any], key: str) -> dict[str, Any]:
    entry = pinned[key]
    assert isinstance(entry, dict), f"{key} must be an object"
    assert "value" in entry, f"{key} must include a pinned value"
    return entry


def _assert_pin_matches(entry: dict[str, Any], observed: float | int) -> None:
    tolerance = entry.get("abs_tolerance", 0)
    assert observed == pytest.approx(entry["value"], abs=tolerance)


@pytest.fixture(scope="module")
def manuscript_dir() -> Path:
    """Resolved path to the committed manuscript directory."""

    config = load_project_config(PROJECT_ROOT / "manuscript" / "config.yaml")
    return (PROJECT_ROOT / config.manuscript_dir).resolve()


@pytest.fixture(scope="module")
def derived_variables(manuscript_dir: Path) -> ManuscriptVariables:
    """Re-derive the manuscript substitution variables from committed source.

    Mirrors ``scripts/z_generate_manuscript_variables.py`` /
    ``scripts/run_prose_pipeline.py`` but computes in-process from the source
    functions rather than reading the disposable ``output/`` JSON.
    """

    config = load_project_config(PROJECT_ROOT / "manuscript" / "config.yaml")
    report = analyze_manuscript(
        manuscript_dir,
        long_sentence_threshold=config.prose.long_sentence_threshold,
    )
    return compute_variables(config_title=config.title, manuscript_report=report.to_dict())


def test_abstract_run_snapshot_claims_rederive_from_source(
    load_pinned_values: Any,
    derived_variables: ManuscriptVariables,
) -> None:
    """Bind the abstract Run-snapshot counts + readability to a fresh source run."""

    pinned = load_pinned_values("template_prose_project")

    _assert_pin_matches(_pin(pinned, "abstract_files_analysed"), derived_variables.files_analysed)
    _assert_pin_matches(_pin(pinned, "abstract_total_words"), derived_variables.total_words)
    _assert_pin_matches(_pin(pinned, "abstract_total_sentences"), derived_variables.total_sentences)
    _assert_pin_matches(_pin(pinned, "abstract_avg_grade_level"), derived_variables.avg_grade_level)
    _assert_pin_matches(_pin(pinned, "abstract_citation_count"), derived_variables.citation_count)


def test_bibliography_consistency_claim_rederives_from_source(
    load_pinned_values: Any,
    manuscript_dir: Path,
) -> None:
    """Bind the Results ``bibliography_consistency`` claim to the committed bib.

    The prose asserts every cited key resolves against ``references.bib``. We
    re-derive the count of BibTeX entries that are present but never cited
    (the ``unused`` set) directly from source and pin it at 0.
    """

    pinned = load_pinned_values("template_prose_project")

    config = load_project_config(PROJECT_ROOT / "manuscript" / "config.yaml")
    report = analyze_manuscript(
        manuscript_dir,
        long_sentence_threshold=config.prose.long_sentence_threshold,
    )
    bib_keys = parse_bib_keys(manuscript_dir / "references.bib")
    cited_keys = set(report.citation_keys)
    unused = bib_keys - cited_keys
    missing = cited_keys - bib_keys

    # The claim: no cited key is missing from the bib.
    assert missing == set(), f"cited keys missing from bib: {sorted(missing)}"
    _assert_pin_matches(_pin(pinned, "bibliography_unused_entries"), len(unused))


def test_pin_mutation_negative_control_fails(load_pinned_values: Any) -> None:
    """Changing a committed pin must fail the comparison predicate.

    Non-vacuity control: proves the assertion harness actually discriminates a
    wrong value rather than passing unconditionally.
    """

    pinned = load_pinned_values("template_prose_project")
    entry = dict(_pin(pinned, "abstract_total_words"))
    observed = entry["value"]
    entry["value"] = observed + 1

    with pytest.raises(AssertionError):
        _assert_pin_matches(entry, observed)
