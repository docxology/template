# infrastructure.doctor

A diagnostic engine and audited resolution engine for the template
repository — `python -m infrastructure.doctor`.

The doctor abides by **"do no harm"**: every mutation is backed up to
`.doctor/backups/<action_id>/` and recorded in `.doctor/actions.jsonl`
before any fix runs, so any change can be reversed byte-for-byte.

## Why

Repeated operational pain — stale caches, missing executable bits, a
drifted `uv.lock`, orphan `output/` trees, an uninstalled pre-commit
hook — burns the time of every contributor and every agent that lands
in a fresh clone. The doctor converts each of those into:

* a **detector** (read-only, idempotent),
* a **fixer** (declarative `FixPlan`, executed via the safety chokepoint),
* a **regression test** that exercises the fix end-to-end against a
  temporary tree,
* and a **scorecard row** that makes "healthy" measurable rather than
  vibes-based.

## CLI

```bash
uv run python -m infrastructure.doctor                  # diagnose (default)
uv run python -m infrastructure.doctor --json           # JSON output

uv run python -m infrastructure.doctor fix --plan       # dry-run
uv run python -m infrastructure.doctor fix --apply      # safe set only
uv run python -m infrastructure.doctor fix --apply --moderate   # + uv sync etc.
uv run python -m infrastructure.doctor fix --apply --aggressive # + radical

uv run python -m infrastructure.doctor undo --last
uv run python -m infrastructure.doctor undo --action-id 20260510T161603Z_xxx

uv run python -m infrastructure.doctor history
uv run python -m infrastructure.doctor capabilities     # agent manifest
uv run python -m infrastructure.doctor robot-docs       # stable text manual
```

### Narrowing scope

```bash
# Only fix specific finding codes.
uv run python -m infrastructure.doctor fix --apply --select DOC103,DOC302

# Only invoke specific fixers.
uv run python -m infrastructure.doctor fix --apply \
    --fix-id fix_clean_coverage_files
```

## File layout

```
infrastructure/doctor/
├── __init__.py           # Public API
├── __main__.py           # `python -m infrastructure.doctor`
├── cli.py                # Argparse, subcommand dispatch
├── detectors/            # Read-only diagnostic checks (package)
│   ├── registry.py       # DETECTORS tuple + run_detectors()
│   ├── tooling.py        # DOC1xx environment / DOC4xx tooling state
│   ├── layout.py         # DOC2xx project layout
│   ├── hygiene.py        # DOC3xx hygiene
│   └── state.py          # DOC5xx optional services / DOC6xx safety
├── fixers.py             # FixPlan builders (no FS writes here)
├── models.py             # Severity, Finding, FixPlan, MutateRecord, ...
├── reporter.py           # Text + JSON renderers, exit codes
├── safety.py             # The mutate() chokepoint, backup, journal, undo
├── scorecard.py          # 6-dimension rubric
├── SKILL.md
├── README.md
└── AGENTS.md
```

```
.doctor/                  # created automatically; gitignore it
├── backups/
│   └── <action_id>/
│       ├── manifest.json
│       └── <mirrored paths>
└── actions.jsonl         # append-only journal
```

## Tests

```bash
uv run pytest tests/infra_tests/doctor/ -v --no-cov
```

49 tests, no mocks, sub-second wall time. Covers:

* `mutate()` refuses paths outside the repo or inside `.doctor/`.
* Every action kind (`delete_paths`, `chmod`, `write_file`,
  `run_uv_sync` is exercised via separate test) round-trips through
  backup and undo with SHA-256 verification.
* Detectors are idempotent (two runs on the same tree → identical
  findings).
* A crash in one detector does not mask the others — it surfaces as a
  CRITICAL `DOC000` finding.
* Scorecard math: INFO=0, WARN=15, ERROR=40, CRITICAL=70 deductions,
  clamped to `[0, 100]`.
* CLI exit codes match the contract (0 healthy, 1 warn, 2 error, 3
  critical, 64 usage).

## Adding a new detector

1. Append a function `detect_<thing>(repo_root) -> list[Finding]` to
   the matching concern module under `infrastructure/doctor/detectors/`
   (`tooling.py`, `layout.py`, `hygiene.py`, or `state.py`), then add it
   to the `DETECTORS` tuple in `infrastructure/doctor/detectors/registry.py`.
2. Pick a stable `code` — prefix decides the scorecard dimension:
   `DOC1xx` environment, `DOC2xx` project layout, `DOC3xx` hygiene,
   `DOC4xx` tooling state, `DOC5xx` optional services, `DOC6xx`
   safety surface.
3. If automatable, register a builder in
   `infrastructure/doctor/fixers.py` and add a `RepairLevel(fix_id=...)`
   to the finding.
4. Add a test in `tests/infra_tests/doctor/`.

The detector modules never import `fixers.py`; the fixer never imports
the `detectors/` package. They communicate via stable string `fix_id`s on
`RepairLevel`. Keeping that boundary clean is what lets agents reason
about either side independently.

## Adding a new fix action kind

If a new fixer needs an action that isn't covered by the four built-in
handlers (`delete_paths`, `chmod`, `write_file`, `run_uv_sync`):

```python
from infrastructure.doctor.safety import register_handler

def _my_handler(plan, state):
    for path in plan.affected_paths:
        ...  # only touch declared paths

register_handler("my_action_kind", _my_handler)
```

Register at module import time so the handler is always available by
the time `mutate()` is called.

## Related infrastructure

* `infrastructure/core/health.py` — runs every CI gate (mypy, ruff,
  bandit, no-mocks, docs-lint) as subprocesses; complementary, not
  redundant. Doctor diagnoses local repo state; `health` runs the
  quality gates.
* `scripts/shell/health-check.sh` — pre-flight tooling check (uv, Python,
  Docker, disk). Doctor's `DOC1xx` family covers the same surface but
  produces structured findings with optional remediation.

<!-- foam-orphan-nav:start (auto-managed: links sub-docs so they are reachable) -->

## Directory & sub-document map

Navigation links to in-tree documents (keeps them discoverable):

- [Doctor detectors package](detectors/AGENTS.md)
- [infrastructure/doctor/detectors/](detectors/README.md)

<!-- foam-orphan-nav:end -->
