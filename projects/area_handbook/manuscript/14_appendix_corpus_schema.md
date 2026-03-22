# Appendix: YAML corpus schema (normative summary)

| Field | Location | Constraint |
|-------|-----------|--------------|
| `area_id` | root | Non-empty string |
| `area_label` | root | Non-empty string |
| `version` | root | Non-empty string (semantic or calendar versioning recommended) |
| `themes` | root | Non-empty list of objects with `id`, `label`, `description` |
| `evidence` | root | List (may be empty) of objects with `id`, `statement`, `theme`, `weight`, `source_label`, `reviewed_at` |

Each `evidence.theme` must equal some `themes[].id`. Weights are unitless credibility or strength signals capped per row at $1.0$; section scores cap the sum per chapter at $1.0$ in `src/synthesis.py`.

**Example evidence object (Riverbend).**

```yaml
- id: ev-007
  statement: Deferred bridge maintenance now spans 47 structures flagged as priority repair.
  theme: infrastructure
  weight: 0.9
  source_label: DOT condition database export
  reviewed_at: "2025-11-28"
```

**Example theme object.**

```yaml
- id: infrastructure
  label: Infrastructure
  description: Transport, utilities, broadband, and maintenance backlogs.
```

Machine-readable outline and metrics after a build:

- `projects/area_handbook/output/data/area_outline.json`
- `projects/area_handbook/output/data/handbook_report.json`
- `projects/area_handbook/output/data/handbook_toc.md`

The combined human-readable rollup lives in `handbook_body.md` in the same directory.

**Figures and registry.** Running `scripts/02_generate_handbook_figure.py` writes PNGs under `projects/area_handbook/output/figures/` and updates `figure_registry.json` for validation. Manuscript labels `fig:coverage`, `fig:bytheme`, and `fig:gapstatus` must stay aligned with that script.

**Empty evidence list.** An empty `evidence` array still instantiates all template sections with score zero; metrics report `gap_count` equal to section count. This edge case is tested to prevent divide-by-zero surprises in coverage ratios.

**JSON interchange.** `load_corpus_from_dict` accepts Python dicts shaped like parsed JSON for tests and API adapters; the same constraints as YAML apply [@template2026].
