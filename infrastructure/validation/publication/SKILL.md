---
name: publication-readiness-audit
description: "Use when auditing public research exemplars for deterministic publication readiness across tests, methods, evidence, artifacts, figures, manuscript sources, and generated outputs."
---

# Publication-readiness audit

Run the shared audit after source, tests, methods, manuscript, or generated
output changes. Deterministic failures block; review-required findings are
explicit handoff items for a human editor or domain reviewer.

```bash
uv run python -m infrastructure.validation.cli publication-audit \
  --all-public --strict --rendered --format markdown
```

The audit is read-only. Fix the producer or source contract, regenerate, and
run it again. Do not edit reports by hand.
