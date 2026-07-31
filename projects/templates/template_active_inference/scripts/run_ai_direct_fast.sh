#!/usr/bin/env bash
# Usage: uv run bash scripts/run_ai_direct_fast.sh
#
# Fast local development loop for template_active_inference.
# Runs only the test_*_direct.py family (251 tests) — these never trigger
# the expensive gate-artifact prewarm (the full research pipeline).
# Covers all promoted artifact builders, helpers, and edge cases.
# The full suite (777 tests) is for CI/release.
#
# Typical wall time: ~5 min (direct tests, isolated tree copies).
# Full suite: ~10-15 min (includes gate prewarm pipeline).

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

UV="uv"
PYTEST_AI="projects/templates/template_active_inference/tests"

echo "=== template_active_inference: fast direct-only run ==="
echo "Gate prewarm: NOT triggered (test_*_direct.py override)"
echo "251 tests expected (~5 min)"
echo ""

"$UV" run pytest "$PYTEST_AI" \
  --override-ini="python_files=test_*_direct.py" \
  --timeout=300 \
  -q \
  -x \
  2>&1 | tail -15

echo ""
echo "=== DONE ==="
echo "Full suite:"
echo "  uv run pytest $PYTEST_AI/ --timeout=600 -m 'not slow and not long_running'"