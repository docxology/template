# docs/ - Agent-Facing Documentation Hub

This directory documents how to work on the `template_advanced_literature_review` exemplar — the multi-phase sibling of `template_literature_meta_analysis`. Keep these files project-specific; do not copy single-term or private-sidecar wording into this public template.

## File Inventory

| File | Purpose |
| --- | --- |
| `README.md` | Quick navigation and canonical commands |
| `agent_instructions.md` | Rules agents must read before source, test, config, or manuscript edits |
| `architecture.md` | Pipeline layers, symlinked vs project-specific modules, and dependency direction |
| `testing_philosophy.md` | No-mocks testing policy and representative multi-phase test surfaces |
| `style_guide.md` | Source, script, doc, and error-message conventions |
| `syntax_guide.md` | Markdown, citations, figure refs, and phase-aware token syntax |
| `rendering_pipeline.md` | Manuscript hydration and render sequence across the 11-stage pipeline |
| `output_conventions.md` | What `output/` means and how to regenerate it |
| `output_inventory.md` | Producer/consumer inventory for every generated artifact, including per-phase corpora |
| `forking_guide.md` | Retargeting the exemplar to a new domain and a new phase design |
| `troubleshooting.md` | Common pipeline failures and fixes, including phase-specific failure modes |
| `quickstart.md` | First-run commands |
| `faq.md` | Recurring project questions |

## Why This Project Has Its Own docs/ Hub

`template_advanced_literature_review` is not a copy of `template_literature_meta_analysis` — it shares four modules by symlink (`src/analysis/`, `src/knowledge_graph/`, `src/reproducibility/`, `src/visualization/`, `src/config_loader.py`; see `architecture.md`) but owns a distinct multi-phase search layer (`src/multi_phase/`, `src/literature/multi_phase_search.py`, phase-aware `src/manuscript/variables/`). Documentation that only describes the single-term flow would misrepresent this project's actual control surface (`manuscript/config.yaml` → `project_config.search_phases`). This hub documents the advanced surface on its own terms, per `TODO.md`'s "Documentation and signposting gaps" entry: *"Document multi-phase architecture distinctly from single-term template capabilities."*

## Verification

```bash
uv run pytest projects/templates/template_advanced_literature_review/tests/ \
  --cov=projects/templates/template_advanced_literature_review/src --cov-fail-under=90 -q
uv run python scripts/audit/check_template_drift.py --strict --project templates/template_advanced_literature_review
uv run python scripts/docgen/exemplar_roster.py --check
```

If a numeric or roster-shaped claim drifts, move it to a generator or link `../../../../docs/_generated/COUNTS.md` / `../../../../docs/_generated/active_projects.md`. Do not hardcode corpus sizes, per-phase paper counts, or coverage percentages in this hub — link the generated evidence instead.
