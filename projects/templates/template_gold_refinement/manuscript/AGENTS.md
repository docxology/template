# manuscript

Source manuscript files are token shells. Generated prose belongs in
`output/manuscript/` after `scripts/z_generate_manuscript_variables.py` runs.

Rules:

- Keep H1 titles variable-backed with `{{TITLE_*}}` tokens.
- Keep tables generated from source functions, not hand-authored.
- Keep figure references behind generated variables.
- Add new placeholders only after adding corresponding keys in
  `src/manuscript_variables.py` and tests in `tests/test_manuscript_variables.py`.

```bash
uv run python projects/templates/template_gold_refinement/scripts/z_generate_manuscript_variables.py
grep -r "{{" projects/templates/template_gold_refinement/output/manuscript/
```
