# DEEP_PASS_2026-08-21c — Major-finding implementation (module splits)

Follow-up to the same-day deep passes. This pass **implemented J1** (the
Major-scoped oversized-module split), which earlier passes scoped but did not
execute. All measurements below were executed live in this checkout.

## J1 — Oversized validation/rendering modules: IMPLEMENTED

Three modules were split; every public import path is preserved because the
parents re-import the moved names.

### 1. `infrastructure/validation/rendered_snapshot.py` (800 lines) → package

- `rendered_snapshot/__init__.py` (public API: dataclasses,
  `build_current_rendered_snapshot`, `validate_green_report_payload`,
  `read_committed_validation_report`, `rendered_manuscript_paths`, `_output_records`)
- `rendered_snapshot/_scan.py` — repository-boundary walk, symlink confinement,
  Git-cached-record machinery, `RenderedSnapshotError`, `Fingerprint`, `FileRecord`
- `rendered_snapshot/_records.py` — stage/source/config record builders

### 2. `infrastructure/validation/output/pipeline.py` (810 lines) → 637 + report.py

- `output/report.py` — `generate_validation_report` with the full
  recommendation table and persistence paths; parent imports it back so
  `from infrastructure.validation.output.pipeline import generate_validation_report`
  still works (tests depend on that path).

### 3. `infrastructure/rendering/slide_deck.py` (842 lines) → 573 + _slide_draw.py

- `rendering/_slide_draw.py` — all `_draw_*` ReportLab primitives and
  `_draw_wrapped`; `render_pdf` imports them lazily (the companion imports
  `slide_deck` for shared constants, so the parent must not import it at module
  load). PDF/PPTX parity contracts untouched — both still consume the same
  constants and layout planners from `slide_deck`.

## Verification (measured)

| Check | Result |
| --- | --- |
| `pytest tests/infra_tests/validation/` | 1520 passed |
| `pytest tests/infra_tests/validation/test_rendered_provenance.py` | 45 passed |
| `pytest tests/infra_tests/rendering/` | 1338 passed, 2 skipped |
| `pytest projects/templates/template_pitch_deck/tests/` | 149 passed (90% src coverage gate) |
| `pytest tests/infra_tests/validation/test_validation_output_pipeline.py test_render_formats.py` | 90 passed |
| ruff check + ruff format --check (all touched files) | clean |
| mypy (rendering/ + validation/, 176 files) | no issues |
| `module_line_count_check.py` | exit 0; slide_deck (842), output/pipeline (810), rendered_snapshot (800) no longer warned |
| `check_template_drift.py --strict` | no drift |
| `infrastructure.skills check` / `check-all-exports` | ok / 0 violations |
| `verify_no_mocks.py` | exit 0 |
| Line counts after split | `rendered_snapshot/__init__` 398, `_scan` ~365, `_records` ~125; `output/pipeline` ~637, `report` ~215; `slide_deck` 573, `_slide_draw` 326 — all under the 800 warn threshold |

Byte-determinism contracts (PPTX ZIP timestamp normalization, EPUB identity,
ReportLab `invariant=1`) were not modified; the pitch-deck suite re-rendered
real decks and passed.

## Known pre-existing failure (not mine, not touched)

`tests/infra_tests/validation/docs/test_mermaid_lint.py::test_validate_blocks_retries_transient_timeout_then_succeeds`
fails deterministically in this checkout. Both it and
`infrastructure/validation/docs/mermaid_lint.py` carry uncommitted modifications
from a concurrent writer; per mission hard rules I did not touch them.

## Docs

- `infrastructure/validation/output/AGENTS.md`, `infrastructure/validation/AGENTS.md`,
  `infrastructure/rendering/AGENTS.md` updated for the new module layout.

## Commit scope / concurrent-writer note

A concurrent session committed the `rendered_snapshot` package and
`output/report.py` halves of this same work mid-pass (commit `2b36d6671`,
which also added its own package AGENTS.md/README.md). This pass's commit
therefore contains: the `slide_deck.py` → `_slide_draw.py` split, the three
AGENTS.md map updates, and this report. Nothing pushed.
