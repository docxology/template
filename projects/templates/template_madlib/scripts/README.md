# Scripts

Scripts are thin orchestrators.

```bash
uv run python projects/templates/template_madlib/scripts/01_generate_madlib_artifacts.py
uv run python projects/templates/template_madlib/scripts/z_generate_manuscript_variables.py
```

The root analysis stage uses the allowlist in `manuscript/config.yaml` and runs these in order.

| Script | Responsibility |
| --- | --- |
| `01_generate_madlib_artifacts.py` | Calls `src.analysis.generate_artifacts`, writing token inventory, configured-field inventory, section plan, injection trace, summary report, configured-field report, cover overview, manuscript figures, and figure registry. These artifacts are the evidence surface for method protocol rows, pipeline phases, QA probes, failure modes, claim-ledger alignment, and reviewer-packet assembly. |
| `z_generate_manuscript_variables.py` | Regenerates artifacts, writes `output/data/manuscript_variables.json`, and delegates token substitution to shared manuscript injection. It is the only path that should hydrate `output/manuscript/`. |
| `00_preflight.py` | Inherited render preflight plumbing; not part of Stage 02 analysis. |

Do not put token selection, section composition, schema validation, provenance logic, method-protocol logic, invariant logic, claim-ledger logic, review-packet logic, or figure-evidence logic in scripts.
