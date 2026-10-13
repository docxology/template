# Publication consistency review — 2026-10-13

The current source distinguishes converged, iteration-capped and non-finite runs. For a positive-definite quadratic, contraction requires `0 < alpha < 2/lambda_max`; the unit-Hessian factor `abs(1-alpha)` is not monotonic across the configured sweep. Accuracy applies to converged rows. Scalar objective-evaluation stability is distinct from gradient-descent convergence.

This is a correction to current manuscript source. It does not replace any historical PDF, DOI deposit or release asset. The declared project suite passed 301 tests with 93.89% coverage using its own coverage configuration. Generated manuscript outputs are checked separately; broader experimental and publication acceptance remains subject to the repository's declared contracts.

The counts above are fresh local checks on the current source, using `uv run pytest projects/templates/template_code_project/tests --cov=template_code_project --cov-config=projects/templates/template_code_project/pyproject.toml --cov-fail-under=90 -q`. Retained `output/reports/test_results.json` files describe their earlier pipeline epoch and are not substituted for these local checks. Historical tracked output bytes remain unchanged; fresh renders are review artifacts, not a new release.

Fresh local HTML renders embed source-font bodies in each document and exceeded the existing aggregate tracked-output budget. They remain private review artifacts; this correction does not weaken the budget or publish a new output set. A bounded HTML projection requires a separate reviewed rendering change before tracked-output publication.

A sampled local PDF page showed an overflowing infrastructure path. Automated render success is not full format acceptance; inspect and correct layout in a separate candidate before publishing new output artifacts.
