"""Regression pins for the deterministic newspaper layout statistics.

Manuscript: projects/templates/template_newspaper/manuscript/04_reproducibility.md.

Unlike the scientific-results exemplars, template_newspaper is a *layout /
rendering* engine, so its quantitative claims are layout statistics rather than
coefficients or p-values. ``04_reproducibility.md`` names them explicitly --
"Every quantitative claim in this project -- the page count, the trim
dimensions, the figure count -- is recorded in ``data/claim_ledger.yaml``
against the artifact that substantiates it" -- and the abstract calls the
edition "twelve-page, large-format". These pins bind those exact numbers to the
source by re-deriving each via the same functions the real render path
(``newspaper.engine.build_and_render``) uses:

* page count      -> ``content.load_edition(content_dir).page_count``
                     (content/edition.yaml lists exactly 12 page files)
* trim width  (pt) -> ``config.load_newspaper_config(content_dir).geometry().width``
* trim height (pt) -> ``config.load_newspaper_config(content_dir).geometry().height``
                     (edition.yaml declares ``page: tabloid`` -> 11in x 17in
                      -> 792 x 1224 pt, the pagesize the Canvas is opened with)
* figure count    -> ``len(figures.generate_all(tmp_path))``
                     (6 halftone scenes + 4 color ad graphics + 3 charts = 13)

The trim pins run through the config loader rather than the bare ``PageGeometry``
default so they exercise the same trim-selection path the renderer uses. The
figure-count pin actually runs the real Pillow/Matplotlib generators into a
``tmp_path`` -- no mocks, in line with the repo no-mock policy -- and never
copies a number from the manuscript or the claim ledger.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
PROJECT_ROOT = REPO_ROOT / "projects" / "templates" / "template_newspaper"
CONTENT_DIR = PROJECT_ROOT / "content"

_PKG_ALIAS = "_newspaper_src"


def _load_src_package() -> ModuleType:
    """Load this exemplar's ``src`` package under a project-unique alias.

    Every public exemplar ships a top-level ``src`` package, so a bare
    ``sys.path.insert`` + ``from src...`` collides on ``sys.modules['src']``
    once a second project's regression test joins the same pytest session.
    Registering under a namespaced key keeps the real tested functions in
    scope (no mocks) and stays collision-free regardless of collection order.

    template_newspaper nests its importable package one level down
    (``src/newspaper/``), so the alias is anchored at ``src`` and submodules
    are imported as ``_newspaper_src.newspaper.<mod>``.
    """

    if _PKG_ALIAS in sys.modules:
        return sys.modules[_PKG_ALIAS]
    src_init = PROJECT_ROOT / "src" / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        _PKG_ALIAS,
        src_init,
        submodule_search_locations=[str(PROJECT_ROOT / "src")],
    )
    assert spec is not None and spec.loader is not None, f"cannot load {src_init}"
    package = importlib.util.module_from_spec(spec)
    sys.modules[_PKG_ALIAS] = package
    spec.loader.exec_module(package)
    return package


def _import_submodule(dotted: str) -> ModuleType:
    _load_src_package()
    return importlib.import_module(f"{_PKG_ALIAS}.{dotted}")


load_edition = _import_submodule("newspaper.content").load_edition
load_newspaper_config = _import_submodule("newspaper.config").load_newspaper_config
figures = _import_submodule("newspaper.figures")


def _pin(pinned: dict[str, Any], key: str) -> dict[str, Any]:
    entry = pinned[key]
    assert isinstance(entry, dict), f"{key} must be an object"
    assert "value" in entry, f"{key} must include a pinned value"
    return entry


def _assert_pin_matches(entry: dict[str, Any], observed: float | int) -> None:
    tolerance = entry.get("abs_tolerance", 0)
    assert observed == pytest.approx(entry["value"], abs=tolerance)


def test_page_and_trim_claims_rederive_from_source(load_pinned_values: Any) -> None:
    """Bind the twelve-page / tabloid-trim claims to a fresh source derivation.

    04_reproducibility.md (line 17: "exactly twelve pages at the correct trim")
    + 00_abstract.md ("twelve-page, large-format newspaper")
    + data/claim_ledger.yaml (page-count, page-trim-width-pt, page-trim-height-pt).
    """

    pinned = load_pinned_values("template_newspaper")

    # Page count comes from the content data model, exactly as the renderer reads it.
    edition = load_edition(CONTENT_DIR)
    _assert_pin_matches(_pin(pinned, "layout_edition_page_count"), edition.page_count)

    # Trim dimensions come through the real config loader (edition.yaml -> tabloid),
    # which is the same PageGeometry the Canvas is opened with in render_edition.
    geometry = load_newspaper_config(CONTENT_DIR).geometry()
    _assert_pin_matches(_pin(pinned, "layout_trim_width_pt"), geometry.width)
    _assert_pin_matches(_pin(pinned, "layout_trim_height_pt"), geometry.height)


def test_generated_figure_count_claim_rederives_from_source(load_pinned_values: Any, tmp_path: Path) -> None:
    """Bind the figure-count claim to what generate_all actually emits.

    04_reproducibility.md ("the figure count") + data/claim_ledger.yaml
    (figure-count). Re-derived by running the real Pillow/Matplotlib generators
    into a temp dir: 6 halftone scenes + 4 color ad graphics + 3 charts = 13.
    """

    pinned = load_pinned_values("template_newspaper")
    written = figures.generate_all(tmp_path)
    _assert_pin_matches(_pin(pinned, "layout_generated_figure_count"), len(written))


def test_pin_mutation_negative_control_fails(load_pinned_values: Any) -> None:
    """Changing a committed pin must fail the comparison predicate.

    Non-vacuity control (feedback-verify-not-trust-machine-proof): proves the
    assertions above can actually fail, so a green run means the re-derivation
    genuinely matched the pin -- not that the comparison is a no-op.
    """

    pinned = load_pinned_values("template_newspaper")
    entry = dict(_pin(pinned, "layout_edition_page_count"))
    observed = entry["value"]
    entry["value"] = observed + 1  # perturb the pinned ground truth

    with pytest.raises(AssertionError):
        _assert_pin_matches(entry, observed)
