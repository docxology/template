---
name: template-publication-audit
description: |
  End-to-end publication-readiness audit for public template exemplars — tests,
  no-mocks, methods contracts, claims, evidence, figures, references, rendered
  outputs, and deterministic regeneration. USE WHEN preparing a template or
  project for release, DOI deposit, peer review, or a publication sign-off.
metadata:
  version: "1.0.0"
  last_updated: "2026-07-17"
  status: active
  data_access_level: verified_only
  task_type: open-ended
  modes:
    - deterministic-gate
    - editorial-review
  related_skills:
    - template-comprehensive-assessment
    - template-reproducibility-audit
    - template-methods-orchestration
    - template-manuscript-claim-verification
---

# Publication audit workflow

Use the deterministic infrastructure gate first:

```bash
uv run python -m infrastructure.validation.cli publication-audit \
  --project templates/template_code_project --strict --rendered --format markdown
```

Then run the project’s tests, methods plan, prerender gate, render, output
validation, no-mock inventory, and clean double-run comparison. Treat only
stable validator failures as blocking. Preserve `review_required` findings for
human assessment of scientific scope, unsupported generalization, prose, and
visual quality.

## Required evidence

- real tests and zero prohibited mock frameworks;
- source-backed claim ledger and evidence registry;
- methods-to-stage-to-artifact mapping with definitions of done;
- figure registry with labels, captions, provenance, and existing files;
- generated artifact manifest and validation report;
- clean rendered PDF/HTML/slides where supported;
- second-run comparison with no unexplained differences.

Never hand-edit generated output. Correct the source producer or manuscript
source and regenerate the affected artifacts.
