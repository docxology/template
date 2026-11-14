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

Use the [single prepared corpus/replay recipe](../STANDALONE.md#multi-phase-corpus)
and [README provider order](../README.md#dependencies). A clean export omits
`output/`, so explicitly generate its synthetic fixture before replay. The
project's prepared own interpreter runs the numbered producers; Stage 01 admits
prepared runtimes and does not provision dependencies. See
[quickstart](quickstart.md) for the offline producer order and
[rendering pipeline](rendering_pipeline.md) for the separate repository render handoff.

Live test counts and coverage snapshots belong in `../../../../docs/_generated/COUNTS.md`; do not duplicate them here.

## Boundary Summary

- `manuscript/config.yaml` → `project_config.search_phases` owns the phase design: query sets, engines, deterministic filters, and `depends_on` ordering for each phase.
- `manuscript/config.yaml` → `project_config.llm_filters` and `project_config.phase_integration` own LLM-based content filtering and cross-phase deduplication/validation/quality-gate policy.
- `src/multi_phase/` owns phase-aware search orchestration and provenance.
- `src/literature/` owns per-engine retrieval clients, the canonical `Paper` model, and corpus persistence — the same contracts as the single-term sibling.
- Shared analysis, knowledge-graph, reproducibility and figure methods come from the declared `template_literature_meta_analysis` distribution. Edit those methods in Meta's canonical `src/` and verify both consumers; Advanced owns its configuration loader. See `architecture.md` and `../STANDALONE.md` for the provider boundary.
- `src/manuscript/variables/` owns phase-aware `{{TOKEN}}` computation (`extractors/multi_phase.py` in particular).
- `src/deep_research/` owns the deterministic offline replay of the optional deep-research dispatch stage.
- `scripts/` (11 numbered stages) are thin orchestrators only.

Generated `output/` files can be tracked as a guarded public snapshot below the
size ceiling. The default corpus is synthetic; neither tracking nor regeneration
promotes it to live scientific evidence. Fix producers, never hand-edit outputs.
