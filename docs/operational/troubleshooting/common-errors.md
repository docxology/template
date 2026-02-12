# Common Errors Reference

> **Quick lookup** for error messages and solutions

**Quick Reference:** [Main Troubleshooting](../troubleshooting-guide.md) | [FAQ](../../reference/faq.md)

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
ls project/output/figures/
grep "includegraphics" project/output/pdf/_combined_manuscript.tex
python3 scripts/02_run_analysis.py   # Regenerate figures
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
ls -la project/output/.checkpoints/pipeline_checkpoint.json
cat project/output/.checkpoints/pipeline_checkpoint.json | python3 -m json.tool
```

**Solutions:**

1. Verify checkpoint is valid JSON
2. Ensure `PIPELINE_RESUME=1` is set
3. Clear invalid checkpoint: `rm project/output/.checkpoints/pipeline_checkpoint.json`

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

**Related:** [Environment Setup](environment-setup.md) | [Build Tools](build-tools.md) | [Main Guide](../troubleshooting-guide.md)
