# Gate-Script Tests - Quick Reference

Tests for the opt-in gate scripts under [`scripts/gates/`](../../../scripts/gates/).

## Overview

These gates are **not** part of the default pipeline or CI — they are run on
demand. Each test scaffolds a real project tree under `tmp_path` (no mocks) and
exercises both the pass and fail paths of its gate.

## Files

| Test | Gate under test | Covers |
|------|-----------------|--------|
| `test_methods_plan_check.py` | `scripts/gates/methods_plan_check.py` | The methods-orchestration publication contract (definition-of-done per stage, manuscript methods section, evidence/manifest surfaces): pass on a fully-specified repo, exit 1 with actionable FAIL lines when the contract is unmet. |

## Running

```bash
uv run pytest tests/infra_tests/gates/ -p no:cacheprovider --no-cov
```
