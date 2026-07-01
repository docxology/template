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

Import-isolation note (madlib-specific): unlike the other exemplars,
``template_madlib``'s ``src`` package uses *bare* intra-package imports
(``from config import ...``) rather than relative imports, and it ships
``config`` / ``tokens`` / ``analysis`` / ``manuscript_variables`` submodule
names that also exist in other exemplars. A plain
``spec_from_file_location`` alias exec (the autoscientists shape) raises
``ModuleNotFoundError: No module named 'config'`` here. So ``_load_src_package``
loads the bare submodules in dependency order with ``src/`` temporarily on
``sys.path``, re-homes them under a project-unique ``_madlib_src.`` alias, and
pops the bare names back out of ``sys.modules`` afterward — keeping the real
tested functions in scope (no mocks) and staying collision-free regardless of
collection order, exactly as the ``_autoscientists_src`` alias does for its
relative-import package.
"""

from __future__ import annotations

import importlib
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
PROJECT_ROOT = REPO_ROOT / "projects" / "templates" / "template_madlib"
SRC_DIR = PROJECT_ROOT / "src"

_PKG_ALIAS = "_madlib_src"

# Bare intra-package submodule names this exemplar defines, in dependency order
# (``config`` is the leaf; ``manuscript_variables`` is the root). These names
# would collide with other exemplars' top-level modules if left in
# ``sys.modules``, so the loader below cleans them up after exec.
_BARE_SUBMODULES = (
    "config",
    "tokens",
    "composition",
    "analysis_fields",
    "analysis_figures",
    "analysis_reports",
    "analysis",
    "manuscript_variables",
)


def _load_src_package() -> ModuleType:
    """Load this exemplar's ``src`` package under a project-unique alias.

    ``template_madlib``'s ``src`` uses bare intra-package imports, so a plain
    aliased ``spec_from_file_location`` exec fails (``No module named
    'config'``). Instead: temporarily put ``src/`` on ``sys.path``, import the
    bare submodules in dependency order, re-home each under the
    ``_madlib_src.`` alias namespace, then pop the bare names back out of
    ``sys.modules`` so they cannot collide with any other exemplar's
    same-named module in the shared pytest session.
    """

    if _PKG_ALIAS in sys.modules:
        return sys.modules[_PKG_ALIAS]

    saved = {name: sys.modules.pop(name, None) for name in _BARE_SUBMODULES}
    sys.path.insert(0, str(SRC_DIR))
    try:
        package = ModuleType(_PKG_ALIAS)
        package.__path__ = [str(SRC_DIR)]  # type: ignore[attr-defined]
        for name in _BARE_SUBMODULES:
            module = importlib.import_module(name)
            setattr(package, name, module)
            sys.modules[f"{_PKG_ALIAS}.{name}"] = module
        sys.modules[_PKG_ALIAS] = package
        return package
    finally:
        sys.path.remove(str(SRC_DIR))
        for name in _BARE_SUBMODULES:
            sys.modules.pop(name, None)
            if saved[name] is not None:
                sys.modules[name] = saved[name]


def _submodule(name: str) -> ModuleType:
    return getattr(_load_src_package(), name)


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
