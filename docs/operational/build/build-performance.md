# 📈 Build Performance Analysis

> **Detailed performance metrics** and per-stage breakdowns

**Quick Reference:** [Build System](build-system.md) | [Build History](build-history.md) | [Troubleshooting](../troubleshooting/README.md)

This document provides detailed performance analysis extracted from the build system. For pipeline overview and troubleshooting, see [build-system.md](build-system.md).

---

## Detailed Stage Breakdowns

### Test Execution — wall-clock varies; live counts in `_generated/COUNTS.md`

**Indicative breakdown** (numbers drift with every commit; verify live counts in [`../../_generated/COUNTS.md`](../../_generated/COUNTS.md)):

- Pipeline infrastructure smoke: ~20 seconds, focused on DAG/control/evidence/profile/benchmark/doc guardrails
- Full infrastructure gate: explicit coverage-bearing repo suite; runtime varies with the full `tests/infra_tests/` + integration matrix
- Project Tests: ~5 seconds, matrix of all active exemplars (see `active_projects.md`)

**Result:** ✅ **ALL TESTS PASSING**

**Coverage Breakdown:** *dated benchmark snapshot — live % → [`../../development/coverage-gaps.md`](../../development/coverage-gaps.md)*

| Module | Notes |
|--------|-------|
| `projects/{name}/src/` | Per-exemplar gates → [`../../_generated/COUNTS.md`](../../_generated/COUNTS.md) |
| `infrastructure/*` | Per-module % → [`../../development/coverage-gaps.md`](../../development/coverage-gaps.md) |

### Project Analysis — Script Execution (6 seconds)

**Result:** ✅ **ALL SCRIPTS SUCCESSFUL**

#### Script 1: `projects/templates/template_code_project/scripts/optimization_analysis.py`

- ✅ Demonstrates thin orchestrator pattern
- ✅ Imports from `src/analysis.py`, `src/figures.py`, `src/optimizer.py`
- ✅ Generates: `output/figures/convergence_plot.png`, `output/data/optimization_results.csv`, reports under `output/reports/`

#### Script 2: `projects/{name}/scripts/<analysis>.py`

- ✅ Additional project scripts follow the same pattern (figures + data via `src/`)

### Repository Utilities (< 1 second)

**Result:** ✅ **COMPLETED**

#### Glossary Generation

- ✅ Auto-generated from `projects/{name}/src/` API
- ✅ Output: `manuscript/98_symbols_glossary.md`

#### Markdown Validation

- ⚠️ **Warnings Found (non-strict mode):**
  - Use equation environment instead of `$$` in `manuscript/AGENTS.md`
  - Use equation environment instead of `\[ \]` in `manuscript/AGENTS.md`

**Analysis:** These warnings are expected — `AGENTS.md` is documentation, not manuscript content.

### PDF Rendering

Rendering time depends on the project, section count, figures, Mermaid diagrams, and local
LaTeX/browser availability. Treat old wall-clock numbers as benchmark snapshots, not as
service-level objectives.

Current renderer behavior:

- Manuscript sections are discovered from `projects/{name}/manuscript/*.md`.
- Working render artifacts are written under `projects/{name}/output/`.
- Stage 07 copies final deliverables to `output/{name}/`.
- The primary combined PDF is available at `output/{name}/pdf/{name}_combined.pdf`;
  a root convenience copy may also exist at `output/{name}/{name}_combined.pdf`.
- Web output is under `output/{name}/web/`.

### Combined Document

**Compilation Steps:**

1. Markdown concatenation
2. Bibliography placement correction
3. LaTeX generation
4. XeLaTeX and BibTeX passes until references settle
5. Final PDF validation

### Alternative Formats

When enabled by the renderer and project configuration, non-PDF formats are copied under
project-specific directories such as `output/{name}/web/`, `output/{name}/docx/`, and
`output/{name}/epub/`.

---

## Output File Inventory

### PDFs Generated

**Combined Document:**

- `output/{name}/pdf/{name}_combined.pdf` - primary validated PDF
- `output/{name}/{name}_combined.pdf` - optional root convenience copy

**Slides and intermediates:**

- `output/{name}/slides/` - Beamer slide PDFs and LaTeX intermediates when generated
- `output/{name}/pdf/_combined_manuscript.*` - combined Markdown/LaTeX/log intermediates

### Other Formats

- `output/{name}/web/index.html` - web view when generated
- `output/{name}/docx/{name}_combined.docx` - DOCX when generated
- `output/{name}/epub/{name}_combined.epub` - EPUB when generated

### Output Directory Structure

```text
output/{name}/
├── data/             # Project data artifacts
├── figures/          # Figures from project scripts
├── pdf/              # Combined PDF and render intermediates
├── slides/           # Slide artifacts when generated
├── web/              # HTML artifacts when generated
├── docs/             # Generated API/glossary docs when generated
└── reports/          # Validation, test, telemetry, and manifest reports
```

---

## Performance Optimization Tips

1. **Parallel testing** — Use `pytest-xdist` for faster test runs
2. **Caching** — Enable pytest caching for repeated runs
3. **Incremental builds** — Only rebuild changed components when possible
4. **System dependencies** — Keep LaTeX and Pandoc updated

---

**Related Documentation:**

- [Build System](build-system.md) — Pipeline overview and troubleshooting
- [Build History](build-history.md) — Historical fixes
- [PDF Validation](../../modules/pdf-validation.md) — Quality checks
