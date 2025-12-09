# Comprehensive Troubleshooting Guide

> **Systematic approach** to resolving issues and errors

**Quick Reference:** [FAQ](FAQ.md) | [Common Workflows](COMMON_WORKFLOWS.md) | [Build System](BUILD_SYSTEM.md) | [Configuration](CONFIGURATION.md)

**Specialized Guides:**
- [LLM Review Troubleshooting](LLM_REVIEW_TROUBLESHOOTING.md) - LLM-specific issues
- [Checkpoint and Resume](CHECKPOINT_RESUME.md) - Checkpoint system troubleshooting
- [Performance Optimization](PERFORMANCE_OPTIMIZATION.md) - Performance issues and optimization

This guide provides a systematic approach to troubleshooting common issues in the Research Project Template. Follow these steps to diagnose and resolve problems effectively.

## Systematic Troubleshooting Approach

### Step 1: Gather Information

**Before troubleshooting, collect:**

1. **Error messages** - Full error output
2. **Environment** - Python version, OS, dependencies
3. **Recent changes** - What changed before the issue
4. **Logs** - Build logs, test output, validation results

**Diagnostic commands:**
```bash
# System information
python --version
uv --version
pandoc --version
xelatex --version

# Environment
env | grep -E "AUTHOR|PROJECT|DOI"

# Dependency status
uv tree
uv pip list
```

### Step 2: Reproduce the Issue

**Ensure you can reproduce:**

1. **Clean state** - Start from clean output directory
2. **Isolate** - Run individual components
3. **Document** - Record exact steps to reproduce
4. **Verify** - Confirm issue is consistent

### Step 3: Check Common Causes

**Most issues are caused by:**

1. **Missing dependencies** - System or Python packages
2. **Configuration errors** - Environment variables, paths
3. **Version mismatches** - Python, packages, tools
4. **File permissions** - Read/write access
5. **Path issues** - Incorrect file paths

### Step 4: Apply Fixes

**Follow these principles:**

1. **Start simple** - Try easiest fixes first
2. **One change at a time** - Isolate what fixes it
3. **Test after each fix** - Verify resolution
4. **Document solution** - Note what worked

## Environment Issues and Solutions

This section documents common environment-related issues and their solutions based on real troubleshooting scenarios.

### Missing `patch` Import in Tests

**Symptom:**
```
NameError: name 'patch' is not defined
tests/infrastructure/publishing/test_publishing.py::TestEdgeCases::test_extract_metadata_with_invalid_path FAILED
```

**Cause:**
Test files using `unittest.mock.patch` without importing it.

**Solution:**
Add the import statement at the top of the test file:
```python
from unittest.mock import patch
```

**Prevention:**
- Always import `patch` explicitly when using mocks in tests
- Check imports when copying test code between files
- Lint test files to catch missing imports early

### Optional `python-dotenv` Dependency

**Symptom:**
```
ModuleNotFoundError: No module named 'dotenv'
```

**Cause:**
The `infrastructure.core.credentials` module imports `python-dotenv` but it's not installed.

**Impact:**
System can work without `python-dotenv` - it's an optional dependency for loading `.env` files.

**Solution:**
The system now uses conditional import with graceful fallback:
```python
try:
    from dotenv import load_dotenv
    _DOTENV_AVAILABLE = True
except ImportError:
    _DOTENV_AVAILABLE = False
```

**Installation (Optional):**
```bash
# Install if you want .env file support
pip install python-dotenv
# or
uv add python-dotenv
```

**What Works Without It:**
- Environment variables from shell still work
- YAML config files still work
- All core functionality remains operational

### Missing `infrastructure.build` Modules

**Symptom:**
```
ModuleNotFoundError: No module named 'infrastructure.build'
project/scripts/manuscript_preflight.py - failed
project/scripts/quality_report.py - failed
```

**Cause:**
Scripts trying to import quality checker and reproducibility modules that don't exist in the codebase.

**Solution:**
Scripts now use graceful fallback with stub functions:
```python
try:
    from infrastructure.build.quality_checker import analyze_document_quality
    _BUILD_MODULES_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    _BUILD_MODULES_AVAILABLE = False
    def analyze_document_quality(path):
        return {"status": "skipped", "reason": "infrastructure.build not available"}
```

**Impact:**
- Scripts run successfully
- Optional features gracefully skipped
- Core validation still works
- Clear logging indicates what was skipped

**Files Affected:**
- `project/scripts/manuscript_preflight.py`
- `project/scripts/quality_report.py`

### Matplotlib Configuration Issues

**Symptom:**
```
Exit code 134 (SIGABRT)
/Users/mini/.matplotlib is not a writable directory
```

**Cause:**
Matplotlib trying to write to non-writable directories during figure generation in subprocess execution.

**Solution:**
Analysis orchestrator now sets matplotlib environment variables:
```python
env = os.environ.copy()
env.setdefault('MPLBACKEND', 'Agg')
env.setdefault('MPLCONFIGDIR', '/tmp/matplotlib')

subprocess.run(cmd, env=env)
```

**Manual Override:**
```bash
# Set for current shell session
export MPLBACKEND=Agg
export MPLCONFIGDIR=/tmp/matplotlib

# Run analysis scripts
python3 scripts/02_run_analysis.py
```

**Verification:**
```bash
# Should complete without errors
python3 scripts/02_run_analysis.py

# Check generated figures
ls -la project/output/figures/
```

**Why This Happens:**
- Default matplotlib tries to use GUI backends
- Tries to write config to home directory
- Fails when directory not writable or in headless environments

**Prevention:**
- Always set `MPLBACKEND=Agg` for headless operation
- Use writable directory for `MPLCONFIGDIR`
- Orchestrators handle this automatically now

### LaTeX Installation on macOS

**Symptom:**
```
xelatex: command not found
pdflatex: command not found
```

**Diagnosis:**
```bash
# Check if LaTeX is installed
which xelatex
which pdflatex

# Check PATH
echo $PATH | grep -i tex
```

**Solution 1: Install BasicTeX (Recommended - ~100MB):**
```bash
# Install via Homebrew
brew install --cask basictex

# Add to PATH
export PATH="/Library/TeX/texbin:$PATH"
echo 'export PATH="/Library/TeX/texbin:$PATH"' >> ~/.zshrc

# Update TeX Live Manager
sudo tlmgr update --self

# Install required packages
sudo tlmgr install \
    collection-fontsrecommended \
    collection-latexrecommended \
    xetex \
    ucs \
    fancyhdr \
    babel-english \
    hyperref \
    url \
    graphics \
    oberdiek \
    tools \
    amsmath
```

**Solution 2: Install MacTeX (Full - ~4GB):**
```bash
# Install full distribution
brew install --cask mactex

# Add to PATH (same as above)
export PATH="/Library/TeX/texbin:$PATH"
echo 'export PATH="/Library/TeX/texbin:$PATH"' >> ~/.zshrc
```

**Verification:**
```bash
# Reload shell
source ~/.zshrc

# Verify installation
xelatex --version
pdflatex --version

# Test PDF rendering
python3 scripts/03_render_pdf.py
```

**Common Issues:**
- **PATH not updated**: Restart terminal or run `source ~/.zshrc`
- **Packages missing**: Run `sudo tlmgr install <package-name>`
- **Permission errors**: Use `sudo` with `tlmgr` commands

### Test Failure Tolerance

**Feature:**
Configure maximum allowed test failures before halting pipeline.

**Environment Variable:**
```bash
export MAX_TEST_FAILURES=5  # Allow up to 5 failures
```

**Default:** `0` (strict - any failure halts pipeline)

**Usage:**
```bash
# Allow limited failures during development
export MAX_TEST_FAILURES=3
python3 scripts/01_run_tests.py

# Or with full pipeline
export MAX_TEST_FAILURES=5
python3 scripts/run_all.py
```

**Behavior:**
- **Below threshold**: Pipeline continues, warning logged
- **At/above threshold**: Pipeline halts, error logged
- **All pass**: Pipeline continues normally

**When to Use:**
- **Development**: Work on features while some tests are broken
- **CI/CD**: Allow known flaky tests without blocking builds
- **Migration**: Gradual fixing of test suites

**When NOT to Use:**
- **Production**: Should always be 0 (strict)
- **Releases**: All tests must pass
- **Code review**: Tests should pass before PR merge

**Example Output:**
```bash
# With MAX_TEST_FAILURES=3 and 2 failures
Infrastructure tests: 2 failures (max allowed: 3)
✓ Infrastructure tests passed (within tolerance)

# With MAX_TEST_FAILURES=3 and 5 failures
Infrastructure tests: 5 failures (max allowed: 3)
✗ Infrastructure tests failed (exceeded threshold)
```

### Environment Variables Reference

Complete list of environment variables affecting system behavior:

| Variable | Default | Purpose | Example |
|----------|---------|---------|---------|
| `MAX_TEST_FAILURES` | `0` | Maximum allowed test failures | `export MAX_TEST_FAILURES=5` |
| `MPLBACKEND` | (system) | Matplotlib backend | `export MPLBACKEND=Agg` |
| `MPLCONFIGDIR` | `~/.matplotlib` | Matplotlib config directory | `export MPLCONFIGDIR=/tmp/matplotlib` |
| `LOG_LEVEL` | `1` | Logging verbosity (0=DEBUG, 1=INFO, 2=WARN, 3=ERROR) | `export LOG_LEVEL=0` |
| `AUTHOR_NAME` | `"Project Author"` | Primary author name | `export AUTHOR_NAME="Dr. Jane Smith"` |
| `AUTHOR_ORCID` | `"0000-0000-0000-0000"` | Author ORCID identifier | `export AUTHOR_ORCID="0000-0001-2345-6789"` |
| `AUTHOR_EMAIL` | `"author@example.com"` | Author contact email | `export AUTHOR_EMAIL="jane@university.edu"` |
| `PROJECT_TITLE` | `"Project Title"` | Project/research title | `export PROJECT_TITLE="Novel Framework"` |
| `DOI` | `""` | Digital Object Identifier | `export DOI="10.5281/zenodo.12345"` |

**Setting Multiple Variables:**
```bash
# Create .env file (requires python-dotenv)
cat > .env << 'EOF'
MAX_TEST_FAILURES=3
MPLBACKEND=Agg
LOG_LEVEL=0
AUTHOR_NAME=Dr. Jane Smith
EOF

# Or set in shell
export MAX_TEST_FAILURES=3 MPLBACKEND=Agg LOG_LEVEL=0
```

### Quick Diagnostics

**Check Environment:**
```bash
# Show all template-related variables
env | grep -E "MAX_TEST|MPL|LOG_LEVEL|AUTHOR|PROJECT|DOI"

# Test matplotlib configuration
python3 -c "import matplotlib; print(matplotlib.get_backend())"

# Verify LaTeX installation
which xelatex && echo "LaTeX OK" || echo "LaTeX missing"

# Check Python imports
python3 -c "from infrastructure.core import credentials; print('Imports OK')"
```

**Full Environment Report:**
```bash
#!/bin/bash
echo "=== Test Configuration ==="
echo "MAX_TEST_FAILURES: ${MAX_TEST_FAILURES:-0 (strict)}"

echo -e "\n=== Matplotlib Configuration ==="
echo "MPLBACKEND: ${MPLBACKEND:-system default}"
echo "MPLCONFIGDIR: ${MPLCONFIGDIR:-~/.matplotlib}"

echo -e "\n=== LaTeX Installation ==="
which xelatex >/dev/null && echo "✓ xelatex found" || echo "✗ xelatex missing"
which pdflatex >/dev/null && echo "✓ pdflatex found" || echo "✗ pdflatex missing"

echo -e "\n=== Optional Dependencies ==="
python3 -c "import dotenv" 2>/dev/null && echo "✓ python-dotenv installed" || echo "○ python-dotenv not installed (optional)"

echo -e "\n=== Project Metadata ==="
echo "AUTHOR_NAME: ${AUTHOR_NAME:-not set}"
echo "PROJECT_TITLE: ${PROJECT_TITLE:-not set}"
```

## Progress Display Issues

### Progress Bar Not Updating

**Symptoms:**
- Progress bar appears but doesn't move
- ETA shows incorrect values
- Progress stuck at 0%

**Diagnosis:**
```bash
# Check if running in TTY
test -t 1 && echo "TTY" || echo "Not TTY"

# Check for output redirection
# Progress bars work best in interactive terminals
```

**Solutions:**
1. Progress bars require TTY - don't redirect stdout/stderr
2. Use `log_progress()` instead of progress bars in non-TTY environments
3. Check update interval - may be throttled for performance
4. Verify progress.update() is being called

### ETA Estimates Inaccurate

**Symptoms:**
- ETA shows unrealistic times
- ETA doesn't update smoothly
- ETA jumps around

**Solutions:**
1. Enable EMA for smoother estimates: `use_ema=True`
2. Provide item durations for better accuracy: `item_durations=[...]`
3. Wait for a few items before trusting ETA
4. Use confidence intervals: `get_eta_with_confidence()`

### LLM Progress Not Showing

**Symptoms:**
- No token generation progress during LLM operations
- Can't see throughput metrics

**Solutions:**
1. Ensure using `LLMProgressTracker` for token-based operations
2. Check that streaming is enabled in LLM client
3. Verify progress tracker is updated with each chunk
4. Check terminal supports carriage return updates

## Common Error Messages

### Build System Errors

#### Error: "No such file or directory"

**Symptoms:**
```
cat: /path/to/file: No such file or directory
```

**Diagnosis:**
```bash
# Check if file exists
ls -la /path/to/file

# Check file permissions
stat /path/to/file

# Verify path is correct
pwd
```

**Solutions:**
1. Verify file path is correct
2. Check file exists in expected location
3. Ensure file permissions allow reading
4. Verify working directory is correct

#### Error: "Command not found"

**Symptoms:**
```
pandoc: command not found
xelatex: command not found
```

**Diagnosis:**
```bash
# Check if command exists
which pandoc
which xelatex

# Check PATH
echo $PATH
```

**Solutions:**
1. Install missing tool
2. Add to PATH
3. Use full path to command
4. Verify installation

#### Error: "Permission denied"

**Symptoms:**
```
Permission denied: /path/to/file
```

**Diagnosis:**
```bash
# Check permissions
ls -la /path/to/file

# Check directory permissions
ls -la /path/to/
```

**Solutions:**
1. Fix file permissions: `chmod +r file`
2. Fix directory permissions: `chmod +x directory`
3. Check ownership: `chown user:group file`
4. Run with appropriate permissions

### Test Failures

#### Error: "ImportError: No module named"

**Symptoms:**
```
ImportError: No module named 'module_name'
```

**Diagnosis:**
```bash
# Check if module is installed
uv pip list | grep module_name

# Check Python path
python -c "import sys; print(sys.path)"

# Verify module location
find . -name "module_name.py"
```

**Solutions:**
1. Install missing module: `uv add module_name`
2. Add to Python path: `export PYTHONPATH="${PYTHONPATH}:path/to"`
3. Verify module location
4. Check import statement

#### Error: "AssertionError"

**Symptoms:**
```
AssertionError: Expected value but got other
```

**Diagnosis:**
```bash
# Run test with verbose output
uv run pytest tests/test_file.py -vv

# Run specific test
uv run pytest tests/test_file.py::test_function -v

# Check test data
cat tests/test_data.json
```

**Solutions:**
1. Review test expectations
2. Check test data
3. Verify function output
4. Update test if expectations changed

#### Error: "Coverage below threshold"

**Symptoms:**
```
Coverage: 65% (below 90% requirement)
```

**Diagnosis:**
```bash
# Generate coverage report
uv run pytest tests/ --cov=src --cov-report=term-missing

# View HTML report
open htmlcov/index.html
```

**Solutions:**
1. Add tests for uncovered code
2. Review coverage report
3. Identify missing test cases
4. Write tests for uncovered paths

### PDF Generation Issues

#### Error: "Pandoc conversion failed"

**Symptoms:**
```
Error: Pandoc conversion failed
```

**Diagnosis:**
```bash
# Test pandoc directly
pandoc --version

# Try manual conversion
pandoc input.md -o output.pdf

# Check pandoc logs
pandoc input.md -o output.pdf --verbose
```

**Solutions:**
1. Verify Pandoc installation
2. Check markdown syntax
3. Review pandoc logs
4. Test with minimal example

#### Error: "LaTeX compilation failed"

**Symptoms:**
```
Error: LaTeX compilation failed
Undefined control sequence
```

**Diagnosis:**
```bash
# Check LaTeX installation
xelatex --version

# Try manual compilation
xelatex document.tex

# Review LaTeX logs
cat document.log | grep Error
```

**Solutions:**
1. Install missing LaTeX packages
2. Fix LaTeX syntax errors
3. Check preamble configuration
4. Review LaTeX logs

#### Error: "Figure not found" or Figures Not Appearing

**Symptoms:**
```
Warning: Figure not found or figures not visible in PDF
⚠️  Figure file not found: output/figures/figure.png
Figures appearing as blank spaces in PDF
```

**Root Cause Analysis**:

The rendering system can fail to display figures for several reasons:
1. **Missing graphicx package** - The LaTeX `\usepackage{graphicx}` may not be loaded
2. **Figure files not found** - Files don't exist in `project/output/figures/`
3. **Path resolution issues** - Incorrect relative paths in LaTeX
4. **File access problems** - Permissions or encoding issues

**Diagnosis:**
```bash
# 1. Verify graphicx package is included
grep "usepackage{graphicx}" project/output/pdf/_combined_manuscript.tex

# 2. Check if figures exist
ls -la project/output/figures/ | grep -E "\.png|\.pdf|\.jpg"

# 3. Check figure references in markdown
grep -r "includegraphics" project/manuscript/ | head -5

# 4. Verify figure paths in LaTeX source
grep "includegraphics" project/output/pdf/_combined_manuscript.tex | head -5

# 5. Check LaTeX compilation log for graphics errors
tail -150 project/output/pdf/_combined_manuscript.log | grep -A2 -B2 "graphics\|Error\|Warning" | head -30

# 6. Check for specific graphics errors
grep -i "undefined.*includegraphics\|file.*not found" project/output/pdf/_combined_manuscript.log
```

**Solutions:**

1. **Ensure graphicx package is loaded** (system adds it automatically):
   ```bash
   # Check if it's in the generated LaTeX
   grep "\\\\usepackage{graphicx}" project/output/pdf/_combined_manuscript.tex
   
   # If not found, it should be added automatically. Check build output.
   # If missing, add to manuscript/preamble.md:
   echo "\usepackage{graphicx}" >> project/manuscript/preamble.md
   ```

2. **Generate missing figures**:
   ```bash
   python3 scripts/02_run_analysis.py
   ls -la project/output/figures/
   ```

3. **Verify figure filenames** (case-sensitive on Unix):
   ```bash
   # List all figures
   ls project/output/figures/
   
   # Search for similar filenames
   ls project/output/figures/ | grep -i "your_figure_name"
   ```

4. **Check file format** (PNG/PDF/JPG only):
   ```bash
   file project/output/figures/your_figure.png
   # Should output something like: PNG image data, 800 x 600, 8-bit RGB
   ```

5. **Fix paths in markdown**:
   ```bash
   # Correct format
   grep "includegraphics\[width" project/manuscript/*.md | head -2
   # Should show: \includegraphics[width=0.8\textwidth]{../output/figures/name.png}
   
   # Update if paths are wrong
   sed -i 's|{figures/|{../output/figures/|g' project/manuscript/*.md
   ```

6. **Run full rebuild**:
   ```bash
   python3 scripts/run_all.py --clean
   ```

7. **For Unicode filenames**, ensure proper encoding:
   ```bash
   file project/output/figures/*
   # Check encoding of filenames with special characters
   ls -la project/output/figures/ | cat -v
   ```

**Advanced Debugging**:
```bash
# Check if LaTeX can find figures
cd project/output/pdf/
xelatex --interaction=nonstopmode _combined_manuscript.tex 2>&1 | grep -i "graphics\|error"

# Extract log file for detailed analysis
pdfinfo project_combined.pdf
```

**Expected Output** (after fix):
```
✓ Fixed 14 figure path(s)
  ../output/figures/convergence_plot.png → ../figures/convergence_plot.png
  ../output/figures/scalability_analysis.png → ../figures/scalability_analysis.png
Found: 14/14 figures
```

### Title Page Issues

#### Title Page Not Appearing

**Symptoms:**
```
PDF renders but title page (title, author, date) is missing
First page shows Table of Contents instead of title
```

**Diagnosis:**
```bash
# Check config.yaml exists and is valid
cat project/manuscript/config.yaml

# Verify YAML syntax
python3 -c "import yaml; yaml.safe_load(open('project/manuscript/config.yaml'))"

# Extract first page to check content
pdftotext project/output/pdf/project_combined.pdf - | head -20
```

**Solutions:**
1. Create/verify `project/manuscript/config.yaml` with proper format
2. Ensure YAML syntax is correct (no tabs, proper indentation)
3. Include required fields: `paper.title` and `authors[].name`
4. Regenerate PDF: `python3 scripts/03_render_pdf.py`
5. Check that `\maketitle` appears after `\begin{document}` in LaTeX source

**Config.yaml Template:**
```yaml
paper:
  title: "Your Paper Title"
  subtitle: ""  # Optional
  date: ""  # Auto-generated if empty

authors:
  - name: "Dr. Your Name"
    email: "your@email.edu"
    affiliation: "Your Institution"
    corresponding: true
```

#### Missing Author Information on Title Page

**Symptoms:**
```
Title appears but authors are missing or incorrect
"and" separator appearing instead of author names
```

**Diagnosis:**
```bash
# Check authors section in config.yaml
grep -A 5 "authors:" project/manuscript/config.yaml

# Verify YAML format is correct
python3 << 'EOF'
import yaml
with open("project/manuscript/config.yaml") as f:
    config = yaml.safe_load(f)
    print("Authors:", [a["name"] for a in config.get("authors", [])])
EOF
```

**Solutions:**
1. Ensure authors section has proper YAML list format
2. Each author must have at least a `name` field
3. Use proper YAML indentation (spaces, not tabs)
4. Separate multiple authors with hyphens on new lines
5. Test YAML validity with `python3 -c "import yaml; yaml.safe_load(open(...))"

### Combined PDF Issues

#### "Mixed Figure Issues: Missing Title or Figures

**Symptoms:**
```
PDF generated but with 12 pages (incomplete)
Unresolved references (??), missing figures or title
```

**Diagnosis:**
```bash
# Check PDF page count and size
pdfinfo project/output/pdf/project_combined.pdf

# Check for LaTeX errors in log
grep "Error\|error" project/output/pdf/_combined_manuscript.log | head -10

# List all figure references
grep -c "includegraphics" project/output/pdf/_combined_manuscript.tex
```

**Solutions:**
1. Verify all 14 manuscript sections exist: `ls project/manuscript/*.md | grep "^[0-9]"`
2. Check for LaTeX syntax errors in markdown files
3. Ensure figures are generated and exist: `ls project/output/figures/ | wc -l`
4. Regenerate from scratch:
   ```bash
   rm -f project/output/pdf/project_combined.pdf
   python3 scripts/03_render_pdf.py
   ```
5. Check for special characters or formatting issues in markdown

### Dependency Problems

#### Error: "Dependency resolution failed"

**Symptoms:**
```
Error: Could not find a version that satisfies the requirement
```

**Diagnosis:**
```bash
# Check dependency versions
uv tree

# Check Python version
python --version

# Review pyproject.toml
cat pyproject.toml | grep -A 10 dependencies
```

**Solutions:**
1. Update Python version
2. Relax version constraints
3. Update dependency versions
4. Check compatibility

#### Error: "Lock file conflicts"

**Symptoms:**
```
Merge conflict in uv.lock
```

**Diagnosis:**
```bash
# Check lock file status
git status uv.lock

# View conflicts
git diff uv.lock
```

**Solutions:**
1. Regenerate lock file: `uv lock`
2. Resolve conflicts manually
3. Accept one version: `git checkout --theirs uv.lock`
4. Re-sync: `uv sync`

## Build System Issues

### Build Fails Immediately

**Checklist:**
- [ ] All dependencies installed (`uv sync`)
- [ ] System tools available (pandoc, xelatex)
- [ ] Output directory writable
- [ ] No permission errors
- [ ] Environment variables set

**Diagnostic:**
```bash
# Run complete pipeline with all stages
python3 scripts/run_all.py

# Or use unified interactive menu
./run.sh

# Check each stage individually
uv run pytest tests/ --cov=src
# Run complete pipeline (includes script execution)
python3 scripts/run_all.py
```

### Build Takes Too Long

**Optimization:**
1. **Enable caching** - Use pytest cache
2. **Parallel execution** - Run tests in parallel
3. **Incremental builds** - Only rebuild changed files
4. **Skip validation** - Skip non-critical checks

**Commands:**
```bash
# Parallel tests
uv run pytest tests/ -n auto

# Cached builds
uv run pytest tests/ --cache-clear
```

### Build Succeeds but PDFs are Wrong

**Check:**
1. **PDF validation** - Run validation script
2. **Content check** - Verify PDF content
3. **Cross-references** - Check references resolved
4. **Figures** - Verify figures included

**Diagnostic:**
```bash
# Validate PDFs
python3 scripts/04_validate_output.py

# Or use CLI directly
python3 -m infrastructure.validation.cli pdf output/project_combined.pdf

# Check PDF content (top-level output after stage 5)
pdftotext output/project_combined.pdf - | head -50
```

## Test Failures

### All Tests Fail

**Check:**
1. **Environment** - Python version, dependencies
2. **Test data** - Test files exist and readable
3. **Import paths** - Python path configured
4. **Configuration** - pytest configuration correct

**Diagnostic:**
```bash
# Run single test
uv run pytest tests/test_example.py::test_add_numbers -v

# Check imports
python -c "from example import add_numbers; print('OK')"

# Verify test data
ls -la tests/test_data/
```

### Specific Test Fails

**Debug steps:**
1. **Run test in isolation** - `pytest tests/test_file.py::test_function`
2. **Add debug output** - Print intermediate values
3. **Check test data** - Verify test inputs
4. **Review test logic** - Verify test expectations

**Commands:**
```bash
# Run with debugger
uv run pytest tests/test_file.py::test_function --pdb

# Run with verbose output
uv run pytest tests/test_file.py::test_function -vv -s

# Check test coverage
uv run pytest tests/test_file.py --cov=src.module_name --cov-report=term-missing
```

### Coverage Below Threshold

**Improve coverage:**
1. **Identify gaps** - Review coverage report
2. **Add test cases** - Cover missing paths
3. **Test edge cases** - Boundary conditions
4. **Test error paths** - Exception handling

**Commands:**
```bash
# Generate coverage report
uv run pytest tests/ --cov=src --cov-report=html

# View report
open htmlcov/index.html

# Find missing lines
uv run pytest tests/ --cov=src --cov-report=term-missing | grep ">>>>>"
```

## PDF Generation Issues

### PDFs Not Generated

**Check:**
1. **Pandoc installed** - `pandoc --version`
2. **LaTeX installed** - `xelatex --version`
3. **Markdown valid** - Syntax correct
4. **Output directory** - Writable

**Diagnostic:**
```bash
# Test pandoc
pandoc manuscript/01_abstract.md -o test.pdf

# Test LaTeX
xelatex --version

# Check output directory
ls -la output/pdf/
```

### PDFs Have Errors

**Common issues:**
1. **Unresolved references** - Check labels exist
2. **Missing figures** - Generate figures first
3. **LaTeX errors** - Review LaTeX logs
4. **Font issues** - Install required fonts

**Diagnostic:**
```bash
# Validate PDFs
python3 scripts/04_validate_output.py

# Check references
grep -r "\\\\ref{" manuscript/ | grep -v "#"

# Check figures
ls -la output/figures/
```

### PDF Quality Issues

**Check:**
1. **Formatting** - LaTeX styling correct
2. **Cross-references** - All references resolved
3. **Citations** - Bibliography complete
4. **Figures** - All figures included

**Tools:**
```bash
# Quality check (top-level output after stage 5)
uv run python -c "from infrastructure.build.quality_checker import analyze_document_quality; print(analyze_document_quality('output/project_combined.pdf'))"

# Integrity check
uv run python -c "from infrastructure.validation import verify_output_integrity; print(verify_output_integrity('output'))"
```

## Performance Issues

### Build Too Slow

**Optimization strategies:**
1. **Parallel tests** - Use pytest-xdist
2. **Caching** - Enable pytest cache
3. **Incremental builds** - Only rebuild changed
4. **Skip validation** - Skip non-critical checks

**Commands:**
```bash
# Parallel execution
uv run pytest tests/ -n auto

# Cached runs
uv run pytest tests/ --cache-clear && uv run pytest tests/
```

### Memory Issues

**Solutions:**
1. **Reduce test data** - Use smaller datasets
2. **Clear caches** - Remove temporary files
3. **Increase memory** - System configuration
4. **Optimize code** - Reduce memory usage

## New Features Troubleshooting

### Checkpoint System

#### Pipeline Won't Resume from Checkpoint

**Symptoms:**
- Pipeline starts from beginning even with `PIPELINE_RESUME=1`
- Checkpoint file exists but is ignored

**Diagnosis:**
```bash
# Check if checkpoint exists
ls -la project/output/.checkpoints/pipeline_checkpoint.json

# View checkpoint contents
cat project/output/.checkpoints/pipeline_checkpoint.json | python3 -m json.tool
```

**Solutions:**
1. Verify checkpoint file is valid JSON
2. Check checkpoint directory permissions
3. Ensure `PIPELINE_RESUME=1` is set
4. Clear invalid checkpoint: `rm project/output/.checkpoints/pipeline_checkpoint.json`

#### Checkpoint Corrupted

**Symptoms:**
- Error loading checkpoint
- Pipeline fails to start

**Solutions:**
```bash
# Clear corrupted checkpoint
rm -f project/output/.checkpoints/pipeline_checkpoint.json

# Restart pipeline
python3 scripts/run_all.py
```

### Retry Logic

#### Operations Still Failing After Retries

**Symptoms:**
- Transient failures not being retried
- Operations fail immediately

**Diagnosis:**
- Check if operation uses `@retry_with_backoff` decorator
- Verify exception types match retry configuration
- Review logs for retry attempts

**Solutions:**
1. Ensure operation is decorated with retry decorator
2. Check exception types match retry configuration
3. Increase `max_attempts` if needed
4. Verify transient vs permanent failures

### Progress Reporting

#### ETA Not Showing

**Symptoms:**
- No ETA displayed in pipeline output
- Progress bars not updating

**Solutions:**
1. Ensure pipeline start time is passed to stage functions
2. Check terminal supports progress output
3. Verify `LOG_LEVEL` allows INFO messages
4. Check for buffering issues (use `-u` flag with Python)

### Performance Monitoring

#### Resource Tracking Not Working

**Symptoms:**
- No performance metrics in logs
- Memory/CPU usage not reported

**Solutions:**
1. Install `psutil`: `uv add psutil`
2. Enable monitoring: `export ENABLE_PERFORMANCE_MONITORING=1`
3. Check log level allows DEBUG messages
4. Verify system supports resource tracking

## Recovery Procedures

### Complete Reset

**If everything fails, reset completely:**
```bash
# Clean virtual environment
rm -rf .venv
rm uv.lock

# Reinstall
uv sync
uv run pytest tests/

# Rebuild complete pipeline
python3 scripts/run_all.py
```

### Recover from Backup

**If you have backups:**
```bash
# Restore from git
git checkout HEAD -- output/

# Restore dependencies
git checkout HEAD -- uv.lock
uv sync
```

### Partial Recovery

**Recover specific components:**
```bash
# Rebuild only tests
uv run pytest tests/

# Regenerate only figures
python3 scripts/example_figure.py

# Rebuild PDFs (run stage 3 only)
python3 scripts/03_render_pdf.py
```

## Expected Warnings

These warnings are normal and do not indicate problems:

### BibTeX `openout_any = p` Warning

**What you'll see:**
```
Warning: Can't open "..." for writing. (openout_any = p)
```

**What it means:**
This is an informational warning from BibTeX indicating that the `openout_any` configuration is set to restricted mode (`p`). This is a security feature that prevents arbitrary file creation.

**Is it a problem?**
**No.** This warning is expected and harmless. It does not affect:
- PDF generation
- Bibliography inclusion
- Cross-references
- Document quality

**Why it occurs:**
BibTeX is reporting its current security configuration. The restricted mode is intentional and protects against potential security issues.

**What to do:**
You can safely ignore this warning. The build completes successfully, and all references are properly resolved in the final PDF.

### LaTeX Rerun Suggestions

**What you'll see:**
```
Rerun to get cross-references right
Rerun to resolve undefined references
```

**What it means:**
LaTeX has detected that references may have changed and suggests rerunning compilation for consistency.

**Is it a problem?**
**No.** The PDF rendering pipeline automatically reruns LaTeX as needed. These messages are informational and indicate the system is working correctly.

**Why it occurs:**
LaTeX's standard behavior when cross-references or page numbers might have changed. The build system handles this automatically.

### Pandoc Metadata Warnings

**What you'll see:**
```
Warning: Couldn't find reference for figure in markdown
```

**What it means:**
Pandoc is noting that some cross-reference formats are being processed or adjusted during conversion.

**Is it a problem?**
**Usually no.** Most of these warnings are harmless and the references are still resolved. Check the final PDF to confirm references work.

**What to do:**
1. Check the final PDF for proper references
2. If references are broken, review markdown syntax
3. Ensure all `@fig:` labels are defined in manuscript

### pypdf "Ignoring wrong pointing object" Warnings

**What you'll see:**
```
Ignoring wrong pointing object 0 0 (offset 0)
Ignoring wrong pointing object 76 0 (offset 0)
Ignoring wrong pointing object 85 0 (offset 0)
```

**What it means:**
These warnings come from the pypdf library during PDF text extraction. They indicate that the PDF file contains malformed cross-reference table entries that point to invalid offsets within the file.

**Is it a problem?**
**No.** These warnings are harmless and expected. The pypdf library gracefully handles these malformed objects by ignoring them and continuing with text extraction. The PDF processing completes successfully despite the warnings.

**Why it occurs:**
PDF files can contain cross-reference tables that map object identifiers to their locations in the file. When these tables contain errors or point to invalid locations, pypdf logs these warnings but continues processing. This is common with PDFs created by various tools or that have been through multiple conversions.

**What to do:**
You can safely ignore these warnings. The system has been updated to suppress these warnings during normal operation (they may still appear at DEBUG logging level). If you need to see them for troubleshooting, set `LOG_LEVEL=0` in your environment.

**Technical details:**
- These warnings appear during `PdfReader` instantiation and page extraction
- They don't affect text extraction quality or completeness
- The warnings are now captured and logged at DEBUG level only
- No action is required - the PDF processing continues normally

### Python SyntaxWarnings (Fixed)

**What you might have seen:**
```
SyntaxWarning: invalid escape sequence '\m' in line 257
```

**Status:** ✅ **FIXED** - These warnings have been resolved by using raw string literals (`r"..."`).

## Getting Help

### Before Asking for Help

**Collect this information:**
1. **Error messages** - Full output
2. **Environment** - OS, Python version, tools
3. **Steps to reproduce** - Exact commands
4. **What you've tried** - Attempted solutions

### Resources

- **[FAQ](FAQ.md)** - Common questions
- **[Common Workflows](COMMON_WORKFLOWS.md)** - Step-by-step solutions
- **[Build System](BUILD_SYSTEM.md)** - Build details
- **[GitHub Issues](https://github.com/docxology/template/issues)** - Report bugs

### Diagnostic Script

**Run comprehensive diagnostics:**
```bash
#!/bin/bash
echo "=== System Information ==="
python --version
uv --version
pandoc --version 2>/dev/null || echo "Pandoc not found"
xelatex --version 2>/dev/null || echo "XeLaTeX not found"

echo -e "\n=== Environment ==="
env | grep -E "AUTHOR|PROJECT|DOI" || echo "No environment variables set"

echo -e "\n=== Dependencies ==="
uv tree | head -20

echo -e "\n=== Test Status ==="
uv run pytest tests/ --collect-only -q | tail -5

echo -e "\n=== Output Directory ==="
ls -la output/ 2>/dev/null || echo "Output directory not found"
```

## Summary

Troubleshooting checklist:

1. **Gather information** - Error messages, environment
2. **Reproduce issue** - Confirm consistent behavior
3. **Check common causes** - Dependencies, configuration
4. **Apply fixes** - One change at a time
5. **Verify resolution** - Test after each fix
6. **Document solution** - Note what worked

For specific issues, see:
- [FAQ](FAQ.md) - Common questions
- [Build System](BUILD_SYSTEM.md) - Build troubleshooting
- [Common Workflows](COMMON_WORKFLOWS.md) - Step-by-step guides

---

**Related Documentation:**
- [FAQ](FAQ.md) - Frequently asked questions
- [Build System](BUILD_SYSTEM.md) - Build system details
- [Common Workflows](COMMON_WORKFLOWS.md) - Workflow troubleshooting


