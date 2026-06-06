# Experimental Setup {#sec:setup}

## Objective and budget

All experiments optimize the synthetic objective of @sec:methodology with $d = 4$ dimensions, ripple amplitude $\rho = 0.15$, and per-evaluation noise scale $\sigma_{\text{noise}} = 0.02$. The global optimum is the origin, where the clean objective equals $0$. Every configuration is given the **same** budget of $60$ sequential experiments; coordinated configurations partition that budget across teams.

## Configurations

The configurations compared in @sec:results correspond directly to `SearchConfig` objects:

- **Coordinated teams** — the full configuration: $3$ teams, all mechanisms on (`use_confirmation`, `use_dead_ends`, `use_ranking`, `use_reorganization` all true).
- **Single-thread baseline** — `SearchConfig.single_thread_baseline()`: $1$ team, confirmation on (so the baseline is itself noise-honest), all structural coordination off.
- **Ablations** — the full configuration with exactly one mechanism switched off, generated via `dataclasses.replace`.

Confirmation averages each candidate over seeds $(101, 202, 303)$ and tests against a $\sigma = 2$ noise band; the primary evaluation seed is $7$; the stagnation window is $10$ experiments; a direction is retired after $3$ consecutive non-improving experiments. These values are the `SearchConfig` defaults and are echoed in `manuscript/config.yaml`.

## Proposer

The rendered figures and the JSON summaries are produced with `DeterministicProposer`, a rule-based agent that reads the shared state and emits a concrete proposal. No mock objects are used anywhere. The live `HermesProposer` path is not part of the rendered pipeline; it is exercised separately (see @sec:reproducibility).

## Outputs

Two thin orchestrator scripts produce all results:

- `scripts/run_search_comparison.py` → `output/figures/search_comparison.png`, `output/data/search_comparison.json`.
- `scripts/run_ablation.py` → `output/figures/ablation.png`, `output/data/ablation.json`.

Each script imports all computation from `src/`, runs the configurations, and writes a figure plus a machine-readable summary. The numbers quoted in @sec:results are read directly from those JSON files.
