# Manuscript

Sections are combined in lexicographic order (`00_` … `09_`, including `03a`–`03f`). Filenames must not use a leading `S` unless they are true supplemental sections: discovery treats `S*.md` as supplemental and inserts them after numbered main sections. `config.yaml` holds paper metadata and `experiment.*` parameters consumed by `scripts/proximity_monte_carlo.py`.

Markdown/LaTeX conventions for authors live in [`../docs/manuscript_conventions.md`](../docs/manuscript_conventions.md) (not included in the PDF).

## Quick check

```bash
python3 -m infrastructure.validation.cli markdown projects/special_number_proximity/manuscript/
```
