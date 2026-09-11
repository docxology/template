# AGENTS.md — AutoScientists Coordination Testbed

Technical reference for the deterministic AutoScientists exemplar. Companion to
[README.md](README.md). All business logic lives in `src/`; `scripts/` are thin
orchestrators that import from `src/`, run the loop, and write figures/JSON.

Decision memory and verifier hardening follow [`docs/rules/memory_and_decision_records.md`](../../../docs/rules/memory_and_decision_records.md): use nearby `WHY:` comments only for surprising local choices, keep volatile counts generated, and add negative controls for verifier-like gates.

## Module map (`src/`)

| Module | Responsibility |
| --- | --- |
| [`analysis/state.py`](src/template_autoscientists/analysis/state.py) | `Proposal`, `ExperimentOutcome`, `Champion`, and the mutable `SharedState` (append-only log + champion promotion). The deterministic data core; no agent logic. |
| [`analysis/objective.py`](src/template_autoscientists/analysis/objective.py) | `SyntheticObjective` — a multi-axis landscape with a single global optimum, deceptive cosine ripples, and seeded evaluation noise. `clean(params)` is the noise-free ground truth; `evaluate(params, seed)` adds reproducible `(params, seed)`-hashed noise. |
| [`analysis/confirmation.py`](src/template_autoscientists/analysis/confirmation.py) | `confirm_improvement` — accepts a candidate only when its multi-seed mean beats the incumbent by more than the noise band (σ × standard error). Synchronized standalone copy of `infrastructure/scientific/confirmation.py`. |
| [`search/dead_ends.py`](src/template_autoscientists/search/dead_ends.py) | `DeadEndRegistry` — retires an `(axis, direction)` after `threshold` consecutive non-improving experiments. `retired_keys()` exposes the set agents consult to steer away. |
| [`search/ranking.py`](src/template_autoscientists/search/ranking.py) | `axis_effect_sizes` / `rank_axes` — deterministic axis ordering (untried-first, then descending effect). |
| [`search/stagnation.py`](src/template_autoscientists/search/stagnation.py) | `StagnationDetector` + `reorganize_axes` — fires when the champion stalls for a window and re-deals live axes across teams. |
| [`agents/agents.py`](src/template_autoscientists/agents/agents.py) | `Proposer` protocol and `DeterministicProposer` (rule-based, registry-consulting). By design, the live implementation — `HermesProposer` (Ollama, `# pragma: no cover`) — lives in [`scripts/hermes_proposer.py`](scripts/hermes_proposer.py) instead, so `src/` stays infrastructure-free. |
| [`search/search.py`](src/template_autoscientists/search/search.py) | `SearchConfig` (toggles + budgets), `SearchResult`, and the `_Runner` propose→filter→evaluate→confirm→promote→reorganize loop. `run_search(objective, proposer, config)` is the entry point. |
| [`search/ablation.py`](src/template_autoscientists/search/ablation.py) | Canonical single-mechanism ablation matrix, measured rows, and derived noise-inflation ratio used by output generation and tests. |
| [`search/comparison.py`](src/template_autoscientists/search/comparison.py) | Canonical matched-budget coordinated/baseline experiment and honest result summaries. |
| [`figures/figures.py`](src/template_autoscientists/figures/figures.py) | Figure-generation helpers (build/write pairs for the comparison, ablation, and efficiency charts) plus `FIGURE_SPECS`/`write_figure_registry`, so `scripts/` stay thin. |
| [`analysis/transcript.py`](src/template_autoscientists/analysis/transcript.py) | Offline transcript envelope validation (`validate_transcript`, `replay_transcript`) and digesting (`transcript_digest`) — the stale-replay/no-network contract for the opt-in live-agent path. |

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

#
## Agent skill

A Hermes/agentskills.io-compatible skill for this exemplar lives at
[`.agents/skills/template-autoscientists/SKILL.md`](.agents/skills/template-autoscientists/SKILL.md).
Load it when working inside this template to get when-to-use guidance,
quick reference commands, and pitfalls.

# Publishing

- [Publishing guide](../../../docs/guides/publishing-guide.md) · [Publishing module reference](../../../infrastructure/publishing/README.md) · [Zenodo DOI strategy](../../../docs/guides/zenodo-doi-strategy.md) · [Archival targets](../../../docs/maintenance/archival-targets.md)
