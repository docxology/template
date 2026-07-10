# `scripts/` — thin orchestrators

Three entry points. None of them contain business logic — every one imports a
real function from `src/template_formal/` (or shared `infrastructure/`) and
does path wiring, I/O, and printing only.

| Script | Wires up |
| --- | --- |
| [`00_setup_environment.py`](00_setup_environment.py) | Pre-flight check for manuscript rendering prerequisites. Calls `infrastructure.rendering.preflight.run_manuscript_preflight` — the same helper `template_code_project/scripts/00_preflight.py` reuses — and reports the result. |
| [`02_run_analysis.py`](02_run_analysis.py) | Two real runs: `template_formal.colony.demo.run_demo_colony` (deterministic 3-agent/5-tick demo) and `template_formal.colony.demo.run_statistics_sweep` (N=40 seeded heterogeneous trials, the same real harness `tests/colony/test_colony_convergence_statistics.py` uses at N=150). Writes JSON summaries, calls `colony.visualization` for figures, writes the figure registry, and prints every output path for manifest collection. |
| [`check_formal_specs.sh`](check_formal_specs.sh) | Runs the optional Lean 4 build (`lake build` under `formal/lean/`) and the TLA+ TLC model check (`formal/tla/`) and exits non-zero if either fails. Fetches `tla2tools.jar` on first run from a pinned, dated GitHub release tag and verifies it against a hardcoded SHA-256 before ever invoking it. |

## Thin-orchestrator contract

Verified by reading the three scripts above: `02_run_analysis.py`'s own
docstring states it plainly — "all business logic lives in
`src/template_formal`: this script only wires up real on-disk paths, calls
`template_formal.colony.demo` / `template_formal.colony.visualization`,
writes small JSON summaries and the figure registry, and prints the output
paths it produced." `colony/demo.py` and `colony/visualization.py` were
deliberately *moved into* `src/` from `scripts/` for exactly this reason —
see both modules' docstrings ("moved out of `scripts/` per the
thin-orchestrator rule"). `00_setup_environment.py` and
`check_formal_specs.sh` are the same pattern in miniature: `00_setup_environment.py`
calls one shared `infrastructure.rendering.preflight` function and reports
its result; `check_formal_specs.sh` shells out to `lake` and `java -jar
tla2tools.jar` and reports their exit codes — nothing here decides *how* a
Lean proof or a TLA+ spec is checked, only whether the process wiring
succeeded.

Concretely, if you're about to add a `def` with a loop, a conditional beyond
argument validation, or any numeric computation to a file in this directory —
stop, and put it in `src/template_formal/` (with a test) instead. A script
should read as "resolve paths, call one or two `src/` functions, print/write
the result."

## Gated by `check_template_drift.py --strict`

This contract isn't just documented, it's enforced repo-wide:

```bash
cd /path/to/template  # monorepo root
uv run python scripts/audit/check_template_drift.py --strict
```

passes clean for this project (verified this session — `template_drift: no
drift detected.`). The `--strict` flag turns on the `thin_orchestrator` check
among others; a script here that grows real business logic (rather than
calling into `src/template_formal/`) is exactly what that check exists to
catch before it ships.
