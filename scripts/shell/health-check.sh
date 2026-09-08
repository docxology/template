#!/usr/bin/env bash
################################################################################
# Health Check Script
# Quick verification that the system is ready for pipeline operations.
# Suitable for CI/CD, cron, or manual pre-flight checks.
################################################################################

set -euo pipefail

echo "=== Health Check ==="
ERRORS=0

# 1. Python environment
if python -c "import sys; print(f'Python {sys.version}')" 2>/dev/null; then
    echo "✅ Python available"
else
    echo "❌ Python missing or broken"
    ERRORS=$((ERRORS + 1))
fi

# 2. uv package manager
if uv --version >/dev/null 2>&1; then
    echo "✅ uv ($(uv --version | head -1))"
else
    echo "❌ uv not found"
    ERRORS=$((ERRORS + 1))
fi

# 3. pandoc (required for HTML/DOCX/EPUB rendering)
if command -v pandoc &>/dev/null; then
    echo "✅ pandoc ($(pandoc --version | head -1))"
else
    echo "❌ pandoc not found (required for rendering) — bash scripts/shell/setup-system-deps.sh"
    ERRORS=$((ERRORS + 1))
fi

# 4. xelatex (required for PDF rendering)
if command -v xelatex &>/dev/null; then
    echo "✅ xelatex present"
else
    echo "❌ xelatex not found (required for PDF rendering) — bash scripts/shell/setup-system-deps.sh"
    ERRORS=$((ERRORS + 1))
fi

# 5. Ollama (optional but warn)
if command -v ollama &>/dev/null; then
    echo "✅ Ollama present"
else
    echo "⚠️  Ollama not installed (needed for LLM stages)"
fi

# 6. Disk space (warn if < 5GB free on working dir)
FREE_KB=$(df . | tail -1 | awk '{print $4}')
FREE_GB=$((FREE_KB / 1024 / 1024))
if [ "$FREE_KB" -lt 5242880 ]; then
    echo "⚠️  Low disk space: ${FREE_GB} GB remaining"
else
    echo "✅ Disk space OK (${FREE_GB} GB free)"
fi

# 7. Docker (if using containerized Humos)
if docker --version >/dev/null 2>&1; then
    echo "✅ Docker available ($(docker --version | cut -d',' -f1))"
else
    echo "⚠️  Docker not available (Humos container won't run)"
fi

# 8. Verify repository structure
for dir in infrastructure projects docs; do
    if [[ -d "${dir}" ]]; then
        echo "✅ Found ${dir}/"
    else
        echo "❌ Missing ${dir}/"
        ((ERRORS++))
    fi
done

# 9. Check run.sh is executable
if [[ -x "./run.sh" ]]; then
    echo "✅ run.sh executable"
else
    echo "❌ run.sh not found or not executable"
    ((ERRORS++))
fi

# 10. Verify uv sync succeeded (dependencies installed)
if uv sync --quiet 2>/dev/null; then
    echo "✅ Dependencies synced"
else
    echo "❌ uv sync failed — run 'uv sync' to install dependencies"
    ERRORS=$((ERRORS + 1))
fi

echo ""
if [[ ${ERRORS} -eq 0 ]]; then
    echo "=== All checks passed ==="
    exit 0
else
    echo "=== ${ERRORS} error(s) found ==="
    exit 1
fi
