# `tests/` — test suite map

277 tests, mirroring `src/template_formal/`'s subpackage layout one-for-one.
No mocks anywhere — every test uses a real SQLite file (or the one documented
`:memory:` test-only escape hatch), a real `mypy --strict` subprocess, real
`matplotlib` rendering, or hand-derived arithmetic.

| Directory / file | What it tests |
| --- | --- |
| [`agent/`](agent/) | `Agent[StateT]` — hand-computed expected-free-energy numerics (`test_agent_free_energy.py`), structural proof that one agent's SQLite file is unreachable via another agent's public API (`test_agent_isolation.py`), and storage/tick/protocol-endpoint behavior (`test_agent_lifecycle.py`). |
| [`colony/`](colony/) | The multi-agent coordination layer: pheromone-field Protocol conformance (`test_pheromone.py`), the fixed-symmetric-config emergent-convergence demo (`test_colony_integration.py`), pure-function unit tests for `stats.py`/`find_sustained_consensus_tick` (`test_colony_stats_unit.py`), `ColonyTrialConfig.__post_init__` runtime guards (`test_colony_experiment_config.py`), the N=150 statistical-rigor claim plus its wall-clock benchmark (`test_colony_convergence_statistics.py`), the random-choice null-model baseline's determinism and structural isolation (`test_nullmodel.py`), the generic parameter-sweep runner (`test_sweep.py`), eight pre-registered analyses grouped across three experiment families (`test_colony_experiments_extended.py`), and the demo/visualization runners (`test_demo.py`, `test_visualization.py`). |
| [`network/`](network/) | The in-process fault-injectable bus (`test_bus.py`: seeded determinism, each fault mode actually firing) and an end-to-end handshake driven through it (`test_handshake_over_bus.py`). |
| [`protocol/`](protocol/) | The session-typed state machine and its wire codec (`test_session.py`). |
| [`storage/`](storage/) | Schema-to-DDL generation (`test_storage_schema.py`), the real on-disk `QueryBuilder` (`test_storage_db.py`), and the affine-discipline `TransactionHandle` (`test_storage_transaction.py`). |
| [`mypy_fixtures/`](mypy_fixtures/) | Not pytest tests themselves — real Python source files, each encoding one illegal or (for `good_*.py`) legal state, driven by `test_mypy_oracle.py` below. |
| [`test_mypy_oracle.py`](test_mypy_oracle.py) | Runs `mypy --strict` as a real subprocess against every fixture and the real `src/` tree — see "mypy-oracle harness" below. |
| [`test_types_ids.py`](test_types_ids.py), [`test_types_result.py`](test_types_result.py) | The two leaf `types/` modules that have no natural subpackage test directory of their own. |
| [`conftest.py`](conftest.py) | Puts repo root, project root, and `src/` onto `sys.path` (see [`../src/AGENTS.md`](../src/AGENTS.md)) — no fixtures beyond path wiring. |

## No-mocks policy

`MagicMock`/`mocker.patch`/`unittest.mock` are banned repo-wide. Concretely,
in this project:

- **Real SQLite**, always — `storage/` and `agent/` tests open real files via
  `tmp_path`; the *only* `:memory:` use anywhere is
  `storage.db.open_fast_test_database`, named and docstringed as test-only so
  it can never be mistaken for a durability claim (ISC-66).
- **Real `mypy --strict` subprocess calls** — `test_mypy_oracle.py` never
  hand-inspects a type signature; it shells out to the real type checker and
  asserts on its real exit code and stdout.
- **Real `matplotlib` rendering** — `test_visualization.py` and
  `test_demo.py` write real PNG files to `tmp_path` and assert they exist and
  are non-trivially sized; nothing about figure generation is stubbed.
- **Real computation everywhere else** — the statistics module
  (`colony/stats.py`) is stdlib-only, so its tests bind to hand-derived
  numbers, not a second call to the function under test.

## Coverage gate

90% floor (`pyproject.toml`'s `[tool.coverage.report] fail_under = 90`),
currently **96.03%** measured this session via:

```bash
uv run pytest tests -q --cov=src/template_formal --cov-report=term-missing
```

The lowest-covered modules are `storage/db.py` (88.04%, missing a few
`sqlite3.Error` exception branches that are hard to trigger without a
corrupted file) and `colony/experiment.py` (90.08%, missing a couple of
`RuntimeError` branches documented as "unreachable in practice" guards);
neither is a `# pragma: no cover` — they are simply below 100% and still
comfortably above the 90% floor.

## The mypy-oracle harness

`test_mypy_oracle.py` auto-discovers its fixtures by glob —
`tests/mypy_fixtures/bad_*.py` and `tests/mypy_fixtures/good_*.py` — rather
than an explicit hand-maintained list. Adding a new fixture file is enough to
get it parametrized into the suite:

- **`bad_*.py`** fixtures must each be rejected by `mypy --strict`, and each
  must have an entry in `_EXPECTED_BAD_FIXTURE_SUBSTRINGS` binding it to the
  *specific* error substring mypy actually emits for it — a fixture with no
  entry raises `KeyError` rather than silently passing under a generic
  `"error:" in stdout` check (a hollow-gate class this harness deliberately
  refuses to be).
- **`good_*.py`** fixtures must each be *accepted* cleanly — these are
  positive controls proving a generic/structural-conformance surface
  `src/`-only checking can't see (e.g. `Agent[BeliefState]` actually
  instantiates) really does type-check, not merely that the corresponding
  `bad_*.py` fixture is broken.
- A third assertion runs `mypy --strict` against the real `src/` tree and
  requires a clean exit — the harness can't be gamed by fixtures alone while
  the shipped code itself has errors.

## Test parallelization (pytest-xdist)

`pytest-xdist>=3.6.0` is a real `[project.optional-dependencies] dev` entry
in `pyproject.toml`. `uv run pytest tests -n auto` and `-n 4` both run to
completion and (usually) pass all 277 tests — verified this session. Be
skeptical of any claim that `-n auto`/`-n 4` make the *full* suite faster
here: they don't, and they introduce a real flakiness risk. Measured this
session, on this machine:

| Invocation | Wall clock | Result |
| --- | --- | --- |
| `pytest tests` (serial) | machine-dependent | 277 passed in the current full run |
| `pytest tests -n auto` (14 workers) | machine-dependent | Re-run serially if a wall-clock assertion trips under CPU contention |
| `pytest tests -n 4` | machine-dependent | Use only when overlapping the two heavy experiment modules is worth the worker overhead |

The single failure observed under `-n auto` was
`test_colony_convergence_statistics.py::test_wall_clock_benchmark_stays_within_budget`
tripping its own internal budget (it measured 45.62s against a 45.0s ceiling)
— not a real regression, but real CPU contention from 14 concurrent workers
each running a chunk of the N=150 trial batch on the same machine at once.
Re-running the identical `-n auto` invocation immediately after passed
cleanly. This is the same class of nondeterministic wall-clock-under-load
flake documented for the repo's infra suite (see root `CLAUDE.md`'s note on
`-n auto` tripping LaTeX/subprocess timeouts on loaded machines) — it is not
specific to this project, and it is not a reason to avoid `-n auto`/`-n 4`
outright, but it does mean a red run of the full suite under either flag
should be re-run serially before treating it as a real failure.

**Why xdist doesn't help here**: four large, module-scoped, sequential
real-trial batches dominate the suite's wall clock —
`test_colony_convergence_statistics.py` (N=150 real colony trials) and
`test_colony_experiments_extended.py` (three N-trial sweeps/null-model
batches) together account for the majority of total runtime, and each is
*one* Python test function running hundreds of sequential real trials in a
tight loop. `pytest-xdist` distributes whole test functions across workers,
not the iterations inside one function, so these two files cannot be split
across workers no matter the worker count — the fastest any parallel
invocation can go is bounded below by whichever single worker draws one of
these two files.

**Recommendation**:

- Iterating on the many small/fast unit tests (everything except the two
  heavy files): `-n auto` is a reasonable default, but measure before relying
  on it — this session, excluding those two files, serial (`2.54s`, 199
  tests) was actually *faster* than `-n auto` (`3.85s`, 14 workers spun up)
  on this machine, because worker-spawn overhead outweighs the saving on a
  suite that already runs in a few seconds:

  ```bash
  uv run pytest tests -k "not experiments_extended and not convergence_statistics" -n auto
  ```

- Running the **full** suite (including the two heavy sweep files): prefer
  serial, or a small worker count if you specifically want to overlap the two
  heavy files with the rest of the suite. Do not assume `-n auto` is faster
  for the full suite on every machine — on this one, it measured slower than
  serial and once flaked on the wall-clock gate.
