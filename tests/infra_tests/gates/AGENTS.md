# Gate-Script Tests

## Overview

The `tests/infra_tests/gates/` directory contains tests for the opt-in gate
scripts under [`scripts/gates/`](../../../scripts/gates/). Those gates are
advisory/opt-in — **none run in the default `./run.sh` pipeline or CI** — so
their tests guard the gate logic itself (pass and fail paths) rather than wiring.

## Conventions

- **No mocks.** Each test scaffolds a real project tree under `tmp_path` and runs
  the gate's underlying infrastructure functions (or the gate script via
  subprocess) against it.
- Cover both directions: a fully-specified repo passes; a repo missing the
  contracted artifacts exits non-zero with actionable messages.

## Files

| Test | Gate | Delegates to |
|------|------|--------------|
| `test_methods_plan_check.py` | `scripts/gates/methods_plan_check.py` | `infrastructure.methods.build_methods_orchestration_plan` + `validate_methods_orchestration_plan` |

## See also

- [`scripts/gates/AGENTS.md`](../../../scripts/gates/AGENTS.md) — the gate scripts themselves
- [`tests/infra_tests/AGENTS.md`](../AGENTS.md) — infrastructure test suite overview
