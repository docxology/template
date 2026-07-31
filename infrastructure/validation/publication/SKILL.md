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
run it again. Source placeholders may remain when the canonical hydrated or
combined rendered input is resolved. Do not edit reports or rendered provenance
receipts by hand; stage 04 writes them after a green validation run, and
`scripts/maintenance/refresh_rendered_provenance.py` backfills already-green
tracked snapshots.
