# AGENTS.md — `scripts/` Directory

## Purpose

Project-specific **thin orchestrator scripts** for the literature meta-analysis pipeline (modafinil literature exemplar). Each script coordinates I/O and sequencing; all computational logic resides in `../src/` modules. Script numbers identify roles; dependency order is declared separately.

## Architecture

```
scripts/
├── _bootstrap.py                 # PYTHONPATH + optional infrastructure root
├── _io.py                        # Shared JSON load/write helpers
├── 01_literature_search.py       # → literature/search_runner.py
├── 02_meta_analysis_pipeline.py  # → analysis/pipeline_runner.py
├── 03_build_knowledge_graph.py   # → knowledge_graph/kg_runner.py
├── 04_generate_figures.py        # → visualization/figure_runner.py
├── 05_inject_variables.py        # → manuscript/variables/
├── 06_fulltext_assessment.py     # → literature/fulltext_assessment.py
├── 07_literature_evaluation.py   # → literature/evaluation.py
├── 08_deep_research_dispatch.py  # → deep_research/deep_research_adapter.py
├── 09_export_bibliography.py     # → literature/bibliography.py
├── 10_reproducibility_assessment.py # → reproducibility/runner.py
├── 11_fulltext_download.py       # → literature/fulltext_download_cli.py
└── __pycache__/                  # Python bytecode cache (gitignored)
```

## Execution Order

Scripts are numbered by role, but numeric order is **not** run order: `05_inject_variables.py`
assembles the final manuscript from every other stage's output (including `06`'s
`fulltext_assessment.json`, which `00_abstract.md` renders unconditionally), so it must run
*last* among the analysis scripts. The default offline order lives in
`manuscript/config.yaml`'s `analysis.scripts` list (`02`, `04`, `06`, `07`, `08`, `09`, then
`05`). Network/LLM-gated scripts `01`, `03`, `10`, and `11` are excluded from that default
allowlist. Run the opt-in producer/consumer chain explicitly as `11` then `10`, and run `05`
again afterward when those optional artifacts must be reflected in the manuscript.

| Script | Inputs | Outputs | Dependencies |
|--------|--------|---------|--------------|
| `01` | API responses | `output/data/corpus.jsonl`, `output/data/retrieval_report.json` | Network / cached corpus; legacy resumes are labelled instead of assigned inferred engine counts |
| `02` | `corpus.jsonl` | `subfield_classification.json`, `temporal_analysis.json`, `tfidf_data.json`, `topics.json`, `citation_network.json`, `citation_graph.gml` | `01` |
| `03` | `corpus.jsonl` | `nanopublications.jsonl`, `nanopublications.trig`, `hypothesis_scores.json`, `hypothesis_trends.json`, `assertion_summary.json` | `01`, Ollama (optional) |
| `04` | All `output/data/*.json`, `citation_graph.gml` | `output/figures/*.png`, `figure_registry.json` | `02`, `03` |
| `06` | `corpus.jsonl` | `fulltext_assessment.json`, `output/fulltext/fulltext_inventory.json` | `01` |
| `07` | `corpus.jsonl` | `output/data/literature_evaluation.json` | `01` |
| `08` | provider config | `deep_research_replay.json` | none |
| `09` | `corpus.jsonl` | `output/data/bibliography.bib` | `01` |
| `11` | `corpus.jsonl` | `output/fulltext/`, `output/data/fulltext_extraction.json` | `01`, network (Unpaywall) |
| `10` | `corpus.jsonl`, `output/fulltext/` | `workflow_graphs.jsonl`, `reproducibility_scores.json`, `reproducibility_summary.json` | `01`, `11` (or manual fulltext), Ollama (optional) |
| `05` | `output/data/*.json` (incl. `06`'s `fulltext_assessment.json`), `manuscript/*.md` | `output/manuscript/*.md` (rendered) | `02`, `03`, `06` |

## Script Details

### `01_literature_search.py`

Multi-source literature search orchestrator.

**APIs queried:** arXiv (default query list in `src/config.py` → `DEFAULT_ARXIV_QUERIES`), Semantic Scholar, OpenAlex, Crossref, PubMed, SovietRxiv, ChinaRxiv, Europe PMC, bioRxiv, and medRxiv (10 engines total). Override via `project_config.search.arxiv_queries` in `manuscript/config.yaml`.

**Key flags:**
- `--resume` / `--no-resume` — load existing `corpus.jsonl` before fetching (default: resume on)
- `--clear-corpus` — delete existing corpus and start fresh
- `--skip-arxiv` / `--skip-s2` / `--skip-openalex` / `--skip-crossref` / `--skip-pubmed` / `--skip-sovietrxiv` / `--skip-chinarxiv` / `--skip-europepmc` / `--skip-biorxiv` / `--skip-medrxiv` — skip individual sources
- `--max-results N` — cap per-source results (default: 1000)
- `--start-year YYYY` — exclude papers before this year
- `--config PATH` — load search settings from YAML

**Relevance filter:** Requires at least one core keyword in title/abstract. Configurable via `search.relevance_keywords` in YAML config.

**Imports from `src/`:** `literature.search_runner.run_literature_search`, which in turn wires
`literature.corpus.Corpus`, `literature.models.Paper`, `literature.query_router.QueryRouter`,
`literature.engine_dispatch.dispatch_ordered`, and all ten engine adapters
(`arxiv_client`, `semantic_scholar`, `openalex_client`, `crossref_client`, `pubmed_client`,
`sovietrxiv_client`, `europepmc_client`, `biorxiv_client`).

### `02_meta_analysis_pipeline.py`

Runs all quantitative analyses: subfield classification, temporal metrics, TF-IDF/NMF topic modeling, and citation network construction with reference normalization.

**Key flags:**
- `--corpus PATH` — path to corpus JSONL
- `--n-topics N` — NMF topic count (default: 5)
- `--max-features N` — TF-IDF vocabulary size (default: 500)
- `--min-year YYYY` — pre-filter (default: 2000)
- `--seed N` — NMF random seed (default: 42)

**Stages:**
1. Subfield classification (keyword-based, config-driven)
2. Per-subfield temporal breakdown
3. Global temporal metrics (CAGR, doubling time, peak year)
4. TF-IDF matrix construction
5. NMF topic decomposition
6. Citation network (reference normalization → graph → metrics → communities)

**Imports from `src/`:** `analysis.text_processing`, `analysis.citation_network`, `analysis.temporal_analysis`, `analysis.subfield_classifier`, `analysis.topic_modeling`.

### `03_build_knowledge_graph.py`

LLM-based assertion extraction and hypothesis scoring via Ollama.

**Incremental by default:** Assertions are appended to `nanopublications.jsonl` at checkpoint intervals. On restart, already-processed papers are skipped automatically.

**Key flags:**
- `--llm-model MODEL` — Ollama model name (default: `gemma3:4b`)
- `--llm-url URL` — Ollama API base URL (default: `http://localhost:11434`)
- `--checkpoint-interval N` — flush every N papers (default: 50)
- `--clear-assertions` — discard previous extraction results
- `--max-papers N` — limit LLM processing (default: no limit)
- `--config PATH` — load KG settings from YAML

**Outputs:** Nanopublications (JSONL + RDF/TriG), hypothesis scores, temporal trends, assertion summary.

**Imports from `src/`:** `knowledge_graph.schema`, `knowledge_graph.nanopublication`, `knowledge_graph.extraction`, `knowledge_graph.llm_extraction`, `knowledge_graph.hypothesis`.

### `04_generate_figures.py`

Generates publication-quality figures from analysis JSON files. The figure count is
**computed dynamically**, not fixed: each figure is emitted only when its source JSON
input is present, and the caption registry (`src/visualization/figure_runner.py` →
`FIGURE_CAPTIONS`) currently defines 21 possible figures. Do not hardcode a figure count
in docs — link this section or the registry instead.

**Figure categories:**
- **Field overview:** `field_summary.png`, `subfield_distribution.png`
- **Temporal:** `growth_curve.png`, `subfield_timeline.png`
- **Citation:** `citation_network.png`, `degree_distribution.png`
- **Hypothesis:** `hypothesis_dashboard.png`, `evidence_timeline.png`
- **Text analytics:** `word_cloud.png`, `topic_term_bars.png`, `pca_embeddings.png`, `term_heatmap.png`, `dendrogram.png`, `cooccurrence_matrix.png`
- **Assertions:** `assertion_breakdown.png`, `assertion_summary.png`

**Key flags:**
- `--dpi N` — output resolution (default: 300)
- `--input-dir PATH` — analysis JSON directory
- `--output-dir PATH` — figure output directory

**Uses:** `infrastructure.documentation.figure_manager.FigureManager` for figure registration, `src/visualization/` modules for all rendering.

### `05_inject_variables.py`

Template variable injection: replaces `{{VAR}}` placeholders in manuscript markdown with computed values from pipeline output.

**Key flags:**
- `--project NAME` — project name (default: `template_literature_meta_analysis`)
- `--dry-run` — show changes without writing

**Process:**
1. Compute variables from `output/data/*.json`
2. Inject into each `.md` file → write rendered copies to `output/manuscript/`
3. Copy non-md support files (config, bib, etc.)
4. Verify no unresolved `{{VAR}}` placeholders remain

**Imports from `src/`:** `manuscript.variables.compute_variables`, `manuscript.variables.inject_variables`.

### `06_fulltext_assessment.py`

Reports full-text and open-access availability across the corpus.

**Key flags:**
- `--corpus PATH` — corpus JSONL path

**Reports:** Abstract coverage, OA status, PDF URL availability, PDF domain breakdown, identifier coverage (DOI, arXiv, S2, OpenAlex), full-text format assessment (LaTeX source vs publisher PDF vs none).

**Imports from `src/`:** `literature.corpus.Corpus`.

### `07_literature_evaluation.py`

Corpus-quality and routing coverage summary for the literature workflow.

**Key flags:**
- `--corpus PATH` — corpus JSONL path
- `--query TEXT` — optional query string for routing diagnostics
- `--output-dir PATH` — output directory for `literature_evaluation.json`
- `--fixture-honesty` — audit `manuscript/*.md` for undisclosed empirical claims on the
  synthetic fixture corpus via `literature.fixture_honesty.validate_fixture_honesty`;
  exits non-zero and logs each finding's `message`/`line_number` on violation

**Reports:** total paper count, DOI coverage, preprint coverage, metadata completeness, duplicate-title groups, source distribution, query routing choice, and optional claim-verification summary.

**Imports from `src/`:** `literature.corpus.Corpus`, `literature.evaluation.evaluate_corpus`, `literature.fixture_honesty.validate_fixture_honesty`.

### `08_deep_research_dispatch.py`

Thin wrapper around `infrastructure.search.deep_research` demonstrating the deep-research
adapter without any network call or API key. By default it replays a recorded report
fixture (deterministic, offline, CI-safe); it also exposes the real provider-neutral
request a live `submit` would dispatch.

**Key flags:**
- `--query TEXT` — query used to build the (real) provider-neutral deep-research request
- `--fixture PATH` — optional explicit recorded-report JSON to replay (defaults to the
  bundled fixture)
- `--output-dir PATH` — output directory for dispatch artifacts

**Imports from `src/`:** `deep_research.deep_research_adapter.build_offline_request`, `deep_research.deep_research_adapter.list_provider_profile`, `deep_research.deep_research_adapter.replay_recorded_report`.

### `09_export_bibliography.py`

Thin wrapper around `literature/bibliography.py`. Exports the literature corpus to a single
unified BibTeX file, deduplicating entries and normalizing citation keys across all ten
engine sources.

**Key flags:**
- `--corpus PATH` — corpus JSONL path (default: `output/data/corpus.jsonl`)
- `--output-dir PATH` — directory for the exported `.bib` file
- `--log-level {DEBUG,INFO,WARNING,ERROR}`

**Imports from `src/`:** `literature.corpus.Corpus`, `literature.bibliography.corpus_to_bibtex`.

### `11_fulltext_download.py`

Opt-in network producer for open-access PDFs and extracted text. It resolves
`project_config.fulltext.download_dir` relative to the project root unless
`--output-dir` explicitly overrides it, so script `10` consumes the same directory.

**Key flags:**
- `--corpus PATH` — corpus JSONL path
- `--output-dir PATH` — explicit full-text directory override
- `--config PATH` — configuration containing `project_config.fulltext`
- `--max-papers N` — cap download attempts

**Imports from `src/`:** `literature.fulltext_download_cli.main`, which owns
configuration resolution, download accounting, and extraction-report persistence.

### `10_reproducibility_assessment.py`

Opt-in LLM consumer for the text produced by script `11`. It extracts workflow
graphs, computes content/structural reproducibility scores, and verifies source
quotes against extracted full text.

**Key flags:**
- `--corpus PATH` — corpus JSONL path
- `--fulltext-dir PATH` — explicit full-text directory override
- `--config PATH` — sampling, full-text, LLM, and scoring configuration
- `--max-papers N` — cap papers after deterministic sampling

**Imports from `src/`:** `reproducibility.runner.run_reproducibility_pipeline`.

## Thin Orchestrator Pattern

**CRITICAL:** These scripts must NOT contain computational logic. They:
- Parse CLI arguments
- Load/save JSON and JSONL files
- Import and call `src/` functions
- Log timing and summary statistics

Violations of this pattern break the architecture and test coverage guarantees.

## Configuration

All scripts support `--log-level {DEBUG,INFO,WARNING,ERROR}` for verbosity control.

Scripts `01`, `02`, `03`, `10`, and `11` accept `--config PATH` (default `manuscript/config.yaml`), which **supplies settings** — search queries, relevance keywords, checkpoint intervals, custom hypothesis definitions, sampling, full-text paths, and scoring settings. Project *discovery* itself is by filesystem convention (a `src/` of Python modules plus `tests/`); `config.yaml` carries metadata and render/search settings, not the discovery predicate.

## Output Directory Structure

```
output/
├── data/
│   ├── corpus.jsonl                  # 01
│   ├── retrieval_report.json         # 01, timestamp-free per-engine outcomes
│   ├── subfield_classification.json  # 02
│   ├── subfield_timeline.json        # 02
│   ├── temporal_analysis.json        # 02
│   ├── tfidf_data.json               # 02
│   ├── topics.json                   # 02
│   ├── citation_network.json         # 02
│   ├── citation_graph.gml            # 02
│   ├── nanopublications.jsonl        # 03
│   ├── nanopublications.trig         # 03
│   ├── hypothesis_scores.json        # 03
│   ├── hypothesis_trends.json        # 03
│   ├── assertion_summary.json        # 03
│   ├── fulltext_assessment.json      # 06
│   ├── literature_evaluation.json    # 07
│   ├── deep_research_replay.json     # 08
│   ├── bibliography.bib              # 09
│   ├── workflow_graphs.jsonl          # 10
│   ├── reproducibility_scores.json    # 10
│   ├── reproducibility_summary.json   # 10
│   └── fulltext_extraction.json       # 11
├── fulltext/                         # 06 inventory + 11 downloads; configurable
│   ├── *.pdf
│   ├── *.txt
│   ├── fulltext_inventory.json       # declared license/provider fields + local PDF SHA-256
│   └── figures/
├── figures/                          # 04
│   ├── *.png (count computed dynamically from available inputs — see caption registry)
│   └── figure_registry.json
└── manuscript/                       # 05
    └── *.md (rendered with variables)
```
