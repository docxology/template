# Common Errors Reference

> **Quick lookup** for error messages and solutions

**Quick Reference:** [Main Troubleshooting](README.md) | [FAQ](../../reference/faq.md)

---

## File System Errors

### No such file or directory

**Symptom:** `cat: /path/to/file: No such file or directory`

**Solutions:**

```bash
ls -la /path/to/file    # Check if file exists
stat /path/to/file      # Check permissions
pwd                     # Verify working directory
```

---

### Permission denied

**Symptom:** `Permission denied: /path/to/file`

**Solutions:**

```bash
ls -la /path/to/file     # Check permissions
chmod +r file            # Fix file permissions
chmod +x directory       # Fix directory permissions
chown user:group file    # Check ownership
```

---

## Command Errors

### Command not found

**Symptom:** `pandoc: command not found` or `xelatex: command not found`

**Solutions:**

```bash
which pandoc           # Check if exists
echo $PATH             # Check PATH
# Install missing tool or add to PATH
```

---

## Dependency Errors

### Could not find version

**Symptom:** `Error: Could not find a version that satisfies the requirement`

**Solutions:**

```bash
uv tree                              # Check dependency versions
python --version                     # Check Python version
cat pyproject.toml | grep -A 10 dependencies  # Review constraints
```

---

### Lock file conflicts

**Symptom:** `Merge conflict in uv.lock`

**Solutions:**

```bash
uv lock                              # Regenerate lock file
git checkout --theirs uv.lock        # Accept one version
uv sync                              # Re-sync
```

---

### ⚠️ Project packages missing from root venv — silent Stage 4 failure

**Symptom:** `❌ act_inf_metaanalysis: 4 stages, 7.7s` — Stage 4 fails in under 1 second with no visible import error in console.

**Root Cause:** Each project sub-directory may have its own `pyproject.toml` declaring extra dependencies (`scipy`, `pandas`, `wordcloud`, `rdflib`, `scikit-learn`, `networkx`, `requests`, etc.). When `02_run_analysis.py` runs analysis scripts, it uses the **root venv** unless the project has a local `.venv` directory. If these packages are only in the project's `pyproject.toml` and not in the root `pyproject.toml`, analysis scripts crash on import immediately — but the error is captured by subprocess and only logged as a stage failure.

**Diagnosis:**

```bash
# Check what's in the root venv
.venv/bin/python -c "import scipy, pandas, wordcloud, rdflib, sklearn, networkx" 2>&1

# Check what's in the project's pyproject.toml
cat projects/<name>/pyproject.toml | grep -A 20 dependencies

# Confirm project has no local venv (so root venv is used)
ls projects/<name>/.venv 2>/dev/null || echo "No local venv → uses root venv"
```

**Fix:** Add all project-specific packages to the root `pyproject.toml` core `dependencies` list, then run `uv sync`:

```toml
# pyproject.toml (root)
[project]
dependencies = [
  "numpy>=1.22",
  "pyyaml>=6.0",
  "matplotlib>=3.7",
  # act_inf_metaanalysis project requirements
  "scipy>=1.10.0",
  "pandas>=2.0.0",
  "networkx>=3.0",
  "requests>=2.31.0",
  "rdflib>=7.0.0",
  "wordcloud>=1.9.0",
  "scikit-learn>=1.3.0",
]
```

```bash
uv sync   # installs newly listed packages
./run.sh  # should now pass all projects
```

**Rule:** If a project has its own `pyproject.toml` but **no** `.venv/` directory, every package in that project's `dependencies` must also be in the root `pyproject.toml`.

---

### `ModuleNotFoundError: No module named 'matplotlib'` in analysis scripts

**Symptom:** `generate_architecture_viz.py` or other analysis scripts fail with `No module named 'matplotlib'`.

**Root Cause:** `matplotlib` was declared only in the `[project.optional-dependencies] dashboard` group in the root `pyproject.toml`. Running `uv sync` (default, no group flags) does not install optional groups.

**Fix:** Move `matplotlib` to core `dependencies`:

```toml
# pyproject.toml
[project]
dependencies = [
  "numpy>=1.22",
  "pyyaml>=6.0",
  "matplotlib>=3.7",  # ← must be in CORE, not optional group
]
```

```bash
uv sync
```

---

## Build Errors

### Pandoc conversion failed

```bash
pandoc --version
pandoc input.md -o output.pdf --verbose
```

---

### LaTeX compilation failed

```bash
xelatex --version
xelatex document.tex
cat document.log | grep Error
```

---

### Figure not found

```bash
ls projects/{name}/output/figures/
grep "includegraphics" projects/{name}/output/pdf/_combined_manuscript.tex
uv run python scripts/02_run_analysis.py   # Regenerate figures
```

---

## Progress & Features

### Progress bar not updating

**Solutions:**

1. Progress bars require TTY - don't redirect stdout/stderr
2. Use `log_progress()` in non-TTY environments
3. Check update interval

---

### Checkpoint won't resume

**Diagnosis:**

```bash
ls -la projects/{name}/output/.checkpoints/pipeline_checkpoint.json
cat projects/{name}/output/.checkpoints/pipeline_checkpoint.json | uv run python -m json.tool
```

**Solutions:**

1. Verify checkpoint is valid JSON
2. Ensure `PIPELINE_RESUME=1` is set
3. Clear invalid checkpoint: `rm projects/{name}/output/.checkpoints/pipeline_checkpoint.json`

---

## Edge Cases

### Very large manuscripts (100+ pages)

**Solutions:**

1. Split into sections - generate individual PDFs
2. Increase LaTeX memory: `max_print_line=10000`
3. Compress large images before inclusion

---

### Unicode and special characters

**Solutions:**

1. Use UTF-8 encoding for all files
2. Ensure `inputenc` and `fontenc` LaTeX packages loaded
3. Escape LaTeX specials: `\textbackslash` for backslash

---

### Multiple Python versions

**Solutions:**

1. Pin Python version in `pyproject.toml`: `requires-python = ">=3.10"`
2. Use uv: `uv sync` ensures consistent environment
3. Always use project-specific venv

---

### Network-dependent operations failing

**Solutions:**

1. Check connectivity: `ping` or `curl`
2. Configure HTTP_PROXY if behind firewall
3. Increase timeout values
4. Use cached results when available
5. Skip optional features: `--skip-llm`

---

## Pipeline Stage Errors

### Stage 01: `ModuleNotFoundError` for project packages

**Symptom:** `ModuleNotFoundError: No module named '<package>'` during test collection

**Root Cause:** Missing `tests/conftest.py` that adds `src/` to `sys.path`.

**Fix:** Create `tests/conftest.py`:

```python
import os, sys
os.environ.setdefault("MPLBACKEND", "Agg")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)
```

---

### Stage 02: `ImportError` in analysis scripts

**Symptom:** `ImportError: cannot import name 'X' from 'infrastructure.core.Y'`

**Root Cause:** Pipeline scripts import symbols that were never defined in the target module (e.g., `format_error_with_suggestions` in `02_run_analysis.py`).

**Prevention:** Run each stage standalone before full pipeline:

```bash
uv run python scripts/02_run_analysis.py --project <name>
```

---

### `functools.partial` missing `__name__`

**Symptom:** `AttributeError: 'functools.partial' object has no attribute '__name__'`

**Where:** `infrastructure/scientific/stability.py`, `infrastructure/scientific/benchmarking.py`

**Fix:**

```python
# ❌ Breaks on partial objects
name = func.__name__

# ✅ Safe for any callable
name = getattr(func, "__name__",
    getattr(getattr(func, "func", None), "__name__", repr(func)))
```

---

### Undefined `project_root` in scripts

**Symptom:** `NameError: name 'project_root' is not defined`

**Root Cause:** `project_root` used in functions but only defined inside `if __name__ == "__main__":`.

**Fix:** Define as module-level constant:

```python
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
```

---

### Matplotlib emoji glyph warnings

**Symptom:** `UserWarning: Glyph XXXXX (\N{CLIPBOARD}) missing from font(s) DejaVu Sans`

**Fix:** Replace emoji characters (📋, 📖) with text labels in matplotlib figures. DejaVu Sans does not include emoji codepoints.

---

**Related:** [Environment Setup](environment-setup.md) | [Build Tools](build-tools.md) | [Main Guide](README.md) | [New Project Setup](../../guides/new-project-setup.md)
