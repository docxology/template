# 🔧 Build System Historical Fixes

> **Historical record** of build system fixes and resolved issues

**Parent Document:** [Build System](build-system.md) | **Related:** [Troubleshooting](../troubleshooting/)

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

The build pipeline evolved from a 6-stage core path, to an 8-stage `--core-only` path, to the current declarative DAG in [`pipeline.yaml`](../../../infrastructure/core/pipeline/pipeline.yaml):

- **14 declared stages** in YAML: 8 default core, 2 LLM-tagged, 2 opt-in publishing, 2 opt-in bundle/archival
- **Default full run:** Clean Output Directories + 9 numbered stages (10 core+LLM path)
- **`--core-only`:** 8 stages (LLM-tagged stages excluded)

**Script mapping** (YAML stage index ≠ `scripts/NN_*.py` prefix — see [`scripts/AGENTS.md`](../../../scripts/AGENTS.md) stage table):

| Stage | Script | Notes |
| ----- | ------ | ----- |
| 0 | built-in clean | pre-step |
| 1 | `00_setup_environment.py` | Environment setup |
| 2 | `01_run_tests.py --infra-only` | Infrastructure tests |
| 3 | `01_run_tests.py --project-only` | Project tests |
| 4 | `02_run_analysis.py` | Project analysis |
| 5 | `03_render_pdf.py` | PDF rendering |
| 6 | `04_validate_output.py` | Output validation |
| 7 | `06_llm_review.py --reviews-only` | LLM Scientific Review (optional) |
| 8 | `06_llm_review.py --translations-only` | LLM Translations (optional) |
| 9 | `05_copy_outputs.py` | Copy deliverables |
| — | `07_generate_executive_report.py` | Multi-project only (not a numbered DAG stage) |

**Usage:**

```bash
# Core pipeline (8 stages — no LLM)
uv run python scripts/execute_pipeline.py --project {name} --core-only

# Full pipeline (default 10-stage core+LLM path)
./run.sh --pipeline --project {name}
```

---

**Build Version:** v2.0 (declarative DAG in `pipeline.yaml`; 10-stage default core+LLM path)
**Status:** ✅ Documented for reference
