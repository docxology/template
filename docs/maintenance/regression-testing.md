# Regression Testing — bind tests to scientific claims, not just to shape

> Created 2026-05-20. Addresses World-Threat-Model RedTeam attack A4 (reproducibility theater vs reproducibility reality) and converts the operator's already-logged lessons into infrastructure:
> - `feedback-shape-tests-dont-bind-truth` — "a lock that checks a split's shape passes on a silent relabel"
> - `feedback-remediation-agent-launders-fabrication` — "a fix-agent will hardcode a flagged fake number to satisfy prose & make tests greener"
> - `feedback-verify-not-trust-machine-proof` — "verify by running build + #print axioms + a self-designed non-vacuity negative control"

## The problem

The template currently enforces **coverage floors** (60% infra, 90% per-project, plus a 75% combined union in the local all-project orchestrator) as quality signals. Coverage is hygiene, not correctness. A function can be 100% covered and still wrong.

The operator's own memory ledger documents this failure mode across several private workspaces (for example a large symlinked textbook checkout under `projects/`). Shape tests, count tests, "the file exists" tests — all pass while the underlying scientific claim is broken.

A reproducibility template that claims to make science *reproducible* needs to bind tests to **the actual quantitative claims in the manuscript**, not just to the existence and shape of the code.

## The contract this directory creates

> **Current state:** this tier has its first populated slice. As of 2026-06-13,
> `tests/regression/projects/template_code_project/tables/test_optimization_results_claims.py`
> collects three real tests against deterministic optimizer manuscript claims, and
> `tests/regression/pinned_values/template_code_project.json` carries source-backed pins
> plus provenance. The broader per-figure/per-table contract below remains the target for
> the rest of the public exemplars.

Every quantitative claim in a manuscript figure or table — a coefficient, a p-value, an effect size, a count, a percentage, a ratio — **should** have a corresponding **pinned regression test** in `tests/regression/` that:

1. **Re-derives the value** from the deterministic pipeline (same code, same data, same seed)
2. **Compares against a pinned ground-truth value** (committed to the repo at manuscript freeze)
3. **Fails loudly if the value drifts** by more than a documented tolerance

If a value changes, the failure must be **investigated** — is the change correct (because the data/model/code was improved), or is it a regression? Either way, the manuscript text and the test must be updated **together**.

## Why this is different from coverage

| Coverage tells you | Regression tests tell you |
| --- | --- |
| "This code path ran during the test suite" | "This specific number in the manuscript was re-derived correctly" |
| "The function returns a value of the right type" | "The value matches what the manuscript says, to documented tolerance" |
| "No exceptions were thrown" | "If you change the code and the science breaks, the test will tell you" |
| Necessary but not sufficient | The actual binding between code and claim |

## Directory layout

The tree below is the live shape plus target naming convention. The
`template_code_project/tables/test_optimization_results_claims.py` file is populated;
other illustrative `test_figure_*` and `test_table_*` names show the intended expansion.

```
tests/regression/
├── README.md                          (philosophy + how to add a regression case)
├── __init__.py
├── conftest.py                        (fixtures for deterministic re-execution)
├── projects/
│   ├── template_code_project/
│   │   ├── __init__.py
│   │   ├── figures/                   (one test file per manuscript figure)
│   │   │   └── test_figure_TEMPLATE.py (non-collected scaffold)
│   │   └── tables/                    (one test file per manuscript table)
│   │       └── test_optimization_results_claims.py
│   └── template_prose_project/
│       └── (same shape)
└── pinned_values/                     (committed ground-truth values, JSON)
    ├── template_code_project.json
    └── template_prose_project.json
```

## How to add a regression case

For each quantitative claim in a manuscript:

1. **Identify the value** in the manuscript text or figure caption.
2. **Trace it back** to the function in `projects/<name>/src/` or `projects/<name>/scripts/` that produces it.
3. **Re-run the pipeline** with `--deterministic` and a fixed seed, capture the output value.
4. **Pin the value** in `pinned_values/<project>.json` with a unique key.
5. **Write a test** under `figures/` or `tables/` that:
   - Re-derives the value (calling the same function, not a mock)
   - Loads the pinned value from JSON
   - Asserts equality (or near-equality with documented tolerance)
6. **Document the source** — the test docstring should cite the manuscript section/figure/table where the value appears.

## Example test (canonical pattern)

```python
"""Regression pins for deterministic optimization result claims.

Manuscript: projects/templates/template_code_project/manuscript/03_results.md.
Claim: "Target solution: x = {{RESULT_OPTIMUM_X}} ..."
"""

from pathlib import Path
import sys
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[5] / "projects" / "templates" / "template_code_project"
sys.path.insert(0, str(PROJECT_ROOT))

from src.experiment_config import load_experiment_config  # noqa: E402
from src.optimizer import quadratic_optimum  # noqa: E402


def test_solution_accuracy_claims_rederive_from_quadratic(load_pinned_values: Any) -> None:
    """Re-derive the configured quadratic optimum; compare to committed pins."""
    pinned = load_pinned_values("template_code_project")
    config = load_experiment_config(PROJECT_ROOT)
    optimum_x, optimum_f = quadratic_optimum(config.A_array(), config.b_array())
    solution_pin = pinned["solution_accuracy_target_solution"]
    objective_pin = pinned["solution_accuracy_target_objective"]

    assert float(optimum_x[0]) == pytest.approx(solution_pin["value"], abs=solution_pin["abs_tolerance"])
    assert optimum_f == pytest.approx(objective_pin["value"], abs=objective_pin["abs_tolerance"])
```

## Example pinned-values JSON

```json
{
  "solution_accuracy_target_solution": {
    "manuscript_section": "manuscript/03_results.md / Solution Accuracy",
    "claim_text": "Target solution: x = {{RESULT_OPTIMUM_X}} ...",
    "value": 1.0,
    "abs_tolerance": 1e-12,
    "verifier_function": "src.optimizer.quadratic_optimum",
    "verifier_args": {"source": "projects/templates/template_code_project/manuscript/config.yaml"},
    "pinned_on": "2026-06-13",
    "pinned_by": "Codex",
    "pinned_at_commit": "b85f2753"
  }
}
```

## Tolerance policy

- **Counts** (number of items, sample sizes): exact match required (tolerance = 0).
- **Proportions / percentages**: tolerance = 0 if computed from exact counts; otherwise see numeric below.
- **Numeric coefficients / rates / effect sizes**: tolerance documented per pin. Default to 3 significant figures (e.g., tolerance = `1e-4` for a value like 0.4271).
- **p-values**: pin the value but tolerance is more permissive (1e-3) because numerical instability is normal at small p; if the value changes by orders of magnitude, fail.
- **NEVER** use a percentage tolerance that's so wide a real regression would pass.

## Workflow: changing a value

When a code or data change shifts a regression value:

1. **CI fails.** Good — the test caught it.
2. **Investigate.** Is the new value correct, or is this a regression?
3. **If correct (the science improved):** open a PR that updates *both* (a) `pinned_values/<project>.json` and (b) the manuscript text. The PR description must explain why the change is correct. Both files must change in the same commit.
4. **If a regression:** fix the code, don't update the pin. The pin is the **claim**; the code must match the claim, not the other way around.

## Workflow: adding a new claim

When a new figure or table is added:

1. Add the figure/table to the manuscript.
2. Add a corresponding entry to `pinned_values/<project>.json`.
3. Add a corresponding test in `tests/regression/projects/<project>/figures/` or `.../tables/`.
4. The PR cannot merge until the test exists and passes.

## What this catches that coverage doesn't

- **Silent regressions:** a refactor changes the result of a computation by 5%; coverage stays 90%; manuscript value is now wrong.
- **Data drift:** an updated dataset changes a coefficient; if the manuscript text is not updated, the claim is now false.
- **Numerical instability:** a library upgrade changes floating-point behavior; the regression test pins this down.
- **Fabrication-via-remediation:** the documented failure mode where an LLM-driven fix hardcodes a flagged value to satisfy prose. A regression test that re-derives from source data catches this; a shape test does not.

## What this does NOT catch

- A manuscript claim that was wrong *at pin time*. Pinning preserves what you committed, not what is true.
- Claims that depend on data not in the repo. If the dataset is external and changes, the value will drift; this is expected and the pin needs updating.
- Conceptual / interpretive claims ("this suggests that X causes Y"). Regression tests bind numbers, not interpretations.

## Status

This directory is **partially populated** as of 2026-06-13. See [`STATUS.md`](../../STATUS.md) — row `Regression tests`: 🟡 first pins live; expand beyond canonical optimizer claims.

Next step: expand from the canonical optimizer claims into the remaining `template_code_project` figure/table claims and then the other public exemplar manuscripts.

## Related

- [`README.md`](README.md) — guide hub
- [`toolchain-migration.md`](toolchain-migration.md) — why pytest-based tests are likely durable
- [`tests/regression/README.md`](../../tests/regression/README.md) — directory-level entry point
- [`MAINTAINERS.md`](../../MAINTAINERS.md) — `tests/regression/` owner
