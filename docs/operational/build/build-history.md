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

- **16 declared stages** in YAML: 8 default core, 2 science/provenance, 2 LLM-tagged, 2 opt-in publishing, 2 opt-in bundle/archival
- **Default full run:** Clean Output Directories + 9 numbered stages (10 core+LLM path)
- **`--core-only`:** 8 stages (LLM-tagged stages excluded)

**Script mapping** (YAML stage index ≠ `scripts/NN_*.py` prefix — see [`scripts/AGENTS.md`](../../../scripts/AGENTS.md) stage table):

| Stage | Script | Notes |
| ----- | ------ | ----- |
| 0 | built-in clean | pre-step |
| 1 | `scripts/pipeline/stage_00_setup.py` | Environment setup |
| 2 | `scripts/pipeline/stage_01_test.py --infra-only` | Infrastructure tests |
| 3 | `scripts/pipeline/stage_01_test.py --project-only` | Project tests |
| 4 | `scripts/pipeline/stage_02_analysis.py` | Project analysis |
| 5 | `scripts/pipeline/stage_03_render.py` | PDF rendering |
| 6 | `scripts/pipeline/stage_04_validate.py` | Output validation |
| 7 | `scripts/pipeline/stage_06_llm_review.py --reviews-only` | LLM Scientific Review (optional) |
| 8 | `scripts/pipeline/stage_06_llm_review.py --translations-only` | LLM Translations (optional) |
| 9 | `scripts/pipeline/stage_05_copy.py` | Copy deliverables |
| — | `scripts/pipeline/stage_07_executive_report.py` | Multi-project only (not a numbered DAG stage) |

**Usage:**

```bash
# Core pipeline (8 stages — no LLM)
uv run python scripts/runner/execute_pipeline.py --project {name} --core-only

# Full pipeline (default 10-stage core+LLM path)
./run.sh --pipeline --project {name}
```

---

**Build Version:** v2.0 (declarative DAG in `pipeline.yaml`; 10-stage default core+LLM path)
**Status:** ✅ Documented for reference
