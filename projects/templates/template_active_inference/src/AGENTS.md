# Source Module Notes

All reusable, tested logic lives here; `../scripts/` only parses arguments,
resolves paths, and calls these functions (thin-orchestrator pattern).

- Keep computation deterministic (fixed seeds, no network, no runtime downloads).
- The analytical, simulation/pymdp, GNN, ontology, Lean, visualization, and
  validation-spine tracks must stay concordant: numeric results, notation,
  proof boundaries, provenance, and manuscript claims describe the same objects.
  Use `gnn/concordance.py`, `validation_spine/`, and `gates/validation.py` to
  enforce this.
- Preserve public exports when splitting modules; tests import from these paths.

## Module map (post quality split)

| Area | Modules | Role |
| --- | --- | --- |
| Orchestration | `orchestration/analysis.py`, `orchestration/coverage_pipeline.py` | Analysis entry + sheaf coverage PNG/page (no matplotlib in `manuscript/`) |
| Analytical | `analytical/invariants.py` (+ facades at `invariants.py`) | Closed-form invariant checks |
| Simulation | `simulation/si_{belief,policy,loop,artifacts}.py`, `si_runner.py` (facade) | pymdp T-maze runner |
| Sheaf | `manuscript/sheaf/*` | Coverage matrix JSON only in `coverage.py` |
| Visualizations | `visualizations/figures_sheaf_{payload,draw}.py`, `figures_sheaf.py` | JSON payload → matplotlib |
| Validation spine | `validation_spine/artifacts.py` | Provenance, deterministic replay, and counterexample artifacts |
| Gates | `gates/{output_checks,output_checks_*,manuscript_checks,claim_ledger,lean}.py`, `validation.py` (facade) | Output/manuscript validation |
| Contracts | [`contracts/artifact_contract.py`](contracts/artifact_contract.py) | SSOT for promoted/variable/gate artifact paths and experiment-plan metric keys |
| JSON I/O | [`json_io.py`](json_io.py) | `load_json`, `read_json`, `write_json` shared helpers |
| Manuscript refresh | [`manuscript/refresh.py`](manuscript/refresh.py) | `refresh_manuscript_pipeline`, `settle_manuscript_artifacts` |

Sheaf coverage flow: `coverage.emit_coverage_artifacts` writes JSON at compose time →
`ensure_coverage_artifacts` (figures stage) renders PNG + page →
`scripts/generate_figures.py` dispatches `FIGURE_GENERATORS`.
