# Gate Scripts

Pipeline gate scripts for template.

## Gates

- `gate_cache` — Validates and populates the cache
- `infra_ci_partition.py` — Emits the complete ordinary infrastructure CI matrix or packages/verifies its actual branch-coverage union; selection and coverage implementations reside in Layer 1.
- `ci_policy.py` — Emits the complete source-owned hosted job set; CI Gate refuses missing, extra, failed, or unjustifiably skipped outcomes.
- `security_scan` — Runs security scanning (bandit, safety, pip-audit)
- `mypy_ratchet.py` — Compatibility-named strict gate; fails on any typing error.
- `installed_public.py` — Builds genuine root and public exemplar wheels, admits exact source/resource bytes, supplies declared provider wheels and locked transitives, and probes isolated installed runtimes outside source. See [the installed-wheel matrix](../../docs/development/installed-wheel-matrix.md).
- `pip_audit_ignore_policy.py` — Requires accountable metadata on every dependency-audit exemption.
- `plugin_export_check` — Verifies plugin exports
- `methods_plan_check` — Validates source or rendered methods contracts for one project or all public exemplars. Source mode runs in unified health; rendered mode is an explicit publication gate.
- `public_capabilities.py` — Emits the deterministic public-exemplar capability manifest and fails closed on roster/matrix, package/Python, source/test syntax, render, hydration, analysis, and skip-contract drift.
- `check_private_project_promotion.py` — Candidate security scan and composite private-promotion gate, with the historical script entrypoint retained.
- `ci_module_durations_check.py` — Validates the committed measured module-duration manifest: every key is a real roster module and every value is a finite positive number of seconds.
- `local_gate.py` — One local entry point for the commands CI runs (`format`, `lint`, `types`, `security`, `gates`, `unit`, `infra`, `all`), offline by default, with `--changed` and `--list`.

## Fast local verification

`local_gate.py` orders the existing gate scripts and modules; it never
re-implements them. Stages map onto hosted work:

| Stage | Hosted counterpart | Commands |
| --- | --- | --- |
| `format` | `Lint & Type Check` | `ruff format --check` over `public_scope ci-paths` lint paths |
| `lint` | `Lint & Type Check` | `ruff check` over the same paths, then `module_line_count_check.py` |
| `types` | `Lint & Type Check` | `mypy_ratchet.py` over the source paths |
| `security` | health `bandit` gate | `bandit -r -ll -c bandit.yaml` over the public scope |
| `gates` | `Lint & Type Check` hygiene steps | tracked-artifact, confidentiality, mirror-symlink, export/manifest and duration-manifest checks |
| `unit` | `test-project` | `scripts/pipeline/stage_01_test.py --project …` |
| `infra` | `detect-projects` + `Infrastructure Smoke` | one `infrastructure.core.testing.ci_infra` job per declared shard and contract |

```bash
# Print the exact plan without running anything
uv run --no-sync python scripts/gates/local_gate.py --list
uv run --no-sync python scripts/gates/local_gate.py --list infra

# Fast feedback, then the full local reproduction of the CI jobs
uv run --no-sync python scripts/gates/local_gate.py format lint types
uv run --no-sync python scripts/gates/local_gate.py all

# Only the working-tree modules that a stage can actually re-check
uv run --no-sync python scripts/gates/local_gate.py --changed format lint types

# Inspection only: which modules the functional roster would run
uv run --no-sync python scripts/gates/local_gate.py --changed --list infra
```

Every stage runs `uv run --no-sync --offline`, so verification never resolves or
downloads dependencies. `--changed` narrows file-scoped stages to existing
working-tree paths (staged, unstaged and untracked), builds the functional plan
from those paths through the same selection functions CI calls, and skips
whole-tree controls it cannot honestly report on. Local feedback never replaces
the required CI matrix or release acceptance.

Functional shard balancing reads `infrastructure/config/ci-module-durations.json`:
observed hosted seconds where a module has a measurement, a byte-size estimate on
the same scale otherwise. `ci_module_durations_check.py` keeps that manifest
pointed at real roster modules.

```bash
uv run --no-sync python scripts/gates/ci_module_durations_check.py
```

```bash
# Methods gates (all public exemplars, or one --project)
uv run python scripts/gates/methods_plan_check.py --all-public --artifact-mode source
uv run python scripts/gates/methods_plan_check.py --all-public --artifact-mode rendered
uv run python scripts/gates/methods_plan_check.py --project templates/template_code_project
```

## Running

For ordinary development, start with the existing direct local lane for the
area changed. The [local command map](../../docs/maintenance/ci-local.md) lists
owning tests, supported lanes and the separate release acceptance route.
Run these commands from repository root:

```bash
# Inspect a selected development lane before running it
./scripts/shell/ci_local.sh --no-act --dry-run -j lint
./scripts/shell/ci_local.sh --no-act -j lint

# Inspect all supported direct lanes
./scripts/shell/ci_local.sh --no-act --list

# Run the complete static health registry
uv run --no-sync --offline python -m infrastructure.core.health --json
```

Focused local feedback must be followed by the required CI matrix and release
acceptance for the exact source revision. The local wrapper documents which
workflow jobs require `act` or GitHub Actions.
