#!/usr/bin/env bash
################################################################################
# Health Check Script
# Quick verification that the system is ready for pipeline operations.
# Suitable for CI/CD, cron, or manual pre-flight checks.
################################################################################

set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: $0"
    echo "  Verifies Python, uv, and optional tools (ollama) are available."
    echo "  Exits 0 if healthy, 1 if critical checks fail."
    exit 0
fi

echo "=== Health Check ==="
ERRORS=0

# 1. Python environment
if python -c "import sys; print(f'Python {sys.version}')" 2>/dev/null; then
    echo "✅ Python available"
else
    echo "❌ Python missing or broken"
    ((ERRORS++))
fi

# 2. uv package manager
if uv --version >/dev/null 2>&1; then
    echo "✅ uv ($(uv --version | head -1))"
else
    echo "❌ uv not found"
    ((ERRORS++))
fi

# 3. Ollama (optional but warn)
if command -v ollama &>/dev/null; then
    echo "✅ Ollama present"
else
    echo "⚠️  Ollama not installed (needed for LLM stages)"
fi

# 4. Disk space (warn if < 5GB free on working dir)
FREE_KB=$(df . | tail -1 | awk '{print $4}')
FREE_GB=$((FREE_KB / 1024 / 1024))
if [ "$FREE_KB" -lt 5242880 ]; then
    echo "⚠️  Low disk space: ${FREE_GB} GB remaining"
else
    echo "✅ Disk space OK (${FREE_GB} GB free)"
fi

# 5. Docker (if using containerized Humos)
if docker --version >/dev/null 2>&1; then
    echo "✅ Docker available ($(docker --version | cut -d',' -f1))"
else
    echo "⚠️  Docker not available (Humos container won't run)"
fi

# 6. Verify repository structure
for dir in infrastructure projects docs; do
    if [[ -d "${dir}" ]]; then
        echo "✅ Found ${dir}/"
    else
        echo "❌ Missing ${dir}/"
        ((ERRORS++))
    fi
done

# 7. Check run.sh is executable
if [[ -x "./run.sh" ]]; then
    echo "✅ run.sh executable"
else
    echo "❌ run.sh not found or not executable"
    ((ERRORS++))
fi

# 8. Verify uv sync succeeded (dependencies installed)
if uv sync --quiet 2>/dev/null; then
    echo "✅ Dependencies synced"
else
    echo "❌ uv sync failed — run 'uv sync' to install dependencies"
    ((ERRORS++))
fi

echo ""
if [[ ${ERRORS} -eq 0 ]]; then
    echo "=== All checks passed ==="
    exit 0
else
    echo "=== ${ERRORS} error(s) found ==="
    exit 1
fi
