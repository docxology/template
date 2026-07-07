"""Regression pins for the deterministic conditional token-injection exemplar.

Manuscript: projects/templates/template_madlib/manuscript/05_experimental_setup.md
(Configuration Counts) and manuscript/06_evaluation.md (Quality Probes).

This exemplar's manuscript is fully tokenized: every quantitative claim is a
``{{..._COUNT}}`` token rendered from ``manuscript/config.yaml`` (seed 431)
through the deterministic pipeline. These pins bind five load-bearing counts —
the token-plan size, the lexicon size, the QA probe count, the slot-rule count,
and the enabled-visualization-flag count — back to the *source* functions that
produce them:

* ``src.tokens.generate_token_plan(config).choices`` -> TOKEN_CHOICE_COUNT
* ``len(src.config.load_madlib_config(root).lexicon)`` -> LEXICON_CATEGORY_COUNT
* ``len(config.quality_probes)`` -> QUALITY_PROBE_COUNT
* ``len(config.slots)`` -> SLOT_RULE_COUNT
* ``generate_variables(root)['CONFIGURED_FIELD_VISUALIZED_COUNT']``

Each value is re-derived by running the real config loader / token planner /
variable generator against the committed ``manuscript/config.yaml`` — never by
hand-copying a number from the rendered manuscript.

No mocks: real deterministic objects only, in line with the repo no-mock policy.

Import-isolation note: ``template_madlib``'s ``src`` package uses ordinary
relative intra-package imports (``from .config import ...``), the same shape
as the other exemplars, and it ships ``config`` / ``tokens`` / ``analysis`` /
``manuscript_variables`` submodule names that also exist in other exemplars'
``src`` packages. ``_load_src_package`` therefore uses the same
``spec_from_file_location`` alias-exec pattern as ``_autoscientists_src``:
register ``src/__init__.py`` under a project-unique ``_madlib_src`` key in
``sys.modules`` *before* executing it (with ``submodule_search_locations``
pointing at ``src/``) so every relative import inside the package — and
inside submodules imported afterward via ``_madlib_src.<name>`` — resolves
against the alias, not the bare top-level name, and stays collision-free
regardless of collection order.

(A prior version of this loader assumed ``template_madlib/src`` used *bare*
intra-package imports and execed each submodule as a standalone top-level
module — that assumption was stale relative to the actual source, which has
used relative imports throughout since the module was split into multiple
files, so the bare-exec approach raised ``ImportError: attempted relative
import with no known parent package`` and could not even collect.)
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
PROJECT_ROOT = REPO_ROOT / "projects" / "templates" / "template_madlib"
SRC_DIR = PROJECT_ROOT / "src"

_PKG_ALIAS = "_madlib_src"


def _load_src_package() -> ModuleType:
    """Load this exemplar's ``src`` package under a project-unique alias.

    Every public exemplar ships a top-level ``src`` package, so a bare
    ``sys.path.insert`` + ``from src...`` collides on ``sys.modules['src']``
    once a second project's regression test joins the same pytest session.
    Registering ``src/__init__.py`` under a namespaced key *before* executing
    it (with ``submodule_search_locations`` set) lets every relative import
    inside the package — and inside submodules imported afterward via
    ``_madlib_src.<name>`` — resolve against the alias, keeping the real
    tested functions in scope (no mocks) and staying collision-free
    regardless of collection order.
    """

    if _PKG_ALIAS in sys.modules:
        return sys.modules[_PKG_ALIAS]
    src_init = SRC_DIR / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        _PKG_ALIAS,
        src_init,
        submodule_search_locations=[str(SRC_DIR)],
    )
    assert spec is not None and spec.loader is not None, f"cannot load {src_init}"
    package = importlib.util.module_from_spec(spec)
    sys.modules[_PKG_ALIAS] = package
    spec.loader.exec_module(package)
    return package


def _submodule(name: str) -> ModuleType:
    _load_src_package()
    return importlib.import_module(f"{_PKG_ALIAS}.{name}")


generate_variables = _submodule("manuscript_variables").generate_variables
load_madlib_config = _submodule("config").load_madlib_config
generate_token_plan = _submodule("tokens").generate_token_plan


def _pin(pinned: dict[str, Any], key: str) -> dict[str, Any]:
    entry = pinned[key]
    assert isinstance(entry, dict), f"{key} must be an object"
    assert "value" in entry, f"{key} must include a pinned value"
    return entry


def _assert_pin_matches(entry: dict[str, Any], observed: float | int) -> None:
    tolerance = entry.get("abs_tolerance", 0)
    assert observed == pytest.approx(entry["value"], abs=tolerance)


@pytest.fixture(scope="module")
def rendered_variables() -> dict[str, str]:
    """Re-derive the manuscript variable map exactly as the analysis script does."""

    return generate_variables(PROJECT_ROOT)


@pytest.fixture(scope="module")
def madlib_config() -> Any:
    """Load the committed deterministic config (seed 431)."""

    return load_madlib_config(PROJECT_ROOT)


def test_token_plan_and_lexicon_counts_rederive_from_source(
    load_pinned_values: Any,
    rendered_variables: dict[str, str],
    madlib_config: Any,
) -> None:
    """Bind the token-plan-size and lexicon-size claims to a fresh source run.

    05_experimental_setup.md / Configuration Counts:
      "Token choices: `{{TOKEN_CHOICE_COUNT}}`" and
      "Lexicon categories: `{{LEXICON_CATEGORY_COUNT}}`".
    """

    pinned = load_pinned_values("template_madlib")

    # Token-plan size: one deterministic choice per expanded slot ordinal.
    plan = generate_token_plan(madlib_config)
    token_choice_count = len(plan.choices)
    _assert_pin_matches(_pin(pinned, "setup_token_choice_count"), token_choice_count)
    # The rendered manuscript token must agree with the re-derived plan size.
    assert int(rendered_variables["TOKEN_CHOICE_COUNT"]) == token_choice_count
    # Internal integrity: the plan expands each slot's declared count.
    assert token_choice_count == sum(slot.count for slot in madlib_config.slots)

    # Lexicon-size claim.
    lexicon_category_count = len(madlib_config.lexicon)
    _assert_pin_matches(_pin(pinned, "setup_lexicon_category_count"), lexicon_category_count)
    assert int(rendered_variables["LEXICON_CATEGORY_COUNT"]) == lexicon_category_count


def test_probe_slot_and_visualization_counts_rederive_from_source(
    load_pinned_values: Any,
    rendered_variables: dict[str, str],
    madlib_config: Any,
) -> None:
    """Bind the QA-probe, slot-rule, and enabled-visualization counts to source.

    05_experimental_setup.md / Configuration Counts (quality probes, slot rules,
    enabled visualization flags) + 06_evaluation.md / Quality Probes table.
    """

    pinned = load_pinned_values("template_madlib")

    # QA quality probes (drive the Quality Probes table in 06_evaluation.md).
    quality_probe_count = len(madlib_config.quality_probes)
    _assert_pin_matches(_pin(pinned, "evaluation_quality_probe_count"), quality_probe_count)
    assert int(rendered_variables["QUALITY_PROBE_COUNT"]) == quality_probe_count

    # Slot rules that drive token injection.
    slot_rule_count = len(madlib_config.slots)
    _assert_pin_matches(_pin(pinned, "setup_slot_rule_count"), slot_rule_count)
    assert int(rendered_variables["SLOT_RULE_COUNT"]) == slot_rule_count

    # Enabled visualization flags (configured-field audit).
    visualized_count = int(rendered_variables["CONFIGURED_FIELD_VISUALIZED_COUNT"])
    _assert_pin_matches(_pin(pinned, "setup_configured_field_visualized_count"), visualized_count)


def test_pin_mutation_negative_control_fails(load_pinned_values: Any) -> None:
    """Changing a committed pin must fail the comparison predicate.

    Non-vacuity control (feedback-verify-not-trust-machine-proof): proves the
    assertions above can actually fail, so a green run means the re-derivation
    genuinely matched the pin -- not that the comparison is a no-op.
    """

    pinned = load_pinned_values("template_madlib")
    entry = dict(_pin(pinned, "setup_token_choice_count"))
    observed = entry["value"]
    entry["value"] = observed + 1  # perturb the pinned ground truth

    with pytest.raises(AssertionError):
        _assert_pin_matches(entry, observed)
