# Reproducibility {#sec:reproducibility}

Every figure and number in this manuscript is regenerable from a clean checkout with fixed seeds and no network access.

## Deterministic core

The objective is a pure function of `(params, seed)`, and the coordination loop is deterministic given the objective, proposer, and configuration. Re-running the analysis scripts reproduces the figures and the JSON summaries byte-for-byte.

```bash
# Regenerate the matched-budget comparison and the ablation
uv run python projects/templates/template_autoscientists/scripts/run_search_comparison.py
uv run python projects/templates/template_autoscientists/scripts/run_ablation.py
```

## Tests and coverage

The project carries its own test suite under `tests/`, run as a standalone per-project gate. There are no mocks anywhere: the `DeterministicProposer`, the synthetic objective, and the registries are all real objects exercised with real numerical inputs.

```bash
# Project test suite with the per-project coverage gate
uv run pytest projects/templates/template_autoscientists/tests/ \
    --cov=projects/templates/template_autoscientists/src --cov-fail-under=90
```

Source coverage includes domain checks and real controlled HTTP transport. The opt-in installed-model run is separate evidence and fails when its selected capability is missing.

## Bounded local coordination (opt-in)

The default `--mode core` preserves the deterministic figures. `--mode live`
requires the declared platform SDK and an explicitly selected already-installed Ollama model
at a literal loopback endpoint. Both arms execute 3–6 proposals with equal
experiment, token and request-time ceilings, and three-seed confirmation.
Actual token consumption is recorded separately. The JSON proposal may alter
one assigned axis by a finite nonzero step in `[-1,1]`; code and paths are forbidden.

```bash
uv run python projects/templates/template_autoscientists/scripts/run_search_comparison.py \
  --mode live --model llama3.2:1b --endpoint http://127.0.0.1:11434 \
  --output-dir output/.pipeline/local_coordination/selected-run
```

The fresh ignored run retains source and active producer hashes, installed model
digest, every prompt context, exact provider request/response text, proposals,
observed outcomes and budgets. Null and negative differences remain successful
contract outcomes. Missing capabilities return `75`; malformed generations or
source drift return `1`. No acquisition, paid API, source application, or external
publication occurs. Full instructions: `docs/live-coordination.md`.

## Shared estimator

The noise-band confirmation estimator is generic. A synchronized copy lives at `infrastructure.scientific.confirmation` (`confirm_improvement`, `Confirmation`) for reuse by any other project that compares a stochastic metric to a baseline, and is covered by `tests/infra_tests/scientific/test_confirmation.py`. The project keeps its own standalone copy so the exemplar runs self-contained.
