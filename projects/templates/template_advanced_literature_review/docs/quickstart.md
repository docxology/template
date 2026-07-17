# Quick Start Guide

Get up and running with the `template_advanced_literature_review` exemplar in ~5 minutes. This template runs a **three-phase** systematic literature review — each phase has its own query set, engine selection, and temporal filter — then merges the phases into one corpus and runs the same analysis/knowledge-graph/visualization stack as the single-term sibling. The bundled default domain is **exoplanet atmospheric composition**, phased as foundation (2010+) → JWST era (2020+) → molecular detection (2015+).

## Prerequisites

- Python 3.10 or higher
- [`uv`](https://github.com/astral-sh/uv) package manager (repo invariant — see the root `CLAUDE.md`)
- Git
- Network access only if you intend to run `01_multi_phase_search.py` live; the default offline pipeline replays a tracked corpus snapshot
- *(Optional)* a local [Ollama](https://ollama.com) server with `gemma3:4b` for the knowledge-graph and reproducibility stages

## Setup (One-Time)

```bash
git clone https://github.com/docxology/template.git
cd template
uv sync --group scientific --group llm
uv run python --version
```

## Run the Test Suite

```bash
uv run pytest projects/templates/template_advanced_literature_review/tests/ -v --tb=short
```

Expected: a passing suite at ≥90% coverage of `src/`. Live collection counts are tracked in
[`../../../../docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md).

## The Single Control Surface

Everything phase-related is driven by [`manuscript/config.yaml`](../manuscript/config.yaml) →
`project_config.search_phases`. The bundled defaults:

```yaml
project_config:
  search_phases:
    phase_1_foundation:
      queries: ['"exoplanet atmosphere" OR "exoplanet atmospheric"', ...]
      engines: { arxiv: true, openalex: true, semantic_scholar: true, crossref: true }
      deterministic_filters: { min_year: 2010, max_year: 2026, min_citation_count: 0 }
    phase_2_jwst:
      deterministic_filters: { min_year: 2020, max_year: 2026 }
      depends_on: ["phase_1_foundation"]
    phase_3_molecules:
      deterministic_filters: { min_year: 2015, max_year: 2026 }
      depends_on: ["phase_1_foundation", "phase_2_jwst"]
```

To review a different domain, edit each phase's `queries`, `deterministic_filters`, and the
top-level `llm_filters` / `phase_integration.quality_gates` blocks — see `forking_guide.md`.

## Execute the Pipeline

Run from the template repository root:

```bash
# Stage 1 — Phase-aware search: writes per-phase corpora + combined_corpus.jsonl.
# Live/network path — only run when intentionally refreshing the tracked snapshot.
uv run python projects/templates/template_advanced_literature_review/scripts/01_multi_phase_search.py

# Stage 2 — Meta-analysis over the combined corpus (subfields, temporal growth, TF-IDF,
# NMF topics, citation network)
uv run python projects/templates/template_advanced_literature_review/scripts/02_meta_analysis_pipeline.py

# Stage 3 — (Optional) Knowledge graph + phase-aware hypothesis scoring. Requires Ollama.
uv run python projects/templates/template_advanced_literature_review/scripts/03_build_knowledge_graph.py --max-papers 0

# Stage 4 — Render publication-grade figures (PNG)
uv run python projects/templates/template_advanced_literature_review/scripts/04_generate_figures.py --dpi 300

# Stage 5 — Inject computed (including phase-aware) variables into the manuscript Markdown
uv run python projects/templates/template_advanced_literature_review/scripts/05_inject_variables.py
```

See `rendering_pipeline.md` for the full 11-stage sequence, including the optional
full-text/reproducibility enrichment stages (10, 11) and the offline deep-research
replay (08).

## Outputs

**Under `projects/templates/template_advanced_literature_review/output/`:**
- `data/phase_1_foundation_corpus.jsonl`, `phase_2_jwst_corpus.jsonl`, `phase_3_molecules_corpus.jsonl` — per-phase corpora
- `data/combined_corpus.jsonl`, `data/phase_metadata.json` — merged corpus and phase provenance
- `data/*.json` — the same analysis/knowledge-graph artifact family as the single-term sibling (see `output_inventory.md`)
- `figures/*.png` — publication figures, including `hypothesis_dashboard.png`

## Render the Publication PDF

Run this one **from the repository root**:

```bash
uv run python scripts/pipeline/stage_03_render.py --project templates/template_advanced_literature_review
```

Final PDF: `projects/templates/template_advanced_literature_review/output/pdf/template_advanced_literature_review_combined.pdf`

## Getting Help

- **Full documentation**: [`docs/README.md`](README.md) — navigation hub
- **Architecture**: [`docs/architecture.md`](architecture.md)
- **Agent rules**: [`docs/agent_instructions.md`](agent_instructions.md)
- **Troubleshooting**: [`docs/troubleshooting.md`](troubleshooting.md)
- **FAQ**: [`docs/faq.md`](faq.md)

## Quick Command Reference

| Task | Command |
|---|---|
| Run tests | `uv run pytest projects/templates/template_advanced_literature_review/tests/ -v` |
| Multi-phase search (live) | `uv run python scripts/01_multi_phase_search.py` |
| Meta-analysis | `uv run python scripts/02_meta_analysis_pipeline.py` |
| Knowledge graph (optional, Ollama) | `uv run python scripts/03_build_knowledge_graph.py --max-papers 0` |
| Generate figures | `uv run python scripts/04_generate_figures.py --dpi 300` |
| Inject manuscript variables | `uv run python scripts/05_inject_variables.py` |
| Render PDF | `uv run python scripts/pipeline/stage_03_render.py --project templates/template_advanced_literature_review` |
| Clean outputs | `rm -rf projects/templates/template_advanced_literature_review/output/` |
