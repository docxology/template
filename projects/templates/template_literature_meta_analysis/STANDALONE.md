# Standalone Fork Guide

## Purpose

`template_literature_meta_analysis` is the canonical **literature meta-analysis**
exemplar: multi-engine retrieval with graceful degradation, record de-duplication,
full-text resolution, descriptive statistics, language/entity analysis, document
embeddings, citation and temporal bibliometrics, an optional knowledge-graph layer,
and an auto-injected manuscript — all deterministic and offline by default
(bundled term: **modafinil**).

## Copy This When

Use it whenever the research object is *a body of literature about a topic*: point
one config key at a search term and get a reproducible, evidence-traceable
meta-analysis whose every manuscript number is computed from committed artifacts.

## Clean Copy Command

From the template repository root:

```bash
uv run python scripts/copy_exemplar.py \
  --source templates/template_literature_meta_analysis \
  --dest projects/working/my_meta_analysis \
  --new-name my_meta_analysis
```

Fallback when the helper is unavailable:

```bash
rsync -a \
  --exclude '.venv/' --exclude '.pytest_cache/' --exclude '.ruff_cache/' \
  --exclude 'htmlcov/' --exclude 'output/' --exclude 'rendered/' --exclude '*.egg-info/' \
  projects/templates/template_literature_meta_analysis/ projects/working/my_meta_analysis/
```

## Required Post-Fork Edits

- Set the topic in `manuscript/config.yaml` → `project_config.search.term` and the
  `query` / `arxiv_queries` / `relevance_keywords` / `subfield_keywords` /
  `hypothesis_definitions` blocks for the new domain.
- Update `CITATION.cff`, `.zenodo.json`, `codemeta.json`, and `pyproject.toml`
  (title, keywords, repository).
- Regenerate the offline seed corpus:
  `uv run python scripts/generate_fixture_corpus.py --term <your_term>`.
- For a live (networked) run, enable engines and supply any optional credentials
  (Unpaywall email, Semantic Scholar key) — every engine degrades to `skipped`
  without them, so the pipeline still completes.

## Validation Commands

From the template repository root after copying into `projects/working/`:

```bash
uv run pytest projects/working/my_meta_analysis/tests/ \
  --cov=projects/working/my_meta_analysis/src --cov-fail-under=90
uv run python projects/working/my_meta_analysis/scripts/generate_fixture_corpus.py
```

For the public exemplar:

```bash
uv run pytest projects/templates/template_literature_meta_analysis/tests/ \
  --cov=projects/templates/template_literature_meta_analysis/src --cov-fail-under=90
```

## Determinism & Offline Default

The committed `data/fixtures/<term>_corpus.jsonl` is **synthetic** (reserved
`10.5555/` test DOIs, generated authors) so CI and a fresh clone exercise the whole
pipeline with no network and byte-identical outputs. Live retrieval replaces it with
real records; only then may you cite real bibliometric findings.

## What Not To Claim

Do not present the synthetic-fixture numbers as empirical findings about the topic.
They demonstrate the machinery; real claims require a live retrieval run plus
regenerated figures, reports, and manuscript variables.
