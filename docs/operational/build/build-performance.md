# 📈 Build Performance Analysis

> **Detailed performance metrics** and per-stage breakdowns

**Quick Reference:** [Build System](build-system.md) | [Build History](build-history.md) | [Troubleshooting](../troubleshooting/README.md)

This document provides detailed performance analysis extracted from the build system. For pipeline overview and troubleshooting, see [build-system.md](build-system.md).

---

## Detailed Stage Breakdowns

### Test Execution — 26 seconds

**Breakdown:**

- Infrastructure Tests: 23 seconds (1796 tests, 2 skipped)
- Project Tests: 3 seconds (320 tests)

**Result:** ✅ **ALL TESTS PASSING**

**Coverage Breakdown:**

| Module | Statements | Missing | Coverage | Status |
|--------|------------|---------|----------|--------|
| `projects/{name}/src/example.py` | 21 | 0 | **100%** | ✅ |
| `infrastructure/documentation/glossary_gen.py` | 56 | 0 | **100%** | ✅ |
| `infrastructure/validation/content/pdf_validator.py` | 39 | 0 | **100%** | ✅ |
| `infrastructure/scientific/` | 300 | 35 | **88%** | ✅ |
| `infrastructure/publishing/` | 305 | 44 | **86%** | ✅ |
| `infrastructure/validation/integrity/checks.py` | 354 | 67 | **81%** | ✅ Very Good |
| **TOTAL** | **1989** | **360** | **81.90%** | ✅ **Excellent** |

### Project Analysis — Script Execution (6 seconds)

**Result:** ✅ **ALL SCRIPTS SUCCESSFUL**

#### Script 1: `example_figure.py`

- ✅ Demonstrates thin orchestrator pattern
- ✅ Imports from `projects/{name}/src/example.py`
- ✅ Generates: `output/figures/example_figure.png`, `output/data/example_data.npz`, `output/data/example_data.csv`

#### Script 2: `generate_research_figures.py`

- ✅ Generates 9 research figures
- ✅ Generates 2 data files (CSV)
- ✅ All scripts properly use `projects/{name}/src/` modules

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

### PDF Rendering (50 seconds)

**Breakdown:**

- Individual section PDFs + slides + HTML: ~45 seconds
- Combined PDF generation: ~5 seconds

| # | Module | Time | Status | Notes |
|---|--------|------|--------|-------|
| 1 | `01_abstract.md` | 2s | ✅ | Clean build |
| 2 | `02_introduction.md` | 3s | ✅ | Clean build |
| 3 | `03_methodology.md` | 3s | ⚠️ | BibTeX warning (expected) |
| 4 | `04_experimental_results.md` | 7s | ✅ | Longer due to figures |
| 5 | `05_discussion.md` | 2s | ✅ | Clean build |
| 6 | `06_conclusion.md` | 3s | ✅ | Clean build |
| 7 | `08_acknowledgments.md` | 2s | ✅ | Clean build |
| 8 | `09_appendix.md` | 2s | ✅ | Clean build |
| 9 | `S01_supplemental_methods.md` | 3s | ✅ | Clean build |
| 10 | `S02_supplemental_results.md` | 2s | ✅ | Clean build |
| 11 | `98_symbols_glossary.md` | 2s | ✅ | Auto-generated |
| 12 | `99_references.md` | 2s | ✅ | Clean build |

#### BibTeX Warning in 03_methodology.md

```
Warning--I didn't find a database entry for "optimization2022"
```

**Analysis:** This warning is expected — when building individual sections, BibTeX may not find all citations. The combined PDF build resolves all citations correctly.

### Combined Document (10 seconds)

**Compilation Steps:**

1. Markdown concatenation ✅
2. Bibliography placement correction ✅
3. LaTeX generation ✅
4. First XeLaTeX pass ✅
5. BibTeX processing ✅
6. Second XeLaTeX pass (references) ✅
7. Third XeLaTeX pass (final) ✅

### Alternative Formats (3 seconds)

- ✅ HTML Version created: `output/project_combined.html`
- ⚠️ IDE-Friendly PDF: Optional format — creation failed (non-critical). Main PDF works perfectly.

---

## Output File Inventory

### PDFs Generated (13 total)

**Individual Section PDFs:**

1. `01_abstract.pdf` ✅
2. `02_introduction.pdf` ✅
3. `03_methodology.pdf` ✅
4. `04_experimental_results.pdf` ✅
5. `05_discussion.pdf` ✅
6. `06_conclusion.pdf` ✅
7. `08_acknowledgments.pdf` ✅
8. `09_appendix.pdf` ✅
9. `S01_supplemental_methods.pdf` ✅
10. `S02_supplemental_results.pdf` ✅
11. `98_symbols_glossary.pdf` ✅
12. `99_references.pdf` ✅

**Combined Documents:**
13. `project_combined.pdf` ✅ **(Main output)**

### Other Formats

- `project_combined.html` ✅ (Web/IDE viewing)
- LaTeX source files (`.tex`) ✅ (All sections)

### Output Directory Structure

```
output/
├── figures/          # PNG files from scripts
├── data/             # CSV/NPZ data files
├── pdf/              # Individual + combined PDFs
├── tex/              # LaTeX source files
└── latex_temp/       # Temporary LaTeX files
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
