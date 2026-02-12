# Recovery Procedures

> **Reset and recovery** procedures for the Research Project Template

**Quick Reference:** [Main Troubleshooting](../troubleshooting-guide.md) | [Build System](../build-system.md)

---

## Complete Reset

**When everything fails, reset completely:**

```bash
# Clean virtual environment
rm -rf .venv
rm uv.lock

# Reinstall
uv sync
uv run pytest tests/

# Rebuild pipeline
python3 scripts/execute_pipeline.py --core-only
```

---

## Recover from Backup

**If you have backups:**

```bash
# Restore from git
git checkout HEAD -- output/

# Restore dependencies
git checkout HEAD -- uv.lock
uv sync
```

---

## Partial Recovery

**Recover specific components:**

```bash
# Rebuild only tests
uv run pytest tests/

# Regenerate only figures
python3 project/scripts/example_figure.py

# Rebuild PDFs (run stage 3 only)
python3 scripts/03_render_pdf.py
```

---

## Checkpoint Recovery

**Clear corrupted checkpoint:**

```bash
rm -f project/output/.checkpoints/pipeline_checkpoint.json
python3 scripts/execute_pipeline.py --core-only
```

---

## Diagnostic Script

**Run full diagnostics:**

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

---

## Getting Help

### Before Asking for Help

**Collect this information:**

1. **Error messages** - Full output
2. **Environment** - OS, Python version, tools
3. **Steps to reproduce** - Exact commands
4. **What you've tried** - Attempted solutions

### Resources

- [FAQ](../../reference/faq.md) - Common questions
- [Common Workflows](../../reference/common-workflows.md) - Step-by-step solutions
- [Build System](../build-system.md) - Build details
- [GitHub Issues](https://github.com/docxology/template/issues) - Report bugs

---

## Troubleshooting Checklist

1. **Gather information** - Error messages, environment
2. **Reproduce issue** - Confirm consistent behavior
3. **Check common causes** - Dependencies, configuration
4. **Apply fixes** - One change at a time
5. **Verify resolution** - Test after each fix
6. **Document solution** - Note what worked

---

**Related:** [Environment Setup](environment-setup.md) | [Build Tools](build-tools.md) | [Main Guide](../troubleshooting-guide.md)
