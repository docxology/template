# Documentation Accuracy Review

**Generated**: 2025-01-XX  
**Purpose**: Verification of command examples, file paths, and code examples against actual implementation

## Command Accuracy Issues Found

### Issue 1: Incorrect Config File Path

**Location:** `AGENTS.md` lines 272-273

**Current (Incorrect):**
```bash
# Edit manuscript/config.yaml with your information
vim manuscript/config.yaml
```

**Should Be:**
```bash
# Edit project/manuscript/config.yaml with your information
vim project/manuscript/config.yaml
```

**Status:** ❌ Needs Fix

**Files Affected:**
- `AGENTS.md` (2 occurrences)

**Verification:**
- ✅ Actual file exists at: `project/manuscript/config.yaml`
- ❌ Documentation references: `project/manuscript/config.yaml`

### Issue 2: Pipeline Stage Numbering Inconsistency

**Location:** `RUN_GUIDE.md` line 77

**Current:**
- States "9-stage build pipeline"
- Lists stages 0-9 (10 stages total)

**Actual Implementation:**
- `run.sh` has STAGE_NAMES array with 9 entries (indices 0-8)
- Stage 0 is "Clean Output Directories" (separate, pre-pipeline)
- Stages 1-8 are main pipeline stages (from STAGE_NAMES)
- But RUN_GUIDE.md lists stages 0-9

**Analysis:**
- `run.sh` STAGE_NAMES: 9 stages (Setup Environment through LLM Translations)
- Stage 0 (Clean) is separate, not in STAGE_NAMES
- Total: 1 clean stage + 9 pipeline stages = 10 operations
- But displayed as "9 stages" because Clean is pre-pipeline

**Recommendation:**
- Clarify: "9-stage pipeline (stages 1-9) plus pre-pipeline cleanup (stage 0)"
- Or: "10 operations total: 1 cleanup + 9 pipeline stages"
- Update RUN_GUIDE.md table to match actual implementation

**Status:** ⚠️ Needs Clarification

## File Path Verification

### Config File Paths

**Correct Path:** `project/manuscript/config.yaml`

**Files to Check:**
- [ ] `AGENTS.md` - Found incorrect reference
- [ ] All other files referencing config.yaml

### Script Paths

**Correct Format:** `scripts/0X_script_name.py`

**Verified Scripts:**
- ✅ `scripts/00_setup_environment.py` - EXISTS
- ✅ `scripts/01_run_tests.py` - EXISTS
- ✅ `scripts/02_run_analysis.py` - EXISTS
- ✅ `scripts/03_render_pdf.py` - EXISTS
- ✅ `scripts/04_validate_output.py` - EXISTS
- ✅ `scripts/05_copy_outputs.py` - EXISTS
- ✅ `scripts/06_llm_review.py` - EXISTS
- ✅ `scripts/07_literature_search.py` - EXISTS
- ✅ `scripts/run_all.py` - EXISTS

**Status:** ✅ All script paths verified

### Output Directory Paths

**Correct Paths:**
- `project/output/` - Project-specific outputs
- `output/` - Top-level outputs (copied from project/output/)

**Need to Verify:**
- [ ] All references use correct paths
- [ ] Distinction between project/output/ and output/ is clear

## Command Syntax Verification

### Python Command Usage

**Standard:** `python3` (not `python`)

**Files Checked:** 35 files with command examples

**Status:** ✅ All use `python3` correctly

### CLI Usage

**Standard Format:** `python3 -m infrastructure.module.cli command args`

**Examples:**
- ✅ `python3 -m infrastructure.validation.cli pdf <path>`
- ✅ `python3 -m infrastructure.validation.cli markdown <path>`

**Status:** ✅ CLI usage correct

## Pipeline Description Accuracy

### Stage Descriptions

**Need to Verify:**
- [ ] Stage names match actual implementation
- [ ] Stage purposes match actual functionality
- [ ] Stage numbering is consistent
- [ ] Entry point distinctions are clear

### Coverage Requirements

**Standard Values:**
- Infrastructure: 49% minimum (currently 55.89%)
- Project: 70% minimum (currently 99.88%)

**Status:** ✅ Need to verify all files use consistent values

### Test Counts

**Standard Values:**
- Total: 1934 tests
- Infrastructure: 1884 tests
- Project: 351 tests

**Status:** ✅ Need to verify all files use consistent counts

## Code Example Accuracy

### Import Statements

**Need to Verify:**
- [ ] All import examples match actual module structure
- [ ] Function signatures match actual code
- [ ] Class names match actual implementation

### API Usage

**Need to Verify:**
- [ ] Function calls use correct parameters
- [ ] Return values match actual behavior
- [ ] Error handling examples are accurate

## Accuracy Checklist

### Commands
- [x] All use `python3` not `python`
- [x] All script paths verified
- [ ] All config file paths correct
- [x] All CLI usage correct

### Paths
- [ ] Config file paths: `project/manuscript/config.yaml`
- [x] Script paths: `scripts/0X_*.py`
- [ ] Output paths: `project/output/` vs `output/`

### Pipeline
- [ ] Stage numbering consistent
- [ ] Stage descriptions accurate
- [ ] Entry point distinctions clear

### Values
- [ ] Coverage percentages consistent
- [ ] Test counts consistent
- [ ] Build times consistent

## Next Steps

1. Fix config file path in AGENTS.md
2. Clarify pipeline stage numbering in RUN_GUIDE.md
3. Verify all file path references
4. Verify all code examples against actual implementation

