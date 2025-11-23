# Comprehensive Troubleshooting Guide

> **Systematic approach** to resolving issues and errors

**Quick Reference:** [FAQ](FAQ.md) | [Common Workflows](COMMON_WORKFLOWS.md) | [Build System](BUILD_SYSTEM.md)

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
Coverage: 65% (below 70% requirement)
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
```

**Diagnosis:**
```bash
# Check if figures exist
ls -la project/output/figures/

# Check figure references in markdown
grep -r "includegraphics" project/manuscript/

# Verify figure paths in LaTeX source
ls project/output/pdf/_combined_manuscript.tex && grep includegraphics project/output/pdf/_combined_manuscript.tex | head -5

# Check LaTeX compilation log
tail -50 project/output/pdf/_combined_manuscript.log | grep -i "graphics\|error\|warning"
```

**Solutions:**
1. Generate missing figures by running analysis scripts
2. Verify figure filenames match exactly (case-sensitive)
3. Check file format is PNG, PDF, or JPG
4. Ensure figures are in `project/output/figures/`
5. Verify paths in markdown use `../output/figures/filename`
6. Run full PDF rendering again (paths are fixed automatically)

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

# Or use shell wrapper
./run_all.sh

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
uv run python repo_utilities/validate_pdf_output.py

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
uv run python repo_utilities/validate_pdf_output.py

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
python scripts/example_figure.py

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


