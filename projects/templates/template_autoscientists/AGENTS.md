# AGENTS.md — AutoScientists Coordination Testbed

Technical reference for the deterministic AutoScientists exemplar. Companion to
[README.md](README.md). All business logic lives in `src/`; `scripts/` are thin
orchestrators that import from `src/`, run the loop, and write figures/JSON.

Decision memory and verifier hardening follow [`docs/rules/memory_and_decision_records.md`](../../../docs/rules/memory_and_decision_records.md): use nearby `WHY:` comments only for surprising local choices, keep volatile counts generated, and add negative controls for verifier-like gates.

## Module map (`src/`)

| Module | Responsibility |
| --- | --- |
| [`state.py`](src/state.py) | `Proposal`, `ExperimentOutcome`, `Champion`, and the mutable `SharedState` (append-only log + champion promotion). The deterministic data core; no agent logic. |
| [`objective.py`](src/objective.py) | `SyntheticObjective` — a multi-axis landscape with a single global optimum, deceptive cosine ripples, and seeded evaluation noise. `clean(params)` is the noise-free ground truth; `evaluate(params, seed)` adds reproducible `(params, seed)`-hashed noise. |
| [`confirmation.py`](src/confirmation.py) | `confirm_improvement` — accepts a candidate only when its multi-seed mean beats the incumbent by more than the noise band (σ × standard error). Synchronized standalone copy of `infrastructure/scientific/confirmation.py`. |
| [`dead_ends.py`](src/dead_ends.py) | `DeadEndRegistry` — retires an `(axis, direction)` after `threshold` consecutive non-improving experiments. `retired_keys()` exposes the set agents consult to steer away. |
| [`ranking.py`](src/ranking.py) | `axis_effect_sizes` / `rank_axes` — deterministic axis ordering (untried-first, then descending effect). |
| [`stagnation.py`](src/stagnation.py) | `StagnationDetector` + `reorganize_axes` — fires when the champion stalls for a window and re-deals live axes across teams. |
| [`agents.py`](src/agents.py) | `Proposer` protocol; `DeterministicProposer` (rule-based, registry-consulting) and `HermesProposer` (live Ollama, `# pragma: no cover`). |
| [`search.py`](src/search.py) | `SearchConfig` (toggles + budgets), `SearchResult`, and the `_Runner` propose→filter→evaluate→confirm→promote→reorganize loop. `run_search(objective, proposer, config)` is the entry point. |

## The coordination loop

Each experiment: pick the next team's axes → drop fully-retired axes (when
dead-ends on) → ask the proposer for a `Proposal` (passing the registry's
`avoid` set) → evaluate with noise-band confirmation → record/promote →
reorganize if stagnant. With every *structural* coordination toggle off and one
team — confirmation stays on — the loop reduces exactly to the single-thread
baseline (`SearchConfig.single_thread_baseline`, which sets `use_confirmation=True`).

The loop is deterministic given `(objective, proposer, config)`, so trajectories
and figures are byte-reproducible.

## Honest instrumentation (`SearchResult`)

`SearchResult` records both the **reported** and **clean** trajectory plus the
two efficiency signals that carry the testbed's honest findings:

- `clean_trajectory` — noise-free value of the champion at each step. The gap
  vs `trajectory` is exactly the noise confirmation failed to filter.
- `experiments_to_target` — first experiment reaching the clean optimum within
  `config.target_tolerance` (`None` if never reached).
- `redundant_experiments` — re-probes of a direction already retired. Measured
  against an **always-on shadow registry** so the count is comparable even in
  configurations that have the registry switched off; the shadow never steers
  the search, only the gated `registry` does.

This is the design constraint: **measure and report whatever the numbers say.**
The dead-end registry buys search hygiene (`redundant_experiments` 36 → 0, early
halt), never a better final answer (clean metric unchanged). See the table in
[README.md](README.md#what-it-honestly-shows).

## Ablation toggles

`scripts/run_ablation.py` switches off one mechanism at a time from the full
configuration and reports, per row: reported vs clean metric, noise inflation,
confirmed improvements, experiments used, experiments-to-target, and redundant
re-probes. Two figures: `ablation.png` (metric/noise) and
`ablation_efficiency.png` (experiments used vs redundant re-probes).

## Conventions

- **No mocks** (absolute): real deterministic objects only.
- **Coverage**: `src/` gated at 90% (`fail_under = 90`); the suite covers it
  comfortably above the floor — read the `TOTAL` line of the coverage report for
  the live figure rather than trusting a pinned number. The live Hermes network
  boundary is `# pragma: no cover`; Protocol stub bodies (`...`) are excluded.
- **Thin orchestrators**: scripts never implement algorithms; they import from
  `src/`, plot, and print output paths for manifest collection.
- **Qualified-name pipeline invocation**: render via
  `--project templates/template_autoscientists` (see README).

## Publishing

- [Publishing guide](../../../docs/guides/publishing-guide.md) · [Publishing module reference](../../../infrastructure/publishing/README.md) · [Zenodo DOI strategy](../../../docs/guides/zenodo-doi-strategy.md) · [Archival targets](../../../docs/maintenance/archival-targets.md)
