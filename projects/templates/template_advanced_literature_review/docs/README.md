# Advanced Literature Review Docs

Project-local rulebook for `template_advanced_literature_review`, a retargetable **multi-phase** literature review exemplar. For a single-term review without phased comparison, see the sibling `template_literature_meta_analysis`.

## Start Here

| Need | Read |
| --- | --- |
| Modify source or scripts | `agent_instructions.md`, then `architecture.md` |
| Add or change tests | `testing_philosophy.md` |
| Change manuscript tokens or PDF output | `rendering_pipeline.md` and `syntax_guide.md` |
| Add generated artifacts | `output_inventory.md` and `output_conventions.md` |
| Fork to a new review topic or phase design | `forking_guide.md` |
| Diagnose a failure | `troubleshooting.md` |

## Canonical Commands

```bash
uv sync --group scientific --group llm

uv run pytest projects/templates/template_advanced_literature_review/tests/ \
  --cov=projects/templates/template_advanced_literature_review/src --cov-fail-under=90 -q

uv run python projects/templates/template_advanced_literature_review/scripts/01_multi_phase_search.py
uv run python projects/templates/template_advanced_literature_review/scripts/02_meta_analysis_pipeline.py
uv run python projects/templates/template_advanced_literature_review/scripts/04_generate_figures.py --dpi 300
uv run python projects/templates/template_advanced_literature_review/scripts/05_inject_variables.py
```

Live test counts and coverage snapshots belong in `../../../../docs/_generated/COUNTS.md`; do not duplicate them here.

## Boundary Summary

- `manuscript/config.yaml` → `project_config.search_phases` owns the phase design: query sets, engines, deterministic filters, and `depends_on` ordering for each phase.
- `manuscript/config.yaml` → `project_config.llm_filters` and `project_config.phase_integration` own LLM-based content filtering and cross-phase deduplication/validation/quality-gate policy.
- `src/multi_phase/` and `src/literature/multi_phase_search.py` own phase-aware search orchestration and provenance.
- `src/literature/` (minus `multi_phase_search.py`) owns per-engine retrieval clients, the canonical `Paper` model, and corpus persistence — the same contracts as the single-term sibling.
- `src/analysis/`, `src/knowledge_graph/`, `src/reproducibility/`, `src/visualization/`, `src/config_loader.py` are **symlinks** into `template_literature_meta_analysis/src/` — see `architecture.md`. Edit them there, not here.
- `src/manuscript/variables/` owns phase-aware `{{TOKEN}}` computation (`extractors/multi_phase.py` in particular).
- `src/deep_research/` owns the deterministic offline replay of the optional deep-research dispatch stage.
- `scripts/` (11 numbered stages) are thin orchestrators only.

Generated `output/` files are tracked as the current evidence snapshot when they stay below the public output ceiling; regenerate them from source rather than editing them by hand.
