# Build Pipeline Rules

## Pipeline Overview

The build pipeline orchestrates the complete build process from source to output:

```
Start
  ↓
Clean Previous Outputs
  ↓
Validate Dependencies
  ↓
Run Tests (100% coverage required)
  ↓
Execute Scripts (thin orchestrators using src/)
  ↓
Generate PDFs from Markdown
  ↓
Validate All Output
  ↓
Complete - All artifacts ready
```

## Key Stages

### 1. Clean
```bash
./repo_utilities/clean_output.sh
```
- Remove `output/` directory
- Remove `latex/` directory if present
- Preserve source files

### 2. Dependency Validation
Check for required tools:
- `python3` - Python 3.10+
- `uv` - Package manager
- `pandoc` - Document converter
- `xelatex` - LaTeX compiler

### 3. Test Execution
```bash
python3 -m pytest tests/ \
    --cov=src \
    --cov-report=term-missing \
    --cov-fail-under=70
```

Requirements:
- 100% coverage for `src/`
- All tests must pass
- No mock methods
- Real data and integration tests

Failure → Stop pipeline

### 4. Script Execution
```bash
python3 scripts/example_figure.py
python3 scripts/generate_research_figures.py
python3 scripts/scientific_simulation.py
# ... all scripts in scripts/
```

Requirements:
- All scripts must complete successfully
- Must import and use `src/` functions
- Output goes to `output/`
- Clear logging of progress

Failure → Stop pipeline

### 5. PDF Generation

Sub-stages:
1. **Markdown Discovery** - Find all `*.md` files
2. **LaTeX Generation** - Convert each markdown to LaTeX
3. **PDF Compilation** - Compile each LaTeX to PDF (3-pass)
4. **Combined Assembly** - Create combined manuscript
5. **Validation** - Check all references resolved

### 6. Output Validation

Checks:
- All expected PDF files exist
- All figures referenced exist
- No unresolved references (`??`)
- No missing citations (`[?]`)
- All data files valid

## Orchestration Scripts

### render_pdf.sh - Main Pipeline
```bash
./repo_utilities/render_pdf.sh
```

Executes complete pipeline in order. Stops on first error.

Environment variables:
- `AUTHOR_NAME` - Author metadata
- `PROJECT_TITLE` - Paper title
- `LOG_LEVEL` - Logging verbosity

### generate_pdf_from_scratch.sh - Enhanced Pipeline
```bash
./generate_pdf_from_scratch.sh [OPTIONS]
```

Options:
- `--clean` - Clean first
- `--verbose` - Verbose output
- `--debug` - Debug logging
- `--no-color` - No colors
- `--skip-validation` - Skip final validation
- `--log-file FILE` - Write log file

### clean_output.sh - Safe Cleanup
```bash
./repo_utilities/clean_output.sh
```

Removes only generated files:
- `output/` directory
- `latex/` directory (if present)

Preserves:
- `manuscript/` - Source documents
- `src/` - Source code
- `scripts/` - Scripts
- `tests/` - Tests

## Error Handling

### Stop on Error
```bash
set -euo pipefail
```

Pipeline stops immediately on:
- Command failure (exit code != 0)
- Undefined variable
- Pipe failure

### Error Recovery
Logging provides:
- Which step failed
- What the error was
- How to troubleshoot
- Where to find logs

### Restart Point
Clean and restart from beginning:
```bash
./repo_utilities/clean_output.sh
./repo_utilities/render_pdf.sh
```

## Pipeline Output

### File Structure Created
```
output/
├── pdf/                    # No AGENTS.md - disposable
│   ├── 01_abstract.pdf
│   ├── ...
│   └── project_combined.pdf
├── tex/                    # No AGENTS.md - disposable
│   ├── 01_abstract.tex
│   └── ...
├── figures/                # No AGENTS.md - disposable
│   ├── *.png
│   └── figure_registry.json
├── data/                   # No AGENTS.md - disposable
│   ├── *.csv
│   └── *.npz
└── reports/                # No AGENTS.md - disposable
    ├── analysis_report.md
    └── simulation_report.md
```

**Important Note**: Output directory and subdirectories contain NO AGENTS.md or README.md files because they are regenerated on every build. Documentation for output types lives in source directories (src/, scripts/, docs/).

### Logging Output
```
[INFO] Step 1: Running tests...
[INFO] ✅ All tests passed (807 passed in 36.51s)
[INFO] Step 2: Executing scripts...
[INFO] Running: generate_scientific_figures.py
[INFO] ✅ Generated 4 figures
[INFO] Step 3: Building PDFs...
[INFO] Building: 01_abstract.md -> 01_abstract.pdf
[INFO] ✅ Built combined PDF
```

## Performance Optimization

### Parallel Execution (Future)
Currently sequential, but designed for parallelization:
- Script execution could be parallel
- PDF compilation could be parallel
- Tests could run in parallel

### Caching Considerations
- Tests re-run always (detect regressions)
- Scripts re-run always (generate fresh output)
- PDFs regenerated on content change
- No caching of generated artifacts

## Continuous Integration

### CI/CD Integration
```bash
# In CI/CD pipeline
set -e
export LOG_LEVEL=1

./repo_utilities/clean_output.sh
./repo_utilities/render_pdf.sh

# Archive outputs
tar -czf artifacts.tar.gz output/
```

### Environment Setup
```bash
# Install dependencies
uv sync

# Check versions
python3 --version    # Should be 3.10+
pandoc --version     # Should be 3.1.9+
xelatex --version    # Required
```

## Troubleshooting

### Tests Fail
```bash
# Check coverage
pytest tests/ --cov=src --cov-report=term-missing

# Run specific test
pytest tests/test_module.py -v

# Check for mocks
grep -r "MagicMock\|Mock\|patch" tests/
```

### Scripts Fail
```bash
# Run script directly
python3 scripts/example_figure.py

# Check imports
python3 -c "from scripts.example_figure import *"

# Verify src/ functions available
python3 -c "from src.example import *"
```

### PDF Generation Fails
```bash
# Check LaTeX compilation log
cat output/pdf/*_compile.log | grep -i error

# Check markdown validity
python3 repo_utilities/validate_markdown.py

# Try single file
pandoc manuscript/01_abstract.md -o test.pdf
```

### Missing Outputs
```bash
# List what was created
ls -la output/

# Check sizes
du -h output/*/*

# Search for errors in logs
grep -i error output/pdf/*_compile.log
```

## Best Practices

### Before Building
1. Commit your changes
2. Run tests locally
3. Check for new scripts
4. Update documentation

### During Build
1. Monitor log output
2. Check timing (should be 1-2 minutes)
3. Note any warnings

### After Build
1. Validate output exists
2. Spot-check PDFs
3. Archive if needed
4. Commit documentation changes

## See Also

- [logging.md](logging.md) - Logging during builds
- [testing.md](testing.md) - Test requirements
- [thin_orchestrator.md](thin_orchestrator.md) - Script requirements
- [../repo_utilities/AGENTS.md](../repo_utilities/AGENTS.md) - Utilities documentation

