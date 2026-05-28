"""Template test file for a regression-pinned manuscript figure value.

Copy this file, rename to ``test_figure_<NN>_<short_descriptor>.py``, and fill
in the placeholders marked ``# TODO``. See
``docs/maintenance/regression-testing.md`` for the full philosophy.

This file is a scaffold only: the example function is intentionally not named
``test_*`` and therefore is not collected until you copy and populate it.
"""

from __future__ import annotations


# TODO: replace with the actual import path of the function that produces this value
# Example (with ``projects/templates/template_code_project/src`` on PYTHONPATH):
#   from analysis.pipeline import run_analysis


PINNED_KEY = "figure_TEMPLATE"  # TODO: replace with the JSON key in pinned_values


def figure_template_scaffold(load_pinned_values):
    """Re-derive a manuscript figure value; compare against pinned ground truth.

    Manuscript reference: TODO — e.g. ``manuscript/03_results.md / Figure 3 panel (b)``
    Claim: TODO — paste the exact sentence from the manuscript that names the value.
    """

    pinned = load_pinned_values("template_code_project")
    assert PINNED_KEY in pinned

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
