# AGENTS.md - template_advanced_literature_review

Advanced multi-phase literature review exemplar for systematic reviews with iterative search refinement, multi-phrase querying, deterministic + LLM-based filtering, and cross-method validation. Features 3 search phases (foundation, JWST-era, molecular detection) with 2505 real exoplanet papers, 11-stage pipeline, and comprehensive knowledge graph extraction. The bundled corpus targets **exoplanet atmospheric composition**, but the project is designed to be retargeted through `manuscript/config.yaml` and phase configuration.

## Ground Truth

| Surface | Source of truth |
| --- | --- |
| Search phases, terms, keywords, hypotheses, subfields | `manuscript/config.yaml` under `project_config` |
| Multi-phase corpus data | `data/fixtures/exoplanet_corpus_phases.jsonl` |
| Phase-aware retrieval/filtering | `src/literature/` and `src/multi_phase/` |
| Bibliometrics, text analytics, embeddings, topics | `src/analysis/` (symlinked to single-term template) |
| Knowledge graph extraction and scoring | `src/knowledge_graph/` (symlinked to single-term template) |
| Reproducibility assessment | `src/reproducibility/` (symlinked to single-term template) |
| Figure styling and generation | `src/visualization/` (symlinked to single-term template) |
| Multi-phase manuscript tokens and variables | `src/manuscript/variables/` and `scripts/05_inject_variables.py` |
| Full 11-stage pipeline orchestration | `scripts/01_multi_phase_search.py` through `scripts/11_validate_outputs.py` |
| Open follow-up scope | `TODO.md` |
| Live public roster/count facts | `../../../docs/_generated/active_projects.md` and `../../../docs/_generated/COUNTS.md` |

Generated `output/` files are regenerable; this canonical public exemplar tracks
its current evidence snapshot. Never hand-edit `output/manuscript/`,
`output/data/`, or `output/figures/`; edit `manuscript/`, `src/`, `scripts/`,
or config and regenerate.

## Where To Look

| Task | Start here | Notes |
| --- | --- | --- |
| Retarget the review topic | `manuscript/config.yaml` | Change phase definitions, queries, keywords, hypotheses, and subfields together. |
| Multi-phase search configuration | `src/multi_phase/AGENTS.md` | Phase-aware search with iterative refinement and filtering. |
| Literature engines | `src/literature/AGENTS.md` (symlinked) | Clients degrade gracefully; shared with single-term template. |
| Bibliometric or NLP metrics | `src/analysis/AGENTS.md` (symlinked) | Pure functions plus runners; shared with single-term template. |
| Knowledge graph / LLM extraction | `src/knowledge_graph/AGENTS.md` (symlinked) | Optional, resumable, network/LLM gated; shared with single-term template. |
| Reproducibility scoring | `src/reproducibility/AGENTS.md` (symlinked) | Workflow-graph assessment; shared with single-term template. |
| Figures and visualization | `src/visualization/AGENTS.md` (symlinked) | Headless matplotlib, colorblind palette; shared with single-term template. |
| Multi-phase manuscript tokens | `src/manuscript/AGENTS.md` and `manuscript/AGENTS.md` | Phase-aware variables from generated JSON outputs and config. |
| Project scripts (11-stage pipeline) | `scripts/AGENTS.md` | Orchestrators for stages 01-11; dependency order is explicit. |
| Tests | `tests/AGENTS.md` | Real data, temp files, multi-phase fixtures, no mocks. |
| Human docs | `docs/README.md` | Project-local architecture, multi-phase specifics, testing. |

## Regeneration Order

For the deterministic offline path from the template repository root:

```bash
uv sync --group scientific --group llm
uv run python projects/templates/template_advanced_literature_review/scripts/01_multi_phase_search.py --offline
uv run python projects/templates/template_advanced_literature_review/scripts/02_filter_and_classify.py
uv run python projects/templates/template_advanced_literature_review/scripts/03_build_knowledge_graph.py --max-papers 0
uv run python projects/templates/template_advanced_literature_review/scripts/04_generate_figures.py --dpi 300
uv run python projects/templates/template_advanced_literature_review/scripts/05_inject_variables.py
uv run python projects/templates/template_advanced_literature_review/scripts/06_fulltext_assessment.py
uv run python projects/templates/template_advanced_literature_review/scripts/07_literature_evaluation.py
uv run python projects/templates/template_advanced_literature_review/scripts/08_deep_research_dispatch.py
uv run python projects/templates/template_advanced_literature_review/scripts/09_export_bibliography.py
uv run python projects/templates/template_advanced_literature_review/scripts/10_reproducibility_assessment.py
uv run python projects/templates/template_advanced_literature_review/scripts/11_validate_outputs.py
```

Stage 01 (`01_multi_phase_search.py`) is the live/network multi-phase retrieval path with iterative refinement. Use it only when intentionally refreshing the corpus from engines. The `--offline` flag uses the bundled fixture corpus. Each phase writes provenance and filtering metadata to `output/data/phase_X_report.json`.

## Verification Commands

```bash
uv run python scripts/pipeline/stage_01_test.py --project templates/template_advanced_literature_review --project-only
uv run python scripts/audit/check_template_drift.py --strict --project templates/template_advanced_literature_review
uv run python scripts/docgen/exemplar_roster.py --check
uv run python scripts/audit/check_tracked_all.py
```

## Multi-Phase Architecture

The advanced template extends the single-term approach with:

- **Phase-based search strategy**: Foundation (pre-2010) → JWST-era (2010-2021) → Molecular detection (2022+)
- **Iterative filtering**: Each phase applies deterministic (year, venue, citation) and LLM-based (abstract content) filters
- **Cross-phase validation**: Papers from later phases validate/extend findings from earlier phases
- **Enhanced variable extraction**: Phase-aware manuscript variables including per-phase statistics
- **Consolidated knowledge graph**: All phases contribute to unified RDF nanopublications

## Contracts

- Keep `src/` as project business logic. Scripts orchestrate I/O, config loading, logging, and stage sequencing only.
- Keep source modules standalone-friendly. Infrastructure imports are allowed only behind documented fallbacks or in script/orchestration glue.
- Keep tests real: no `unittest.mock`, `MagicMock`, `mocker.patch`, or call-count-only assertions.
- Keep stochastic analysis deterministic with explicit seeds (`42` unless a config field says otherwise).
- Treat the committed fixture as synthetic demonstration data. Do not turn fixture-derived exoplanet numbers into empirical claims.
- Link generated repo facts instead of copying counts or public rosters into prose.
- Preserve multi-phase provenance throughout the pipeline: each stage tracks which phase contributed which papers.

Decision memory and verifier hardening follow [`../../../docs/rules/memory_and_decision_records.md`](../../../docs/rules/memory_and_decision_records.md): use nearby `WHY:` comments only for surprising local choices, keep volatile counts generated, and add negative controls for verifier-like gates.

## Agent skill

A Hermes/agentskills.io-compatible skill for this exemplar lives at
[`.agents/skills/template-advanced-literature-review/SKILL.md`](.agents/skills/template-advanced-literature-review/SKILL.md).
Load it when working inside this template to get when-to-use guidance,
quick reference commands, and pitfalls.

# Publishing

- [Publishing guide](../../../docs/guides/publishing-guide.md) · [Publishing module reference](../../../infrastructure/publishing/README.md) · [Zenodo DOI strategy](../../../docs/guides/zenodo-doi-strategy.md) · [Archival targets](../../../docs/maintenance/archival-targets.md)