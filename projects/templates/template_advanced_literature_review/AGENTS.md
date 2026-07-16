# AGENTS.md - template_advanced_literature_review

Advanced multi-phase literature review exemplar for systematic reviews with iterative search refinement, multi-phrase querying, deterministic + LLM-based filtering, and cross-method validation. It demonstrates three configurable search phases (foundation, JWST-era, and molecular detection) over a tracked exoplanet-atmosphere evidence snapshot. The project is designed to be retargeted through `manuscript/config.yaml`; derive corpus counts from generated evidence instead of copying them into prose.

## Ground Truth

| Surface | Source of truth |
| --- | --- |
| Search phases, terms, keywords, hypotheses, subfields | `manuscript/config.yaml` under `project_config` |
| Multi-phase corpus data | `output/data/combined_corpus.jsonl` (tracked evidence snapshot) |
| Phase-aware retrieval/filtering | `src/literature/` and `src/multi_phase/` |
| Bibliometrics, text analytics, embeddings, topics | `src/analysis/` (standalone-safe mirror of the single-term implementation) |
| Knowledge graph extraction and scoring | `src/knowledge_graph/` (standalone-safe mirror of the single-term implementation) |
| Reproducibility assessment | `src/reproducibility/` (standalone-safe mirror of the single-term implementation) |
| Figure styling and generation | `src/visualization/` (standalone-safe mirror of the single-term implementation) |
| Multi-phase manuscript tokens and variables | `src/manuscript/variables/` and `scripts/05_inject_variables.py` |
| Offline deep-research replay | `src/deep_research/dispatch.py` and its tracked fixture |
| Full 11-stage pipeline orchestration | `scripts/01_multi_phase_search.py` through `scripts/11_fulltext_download.py` |
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
| Literature engines | `src/literature/AGENTS.md` | Clients degrade gracefully; drift checks keep the mirror aligned with the single-term template. |
| Bibliometric or NLP metrics | `src/analysis/AGENTS.md` | Pure functions plus runners; copied into standalone exports. |
| Knowledge graph / LLM extraction | `src/knowledge_graph/AGENTS.md` | Optional, resumable, network/LLM gated; copied into standalone exports. |
| Reproducibility scoring | `src/reproducibility/AGENTS.md` | Workflow-graph assessment; copied into standalone exports. |
| Figures and visualization | `src/visualization/AGENTS.md` | Headless matplotlib, colorblind palette; copied into standalone exports. |
| Multi-phase manuscript tokens | `src/manuscript/AGENTS.md` and `manuscript/AGENTS.md` | Phase-aware variables from generated JSON outputs and config. |
| Project scripts (11-stage pipeline) | `scripts/AGENTS.md` | Orchestrators for stages 01-11; dependency order is explicit. |
| Tests | `tests/AGENTS.md` | Real data, temp files, multi-phase fixtures, no mocks. |
| Human docs | `README.md` | Project-local architecture, multi-phase specifics, testing. |

## Regeneration Order

For a live corpus refresh followed by deterministic downstream stages, run from the template repository root:

```bash
uv sync --group scientific --group llm
uv run python projects/templates/template_advanced_literature_review/scripts/01_multi_phase_search.py
uv run python projects/templates/template_advanced_literature_review/scripts/02_meta_analysis_pipeline.py
uv run python projects/templates/template_advanced_literature_review/scripts/03_build_knowledge_graph.py --max-papers 0
uv run python projects/templates/template_advanced_literature_review/scripts/04_generate_figures.py --dpi 300
uv run python projects/templates/template_advanced_literature_review/scripts/06_fulltext_assessment.py
uv run python projects/templates/template_advanced_literature_review/scripts/07_literature_evaluation.py
uv run python projects/templates/template_advanced_literature_review/scripts/08_deep_research_dispatch.py
uv run python projects/templates/template_advanced_literature_review/scripts/09_export_bibliography.py
uv run python projects/templates/template_advanced_literature_review/scripts/05_inject_variables.py
```

Full-text download and reproducibility scoring are explicit network/LLM
enrichments. Run their dependency chain in this order, then reinject the
manuscript variables so the new evidence is visible:

```bash
uv run python projects/templates/template_advanced_literature_review/scripts/11_fulltext_download.py
uv run python projects/templates/template_advanced_literature_review/scripts/10_reproducibility_assessment.py
uv run python projects/templates/template_advanced_literature_review/scripts/05_inject_variables.py
```

Stage 01 (`01_multi_phase_search.py`) is the live/network multi-phase retrieval path with iterative refinement. Use it only when intentionally refreshing the tracked corpus snapshot. Stages 02–09 are the normal deterministic analysis path. Stages 11 and 10 are explicit network/full-text and reproducibility enrichments and must run in that order before rerunning stage 05 variable injection. Stage 01 writes per-phase corpora and `output/data/phase_metadata.json`.

## Verification Commands

```bash
uv run python scripts/pipeline/stage_01_test.py --project templates/template_advanced_literature_review --project-only
uv run python scripts/audit/check_template_drift.py --strict --project templates/template_advanced_literature_review
uv run python scripts/docgen/exemplar_roster.py --check
uv run python scripts/audit/check_tracked_all.py
```

## Multi-Phase Architecture

The advanced template extends the single-term approach with:

- **Phase-based search strategy**: broad foundation (2010+) → JWST-focused work (2020+) → molecular-detection work (2015+), with overlaps preserved in provenance
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
