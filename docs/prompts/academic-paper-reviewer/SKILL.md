---
name: template-academic-paper-reviewer
description: |
  Read-only manuscript review, methodology review, re-review, and calibration workflow
  for template projects. USE WHEN the user asks for peer review, referee-style critique,
  methods/statistics review, or verification that revisions addressed prior comments.
metadata:
  version: "1.0.0"
  last_updated: "2026-05-25"
  status: active
  data_access_level: verified_only
  task_type: open-ended
  modes:
    - full
    - quick
    - methodology-focus
    - re-review
    - calibration
  related_skills:
    - template-academic-paper
    - template-manuscript-claim-verification
    - template-validation-quality
---

# Academic paper reviewer

Read-only review workflow for template manuscripts. Review reports are separate
artifacts; this skill does not edit the manuscript directly.

## Natural invoke

- "Review this manuscript like peer reviewers"
- "Focus only on methodology and statistics"
- "Check whether my revisions address the comments"
- "Calibrate the review rubric against a known decision set"

## Inputs to confirm

- **Manuscript** - project manuscript directory or provided paper file.
- **Mode** - full, quick, methodology-focus, re-review, or calibration.
- **Review lens** - target venue, discipline, methods, and known reviewer comments.
- **Evidence access** - rendered PDF, source markdown, output artifacts, validation reports, and claim ledgers.

## Workflow

1. **Read-only boundary** - produce reports, matrices, and recommendations only; route edits to [academic-paper](../academic-paper/SKILL.md).
2. **Panel lenses** - separate contribution, methods, evidence/citations, presentation, reproducibility, and adversarial-overclaim checks.
3. **Evidence audit** - cite source file paths, generated artifacts, evidence registry entries, and validation reports when flagging issues.
4. **Revision traceability** - in re-review mode, map each reviewer concern to author action, verification status, residual risk, and next owner.
5. **No sycophantic concession** - do not soften a finding unless new evidence from the manuscript or artifacts resolves it.

## Deliverables

- Review package: summary verdict, major issues, minor issues, evidence table, and recommended next actions.
- Methodology-focus mode: methods validity, data/analysis reproducibility, statistical or formalism concerns.
- Re-review mode: traceability matrix with comment, response, evidence checked, verified, and residual issue.
- Calibration mode: rubric, expected decision labels, observed disagreement, and confidence caveats.

## Verification commands

```bash
uv run python -m infrastructure.validation.cli prerender projects/<project>/manuscript --repo-root .
uv run python -m infrastructure.validation.cli evidence projects/<project> --fail-on-issues
uv run python -m infrastructure.prose.cli report projects/<project>/manuscript
```

## References

- [MODE_REGISTRY.md](../MODE_REGISTRY.md)
- [academic-paper](../academic-paper/SKILL.md)
- [manuscript-claim-verification](../manuscript-claim-verification/SKILL.md)
