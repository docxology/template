# Documentation Consistency Review

**Generated**: 2025-01-XX  
**Purpose**: Systematic review of consistency across all documentation files

## Review Categories

### 1. Terminology Consistency

#### Layer Terminology

**Standard Terms:**
- **Layer 1** = Infrastructure (generic, reusable)
- **Layer 2** = Project (project-specific, customizable)
- **Infrastructure** = Generic tools (Layer 1)
- **Project** = Research-specific code (Layer 2)

**Files Reviewed:** 12 files found with layer terminology

**Issues Found:**
- Need to verify consistent usage across all files
- Check for mixing "generic layer" vs "Layer 1"
- Check for mixing "project layer" vs "Layer 2"

#### Pipeline Terminology

**Standard Terms:**
- **Stage 0-8** = Extended pipeline (run.sh, displayed as [1/9] to [8/9])
- **Stage 00-05** = Core pipeline (run_all.py, zero-padded)
- **./run.sh** = Interactive menu orchestrator
- **run_all.py** = Python orchestrator

**Files Reviewed:** 20 files found with stage references

**Issues Found:**
- RUN_GUIDE.md says "9-stage build pipeline" but lists stages 0-9 (10 stages)
- Need to verify stage numbering consistency
- Need to clarify which entry point is being discussed

### 2. Coverage Requirements Consistency

**Standard Values:**
- **Infrastructure**: 49% minimum (currently 55.89%)
- **Project**: 70% minimum (currently 99.88%)

**Files Reviewed:** 42 files found with coverage references

**Issues Found:**
- Need to verify all files use consistent percentages
- Check for outdated coverage claims
- Verify current vs minimum distinction

### 3. Test Count Consistency

**Standard Values:**
- **Total**: 1934 tests
- **Infrastructure**: 1884 tests
- **Project**: 351 tests

**Files Reviewed:** 10 files found with test count references

**Issues Found:**
- Need to verify all files use consistent counts
- Check for outdated test counts

### 4. Command Syntax Consistency

**Standard Commands:**
- `python3 scripts/00_setup_environment.py` (not `python`)
- `./run.sh --pipeline` (not `bash run.sh`)
- `python3 -m infrastructure.validation.cli pdf <path>`

**Files Reviewed:** 35 files found with command examples

**Issues Found:**
- Need to verify all use `python3` not `python`
- Check for outdated script references
- Verify CLI usage is correct

### 5. Outdated Script References

**Known Deprecated:**
- `repo_utilities/validate_pdf_output.py` → Should use `scripts/04_validate_output.py`
- `./repo_utilities/rename_project.sh` → Should use `config.yaml`

**Files Reviewed:** 17 files found with potential outdated references

**Issues Found:**
- Need to verify all references updated
- Check for remaining deprecated script mentions

## Detailed Findings

### Pipeline Stage Numbering Issue

**Location:** `RUN_GUIDE.md` line 77

**Issue:** 
- States "9-stage build pipeline"
- Lists stages 0-9 (which is actually 10 stages)
- Should be "9 stages (0-8)" or "10 stages (0-9)"

**Actual Implementation:**
- `run.sh` defines 9 stages (0-8) in STAGE_NAMES array
- Stage 0 is "Clean Output Directories"
- Stages 1-8 are the main pipeline stages

**Recommendation:**
- Fix RUN_GUIDE.md to say "9 stages (0-8)" or clarify stage 0 is pre-pipeline cleanup
- Verify consistency with run.sh implementation

### Coverage Percentage Consistency

**Need to verify:**
- All files use "49% minimum" for infrastructure (not "49%+" or other variations)
- All files use "70% minimum" for project (not "70%+" or other variations)
- Current achievement values (55.89% and 99.88%) are consistent
- Distinction between "minimum" and "currently achieving" is clear

### Test Count Consistency

**Need to verify:**
- All files use "1934 tests" for total
- All files use "1884 infrastructure + 351 project" breakdown
- No outdated test counts remain

### Command Syntax Verification

**Need to verify:**
- All examples use `python3` not `python`
- All script paths use `scripts/0X_` format
- All CLI usage uses `python3 -m infrastructure.module.cli` format
- No references to deprecated scripts

## Consistency Checklist

### Terminology
- [ ] Layer terminology consistent (Layer 1/2 vs Infrastructure/Project)
- [ ] Pipeline terminology consistent (stages, entry points)
- [ ] Coverage terminology consistent (minimum vs current)
- [ ] Test terminology consistent (counts, breakdowns)

### Values
- [ ] Coverage percentages match (49% infra, 70% project)
- [ ] Current coverage values match (55.89% infra, 99.88% project)
- [x] Test counts match (1934 total, 1884 infra, 351 project)
- [ ] Build times match (84 seconds)
- [ ] PDF counts match (14 PDFs)

### Commands
- [ ] All use `python3` not `python`
- [ ] All script paths correct (`scripts/0X_`)
- [ ] All CLI usage correct (`python3 -m infrastructure.module.cli`)
- [ ] No deprecated script references

### Structure
- [ ] Pipeline stage numbering consistent
- [ ] Entry point descriptions consistent
- [ ] File path references consistent
- [ ] Configuration method references consistent

## Next Steps

1. Complete systematic review of all identified files
2. Document specific inconsistencies found
3. Create prioritized fix list
4. Verify fixes against actual implementation

