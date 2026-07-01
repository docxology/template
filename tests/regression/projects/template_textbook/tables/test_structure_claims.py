"""Regression pins for the config-driven textbook structural claims.

Manuscript: projects/templates/template_textbook/manuscript/front_matter.md
and manuscript/README.md.

template_textbook is a modular, fillable scaffold whose entire structure is
data-driven from a single source of truth, ``manuscript/config.yaml``: it
declares the parts, the chapters inside each part, and the labs and question
banks. The prose commits to concrete counts -- "Twelve chapters across four
parts" (front_matter.md), "(3 chapters)" per part and "One guided lab /
question bank per chapter" (README.md). These pins bind those exact claims to
the source: each value is re-derived by calling the tested loaders
``textbook.config.unit_blocks`` / ``iter_chapters`` / ``load_config`` and
``textbook.toc.build_toc`` on the real committed ``config.yaml`` -- never by
hand-copying a number from the manuscript.

All counts are exact-match pins (abs_tolerance 0): a real regression (adding or
removing a part, chapter, lab, or question in config.yaml without updating the
prose) drifts the count and fails the test.

No mocks: the real config.yaml is loaded and parsed by the real tested
functions, in line with the repo no-mock policy.
"""

from __future__ import annotations

from collections import Counter
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
PROJECT_ROOT = REPO_ROOT / "projects" / "templates" / "template_textbook"
MANUSCRIPT_DIR = PROJECT_ROOT / "manuscript"

_PKG_ALIAS = "_textbook_src"


def _load_src_package() -> ModuleType:
    """Load this exemplar's ``src`` package under a project-unique alias.

    Every public exemplar ships a top-level ``src`` package, so a bare
    ``sys.path.insert`` + ``from src...`` collides on ``sys.modules['src']``
    once a second project's regression test joins the same pytest session.
    Registering under a namespaced key keeps the real tested functions in
    scope (no mocks) and stays collision-free regardless of collection order.
    """

    if _PKG_ALIAS in sys.modules:
        return sys.modules[_PKG_ALIAS]
    src_dir = PROJECT_ROOT / "src"
    src_init = src_dir / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        _PKG_ALIAS,
        src_init,
        submodule_search_locations=[str(src_dir)],
    )
    assert spec is not None and spec.loader is not None, f"cannot load {src_init}"
    package = importlib.util.module_from_spec(spec)
    sys.modules[_PKG_ALIAS] = package
    spec.loader.exec_module(package)
    return package


def _import_submodule(dotted: str) -> ModuleType:
    """Import ``src.<dotted>`` under the project-unique alias.

    ``textbook`` is a nested package inside ``src`` whose own modules do
    ``from textbook.config import ...``. To satisfy those bare
    ``textbook.*`` imports without a global ``sys.path`` mutation that would
    collide across exemplars, the project's ``src`` dir is placed on
    ``sys.path`` only for the duration of the load (the alias package keeps the
    resolved modules cached afterwards, so the path entry is transient).
    """

    _load_src_package()
    src_dir = str(PROJECT_ROOT / "src")
    added = src_dir not in sys.path
    if added:
        sys.path.insert(0, src_dir)
    try:
        return importlib.import_module(dotted)
    finally:
        if added:
            sys.path.remove(src_dir)


_config_mod = _import_submodule("textbook.config")
_toc_mod = _import_submodule("textbook.toc")
load_config = _config_mod.load_config
unit_blocks = _config_mod.unit_blocks
iter_chapters = _config_mod.iter_chapters
build_toc = _toc_mod.build_toc


def _pin(pinned: dict[str, Any], key: str) -> dict[str, Any]:
    entry = pinned[key]
    assert isinstance(entry, dict), f"{key} must be an object"
    assert "value" in entry, f"{key} must include a pinned value"
    return entry


def _assert_pin_matches(entry: dict[str, Any], observed: float | int) -> None:
    tolerance = entry.get("abs_tolerance", 0)
    assert observed == pytest.approx(entry["value"], abs=tolerance)


@pytest.fixture(scope="module")
def config() -> dict[str, Any]:
    """Load the real committed manuscript config (the single source of truth)."""

    return load_config(MANUSCRIPT_DIR)


def test_part_and_chapter_counts_rederive_from_config(
    load_pinned_values: Any,
    config: dict[str, Any],
) -> None:
    """Bind the 'Twelve chapters across four parts' headline to the config source.

    front_matter.md / About This Template + How to Read This Book.
    """

    pinned = load_pinned_values("template_textbook")

    # Four parts: front_matter.md "organised into four parts".
    _assert_pin_matches(_pin(pinned, "structure_num_parts"), len(unit_blocks(config)))

    # Twelve chapters, numbered sequentially 1..N across the whole book.
    chapters = iter_chapters(config)
    _assert_pin_matches(_pin(pinned, "structure_num_chapters"), len(chapters))

    # The TOC numbers the same chapters 1..N; the last entry's number must equal
    # the chapter count (guards against a numbering/flattening drift).
    toc = build_toc(config)
    _assert_pin_matches(_pin(pinned, "structure_num_chapters"), toc[-1].number)


def test_chapters_per_part_uniform_three(
    load_pinned_values: Any,
    config: dict[str, Any],
) -> None:
    """Bind the per-part '(3 chapters)' labels to the config source.

    manuscript/README.md / Layout labels every part directory '(3 chapters)'.
    """

    pinned = load_pinned_values("template_textbook")
    per_part = Counter(chapter.part_id for chapter in iter_chapters(config))

    # Every part must carry the same chapter count, and it must be the pin (3).
    distinct = set(per_part.values())
    assert len(distinct) == 1, f"parts are not uniform in size: {dict(per_part)}"
    _assert_pin_matches(_pin(pinned, "structure_chapters_per_part"), distinct.pop())


def test_lab_and_question_counts_rederive_from_config(
    load_pinned_values: Any,
    config: dict[str, Any],
) -> None:
    """Bind 'one lab / one question bank per chapter' to the config source.

    front_matter.md ("A matching lab and question bank for every chapter") and
    manuscript/README.md ("One guided lab per chapter" / "One question bank per
    chapter"). Both must equal the chapter count.
    """

    pinned = load_pinned_values("template_textbook")
    appendices = config["appendices"]

    num_labs = sum(len(unit["files"]) for unit in appendices["labs"])
    num_questions = sum(len(unit["files"]) for unit in appendices["questions"])

    _assert_pin_matches(_pin(pinned, "structure_num_labs"), num_labs)
    _assert_pin_matches(_pin(pinned, "structure_num_questions"), num_questions)

    # The load-bearing "matching ... for every chapter" claim: labs and question
    # banks are one-per-chapter, so both re-derived counts equal the chapters.
    num_chapters = len(iter_chapters(config))
    assert num_labs == num_chapters
    assert num_questions == num_chapters


def test_pin_mutation_negative_control_fails(load_pinned_values: Any) -> None:
    """Changing a committed pin must fail the comparison predicate.

    Non-vacuity control (feedback-verify-not-trust-machine-proof): proves the
    assertion above can actually fail, so a green run means the re-derivation
    genuinely matched the pin -- not that the comparison is a no-op.
    """

    pinned = load_pinned_values("template_textbook")
    entry = dict(_pin(pinned, "structure_num_chapters"))
    observed = entry["value"]
    entry["value"] = observed + 1  # perturb the pinned ground truth

    with pytest.raises(AssertionError):
        _assert_pin_matches(entry, observed)
