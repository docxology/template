"""Template test file for a regression-pinned manuscript figure value.

Copy this file, rename to ``test_figure_<NN>_<short_descriptor>.py``, and fill
in the placeholders marked ``# TODO``. See
``docs/maintenance/regression-testing.md`` for the full philosophy.

This file is itself skipped at runtime (no pinned value exists for the
``TEMPLATE`` key) — it does not introduce a real test until you copy and
populate it.
"""

from __future__ import annotations

import pytest


# TODO: replace with the actual import path of the function that produces this value
# Example:
#   from projects.template_code_project.src.analysis import compute_convergence_rate


PINNED_KEY = "figure_TEMPLATE"  # TODO: replace with the JSON key in pinned_values


def test_figure_template(load_pinned_values):
    """Re-derive a manuscript figure value; compare against pinned ground truth.

    Manuscript reference: TODO — e.g. ``manuscript/03_results.md / Figure 3 panel (b)``
    Claim: TODO — paste the exact sentence from the manuscript that names the value.
    """

    pinned = load_pinned_values("template_code_project")

    if PINNED_KEY not in pinned:
        pytest.skip(
            f"No pinned value committed yet for {PINNED_KEY!r}. "
            f"This is the scaffold template — copy this file, rename it, "
            f"and populate the pinned value before enabling."
        )

    # TODO: import the producing function and call it with pinned['verifier_args']
    # Example:
    #   result = compute_convergence_rate(**pinned[PINNED_KEY]["verifier_args"])
    #   assert result == pytest.approx(
    #       pinned[PINNED_KEY]["value"],
    #       abs=pinned[PINNED_KEY].get("abs_tolerance"),
    #       rel=pinned[PINNED_KEY].get("rel_tolerance"),
    #   ), (
    #       f"Value drifted: pinned={pinned[PINNED_KEY]['value']}, observed={result}. "
    #       f"If intentional, update BOTH pinned_values JSON AND the manuscript text "
    #       f"in the same commit."
    #   )

    pytest.skip("Template not yet populated.")
