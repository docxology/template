# AGENTS.md - template_literature_meta_analysis

Public literature meta-analysis exemplar for systematic/scoping reviews, bibliometrics, corpus NLP, optional knowledge-graph extraction, and manuscript variable injection. The bundled offline fixture targets `modafinil`, but the project is designed to be retargeted from `manuscript/config.yaml` without changing source code.

## Ground Truth

| Surface | Source of truth |
| --- | --- |
| Search term, engines, keywords, hypotheses, subfields | `manuscript/config.yaml` under `project_config` |
| Offline corpus fixture | `data/fixtures/modafinil_corpus.jsonl` |
| Retrieval/de-duplication | `src/literature/` |
| Bibliometrics, text analytics, embeddings, topics | `src/analysis/` |
| Optional assertion extraction and nanopublications | `src/knowledge_graph/` |
| Figure styling and generation | `src/visualization/` |
| Manuscript tokens and hydrated copies | `src/manuscript/variables/` and `scripts/05_inject_variables.py`, `scripts/06_fulltext_assessment.py`, `scripts/07_literature_evaluation.py`, `scripts/08_deep_research_dispatch.py` |
| Open follow-up scope | `TODO.md` |
| Live public roster/count facts | `../../../docs/_generated/active_projects.md` and `../../../docs/_generated/COUNTS.md` |

Generated `output/` files are disposable. Do not hand-edit `output/manuscript/`, `output/data/`, or `output/figures/`; edit `manuscript/`, `src/`, `scripts/`, or config and regenerate.

## Where To Look

| Task | Start here | Notes |
| --- | --- | --- |
| Retarget the review topic | `manuscript/config.yaml` | Change `project_config.search.term`, query blocks, relevance keywords, subfields, and hypotheses together. |
| Retrieval engines | `src/literature/AGENTS.md` | Clients degrade to `skipped` without network/keys; tests use `pytest-httpserver`. |
| Bibliometric or NLP metrics | `src/analysis/AGENTS.md` | Pure functions plus runner helpers; keep I/O in scripts or runner boundaries. |
| Knowledge graph / LLM extraction | `src/knowledge_graph/AGENTS.md` | Optional, resumable, and network/local-LLM gated. |
| Figures | `src/visualization/AGENTS.md` | Headless matplotlib, colorblind palette, CLI DPI propagation. |
| Manuscript tokens | `src/manuscript/AGENTS.md` and `manuscript/AGENTS.md` | Variables come from generated JSON outputs and config. |
| Project scripts | `scripts/AGENTS.md` | Thin orchestrators for stages 01-08. |
| Tests | `tests/AGENTS.md` | Real data, temp files, local HTTP servers, no mocks. |
| Human docs | `docs/README.md` | Project-local architecture, testing, style, and output docs. |

## Regeneration Order

For the deterministic offline path from the template repository root:

```bash
uv sync --group scientific --group llm
uv run python projects/templates/template_literature_meta_analysis/scripts/generate_fixture_corpus.py
uv run python projects/templates/template_literature_meta_analysis/scripts/02_meta_analysis_pipeline.py
uv run python projects/templates/template_literature_meta_analysis/scripts/03_build_knowledge_graph.py --max-papers 0
uv run python projects/templates/template_literature_meta_analysis/scripts/04_generate_figures.py --dpi 300
uv run python projects/templates/template_literature_meta_analysis/scripts/05_inject_variables.py
```

Stage 01 (`01_literature_search.py`) is the live/network retrieval path. Use it only when intentionally refreshing the corpus from engines configured in `manuscript/config.yaml`.

## Verification Commands

```bash
uv run pytest projects/templates/template_literature_meta_analysis/tests/   --cov=projects/templates/template_literature_meta_analysis/src --cov-fail-under=90
uv run python scripts/check_template_drift.py --strict --project templates/template_literature_meta_analysis
uv run python scripts/generate_exemplar_roster_doc.py --check
uv run python scripts/check_tracked_projects.py
```

Run the focused stage tests for the part you changed. For broad source/doc changes, run the project coverage gate plus the repo public-scope drift and guard checks.

## Contracts

- Keep `src/` as project business logic. Scripts orchestrate I/O, config loading, logging, and stage sequencing only.
- Keep source modules standalone-friendly. Infrastructure imports are allowed only behind documented fallbacks or in script/orchestration glue.
- Keep tests real: no `unittest.mock`, `MagicMock`, `mocker.patch`, or call-count-only assertions.
- Keep stochastic analysis deterministic with explicit seeds (`42` unless a config field says otherwise).
- Treat the committed fixture as synthetic demonstration data. Do not turn fixture-derived modafinil numbers into empirical claims.
- Link generated repo facts instead of copying counts or public rosters into prose.

Decision memory and verifier hardening follow [`../../../docs/rules/memory_and_decision_records.md`](../../../docs/rules/memory_and_decision_records.md): use nearby `WHY:` comments only for surprising local choices, keep volatile counts generated, and add negative controls for verifier-like gates.

#
## Agent skill

A Hermes/agentskills.io-compatible skill for this exemplar lives at
[`.agents/skills/template-literature-meta-analysis/SKILL.md`](.agents/skills/template-literature-meta-analysis/SKILL.md).
Load it when working inside this template to get when-to-use guidance,
quick reference commands, and pitfalls.

# Publishing

- [Publishing guide](../../../docs/guides/publishing-guide.md) · [Publishing module reference](../../../infrastructure/publishing/README.md) · [Zenodo DOI strategy](../../../docs/guides/zenodo-doi-strategy.md) · [Archival targets](../../../docs/maintenance/archival-targets.md)
