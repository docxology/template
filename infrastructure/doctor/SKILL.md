---
name: infrastructure-doctor
description: Skill for the doctor infrastructure module providing repository-level diagnostics and safe, reversible automated repair. Use when the local checkout is acting up, before opening a bug, when onboarding a fresh clone, or as a periodic health probe. Every mutation is backed up under .doctor/backups/ and journalled in .doctor/actions.jsonl so any change can be undone byte-for-byte.
---

# Doctor Module

Repository-level "doctor mode": a diagnostic engine plus an automated, audited resolution engine. The doctor never leaves the patient worse off — every mutation is snapshotted before it runs and can be reversed by a single `undo` command.

## Quick start

```bash
# Diagnose only (read-only).
uv run python -m infrastructure.doctor

# Same, JSON for an agent.
uv run python -m infrastructure.doctor --json diagnose

# Show what would be fixed (no changes).
uv run python -m infrastructure.doctor fix --plan

# Apply the safest set of fixes.
uv run python -m infrastructure.doctor fix --apply

# Allow `uv sync` and other moderate-therapy fixes.
uv run python -m infrastructure.doctor fix --apply --moderate

# Allow radical fixes (e.g. delete orphan output directories — still backed up).
uv run python -m infrastructure.doctor fix --apply --aggressive

# Reverse the most recent applied, reversible action.
uv run python -m infrastructure.doctor undo --last

# Reverse one specific action (see `history`).
uv run python -m infrastructure.doctor undo --action-id <id>

# Inspect the journal.
uv run python -m infrastructure.doctor history

# Agent-facing capability manifest.
uv run python -m infrastructure.doctor capabilities

# Stable-text robot manual.
uv run python -m infrastructure.doctor robot-docs
```

## Safety contract

Every fix flows through `infrastructure.doctor.safety.mutate(plan, state)`. That function is the **only** code in this module that writes to the filesystem on behalf of a fixer. It guarantees:

1. Paths in `plan.affected_paths` are resolved and confirmed to be inside the repo and outside `.doctor/`.
2. Every existing path is copied byte-for-byte into `.doctor/backups/<action_id>/` and its SHA-256 is recorded.
3. The registered handler for `plan.action_kind` runs (`delete_paths`, `chmod`, `write_file`, `run_uv_sync`).
4. Post-mutation hashes are taken; the result is appended to `.doctor/actions.jsonl` as a single JSON line.
5. If the handler raises, the journal still records the attempt with `applied=false` and `error` populated — audit is never silently lost.

`undo(record)` inverts a reversible record by restoring every path from its backup, then verifying the post-restore hash equals the original `pre_hash`. A mismatch raises `DoctorSafetyError` rather than overwriting unexpected content.

## Detector / fixer inventory

| Code   | Detector                            | Default fix (therapy)                              |
| ------ | ----------------------------------- | -------------------------------------------------- |
| DOC101 | uv on PATH                          | — (install manually)                               |
| DOC102 | Python version >= 3.10              | — (install manually)                               |
| DOC103 | run.sh executable                   | `fix_make_run_sh_executable` (conservative)        |
| DOC201 | project layout                      | —                                                  |
| DOC202 | per-project pyproject.toml          | —                                                  |
| DOC203 | manuscript/config.yaml integrity    | —                                                  |
| DOC301 | __pycache__ / pytest / mypy / ruff  | `fix_clean_pycache` (conservative, fully reversible) |
| DOC302 | stale .coverage / coverage_*.json   | `fix_clean_coverage_files` (conservative)          |
| DOC303 | orphan output/<name>/ dirs          | `fix_remove_orphan_output_dirs` (radical, reversible) |
| DOC401 | pre-commit local hook installed     | `fix_install_pre_commit_hook` (conservative)       |
| DOC402 | uv.lock vs pyproject.toml drift     | `fix_run_uv_sync` (moderate, **not** reversible)   |
| DOC501–504 | Ollama / Docker / XeLaTeX / Pandoc | —                                                  |
| DOC601 | .doctor/ writable                   | —                                                  |

## Exit codes (stable)

| Code | Meaning                          |
| ---- | -------------------------------- |
| 0    | healthy                          |
| 1    | warnings present                 |
| 2    | one or more errors               |
| 3    | one or more criticals            |
| 4    | regression after a fix           |
| 64   | usage error (BSD `EX_USAGE`)     |

## Public API

```python
from infrastructure.doctor import (
    DoctorState, run_detectors, build_plans_for_findings,
    mutate, undo, load_journal,
    compute_scorecard, compute_exit_code,
    render_report_text, render_report_json,
)
```

## Where state lives

```
.doctor/
├── backups/<action_id>/   # full snapshot of every path the fix touched
├── actions.jsonl          # append-only audit log (one JSON line per action)
└── state.json             # (reserved for future last-run summary)
```

`.doctor/` should be added to `.gitignore`. The doctor never writes outside this directory except to apply the fix itself.

## Tests

```bash
uv run pytest tests/infra_tests/doctor/ -v --no-cov
```

Follows the repo's no-mocks policy: every test runs against a real temporary repo and exercises the actual mutate/undo path.
