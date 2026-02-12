# 🔧 Build System Historical Fixes

> **Historical record** of build system fixes and resolved issues

**Parent Document:** [Build System](build-system.md) | **Related:** [Troubleshooting](troubleshooting-guide.md)

---

## Fix: Path Concatenation Error

**Issue:** Path concatenation error in `build_combined()` function

**Error Message:**

```
cat: /Users/.../manuscript//Users/.../preamble.tex: No such file or directory
```

**Root Cause:**
The `build_combined()` function was incorrectly handling arguments. The `modules` array was inadvertently including the `$preamble_tex` path as its first element.

**Solution:**
Added `shift` command within the `build_combined()` function to remove the first argument (`$preamble_tex`) before populating the `modules` array with the remaining markdown file paths.

**Fix Applied:**

```bash
build_combined() {
  local preamble_tex="$1"
  shift  # Remove first argument so modules array only contains markdown files
  local modules=("$@")
  # ... rest of function
}
```

**Result:** ✅ Clean build output with zero errors

**Impact:** Code quality improvement, no functional changes

---

## Pipeline Architecture Evolution

The build pipeline evolved from a 6-stage core pipeline to the current 8-stage system:

**Current stages (00-07):**

- **Stage 00**: Environment setup & validation (`scripts/00_setup_environment.py`)
- **Stage 01**: Run tests with coverage (`scripts/01_run_tests.py`)
- **Stage 02**: Execute analysis scripts (`scripts/02_run_analysis.py`)
- **Stage 03**: Render PDFs from markdown (`scripts/03_render_pdf.py`)
- **Stage 04**: Validate outputs (`scripts/04_validate_output.py`)
- **Stage 05**: Copy final deliverables (`scripts/05_copy_outputs.py`)
- **Stage 06**: LLM scientific review (`scripts/06_llm_review.py`)
- **Stage 07**: Generate executive report (`scripts/07_generate_executive_report.py`)

**Usage:**

```bash
# Run pipeline (all 8 stages)
python3 scripts/execute_pipeline.py --core-only

# Or use unified interactive menu
./run.sh

# Run individual stages
python3 scripts/00_setup_environment.py  # Stage 00
python3 scripts/01_run_tests.py          # Stage 01
python3 scripts/02_run_analysis.py       # Stage 02
python3 scripts/03_render_pdf.py         # Stage 03
python3 scripts/04_validate_output.py    # Stage 04
python3 scripts/05_copy_outputs.py       # Stage 05
python3 scripts/06_llm_review.py         # Stage 06
python3 scripts/07_generate_executive_report.py  # Stage 07
```

---

**Build Version:** v2.0 (8-stage core pipeline)
**Status:** ✅ Documented for reference
