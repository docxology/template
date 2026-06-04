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

The deterministic core is tested to full coverage. The live language-model path is excluded from the coverage gate (`# pragma: no cover`) because it requires an external service.

## The live Hermes agent (opt-in)

`HermesProposer` calls a Hermes model served by Ollama. It is not part of the rendered pipeline and is exercised only by an opt-in test marked `requires_ollama`:

```bash
# One-time: start Ollama and pull a Hermes model
ollama serve
ollama pull hermes3

# Run the live round-trip test
uv run pytest projects/templates/template_autoscientists/tests/test_hermes_live.py \
    -m requires_ollama -v
```

Because the loop depends only on the `Proposer` protocol, swapping `DeterministicProposer` for `HermesProposer` is the single change needed to turn the reproducible reference run into a live agentic one — the coordination mechanisms, ablation toggles, and confirmation logic are unchanged.

## Shared estimator

The noise-band confirmation estimator is generic. A synchronized copy lives at `infrastructure.scientific.confirmation` (`confirm_improvement`, `Confirmation`) for reuse by any other project that compares a stochastic metric to a baseline, and is covered by `tests/infra_tests/scientific/test_confirmation.py`. The project keeps its own standalone copy so the exemplar runs self-contained.
