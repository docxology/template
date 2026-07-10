# Testing Guide

The suite is real code and real data end to end: real on-disk SQLite files,
a real in-process message bus with seeded fault injection, and real
`mypy --strict` subprocess invocations — zero mocks anywhere.

## Running the suite

From the **repository root** (the isolated-venv-resolving invocation this
project's own gate is bound to — see `ISA.md`'s Changelog for why a bare
root-venv `pytest` run is not sufficient evidence):

```bash
uv run python scripts/pipeline/stage_01_test.py --project templates/template_formal --project-only
```

Or directly, from inside the project directory:

```bash
uv run pytest projects/templates/template_formal/tests/ -v
uv run pytest projects/templates/template_formal/tests/ --cov=projects/templates/template_formal/src --cov-report=html
```

`pythonpath = [".", "src"]`, `testpaths`, and coverage settings live in
[`pyproject.toml`](../pyproject.toml); `tests/conftest.py` additionally
inserts the repo root and project root onto `sys.path` so tests resolve
both `template_formal.*` and any repo-root imports.

## Suite structure

`tests/` mirrors `src/template_formal/`'s package layout:

| Directory / file | Covers |
| --- | --- |
| `tests/test_types_ids.py`, `tests/test_types_result.py` | `NewType` ID constructors; the `Result` ADT (`Ok`/`Err`, `map_result`, `and_then`, `unwrap_or`). |
| `tests/storage/` | Typed schema-to-DDL (`test_storage_schema.py`), the query builder + real on-disk SQLite (`test_storage_db.py`), the affine `TransactionHandle` (`test_storage_transaction.py`). |
| `tests/protocol/test_session.py` | The session-typed state machine and the wire codec's round-trip + truncation/corruption negative controls. |
| `tests/network/` | The fault-injectable bus in isolation (`test_bus.py`) and a full handshake driven through it, happy-path plus drop/corrupt fault modes (`test_handshake_over_bus.py`). |
| `tests/agent/` | Hand-computed expected-free-energy numerics (`test_agent_free_energy.py`), the tick/storage/protocol lifecycle (`test_agent_lifecycle.py`), and the structural cross-agent-isolation proof (`test_agent_isolation.py`). |
| `tests/colony/` | The pheromone `Protocol` (`test_pheromone.py`), the N≥3 real-agent integration demo (`test_colony_integration.py`), the N=150 statistical-rigor claim (`test_colony_convergence_statistics.py`), config validation (`test_colony_experiment_config.py`), stats unit tests (`test_colony_stats_unit.py`), the demo/visualization runners (`test_demo.py`, `test_visualization.py`), the null model (`test_nullmodel.py`), the generic sweep (`test_sweep.py`), the deterministic cover-art generator (`test_cover_art.py`), and the eight pre-registered analyses A-H (`test_colony_experiments_extended.py`). |
| `tests/test_mypy_oracle.py` | The static-oracle harness itself (see below). |
| `tests/mypy_fixtures/` | `bad_*.py` negative-control and `good_*.py` positive-control fixtures — never imported or executed, only type-checked. |

## No-mocks policy

Zero `MagicMock`/`mocker.patch`/`unittest.mock` anywhere — a repo-wide,
hard rule (`grep -rn "MagicMock\|mocker.patch\|unittest.mock"
projects/templates/template_formal/tests/` must return nothing). Every
test in this project backs its claim with a real artifact: an on-disk
SQLite file via `tmp_path` for anything claiming durability
(`open_fast_test_database`'s `:memory:` escape hatch is named and
docstringed as test-only precisely so it can never stand in for a
durability claim — ISC-66), a real `InProcessBus` for fault injection, and
a real `subprocess.run([..., "mypy", "--strict", ...])` for every static
claim.

## Coverage gate

Project code targets **≥90% coverage** (`fail_under = 90` in
`pyproject.toml`, `source = ["src"]`). The suite currently sits well above
the floor — check the exact current figure yourself rather than trusting a
number in this document, since it moves as the suite grows:

```bash
uv run python scripts/pipeline/stage_01_test.py --project templates/template_formal --project-only
```

ISC-67 (anti-criterion) requires every covered line to be reachable from
at least one *behavioral* assertion — coverage achieved by testing that a
type annotation exists, rather than exercising real behavior, does not
count, and is spot-checked in `ISA.md`'s Verification section.

## The mypy-as-oracle harness

[`tests/test_mypy_oracle.py`](../tests/test_mypy_oracle.py) is the
cross-cutting proof-of-detection layer: it runs `mypy --strict` as a real
subprocess (never a hand-inspected type signature) against every
`bad_*.py`/`good_*.py` fixture under `tests/mypy_fixtures/`, and separately
against the real `src/` tree.

- **`bad_*.py` fixtures** must be rejected (non-zero exit), and must
  contain the *specific* expected error substring bound to that fixture in
  `_EXPECTED_BAD_FIXTURE_SUBSTRINGS` — not a generic `"error:"` check (see
  the [type system guide](type_system_guide.md) for why the generic form
  is a hollow gate).
- **`good_*.py` fixtures** must be accepted (zero exit) — these are
  positive controls proving a generic/`Protocol` binding `src/` itself
  never instantiates concretely (e.g. `Agent[BeliefState]`,
  `InProcessBus[WireMessage]`) actually type-checks cleanly.
- **The real `src/` tree** must exit zero — proof the main code is
  actually clean, not merely that the fixtures are broken.

The authoritative invocation is `MYPYPATH=<project>/src` +
`--explicit-package-bases --namespace-packages`, exactly what
`test_mypy_oracle.py`'s `_run_mypy_strict` helper does — a bare
repo-root `mypy --strict` command resolves the same file under two
different module identities and produces spurious `Generic[...]`/
`"SessionEndpoint" expects no type arguments` errors unrelated to any real
defect (`ISA.md`'s Changelog documents the exact repro). Don't invoke mypy
any other way and trust the result.

## Test parallelization: what `pytest-xdist` actually buys you here

`pytest-xdist` is wired into this project's `dev` optional-dependency
group (`pyproject.toml`), so both of these work:

```bash
uv run pytest projects/templates/template_formal/tests/ -n auto
uv run pytest projects/templates/template_formal/tests/ -n 4
```

**Honest finding on wall-clock**: cross-test parallelism speeds up the
bulk of this suite (the many small, independent unit/integration tests
across `types/`, `storage/`, `protocol/`, `network/`, `agent/`) normally.
It does **not** meaningfully speed up the large, module-scoped
experiment-sweep fixtures in
`tests/colony/test_colony_convergence_statistics.py` (the `main_batch`
fixture, plus the standalone negative-control and positive-control tests,
each running their own batch of real trials) and
`tests/colony/test_colony_experiments_extended.py` — now seven
module-scoped fixtures (`decay_sweep_points`, `real_vs_null_results`,
`heterogeneity_sweep_results`, `heterogeneity_sweep_results_seed7000`,
`decay_sweep_points_seed1000`, `zero_deposit_real_results`,
`capped_low_decay_points`), each running hundreds of sequential real
trials internally (a `for` loop over `run_colony_trial`/
`run_null_model_trial`/`run_parameter_sweep` calls), so `-n auto`/`-n 4`
cannot split that internal loop across workers — xdist parallelizes across
test *functions*, not within one, and several tests share one fixture via
`scope="module"` regardless. These fixtures dominate the suite's total
wall-clock regardless of worker count; if you need to speed one up
specifically, the lever is inside the fixture (fewer trials, a smaller
`n`/`n_per_value`), not `-n`.
