# `src/template_formal/colony/` — the colony layer

The largest subpackage in this template, grown across three adversarial
rounds: round one shipped the shared pheromone substrate and a single
deterministic demo; round two added the statistical-rigor trial harness,
descriptive stats, and figure rendering; round three (scientific-depth) added
a random-choice null-model baseline and a generic parameter-sweep runner to
back eight pre-registered analyses grouped across three experiment families. Eight files, each with one distinct
responsibility — read this map before adding a new one, since it is easy to
misplace new logic into the wrong file once the package has this many
adjacent concerns.

## Modules

| File | Responsibility |
| --- | --- |
| `analysis.py` | The source-owned publication analysis service: executes the deterministic demo and calibrated real sweep, derives Wilson-bounded summary data, requires both figures, writes their registry, and returns a typed `AnalysisArtifacts` manifest to the thin script. |
| `pheromone.py` | The shared stigmergic substrate. `PheromoneField` — a narrow three-method `Protocol` (`deposit`/`sense`/`evaporate`); `InMemoryPheromoneField` — the one reference implementation, backed by a private `dict` never exposed directly. |
| `experiment.py` | The seeded, heterogeneous, real-agent trial harness: `ColonyTrialConfig`/`ColonyTrialResult`, `run_colony_trial` (real `Agent` instances, real per-trial SQLite files, real `InMemoryPheromoneField`), and `find_sustained_consensus_tick` — the shared "converged" definition every other module in this package reuses. |
| `stats.py` | Stdlib-only statistics: `convergence_rate`, `wilson_score_interval`, `consensus_tick_summary`/`ConsensusTickSummary`, `pearson_r`, `fisher_exact_test_two_sided`. No numpy/scipy — every formula is closed-form and hand-checked against a fixture in `tests/colony/test_colony_stats_unit.py`. |
| `demo.py` | Two real, on-disk simulation *runners* (moved out of `scripts/` per the thin-orchestrator rule): `run_demo_colony` (3 identical agents, 5 ticks, no seeded variation — a mechanism demonstration, not a rate claim) and `run_statistics_sweep` (a thin wrapper batching `run_colony_trial` calls for the larger statistical-rigor suite). |
| `visualization.py` | Matplotlib figure rendering, moved out of `scripts/` for the same reason: `write_demo_convergence_figure` (two-panel plot of the deterministic demo) and `write_convergence_tick_histogram` (histogram + ECDF of a trial batch's `consensus_tick` distribution, honestly skipped below `MIN_CONVERGED_FOR_HISTOGRAM=5` converged trials). They return `None` only when the requested distribution is unplottable; expected render or artifact-quality failures raise so publication figures cannot silently disappear. |
| `nullmodel.py` | The random-choice baseline: `NullModelTrialConfig`/`NullModelTrialResult`, `run_null_model_trial` — each agent picks `random.Random(seed).choice(locations)` every tick. Structurally isolated by construction: this module never imports the pheromone field, `Agent`, or `BeliefState`, proven by a source-text grep test, not just a docstring claim. Reuses only `find_sustained_consensus_tick` from `experiment.py`, so a rate comparison against the real mechanism is apples-to-apples under an identical "converged" definition. |
| `sweep.py` | The generic parameter-sweep runner: `SweepPointResult`, `run_parameter_sweep` — runs `n_per_value` real `run_colony_trial` calls at each of several values of one `ColonyTrialConfig` field, aggregating each point via `convergence_rate`/`wilson_score_interval`. `param_name` is validated eagerly against `ColonyTrialConfig`'s real dataclass field names (rejecting `seed` itself and any typo), and every sweep point reuses the identical seed sequence in its own subdirectory (a deliberate paired-samples variance-reduction design, not an accident). |

## Public API (`__init__.py`)

```python
from template_formal.colony import (
    AnalysisArtifacts, ColonyTrialConfig, ColonyTrialResult, ConsensusTickSummary, EmptySummaryError,
    InMemoryPheromoneField, NullModelTrialConfig, NullModelTrialResult, PheromoneField,
    SweepPointResult,
    consensus_tick_summary, convergence_rate, find_sustained_consensus_tick,
    fisher_exact_test_two_sided, pearson_r,
    run_colony_trial, run_demo_colony, run_null_model_trial, run_parameter_sweep,
    run_publication_analysis,
    run_statistics_sweep, wilson_score_interval,
    write_convergence_tick_histogram, write_demo_convergence_figure,
)
```

## Core invariants

**Narrow substrate access (ISC-32, ISC-34).** Agent and coordinator code only
ever holds a reference typed as `PheromoneField`, never the concrete
`InMemoryPheromoneField` or its backing `dict` — mypy --strict enforces the
narrow surface regardless of which concrete class backs it. This is a typing
narrowing only: `Protocol` gives no runtime access control, and the module
docstring says so explicitly rather than overclaiming.

**One real, falsifiable statistical claim per pre-registered experiment
(ISC-76, ISC-87–ISC-92).** Every rate reported in the manuscript is a
Wilson-score interval over real, independently-seeded trials from
`run_colony_trial` — never a point estimate standing alone, and never a
rounded or interpolated number. Eight analyses are pinned by regression
tests in `tests/colony/test_colony_experiments_extended.py`: a decay-rate
sensitivity sweep (non-monotonic, ISC-87), the real mechanism vs. the
`nullmodel.py` random-choice baseline (non-overlapping Wilson intervals,
ISC-88), and a heterogeneity-magnitude sweep (strictly monotonic decrease,
ISC-89). A `fisher_exact_test_two_sided` check (ISC-92) later corrected an
overclaimed "real decline" at one boundary-adjacent decay value once a
cross-vendor audit flagged that a normal-approximation test is invalid there
— the same pathology `wilson_score_interval` was already hardened against
(ISC-82).

**The null model must stay structurally blind to the mechanism (ISC-85).**
`nullmodel.py` is proven — not merely documented — to never reference
`PheromoneField`, `Agent`, or `BeliefState`, by a source-text grep test
(`test_nullmodel_module_never_references_pheromone_field_or_agent_machinery`)
and an AST-based import-allowlist test. Without this, a "no-mechanism
baseline" could quietly leak mechanism-derived behavior and invalidate the
whole comparison in ISC-88.

**Every trial is real, on-disk SQLite, never `:memory:` (ISC-66).** This
applies uniformly across `experiment.py`, `demo.py`, and `sweep.py` — every
`Agent` constructed anywhere in this package gets its own real SQLite file
under a caller-supplied directory, even inside a 150-trial statistical-rigor
batch or a multi-point sweep (each gets its own subdirectory to avoid path
collisions across seeds).

## Tests

`tests/colony/` — eleven files, each paired to one or more modules above:

| Test file | Covers |
| --- | --- |
| `test_analysis.py` | `analysis.py` — complete real artifact set, calibrated sweep result, and figure-registry binding. |
| `test_pheromone.py` | `pheromone.py` — `PheromoneField`/`InMemoryPheromoneField`. |
| `test_colony_integration.py` | The original N≥3 real-agent convergence demonstration and the coordinator-isolation anti-criterion (ISC-33, ISC-34). |
| `test_colony_experiment_config.py` | `ColonyTrialConfig.__post_init__` validation boundaries (`decay`, `sensing_noise_std`, `preference_variance`; ISC-80, ISC-84). |
| `test_colony_convergence_statistics.py` | The N=150 Wilson-bounded convergence-rate claim (ISC-76). |
| `test_colony_stats_unit.py` | Hand-computed expectations for every `stats.py` function, including the `wilson_score_interval` near-1.0 boundary (ISC-82) and the `fisher_exact_test_two_sided` manuscript-pinned p-value (ISC-92). |
| `test_demo.py` | `demo.py` — `run_demo_colony`/`run_statistics_sweep` determinism and shape. |
| `test_visualization.py` | `visualization.py` — real non-empty PNG output and the honest below-minimum skip. |
| `test_nullmodel.py` | `nullmodel.py` — determinism, the structural-isolation grep/AST tests (ISC-85). |
| `test_sweep.py` | `sweep.py` — `param_name` validation, hand-derivable Wilson bounds, disjoint sweep-point subdirectories (ISC-86). |
| `test_colony_experiments_extended.py` | The eight pre-registered analyses' pinned real numbers (ISC-87–ISC-113). |

## ISA cross-reference

ISC-32, ISC-33, ISC-34, ISC-66, ISC-76, ISC-80, ISC-82, ISC-84, ISC-85,
ISC-86, ISC-87, ISC-88, ISC-89, ISC-90, ISC-91, ISC-92. See `ISA.md` for full
criteria text.
