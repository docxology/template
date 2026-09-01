# manuscript

Source manuscript files are token shells. Generated prose belongs in `output/manuscript/` after `scripts/z_generate_manuscript_variables.py` runs.

Rules:

- Keep H1 titles variable-backed with `{{TITLE_*}}` tokens when they correspond to `madlib.section_titles`.
- Keep long prose in generated body variables from `src/composition.py`.
- Keep tables generated from source functions, not hand-authored in Markdown. This includes design-principle, pipeline-phase, protocol, section plan, audit, contribution, evaluation, QA-probe, failure-mode, authoring-obligation, title, token inventory, and provenance tables.
- Expand Methods by editing `madlib.method_protocol`, `madlib.pipeline_phases`, `madlib.quality_probes`, `madlib.failure_modes`, `madlib.audit_rules`, `madlib.contribution_claims`, and `src/composition.py`, not by editing hydrated output.
- Keep review scenario, token-selection invariants, claim-ledger alignment, review-packet handoff, and fork-migration notes generated from the same config/source path as the rest of Methods.
- Keep figure references behind `{{METHODS_FIGURES}}`, `{{RESULTS_FIGURES}}`, `{{CONFIGURATION_FIGURES}}`, and `{{EVALUATION_FIGURES}}`.
- Add new placeholders only after adding corresponding keys in `src/manuscript_variables.py` and tests in `tests/test_manuscript_variables.py`.

```bash
uv run python projects/templates/template_madlib/scripts/z_generate_manuscript_variables.py
rg "\\{\\{" projects/templates/template_madlib/output/manuscript
```
