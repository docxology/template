# FEP Lean Agents — projects/fep_lean/scripts/

**Version**: v0.3.0 | **Status**: Active | **Last Updated**: March 2026

## Purpose

The `scripts/` directory provides shell orchestration scripts for the full `fep_lean` lifecycle: setup, run, test, clean, and results viewing. All scripts are `bash` and use `uv` for Python execution.

## Script Inventory

| Script | Purpose | Key Options |
|--------|---------|-------------|
| `setup.sh` | First-time env setup (uv sync, GAUSS_HOME, API key) | `--no-key` |
| `setup_lean.sh` | Install/configure Lean 4 + Mathlib4 workspace | — |
| `run_full.sh` | Run full 25-topic pipeline | `--force`, `--no-prompt` |
| `run_area.sh` | Run single area | `<area>`, `--force`, `--no-prompt` |
| `run_topic.sh` | Run single topic | `<topic-id>`, `--no-prompt` |
| `clean.sh` | Clear reports and/or GAUSS state | `--all`, `--gauss-only` |
| `test.sh` | Run test suite (113 tests, 7 suites) | `--coverage`, `--verbose`, `--suite <name>` |
| `view_results.sh` | Show latest (or all) run summaries | `--all`, `--open` |
| `fep_analysis.py` | Run analysis + generate 4 figures | (called by infrastructure) |

## Quick Reference

```bash
# First time
./scripts/setup.sh

# Full clean fresh run (CI pattern)
./scripts/clean.sh --all   # (confirms before deleting)
./scripts/run_full.sh --force --no-prompt

# Day-to-day
./scripts/run_full.sh                  # Add to existing sessions
./scripts/run_area.sh BayesianMechanics
./scripts/run_topic.sh fep-014

# Development
./scripts/test.sh
./scripts/test.sh --coverage --verbose

# Review outputs
./scripts/view_results.sh
./scripts/view_results.sh --all
./scripts/view_results.sh --open      # open in $EDITOR
```

## Valid Area Names

```
FEP              (8 topics: Variational FE, ELBO, Predictive Coding, ...)
ActiveInference  (6 topics: Expected FE, Optimal Policy, ...)
BayesianMechanics (6 topics: Markov Blanket, NESS, ...)
InfoGeometry     (4 topics: Fisher Metric, Natural Gradient, ...)
Thermodynamics   (1 topic:  Helmholtz connection)
```

## Valid Topic IDs

```
fep-001 through fep-025
```

Use `uv run python -m src.orchestrator --list` to see all topics, or `--stats` for maturity distribution.

## Operating Contracts

1. **All scripts must be run from the project root** (`/path/to/fep_lean/`) OR are `cd`-safe (they `cd` to project root internally).
2. **`setup.sh` must always be run first** on new machines.
3. **Scripts use `python -m src.orchestrator`** as the canonical entry point (not `run_demo.py`).
4. **Scripts are idempotent**: safe to run multiple times (except `clean.sh` which confirms first).
5. **Never hardcode API keys** in script files.
6. **All scripts exit with code 0 on success, non-zero on failure**.

## Navigation

- **Self**: [AGENTS.md](AGENTS.md)
- **Parent**: [../AGENTS.md](../AGENTS.md)
- **Human README**: [README.md](README.md)
- **Source**: [../src/AGENTS.md](../src/AGENTS.md)
- **Reports output**: [../reports/AGENTS.md](../reports/AGENTS.md)
