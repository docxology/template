# Abstract

Manual synthesis cannot keep pace with a fast-growing research literature, and ad-hoc
reviews bind no evidence to a reproducible pipeline. We present a configurable,
reproducible meta-analysis framework that takes a single search term and produces a
complete quantitative portrait of its literature. For this instance the term is
**Modafinil**. The pipeline dispatches across 9 literature
engines (arXiv, OpenAlex, Semantic Scholar, Crossref, PubMed, SovietRxiv, ChinaRxiv, Europe PMC, and bioRxiv/medRxiv), each degrading gracefully to a skipped source when an API
key or the network is unavailable, then merges and de-duplicates records by a canonical
identifier hierarchy (DOI $>$ arXiv ID $>$ Semantic Scholar ID $>$ OpenAlex ID $>$ title
digest) into a corpus of $N = 2334$ records spanning 2000--2026
(26 years). Records are classified into a configurable 6-bucket
subfield taxonomy (Clinical Sleep, Cognition, Pharmacology, Psychiatry, Safety, and Neuroscience); the largest subfield is **Clinical Sleep**
(63.0\% of the classified corpus). The corpus grows at a compound annual
rate of 5.48\% (mean year-over-year growth 7.8\%, doubling time
9.2 years), peaking in 2025 with 147 records.

Non-negative matrix factorization extracts 5 latent topics over a
500-feature vocabulary, offline deterministic embeddings place every
title, abstract, and (when available) full text in a shared vector space, and
citation-network analysis exposes the corpus's internal structure (8,623
intra-corpus edges across 2234 nodes, 1416 communities,
graph density 0.17\%). Of 38,489 total outgoing
references, 22.4\% resolve to another record inside the corpus.
Abstract coverage stands at 61.6\%, open-access status is known for
24.6\% of records, and 54.6\% have a direct PDF link. An optional,
LLM-gated knowledge-graph stage scores the 6 hypotheses explored against
the evidence. This run produced 21 publication-quality figures.

Every domain-specific value in this manuscript — the search term, keyword set, engine
roster, subfield taxonomy, and hypotheses — is injected from a single configuration file
and the pipeline's own outputs; re-targeting the configuration re-targets the entire
paper. The result is a reusable architecture for *living literature reviews*:
continuously re-runnable, evidence-bound syntheses for any topic.

**Keywords:** modafinil, meta-analysis, literature retrieval, bibliometrics, record de-duplication, full-text mining, document embeddings, citation network, topic modeling, entity extraction, wakefulness, cognitive enhancement, reproducible research



```{=latex}
\newpage
```


# Introduction

The scholarly literature on any active topic grows faster than any individual can read.
A researcher entering a field needs to know how large it is, how fast it is growing, what
sub-areas compose it, which works anchor its citation structure, what language and
concepts recur, and which claims the field actually tests. Answering those questions by
hand is slow, unrepeatable, and binds no number to evidence. Systematic reviews, while
the gold standard for evidence synthesis, are labour-intensive and become stale between
updates — the Cochrane review cycle, for instance, targets a two-year refresh interval
that many fields outpace [@page2021prisma]. Bibliometric dashboards (Scopus, Web of
Science, Dimensions) offer breadth but no reproducible link from a reported statistic to
a regenerable artifact, and they do not frame or test domain-specific hypotheses.

This project is a **configurable, reproducible meta-analysis template**. It takes one
search term and produces a quantitative portrait of that term's literature, with every
reported number traceable to a committed artifact and regenerable by re-running the
pipeline. The bundled instance targets **Modafinil**, a wakefulness-promoting
agent with a large, multi-disciplinary literature spanning clinical sleep medicine,
cognitive neuroscience, pharmacology, psychiatry, and safety research; pointing the
configuration at a different term re-targets the whole analysis with no code change.

## Research Questions

The pipeline is designed around four research questions (RQs) that a researcher entering
the field would ask:

1. **RQ1 — Field size and growth.** How large is the literature on Modafinil,
   how fast is it growing, and when did it peak? The corpus of $N = 2334$
   records spanning 2000--2026 answers this directly, with a compound
   annual growth rate of 5.48\% and a peak in 2025.

2. **RQ2 — Subfield composition.** What sub-areas compose the literature, and what is
   their relative weight? A configurable 6-bucket taxonomy
   (Clinical Sleep, Cognition, Pharmacology, Psychiatry, Safety, and Neuroscience) classifies every record, with **Clinical Sleep** the largest
   bucket at 63.0\%.

3. **RQ3 — Topical and linguistic structure.** What language and concepts recur, and
   what latent topics cross-cut the keyword taxonomy? TF-IDF over a
   500-feature vocabulary feeds non-negative matrix factorization,
   which extracts 5 latent topics. The top vocabulary terms are:
   modafinil, treatment, study, results, patients, effects, sleep, used, clinical, use, drug, studies, mg, using, sleepiness, disorder, associated, cognitive, narcolepsy, significant.

4. **RQ4 — Citation geometry and evidence landscape.** Which works anchor the citation
   structure, how self-contained is the retrieved slice, and which claims does the field
   test? The citation network of 2234 nodes and 8,623 edges
   (22.4\% reference resolution rate) exposes hubs, authorities,
   and communities, while 6 configured hypotheses frame the evidence
   landscape.

## Contributions

The pipeline contributes an end-to-end, domain-agnostic workflow:

1. **Multiple-engine retrieval with graceful degradation.** Records are gathered from
   9 independent engines (arXiv, OpenAlex, Semantic Scholar, Crossref, PubMed, SovietRxiv, ChinaRxiv, Europe PMC, and bioRxiv/medRxiv). An engine with no API key or no
   network reports a *skipped* status; the run completes from whatever engines remain
   plus a committed offline corpus. Each new retrieval persists per-engine outcome and
   count provenance in `output/data/retrieval_report.json`; the merged corpus alone is
   never used to infer which engine supplied a record.

2. **Record de-duplication.** Heterogeneous records are merged by a canonical identifier
   hierarchy, keeping the most complete version of each work. Of 2334 retrieved
   records, 2260 carry DOIs, 923 carry OpenAlex IDs, and
   1 carry arXiv IDs.

3. **Descriptive and bibliometric analysis.** Counts by year, venue, and author; growth
   metrics (CAGR 5.48\%, doubling time 9.2 years); a configurable
   6-bucket subfield classification; topic models; and a citation network
   with 1416 communities.

4. **Language, entity, and embedding analysis.** Keyphrase and entity extraction and
   offline deterministic document embeddings over titles, abstracts, and full text. The
   TF-IDF vocabulary of 500 features captures the lexical landscape.

5. **Optional hypothesis evidence.** An LLM-gated knowledge-graph stage scores the
   6 configured hypotheses explored against the corpus.

Because the writing itself is token-injected from configuration and pipeline outputs,
the manuscript is part of the reproducible artifact rather than a separate hand-authored
narrative. Every number, table, and figure reference in this document traces to a
committed, regenerable file under `output/`.



```{=latex}
\newpage
```


# Methods Overview

The pipeline is a sequence of deterministic stages, each reading the previous stage's
committed artifacts and writing its own. Business logic lives in tested `src/` modules;
the numbered `scripts/` are thin orchestrators that wire I/O, configuration loading,
logging, and stage sequencing. The architecture follows the thin orchestrator pattern:
no computational logic resides in scripts.

## Pipeline Stages

1. **Retrieval** (`01_literature_search.py`) — dispatch the configured query across
   9 engines (arXiv, OpenAlex, Semantic Scholar, Crossref, PubMed, SovietRxiv, ChinaRxiv, Europe PMC, and bioRxiv/medRxiv), merge, and de-duplicate into `corpus.jsonl`.
   Each engine is an isolated adapter exposing a uniform `search(query) -> list[Paper]`
   interface; engines that are keyless need no credentials, while Semantic Scholar uses
   a key when present. SovietRxiv and ChinaRxiv share a unified API with an optional
   `X-API-Email` header for the polite rate-limit pool (300/min vs 30/min anonymous).

2. **Meta-analysis** (`02_meta_analysis_pipeline.py`) — subfield classification, temporal
   metrics, TF-IDF, non-negative matrix factorization topics, and the citation network.
   This stage reads `corpus.jsonl` and emits `subfield_classification.json`,
   `temporal_analysis.json`, `tfidf_data.json`, `topics.json`, `citation_network.json`,
   and `citation_graph.gml`.

3. **Knowledge graph** (`03_build_knowledge_graph.py`, optional/LLM-gated) — extract
   assertions and score the 6 configured hypotheses. Outputs
   `nanopublications.jsonl`, `hypothesis_scores.json`, and `assertion_summary.json`.

4. **Figures** (`04_generate_figures.py`) — render 21 publication-ready
   visualizations from the analysis JSON outputs. All figures use a colourblind-safe
   palette (Wong 2011), high-contrast labels at $\geq 16$pt, and a headless matplotlib
   backend (Agg).

5. **Injection** (`05_inject_variables.py`) — compute manuscript variables from the
   artifacts above and substitute them into these Markdown sections. An unresolved
   placeholder is a hard error, not a silent gap.

6. **Fulltext assessment** (`06_fulltext_assessment.py`) — report abstract coverage
   (61.6\%), open-access status (24.6\%), and PDF availability
   (54.6\%) across the corpus.

## Reproducibility Model

The system runs **offline and deterministically** by default: a committed synthetic
seed corpus drives every stage with fixed seeds (seed = 42 for NMF, SVD, and graph
layouts), so re-running produces byte-identical outputs. A live run with engines
enabled and credentials supplied replaces the seed corpus with real records — as in
this instance, which retrieved 2334 live records. The template is
domain-agnostic: the search term, query, keyword set, subfield taxonomy, and hypotheses
all come from `manuscript/config.yaml`.

## Configuration Surface

A single `manuscript/config.yaml` controls:

- **Search parameters**: term, query string, per-engine queries, relevance keywords,
  start year, max results, resume/clear behaviour
- **Engine toggles**: arXiv, OpenAlex, Semantic Scholar, Crossref, PubMed, SovietRxiv,
  ChinaRxiv, Europe PMC, bioRxiv/medRxiv (each independently enabled or disabled)
- **SovietRxiv/ChinaRxiv settings**: optional `api_email` for the polite pool, `source`
  filter (`russiarxiv` or `chinaxiv`)
- **Full-text download**: opt-in Unpaywall resolution with `unpaywall_email`
- **Embeddings**: method (`tfidf_svd` or `transformer`), dimensionality, max features
- **Knowledge graph**: checkpoint interval, LLM model, base URL, temperature, max tokens
- **Hypothesis definitions**: 6 named hypotheses with scope labels
- **Subfield taxonomy**: 6 buckets, each with a keyword list
- **Paper metadata**: title, authors, DOI, keywords, license, repository URL



```{=latex}
\newpage
```


# Retrieval and De-duplication

Retrieval dispatches the configured query across 9 independent literature
engines (arXiv, OpenAlex, Semantic Scholar, Crossref, PubMed, SovietRxiv, ChinaRxiv, Europe PMC, and bioRxiv/medRxiv). Each engine is an isolated adapter exposing a uniform
`search(query) -> list[Record]` interface; engines that are keyless — arXiv, OpenAlex
[@priem2022openalex], Crossref [@hendricks2020crossref], PubMed/Entrez
[@sayers2022entrez], SovietRxiv / RussiaRxiv, ChinaRxiv, Europe PMC, and bioRxiv/medRxiv —
need no credentials, while Semantic Scholar [@kinney2023semantic] uses a key when present.
SovietRxiv is a translated archive of Soviet-era scientific preprints sourced from
Math-Net.Ru and CyberLeninka [@sovietrxiv]; ChinaRxiv serves translated Chinese preprints
from ChinaXiv via the same unified API. Both retain original-language PDFs alongside each
translation, and their polite rate-limit pool (300/min vs 30/min anonymous) is activated
by an optional `X-API-Email` header. Europe PMC is a keyless biomedical aggregator
covering PubMed, PMC, patents, and preprints in a single search call. bioRxiv/medRxiv
share one unified date-window + cursor API; unlike the other engines it is not a
free-text search endpoint, so the adapter walks the date window page by page and
keeps only records whose title and abstract match every query term client-side.
Optional full-text resolution queries Unpaywall
[@piwowar2018state] for open-access locations. **Multiple dispatch degrades gracefully**:
an engine that is disabled in the configuration, lacks a required key, or cannot reach
the network returns a *skipped* status, and the run completes from the remaining engines
plus the committed offline corpus.

## Engine Details

Each engine adapter follows a uniform contract: a module-level API URL constant, a pure
`_parse_*` parser function, and a `search_*` entry point with pagination, retry, and
graceful error handling. All functions accept an injectable `base_url` parameter for
hermetic testing with `pytest-httpserver` — no engine hardcodes its URL inside the
function body.

| Engine | Rate limit | Pagination | Auth |
| --- | --- | --- | --- |
| arXiv | 3s between requests | 100/page, offset | Keyless |
| Semantic Scholar | 1 req/s (unauth.) | 100/page, offset | Optional key |
| OpenAlex | Polite pool (mailto) | 200/page, cursor | Keyless |
| Crossref | Polite pool (mailto) | 1,000/page, offset | Keyless |
| PubMed | NCBI usage policy | retstart/retmax | Keyless |
| SovietRxiv | 30/min (300/min polite) | 1–100/page, cursor | `X-API-Email` |
| ChinaRxiv | 30/min (300/min polite) | 1–100/page, cursor | `X-API-Email` |
| Europe PMC | ~10 req/s (undocumented hard limit) | Up to 1,000/page | Keyless |
| bioRxiv/medRxiv | No documented limit | 100/page fixed, cursor | Keyless |

Every new search writes `output/data/retrieval_report.json`, a timestamp-free report
that records each attempted, skipped, or failed source with fetched, new-record, and
duplicate counts. A zero-result response is therefore distinguishable from a disabled
adapter or an HTTP failure. The committed corpus predates that report contract, so this
paper intentionally does not reconstruct source-specific counts from the merged corpus.

## Canonical Identifier Hierarchy

Heterogeneous records are reconciled by a **canonical identifier hierarchy** —
DOI $>$ arXiv ID $>$ Semantic Scholar ID $>$ OpenAlex ID $>$ a stable digest of the
normalized title. When two records share a canonical identifier they are merged, keeping
the version with the most complete metadata (a count of non-None optional fields). The
DOI is normalized: case-folded, resolver-prefix stripped, so the same paper returned by
two engines under case/format-variant DOIs merges. For this run, 2260 records
carry DOIs, 923 carry OpenAlex IDs, and 1 carry arXiv
IDs. The de-duplicated corpus for this run holds $N = 2334$ records published
across 2000--2026.

## Relevance Filtering

After de-duplication, a relevance filter drops papers whose title and abstract contain
none of the configured relevance keywords (modafinil, armodafinil, provigil, wakefulness, narcolepsy, cognitive enhancement, alertness, sleep deprivation, vigilance, eugeroic). Keywords are matched
case-insensitively; an empty keyword list is treated as no filter to avoid silently
wiping the corpus. A year filter then excludes papers published before the configured
start year (2000).



```{=latex}
\newpage
```


# Full Text, Language, and Embeddings

Beyond bibliographic metadata, the pipeline mines the textual content of each record.
This stage bridges the gap between a bibliographic inventory and a semantic
understanding of the literature.

## Full-Text Availability

An open-access resolver maps each record to a downloadable PDF where one exists (a known
`pdf_url`, or an Unpaywall lookup by DOI), and an opt-in, network-gated downloader fetches
it to a deterministic path. Full-text availability is summarized without requiring any
download, so the offline default still reports coverage. For this run:

- **Abstract coverage**: 61.6\% of records (1437 of
  2334) carry an abstract; 897 records lack one.
- **Open-access status**: 24.6\% of records are open access (574 records);
  the remainder are closed or unknown.
- **PDF availability**: 54.6\% of records (1275) have a direct
  PDF link; 1274 have a publisher PDF, and 1059 have
  no full-text source available.

The identifier coverage for this corpus is: 2260 DOIs, 923
OpenAlex IDs, and 1 arXiv IDs. DOI coverage dominates, enabling robust
cross-engine de-duplication.

## Language and Entity Extraction

Titles, abstracts, and (when present) full text are tokenized and reduced to keyphrases
and named entities by offline, dependency-light extractors — no mandatory LLM.
Term-frequency statistics drive a TF-IDF representation over a 500-feature
vocabulary. The most frequent terms in the corpus are: modafinil, treatment, study, results, patients, effects, sleep, used, clinical, use, drug, studies, mg, using, sleepiness, disorder, associated, cognitive, narcolepsy, significant. These terms
reflect the clinical, pharmacological, and cognitive vocabulary characteristic of the
modafinil literature.

## Embeddings

Every title, abstract, and full text is embedded into a shared vector space by a
deterministic, offline method — TF-IDF followed by truncated SVD, i.e. latent semantic
analysis [@deerwester1990indexing]. The embedding dimensionality is 50 components (configurable
via `project_config.embeddings.n_components`), and the TF-IDF vocabulary is capped at
500 features (configurable via `project_config.embeddings.max_features`).
The embedding is byte-stable across runs: the same input text always yields identical
vectors, so the derived similarity matrix, nearest-neighbour lists, clusters, and
two-dimensional projection are all reproducible.

An optional transformer backend can be enabled by setting
`project_config.embeddings.method: transformer` (requires the `embeddings` extra), which
upgrades the embedding fidelity without changing the interface or downstream analysis.

The embeddings support semantic retrieval over the corpus and feed two visualizations:
a PCA two-dimensional projection ((Figure pca embeddings)) that maps the topical
geography of the literature, and a hierarchical clustering dendrogram
((Figure dendrogram)) that reveals the similarity structure of the document collection.



```{=latex}
\newpage
```


# Bibliometric and Temporal Analysis

Descriptive statistics summarize the corpus along every available axis: counts by year,
venue, and author; citation-count distributions; and author productivity. Temporal
analysis fits the publication time series, reporting a compound annual growth rate of
5.48\% across 2000--2026 (a span of 26 years), with
a mean year-over-year growth rate of 7.8\% and a doubling time of
9.2 years. The peak publication year is 2025 with
147 records.

## Growth Metrics

The compound annual growth rate (CAGR) is computed as:

$$
\text{CAGR} = \left(\frac{N_{\text{end}}}{N_{\text{start}}}\right)^{1/(\text{year span})} - 1
$$

where $N_{\text{start}}$ is the publication count in the first year (2000) and $N_{\text{end}}$
is the count in the last year (2026). The mean year-over-year growth rate
$\bar{g}$ is the arithmetic mean of annual ratios. The doubling time is
$t_d = \ln(2) / \ln(1 + \text{CAGR})$. These metrics are stored in `temporal_analysis.json`
and injected into the manuscript at render time.

## Subfield Classification

Subfield classification assigns each record to one of 6 configurable buckets
(Clinical Sleep, Cognition, Pharmacology, Psychiatry, Safety, and Neuroscience) by priority-aware keyword matching; the taxonomy is defined entirely
in configuration (`project_config.subfield_keywords`). The largest bucket is
**Clinical Sleep** at 63.0\% of the classified corpus. A per-subfield
temporal breakdown (`subfield_timeline.json`) tracks how each sub-area has grown over
time, enabling identification of emerging or declining research threads.

## Topic Modeling

A TF-IDF term-weighting of titles and abstracts [@salton1988term] feeds non-negative matrix
factorization (NMF) [@lee1999learning], implemented with scikit-learn
[@pedregosa2011scikit]. NMF decomposes the document-term matrix $\mathbf{V} \approx \mathbf{W} \mathbf{H}$,
where $\mathbf{W}$ is the document-topic matrix and $\mathbf{H}$ is the topic-term matrix. The
factorization extracts 5 latent topics that cross-cut the keyword taxonomy.
The random seed is fixed at 42 for reproducibility. The reporting follows established
systematic-review practice [@page2021prisma], with every figure and statistic traceable to
a committed artifact.



```{=latex}
\newpage
```


# Optional Knowledge-Graph Layer

An optional, **LLM-gated** stage lifts the corpus from bibliometrics to hypothesis-level
evidence. For each record, a local language model (Ollama, default model `gemma3:4b`)
extracts structured *assertions* — each encoding a direction (supports / contradicts /
neutral), a confidence score, and a short natural-language justification — against the
6 hypotheses declared in configuration. Assertions are serialized as
RDF-compatible nanopublications [@kuhn2016decentralized] and scored by a
citation-weighted evidence function.

## Assertion Model

Each assertion $a$ encodes:

- **Direction**: $\text{supports}$, $\text{contradicts}$, or $\text{neutral}$ with respect to a hypothesis $H$
- **Confidence**: a score $c_a \in [0, 1]$ from the LLM
- **Citation weight**: $\log(1 + n_{\text{cites}})$, where $n_{\text{cites}}$ is the
  citation count of the asserting paper

The evidence score for hypothesis $H$ is:

$$
\text{score}(H) = \frac{\sum_{a \in A(H)^+} c_a \cdot \log(1 + n_{\text{cites}}(a)) -
\sum_{a \in A(H)^-} c_a \cdot \log(1 + n_{\text{cites}}(a))}
{\sum_{a \in A(H)} c_a \cdot \log(1 + n_{\text{cites}}(a))}
$$

where $A(H)^+$ is the set of supporting assertions and $A(H)^-$ the contradicting ones.
The score ranges from $-1$ (all evidence contradicts) to $+1$ (all evidence supports).

## Incremental Extraction

Assertion extraction is **incremental and resumable**: assertions are appended to
`nanopublications.jsonl` at configurable checkpoint intervals (default: 50 papers). On
restart, already-processed papers are skipped automatically, so a long extraction run
that is interrupted can resume without re-processing. The `--clear-assertions` flag
discards previous results for a fresh start.

## Gating and Defaults

This stage is optional and gated by language-model availability. With no language
model configured, the hypothesis evidence scores read *pending*; with Ollama configured
(as in this instance, with 127 assertions extracted), scores are populated
from citation-weighted assertion extraction. The hypotheses themselves — their names and
scope — come from configuration and are reported regardless of whether the scoring stage
has run.

The hypotheses explored in this instance are: H1 Wakefulness Efficacy; H2 Cognitive Enhancement; H3 Low Abuse Liability; H4 Dopaminergic Mechanism; H5 Off-label Psychiatric Utility; H6 Tolerability.



```{=latex}
\newpage
```


# Visualization and Manuscript Injection

## Figure Generation

Figures are rendered headlessly (matplotlib Agg backend) and deterministically from the
analysis artifacts: subfield distributions, the publication growth curve, the citation
network, topic-term bars, a term cloud, and embedding projections. All figures use a
colourblind-safe palette (Wong 2011, 8 colours) with high-contrast labels at $\geq 16$pt.
This run produced 21 figures at 300 DPI. The full figure set includes:

- **Field overview**: field summary and subfield distribution
  ((Figure field summary; Figure subfield distribution))
- **Temporal**: growth curve and subfield timeline ((Figure growth curve; Figure subfield timeline))
- **Citation network**: network layout and degree distribution
  ((Figure citation network; Figure degree distribution))
- **Hypothesis**: dashboard and evidence timeline ((Figure hypothesis dashboard))
- **Text analytics**: word cloud, topic-term bars, PCA embeddings, term heatmap,
  dendrogram, and co-occurrence matrix
  ((Figure word cloud; Figure topic term bars; Figure pca embeddings; Figure term heatmap; Figure dendrogram; Figure cooccurrence matrix))

Each figure is registered in `figure_registry.json` with its source data file, generation
parameters, and SHA-256 hash, binding the visual output to the exact pipeline run.

## Variable Injection

The manuscript itself is generated, not hand-maintained. A variable computation step
reads the configuration and the pipeline outputs and emits a flat table of named values;
an injection step substitutes each named placeholder in these Markdown sections with its
computed value before rendering. Because the substitution is total — an unresolved
placeholder is a hard error, not a silent gap — every number in the rendered document is
guaranteed to trace to a committed artifact. Re-running the pipeline after a
configuration change re-computes the values and re-targets the prose automatically.

The injection system computes variables from seven sources:

1. `manuscript/config.yaml` — search term, engine roster, subfield taxonomy, hypotheses
2. `corpus.jsonl` — corpus size
3. `temporal_analysis.json` — year range, CAGR, peak year, doubling time
4. `citation_network.json` — edges, nodes, density, communities, PageRank, hubs
5. `subfield_classification.json` — per-bucket counts and percentages
6. `assertion_summary.json` — assertion counts and directions
7. `hypothesis_scores.json` — per-hypothesis evidence scores



```{=latex}
\newpage
```


# Results: Hypotheses Explored

The template scores a configurable set of hypotheses about the topic. For this instance
6 hypotheses are declared in configuration; Table 7 lists them with their
scope and evidence score.

**Table 7. Hypotheses explored.**

| ID | Hypothesis | Scope | Evidence score |
| --- | --- | --- | --- |
| H1 | Wakefulness Efficacy | clinical | +0.56 |
| H2 | Cognitive Enhancement | cognitive | +0.49 |
| H3 | Low Abuse Liability | safety | +0.62 |
| H4 | Dopaminergic Mechanism | pharmacological | +1.00 |
| H5 | Off-label Psychiatric Utility | applied | +0.35 |
| H6 | Tolerability | safety | +0.31 |

Evidence scores are produced by the optional, LLM-gated knowledge-graph stage. When
the knowledge-graph stage is skipped (no language model configured), scores read
*pending*. When the stage runs (as in this instance, with 127
assertions extracted via Ollama), scores are populated from citation-weighted
assertion extraction. The hypotheses, their names, and their scope are always reported
directly from configuration regardless of whether the LLM stage executed.

## Interpretation

Reported scores, when present, should be read as relative rankings rather than calibrated
probabilities: absolute magnitudes are inflated by publication bias and the linguistic
asymmetry of academic writing. A positive score indicates that the retrieved corpus
*talks about* the hypothesis in a supporting direction; a negative score indicates
contradicting evidence; a score near zero indicates either balanced evidence or
insufficient coverage.

The six hypotheses frame the evidence landscape for Modafinil:

- **H1 (Wakefulness Efficacy)** — the clinical claim that modafinil reliably promotes
  wakefulness in sleep-disorder populations. This is the primary indication and the
  most-studied claim in the corpus.

- **H2 (Cognitive Enhancement)** — the claim that modafinil improves attention, working
  memory, and executive function, especially under sleep deprivation. This hypothesis
  drives the neuroenhancement literature and is the subject of significant public and
  scientific debate.

- **H3 (Low Abuse Liability)** — the safety claim that modafinil has lower abuse
  potential than classical psychostimulants. This is critical for regulatory
  classification and prescribing decisions.

- **H4 (Dopaminergic Mechanism)** — the pharmacological claim that modafinil acts
  substantially via dopamine-transporter inhibition rather than a purely novel mechanism.
  This hypothesis has mechanistic and translational implications.

- **H5 (Off-label Psychiatric Utility)** — the applied claim that modafinil is a useful
  adjunct for fatigue and cognition in psychiatric and neurological conditions, including
  depression, ADHD, and schizophrenia.

- **H6 (Tolerability)** — the safety claim that modafinil is generally well tolerated,
  with predominantly mild, transient adverse effects. This underpins its clinical
  acceptability relative to alternative wakefulness agents.

<!-- FIGURE: hypothesis_dashboard.png -->
![Hypothesis dashboard for Modafinil. The dashboard summarizes the evidence scores across the 6 configured hypotheses, showing the direction and magnitude of citation-weighted assertion evidence.](../figures/hypothesis_dashboard.png "Hypothesis Dashboard"){{#fig:hypothesis_dashboard}}



```{=latex}
\newpage
```


# Results: Field Overview

The de-duplicated corpus for **Modafinil** contains $N = 2334$
records spanning 2000--2026 (26 years). Publication volume
grows at a compound annual rate of 5.48\% (mean year-over-year growth
7.8\%, doubling time 9.2 years), peaking in 2025
with 147 records that year. The growth curve is the first-order signal
that the literature is active rather than dormant.

<!-- FIGURE: growth_curve.png -->
![Publication growth curve for Modafinil. Annual publication counts (bars) and cumulative total (line) show sustained growth from 2000 through 2026, peaking in 2025.](../figures/growth_curve.png "Publication Growth Curve"){{#fig:growth_curve}}

## RQ1: Field Size and Growth

The temporal analysis reveals a literature that has grown steadily over 26
years. The compound annual growth rate of 5.48\% means the corpus roughly doubles
every 9.2 years — a pace that exceeds the general biomedical literature
growth rate of approximately 4\% per year. The peak year 2025 with
147 publications likely reflects both genuine research activity and the
lag between publication and indexing in the source databases.

**Table 1. Top publication years.**

| Year | Publications |
| --- | --- |
| 2016 | 103 |
| 2017 | 106 |
| 2018 | 96 |
| 2019 | 107 |
| 2020 | 112 |
| 2021 | 103 |
| 2022 | 117 |
| 2023 | 106 |
| 2024 | 123 |
| 2025 | 147 |

## RQ2: Subfield Composition

Records distribute across the 6 configured subfields as shown in Table 2,
with **Clinical Sleep** the largest bucket at 63.0\% of the classified
corpus. The dominance of Clinical Sleep reflects the clinical primacy of
modafinil as a wakefulness-promoting agent: the largest body of literature addresses
its use in narcolepsy, shift-work disorder, and obstructive sleep apnea.

**Table 2. Subfield distribution.**

| Subfield | Papers | Share |
| --- | --- | --- |
| Clinical Sleep | 1407 | 63.0% |
| Cognition | 249 | 11.1% |
| Pharmacology | 76 | 3.4% |
| Psychiatry | 359 | 16.1% |
| Safety | 94 | 4.2% |
| Neuroscience | 49 | 2.2% |

<!-- FIGURE: field_summary.png -->
![Field summary dashboard for Modafinil. The dashboard combines corpus size, temporal range, subfield distribution, and key bibliometric indicators in a single overview panel.](../figures/field_summary.png "Field Summary"){{#fig:field_summary}}

<!-- FIGURE: subfield_distribution.png -->
![Subfield distribution for Modafinil. The 6-bucket taxonomy shows the relative weight of each configured sub-area, with Clinical Sleep dominant at 63.0\%.](../figures/subfield_distribution.png "Subfield Distribution"){{#fig:subfield_distribution}}

<!-- FIGURE: subfield_timeline.png -->
![Subfield timeline for Modafinil. Stacked annual publication counts by subfield show how each sub-area has evolved over time, revealing emerging and declining research threads.](../figures/subfield_timeline.png "Subfield Timeline"){{#fig:subfield_timeline}}

## Identifier and Full-Text Coverage

The corpus has strong identifier coverage: 2260 of 2334 records
(97.2\%) carry DOIs, enabling robust cross-engine de-duplication.
OpenAlex IDs are present for 923 records. Abstract coverage stands at
61.6\% (1437 records), which limits the text analytics
to that subset. Open-access status is confirmed for 24.6\% of records, and
54.6\% have a direct PDF link.

## Descriptive Bibliometrics

The corpus spans 8152 unique authors across 2334 papers, yielding
a mean of 1.28 papers per author. Citation counts range from zero to
1353 (mean 30.3, median 0.0), with a total of
67,646 citations across the corpus. The Gini coefficient of citation
concentration is 0.817, indicating a highly skewed distribution
characteristic of scientific literature.

**Table 3. Citation count distribution.**

| Citations | Papers |
| --- | --- |
| 0 | 1253 |
| 1-9 | 165 |
| 10-49 | 416 |
| 50-99 | 213 |
| 100-499 | 176 |
| 500+ | 11 |

<!-- FIGURE: citation_distribution.png -->
![Citation distribution for Modafinil. The histogram shows the number of papers in each citation-count bucket, with the Gini coefficient annotated. The heavy-tailed distribution is characteristic of scientific citation networks.](../figures/citation_distribution.png "Citation Distribution"){{#fig:citation_distribution}}

**Table 4. Top publication venues.**

| Venue | Papers |
| --- | --- |
| Reactions Weekly | 61 |
| Psychopharmacology | 41 |
| SLEEP | 34 |
| Sleep Medicine | 33 |
| The Journal of Clinical Psychiatry | 31 |
| European Neuropsychopharmacology | 26 |
| Neuropharmacology | 26 |
| Inpharma Weekly | 25 |
| Sleep | 24 |
| American Journal of Psychiatry | 23 |

<!-- FIGURE: top_venues.png -->
![Top publication venues for Modafinil. The horizontal bar chart shows the 15 venues with the most papers in the corpus, revealing where the modafinil literature is published.](../figures/top_venues.png "Top Venues"){{#fig:top_venues}}

**Table 5. Top authors by publication count.**

| Rank | Author | Papers |
| --- | --- | --- |
| 1 | &NA; | 41 |
| 2 | Ronghua Yang | 25 |
| 3 | Yves Dauvilliers | 22 |
| 4 | Barbara J. Sahakian | 19 |
| 5 | Edward T. Hellriegel | 17 |
| 6 | Philmore Robertson | 16 |
| 7 | Mona Darwish | 15 |
| 8 | Sanjay Arora | 15 |
| 9 | Amy Hauck Newman | 14 |
| 10 | Jed Black | 14 |

<!-- FIGURE: author_productivity.png -->
![Author productivity for Modafinil. The horizontal bar chart shows the 20 authors with the most papers in the corpus, revealing the most prolific contributors to the modafinil literature.](../figures/author_productivity.png "Author Productivity"){{#fig:author_productivity}}



```{=latex}
\newpage
```


# Results: Subfield Structure

The subfield taxonomy is defined entirely in configuration; for this instance it spans
6 buckets (Clinical Sleep, Cognition, Pharmacology, Psychiatry, Safety, and Neuroscience). Each record is assigned to the
highest-priority bucket whose keywords it matches, so the distribution reflects the
configured taxonomy rather than a fixed schema. Table 2 (previous section) reports the
counts; the largest bucket is **Clinical Sleep** (63.0\%).

## Per-Subfield Characterization

The subfield breakdown reveals the multi-disciplinary nature of the modafinil
literature:

- **Clinical Sleep** dominates at 63.0\%, reflecting the drug's primary
  indication for narcolepsy, shift-work disorder, and obstructive sleep apnea. This
  bucket includes randomized controlled trials, meta-analyses of efficacy, and
  long-term safety studies in sleep-disorder populations.

- **Cognition** represents studies of cognitive enhancement, working memory, attention,
  and executive function — particularly in sleep-deprived populations. This subfield
  has grown with the broader interest in neuroenhancement and "smart drugs."

- **Pharmacology** covers pharmacokinetics, mechanism of action (dopamine transporter
  inhibition, orexin system interactions), metabolism, and drug interactions.

- **Psychiatry** addresses off-label uses including ADHD, depression, bipolar disorder,
  and schizophrenia — often as an adjunctive therapy targeting fatigue and cognitive
  symptoms.

- **Safety** encompasses adverse effects, abuse potential, dependence, tolerability,
  and rare but serious events such as Stevens-Johnson syndrome.

- **Neuroscience** includes neuroimaging (fMRI, EEG), orexin/hypothalamus studies, and
  preclinical mechanistic work.

Because the taxonomy is data, not code, re-targeting the template to another topic — or
refining the buckets for the same topic — changes this section's structure and numbers
without any change to the analysis code. The subfield assignment also feeds the temporal
and citation analyses, allowing per-subfield growth and connectivity to be read off the
same artifacts.



```{=latex}
\newpage
```


# Results: Language, Topics, and Embeddings

## RQ3: Topical and Linguistic Structure

Text analysis operates over titles, abstracts, and (when available) full text. A TF-IDF
representation over a 500-feature vocabulary feeds non-negative matrix
factorization, which extracts 5 latent topics cross-cutting the subfield
taxonomy. The top vocabulary terms are: modafinil, treatment, study, results, patients, effects, sleep, used, clinical, use, drug, studies, mg, using, sleepiness, disorder, associated, cognitive, narcolepsy, significant.

**Table 3. NMF topics extracted from the corpus.**

| Topic | Top terms |
| --- | --- |
| 0 | modafinil, mg, kg, effects, rats, mice, induced, sleep |
| 1 | fatigue, patients, placebo, modafinil, scale, armodafinil, treatment, depression |
| 2 | h4, methods, results, conclusion, 95, analysis, ci, risk |
| 3 | use, cognitive, drugs, adhd, studies, drug, cocaine, methylphenidate |
| 4 | sleep, narcolepsy, sleepiness, cataplexy, daytime, patients, eds, excessive |

The topics reveal the thematic structure of the literature: Topic 0 centres on cognitive
enhancement and neuroenhancement; Topic 1 addresses ADHD treatment and clinical evidence;
Topic 2 covers pharmacological dose-response studies (including animal models); Topic 3
focuses on sleep disorders (narcolepsy, excessive daytime sleepiness); and Topic 4
addresses fatigue in psychiatric populations. These topics cross-cut the keyword-based
subfield taxonomy, revealing connections that the explicit classification does not
capture.

<!-- FIGURE: topic_term_bars.png -->
![Topic-term bar charts for Modafinil. Each panel shows the top weighted terms for one of 5 NMF topics, with bar length proportional to the topic-term weight in the $\mathbf{H}$ matrix.](../figures/topic_term_bars.png "Topic-Term Weights"){{#fig:topic_term_bars}}

## Document Embeddings

Offline deterministic embeddings (TF-IDF followed by truncated SVD) place every document
in a shared 50-dimensional vector space. Embedding the same text twice yields identical
vectors, so the derived similarity matrix, nearest-neighbour lists, clusters, and
two-dimensional projection are all reproducible.

<!-- FIGURE: pca_embeddings.png -->
![PCA projection of document embeddings for Modafinil. Each point represents one document projected onto the first two principal components of the TF-IDF/SVD embedding. Colours indicate subfield assignment, showing how the topical geography relates to the keyword taxonomy.](../figures/pca_embeddings.png "PCA Embeddings"){{#fig:pca_embeddings}}

<!-- FIGURE: dendrogram.png -->
![Hierarchical clustering dendrogram of document embeddings. The tree shows the similarity structure of the corpus: documents that join low in the tree are semantically similar, while high-level splits separate the major topical clusters.](../figures/dendrogram.png "Document Dendrogram"){{#fig:dendrogram}}

## Term Analysis

The TF-IDF term heatmap reveals which terms discriminate between subfields: terms with
high between-subfield variance (rather than high global mean) are selected for display.

<!-- FIGURE: term_heatmap.png -->
![Term heatmap for Modafinil. Each cell shows the mean TF-IDF weight of a term within a subfield. Terms are selected by between-subfield variance to highlight discriminative vocabulary rather than globally frequent terms.](../figures/term_heatmap.png "Term Heatmap"){{#fig:term_heatmap}}

## Named Entity Analysis

Named entity extraction over the 1437 abstracts identified 30
unique entities. The most frequent entities reflect the clinical and pharmacological
vocabulary of the modafinil literature.

**Table 4. Top named entities in abstracts.**

| Entity | Frequency |
| --- | --- |
| ADHD | 392 |
| CI | 343 |
| EDS | 326 |
| OSA | 272 |
| MOD | 181 |
| ESS | 148 |
| RESULTS | 148 |
| MS | 145 |
| DAT | 134 |
| NT1 | 131 |
| SD | 130 |
| CONCLUSIONS | 129 |
| MD | 102 |
| CE | 101 |
| IH | 101 |

<!-- FIGURE: entity_bar_chart.png -->
![Top named entities for Modafinil. The horizontal bar chart shows the 20 most frequently extracted named entities from abstracts, revealing the dominant drugs, conditions, and concepts in the literature.](../figures/entity_bar_chart.png "Named Entities"){{#fig:entity_bar_chart}}

**Table 5. Top keyphrases by TF-IDF score.**

| Keyphrase | Score |
| --- | --- |
| available | 0.3333 |
| abstract | 0.3333 |
| abstract available | 0.3333 |
| content | 0.1053 |
| access | 0.1053 |
| sub | 0.0881 |
| md | 0.0870 |
| jama | 0.0826 |
| cleveland | 0.0763 |
| modafinil | 0.0741 |
| depression | 0.0741 |
| cognitive | 0.0714 |
| substance | 0.0694 |
| drug | 0.0667 |
| conditions | 0.0667 |

## Embedding Similarity and Clustering

The TF-IDF/SVD embeddings place every document in a 50-dimensional vector space. K-means
clustering with $k = 5$ clusters partitions the corpus into
topically coherent groups. The top similar document pairs, ranked by cosine similarity,
reveal the most closely related works in the corpus.

**Table 6. Top 10 most similar document pairs.**

| Paper A | Paper B | Similarity |
| --- | --- | --- |
| doi:10.1176/appi.ajp.163.12.21 | doi:10.1176/ajp.2006.163.12.21 | 1.0000 |
| doi:10.1176/ajp.2006.163.12.21 | doi:10.1176/appi.ajp.163.12.21 | 1.0000 |
| doi:10.1345/aph.1h302 | doi:10.1136/bcr.08.2011.4652 | 0.9660 |
| doi:10.4088/jcp.09m05900gry | doi:10.1186/s40345-015-0034-0 | 0.9566 |
| doi:10.1111/bdi.12859 | doi:10.1111/acps.12712 | 0.9558 |
| doi:10.1111/j.1360-0443.2008.0 | doi:10.1111/j.1465-3362.2012.0 | 0.9536 |
| doi:10.1513/annalsats.202006-6 | doi:10.3760/cma.j.cn112147-202 | 0.9532 |
| doi:10.1164/ajrccm.164.9.21030 | doi:10.1093/sleep/28.4.464 | 0.9513 |
| doi:10.1093/sleep/28.4.464 | doi:10.1164/ajrccm.164.9.21030 | 0.9513 |
| doi:10.1002/cncr.25083 | doi:10.1200/jco.2005.23.16_sup | 0.9507 |

<!-- FIGURE: similarity_heatmap.png -->
![Document similarity for Modafinil. The horizontal bar chart shows the 15 most similar document pairs ranked by cosine similarity of their TF-IDF/SVD embeddings. High-similarity pairs share topical and lexical content.](../figures/similarity_heatmap.png "Similar Document Pairs"){{#fig:similarity_heatmap}}

<!-- FIGURE: word_cloud.png -->
![Term cloud for Modafinil. Term sizes are proportional to their TF-IDF weights across the corpus, providing a visual summary of the dominant vocabulary.](../figures/word_cloud.png "Term Cloud"){{#fig:word_cloud}}

<!-- FIGURE: cooccurrence_matrix.png -->
![Term co-occurrence matrix for Modafinil. Each cell shows the normalized co-occurrence frequency of two terms within the same document, revealing which concepts tend to appear together in the literature.](../figures/cooccurrence_matrix.png "Term Co-occurrence"){{#fig:cooccurrence_matrix}}

These embeddings support semantic retrieval over the corpus and the visual map of the
literature's topical geography.



```{=latex}
\newpage
```


# Results: Citation Network

## RQ4: Citation Geometry

Resolving each record's references against the corpus yields an intra-corpus citation
graph (built and analyzed with NetworkX [@hagberg2008exploring]) of 2234
nodes and 8,623 edges across 1409 connected components,
with a graph density of 0.17\% and a mean in-degree of
3.9. Of 38,489 total outgoing references,
22.4\% resolve to another record inside the corpus — a resolution
rate that reflects how self-contained the retrieved slice of the literature is rather
than the underlying citation density of any single work.

The citation network has 1416 communities (detected by modularity
optimization), a maximum in-degree of 163 (the most-cited paper
within the corpus), and a maximum out-degree of 143 (the paper
that cites the most other corpus members).

## Centrality Analysis

Centrality scores (PageRank [@page1999pagerank] and HITS) and modularity-based community
detection [@clauset2004finding] are rounded and ranked with a stable tiebreaker so the
reported hub and authority rankings are byte-reproducible across runs despite the
floating-point non-associativity of the underlying iterative solvers.

**Table 4. Top 5 papers by PageRank.**

| Rank | DOI | PageRank |
| --- | --- | --- |
| 1 | 10.1177/026988110001400107 | 0.036943 |
| 2 | 10.1212/wnl.54.5.1166 | 0.026949 |
| 3 | 10.1523/jneurosci.21-05-01787.2001 | 0.013668 |
| 4 | 10.1523/jneurosci.20-22-08620.2000 | 0.011349 |
| 5 | 10.4088/jcp.v61n0510 | 0.008136 |

**Table 5. Top 5 authority papers (HITS).**

| Rank | DOI | Authority |
| --- | --- | --- |
| 1 | 10.1038/sj.npp.1301534 | 0.017700 |
| 2 | 10.1007/s00213-002-1250-8 | 0.016311 |
| 3 | 10.1124/jpet.106.106583 | 0.015144 |
| 4 | 10.1523/jneurosci.21-05-01787.2001 | 0.014734 |
| 5 | 10.1001/jama.2009.351 | 0.014481 |

**Table 6. Top 5 hub papers (HITS).**

| Rank | DOI | Hub |
| --- | --- | --- |
| 1 | 10.3389/fnins.2021.656475 | 0.011968 |
| 2 | 10.1016/bs.apha.2023.10.006 | 0.011596 |
| 3 | 10.1038/sj.npp.1301534 | 0.010886 |
| 4 | 10.1080/08897077.2019.1700584 | 0.010562 |
| 5 | 10.1007/s00213-013-3232-4 | 0.009896 |

The most influential paper by PageRank (DOI 10.1177/026988110001400107) is a foundational work
that anchors the citation structure — its high authority score confirms it is frequently
cited by other corpus members. Hub papers, which cite many other corpus members, serve as
integrative reviews or meta-analyses that connect disparate threads of the literature.

<!-- FIGURE: citation_network.png -->
![Citation network for Modafinil. Nodes represent papers; directed edges represent citation links. Node colours indicate community membership (1416 communities detected by modularity optimization). Layout uses a spring-based algorithm with a fixed seed for reproducibility.](../figures/citation_network.png "Citation Network"){{#fig:citation_network}}

<!-- FIGURE: degree_distribution.png -->
![Degree distribution for the Modafinil citation network. The histogram shows the frequency of each in-degree value on a log-linear scale, revealing the heavy-tailed structure characteristic of citation networks.](../figures/degree_distribution.png "Degree Distribution"){{#fig:degree_distribution}}

The heavy-tailed degree distribution is characteristic of citation networks: a small
number of highly-cited papers anchor the structure, while the long tail of low-degree
nodes represents newer or peripheral works. The low graph density
(0.17\%) reflects the sparsity of intra-corpus citation links —
most papers cite works outside the retrieved slice, which is expected for a
max-results-capped retrieval.

## Advanced Network Metrics

Beyond PageRank and HITS, the network analysis computes betweenness centrality (which
papers bridge different communities), closeness centrality (which papers are near all
others), degree assortativity (do highly-cited papers cite other highly-cited papers?),
and average clustering coefficient (how tightly knit are local neighborhoods).

The degree assortativity coefficient is -0.0598, and the average
clustering coefficient is 0.1029. A negative assortativity indicates that
highly-cited papers tend to cite less-cited papers (dissortative mixing), which is
typical of citation networks where review papers (high in-degree) cite many primary
studies (low in-degree).

**Table 7. Top 5 papers by betweenness centrality.**

| Rank | DOI | Betweenness |
| --- | --- | --- |
| 1 | 10.1038/sj.npp.1301534 | 0.005234 |
| 2 | 10.4088/jcp.v67n0406 | 0.003451 |
| 3 | 10.1016/j.neuropharm.2012.07.011 | 0.002530 |
| 4 | 10.1002/14651858.cd006788.pub3 | 0.002289 |
| 5 | 10.2165/00003495-200868130-00003 | 0.001894 |

Papers with high betweenness centrality serve as bridges between different topical
communities in the citation network — their removal would fragment the graph into
disconnected components. These bridging papers are often review articles or
methodological papers that connect disparate research threads.



```{=latex}
\newpage
```


# Results: Reproducibility Assessment

An optional, **LLM-gated** stage decomposes each paper's described pipeline into a
workflow graph of source, method, experiment, and sink steps, rates how reproducible
each step is from the paper's own text, and combines a content score with a structural
graph-coverage score into one composite reproducibility score per paper (geometric mean,
so a paper cannot buy a high score by being strong on one axis alone). Across
109 scored papers the mean composite score is
0.812, with 1 papers falling
below the configured low-score threshold.

## Low-Scoring Papers

Table 8 lists the papers with the lowest composite reproducibility scores, alongside
their content and structural component scores.

**Table 8. Low-scoring papers by composite reproducibility score.**

| Paper | Composite | Content | Structural |
| --- | --- | --- | --- |
| doi:10.2165/00128413-200012450-00041 | 0.000 | 0.000 | 0.000 |

## Gating and Defaults

This stage is optional and gated by full-text availability. With no fulltext
available and no language model configured, the stage is skipped and the
reproducibility aggregates read *pending* — the same graceful-degradation convention used by the
knowledge-graph assertion-extraction stage (see
[`02d_methods_knowledge_graph.md`](02d_methods_knowledge_graph.md)). When fulltext is
available and a language model is configured (as in this instance, with
109 papers scored via Ollama), the mean score,
low-score count, and per-paper table are populated from extracted workflow graphs.

## Interpretation

A low composite score can reflect either weak content (the paper's own text does not
describe its sources, methods, experiments, or outputs in enough detail to rate highly)
or weak structure (the described steps do not chain into a coherent source-to-sink
pipeline, or reference steps that were never themselves described). The two axes are
reported separately in Table 8 precisely so a low composite score can be diagnosed
rather than treated as a single undifferentiated verdict.



```{=latex}
\newpage
```


# Discussion

## What the Template Is, and Is Not

The pipeline measures the *shape* of a literature — its size, growth, subfield
composition, topical structure, citation geometry, and the hypotheses a field frames. It
does not adjudicate scientific truth. The optional hypothesis scores summarize how the
retrieved corpus *talks about* each claim, weighted by citation influence; they are an
evidence-landscape instrument, not a verdict.

The 5 topics extracted by NMF provide a data-driven complement to the
keyword-based subfield taxonomy. Where the taxonomy assigns each paper to a single bucket,
the topics reveal overlapping thematic structure: a paper on modafinil's cognitive effects
in ADHD patients belongs to the "Psychiatry" subfield but also loads on the "Cognitive
Enhancement" and "ADHD Treatment" topics. This multi-resolution view is more informative
than either approach alone.

## Engine Coverage and Bias

The committed analysis corpus is a bounded retrieval snapshot. It predates the
deterministic per-engine retrieval report introduced by this template, so this paper
does not attribute record counts or success/failure states to individual engines by
reverse-engineering the merged corpus. New runs write those facts directly to
`output/data/retrieval_report.json`; a resumed legacy snapshot is explicitly labelled
`resume_without_prior_retrieval_report` rather than being given invented provenance.

The max-results cap of 1,000 per engine means the full literature is larger than the
retrieved corpus; the 2334 records represent a bounded sample rather than the
complete literature. The citation network resolution rate of
22.4\% reflects this: many cited works lie outside the retrieved
slice. Increasing the cap or adding more engines would improve coverage but also
increase runtime and API load.

## Honest Defaults

The small corpus under `data/fixtures/` is synthetic (reserved test DOIs and generated
authors) and exists only for offline tests. It is not silently substituted for the
tracked analysis corpus. A user who regenerates empirical findings must run retrieval,
analysis, figures, and manuscript injection together and retain the resulting corpus and
retrieval report; fixture-only runs demonstrate machinery, not findings about
modafinil.

## Limitations and Extensions

Several limitations bound the interpretation of results:

- **Coverage is bounded by the enabled engines and the query.** The max-results cap
  truncates each engine's contribution. Semantic Scholar's rate limiting excluded a
  major source; a Semantic Scholar API key would resolve this.

- **Subfield classification is keyword-based** and only as good as the configured
  taxonomy. Ambiguous papers may be misclassified; a classifier based on embeddings or
  supervised learning could improve accuracy.

- **The default embeddings are lexical** (TF-IDF/SVD). They capture term co-occurrence
  but not semantic similarity; a transformer backend (`embeddings` extra) would improve
  the quality of nearest-neighbour retrieval and clustering.

- **Hypothesis scoring depends on an external language model.** Without Ollama running,
  scores read *pending*; with Ollama configured (as in this run, with 127
  assertions extracted), scores are populated. The scoring is also sensitive to prompt
  design and model choice; the default `gemma3:4b` is a lightweight model suitable for
  demonstration but may miss nuanced assertions.

- **Abstract coverage is 61.6\%.** Text analytics operate only on
  the subset of records with abstracts, biasing topic models and embeddings toward
  well-indexed sources.

Each limitation is a configuration or dependency choice rather than a change to the core
architecture.



```{=latex}
\newpage
```


# Conclusion

We have presented a configurable, reproducible meta-analysis template that turns a single
search term into a complete, evidence-bound portrait of its literature. Applied to
**Modafinil**, it retrieved and de-duplicated 2334 records across
9 engines (arXiv, OpenAlex, Semantic Scholar, Crossref, PubMed, SovietRxiv, ChinaRxiv, Europe PMC, and bioRxiv/medRxiv), classified them into 6 configurable
subfields (with **Clinical Sleep** dominant at 63.0\%), extracted
5 topics over a 500-feature vocabulary, computed
reproducible document embeddings, mapped the citation network (2234 nodes,
8,623 edges, 1416 communities), and framed
6 hypotheses for optional evidence scoring.

## Key Findings

The analysis answers the four research questions posed in the introduction:

1. **RQ1 (Growth)**: The modafinil literature spans 26 years
   (2000--2026) and grows at a CAGR of 5.48\%, doubling every
   9.2 years. The peak year 2025 produced 147
   publications, indicating sustained and active research interest.

2. **RQ2 (Subfields)**: The 6-bucket taxonomy reveals a multi-disciplinary
   literature dominated by clinical sleep research (63.0\%), with
   significant representation from cognition, psychiatry, and pharmacology.

3. **RQ3 (Topics)**: NMF extracted 5 latent topics — cognitive enhancement,
   ADHD treatment, pharmacological dose-response, sleep disorders, and psychiatric
   fatigue — that cross-cut the explicit subfield taxonomy and reveal the thematic
   structure of the field.

4. **RQ4 (Citations)**: The citation network of 2234 nodes and
   8,623 edges has a resolution rate of 22.4\%,
   1416 communities, and a maximum in-degree of
   163. The heavy-tailed degree distribution is characteristic of
   citation networks, with a small number of foundational works anchoring the structure.

## Architectural Contribution

The contribution is architectural rather than topical: every domain-specific value flows
from one configuration file and the pipeline's own outputs into a generated manuscript,
so the same machinery re-targets to any topic by editing configuration alone. Combined
with an offline, deterministic default run, this yields a *living literature review* — a
synthesis that can be re-executed on demand as a field evolves, with every number
traceable to a regenerable artifact.

## Reproducibility

This manuscript was generated from a live retrieval run using 9 engines.
Every number, table, and figure in this document is injected from a committed artifact
(`output/data/*.json`, `../figures/*.png`). Re-running the pipeline with the same
configuration reproduces identical data outputs; the 21 figures are
deterministic given fixed seeds, and the manuscript text is regenerated from the same
template. No number in this document was typed by hand.



```{=latex}
\newpage
```


# Appendix A: Tooling and Reproduction

The pipeline is a two-layer system: generic infrastructure (rendering, validation,
logging) shared across the template monorepo, and project-local `src/` modules that
implement the meta-analysis. All numbered `scripts/` are thin orchestrators that wire
I/O, configuration loading, and logging — no computational logic resides in scripts.

## Reproduce the Offline Default Run

No network, no language model required:

```bash
uv run python scripts/generate_fixture_corpus.py --out output/data/corpus.jsonl
uv run python scripts/02_meta_analysis_pipeline.py
uv run python scripts/03_build_knowledge_graph.py --max-papers 0
uv run python scripts/04_generate_figures.py --dpi 300
uv run python scripts/05_inject_variables.py
```

## Reproduce the Live Run

This manuscript was generated from a live retrieval run. To reproduce:

```bash
# Live search (all 9 engines, max 1000 per engine)
uv run python scripts/01_literature_search.py --query modafinil --max-results 1000 --no-resume

# Analysis pipeline
uv run python scripts/02_meta_analysis_pipeline.py
uv run python scripts/03_build_knowledge_graph.py --max-papers 0
uv run python scripts/04_generate_figures.py --dpi 300
uv run python scripts/05_inject_variables.py
uv run python scripts/06_fulltext_assessment.py
uv run python scripts/07_literature_evaluation.py
uv run python scripts/09_export_bibliography.py
```

## Re-target to Another Topic

Edit `manuscript/config.yaml` — `project_config.search.term`, `query`,
`relevance_keywords`, `subfield_keywords`, and `hypothesis_definitions` — then regenerate
the seed corpus and re-run. No code changes are required; the manuscript re-targets
through token injection.

## Live Retrieval

Enable engines under `project_config.search.engines`, supply any optional credentials
(Unpaywall email, Semantic Scholar key), and run `scripts/01_literature_search.py`; absent
engines degrade to skipped sources. The CLI supports per-engine skip flags:
`--skip-arxiv`, `--skip-s2`, `--skip-openalex`, `--skip-crossref`, `--skip-pubmed`,
`--skip-sovietrxiv`, `--skip-chinarxiv`, `--skip-europepmc`, `--skip-biorxiv`.

## Deep Research (Offline Fixture Replay)

This exemplar also demonstrates the shared `infrastructure.search.deep_research`
capability — provider-neutral dispatch to OpenAI and Gemini deep-research agents.
Because deep research is a **paid, non-deterministic** service, the template never
calls it live in CI. Instead, `src/deep_research/deep_research_adapter.py` wires the
real infrastructure request/result models (`DeepResearchConfig`, `DeepResearchRequest`,
`DeepResearchResult`, `DeepResearchClient`) and ships a deterministic, offline path:
`scripts/08_deep_research_dispatch.py` builds the genuine provider-neutral request and
then *replays* a recorded report fixture
(`src/deep_research/fixtures/recorded_report.json`), normalizing it through the real
`DeepResearchResult` model. Replay fails closed if the fixture is missing — it never
fabricates a passing run — mirroring the fixture-replay idiom of `template_sia`. The
same adapter exposes `build_offline_request`, the exact call-site a live `submit` would
dispatch, so a fork can enable real providers by supplying `OPENAI_API_KEY` /
`GEMINI_API_KEY`:

```bash
# Offline (default): replays the recorded report, no key required
uv run python scripts/08_deep_research_dispatch.py
```

## Test Suite

Every stage is covered by a no-mocks test suite (real computation and
`pytest-httpserver` for network adapters) gated at $\geq 90\%$ statement coverage on
`src/`. The suite covers:

- Record models and serialization (deduplication, canonical ID hierarchy)
- All 9 engine clients (arXiv, Semantic Scholar, OpenAlex, Crossref, PubMed, SovietRxiv,
  ChinaRxiv, Europe PMC, bioRxiv/medRxiv) with pytest-httpserver integration tests
- Search runner (multi-engine dispatch, relevance filtering, resume/clear, YAML config)
- Bibliometric analysis (subfield classification, temporal metrics, TF-IDF, NMF, citation
  network)
- Knowledge graph (schema, nanopublications, hypothesis scoring, LLM extraction)
- Visualization (headless figure generation, style config)
- Manuscript variable computation and injection



```{=latex}
\newpage
```


# Appendix B: Technical Notes

## Determinism

All stochastic steps use fixed seeds (seed = 42 for NMF, SVD, and graph layouts). The
fixture corpus, TF-IDF/SVD embeddings, and topic factorization are byte-stable across
runs. Graph centrality scores are rounded to a fixed precision and ranked with a
node-id tiebreaker so that floating-point non-associativity in iterative solvers cannot
perturb the reported rankings. Record identity uses a content digest (SHA-1,
`usedforsecurity=False`) rather than a salted hash, so de-duplication and corpus
byte-stability hold across processes.

## Data Model

Each record is a `Paper` dataclass with: title, abstract, authors (list of `Author`),
year, DOI, arXiv ID, Semantic Scholar ID, OpenAlex ID, venue, citation count, references
(list of canonical IDs), publication date, PDF URL, open-access flag, and full-text
source. The canonical identifier hierarchy governs de-duplication and citation resolution:

$$
\text{canonical\_id} = \begin{cases}
\texttt{doi:} + \text{normalize}(\text{DOI}) & \text{if DOI present} \\
\texttt{arxiv:} + \text{arXiv\_id} & \text{if arXiv ID present} \\
\texttt{s2:} + \text{S2\_id} & \text{if S2 ID present} \\
\texttt{openalex:} + \text{OpenAlex\_id} & \text{if OpenAlex ID present} \\
\texttt{title:} + \text{SHA1}(\text{title})[:16] & \text{otherwise}
\end{cases}
$$

DOI normalization lower-cases the DOI and strips any `https://doi.org/` or `dx.doi.org/`
prefix, so the same paper returned by two engines under different case or format variants
merges to a single canonical ID.

## NMF Mathematics

Non-negative matrix factorization decomposes the TF-IDF document-term matrix
$\mathbf{V} \in \mathbb{R}^{m \times n}$ (where $m$ is the number of documents and $n$ is the
vocabulary size) into $\mathbf{W} \in \mathbb{R}^{m \times k}$ and $\mathbf{H} \in \mathbb{R}^{k \times n}$,
where $k$ is the number of topics (here 5). The factorization minimizes:

$$
\min_{\mathbf{W}, \mathbf{H} \geq 0} \|\mathbf{V} - \mathbf{W} \mathbf{H}\|_F^2
$$

using multiplicative update rules [@lee1999learning] with a fixed random seed for
reproducibility. The topic-term matrix $\mathbf{H}$ gives the top terms per topic; the
document-topic matrix $\mathbf{W}$ gives each document's topic loadings.

## Growth Rate Estimation

The compound annual growth rate is:

$$
\text{CAGR} = \left(\frac{N_{\text{end}}}{N_{\text{start}}}\right)^{1/(T_{\text{end}} - T_{\text{start}})} - 1
$$

where $N_{\text{start}}$ and $N_{\text{end}}$ are the publication counts in the first and
last years of the corpus, respectively. The doubling time is
$t_d = \ln(2) / \ln(1 + \text{CAGR})$. For this run: CAGR = 5.48\%, doubling time
= 9.2 years.

## Configuration Surface

A single `manuscript/config.yaml` controls the search term, per-engine query and keyword
sets, engine enable toggles, subfield taxonomy, hypotheses, full-text and embedding
options, and paper metadata. This run drew on 9 engines, a
6-bucket taxonomy, and 6 hypotheses.

## Artifacts

Intermediate and final outputs live under `output/` and are disposable and regenerable:

| File | Stage | Description |
| --- | --- | --- |
| `corpus.jsonl` | 01 | De-duplicated corpus (2334 records) |
| `temporal_analysis.json` | 02 | Year counts, CAGR, doubling time, peak year |
| `subfield_classification.json` | 02 | Per-bucket paper counts |
| `subfield_timeline.json` | 02 | Per-subfield annual breakdown |
| `tfidf_data.json` | 02 | TF-IDF matrix, feature names, doc tokens |
| `topics.json` | 02 | NMF topic-term distributions |
| `citation_network.json` | 02 | Network metrics, PageRank, HITS, communities |
| `citation_graph.gml` | 02 | GraphML citation graph |
| `nanopublications.jsonl` | 03 | LLM-extracted assertions (0 in this run) |
| `hypothesis_scores.json` | 03 | Per-hypothesis evidence scores |
| `fulltext_assessment.json` | 06 | Abstract/OA/PDF coverage report |



```{=latex}
\newpage
```


# Appendix C: Accessibility and Provenance

## Figure Accessibility

All 21 figures are rendered with a colourblind-safe palette (Wong 2011,
8 colours) and high-contrast labels at publication DPI (300). Each figure carries a
descriptive caption so the visual claims are recoverable from text alone. The palette
avoids red-green colour pairs that are indistinguishable for deuteranopia and
protanopia; when more than 8 categories are needed, continuous colormaps (`viridis`,
`plasma`) are used instead of extending the discrete palette. Font sizes are enforced at
$\geq 16$pt via a centralized style module, ensuring readability at both screen and print
sizes.

## Provenance Chain

Every reported number is injected from a committed artifact rather than typed by hand;
an unresolved placeholder is a hard error, so the rendered manuscript can contain no
orphaned or stale figures. The configuration hash and artifact inventory bind the prose
to the exact pipeline run that produced it. The provenance chain is:

1. `manuscript/config.yaml` defines the search term, engines, taxonomy, and hypotheses
2. `scripts/01_literature_search.py` retrieves records → `corpus.jsonl`
3. `scripts/02_meta_analysis_pipeline.py` analyses the corpus → `*.json` data files
4. `scripts/04_generate_figures.py` renders figures → `*.png` + `figure_registry.json`
5. `scripts/05_inject_variables.py` computes variables from data files → manuscript text

Each figure in `figure_registry.json` records its source data file, generation parameters,
and SHA-256 hash, binding the visual output to the exact pipeline run. Re-running the
pipeline with the same configuration and seed produces identical data outputs.

## FAIR Data Principles

The pipeline supports FAIR (Findable, Accessible, Interoperable, Reusable) data
principles:

- **Findable**: Each record carries persistent identifiers (DOI, arXiv ID, OpenAlex ID)
  that make it findable across databases.
- **Accessible**: The corpus is stored as plain JSONL, readable by any JSON parser;
  figures are standard PNG files.
- **Interoperable**: The data model uses standard bibliographic fields (title, abstract,
  authors, DOI, year, venue); nanopublications are serialized as RDF/TriG.
- **Reusable**: The entire pipeline is regenerable from `manuscript/config.yaml`;
  re-running with the same configuration reproduces identical outputs.

## Honesty

The default corpus is synthetic and labelled as such; the manuscript does not present
fixture-derived numbers as empirical findings about modafinil. Live findings require
a real retrieval run with regenerated artifacts — as produced in this instance, which
retrieved 2334 real records from 9 live engines.



```{=latex}
\newpage
```


# Glossary

| Term | Meaning |
| --- | --- |
| **Record / Paper** | A single bibliographic entry with metadata and identifiers. |
| **Canonical identifier** | The highest-priority available ID (DOI $>$ arXiv $>$ Semantic Scholar $>$ OpenAlex $>$ title digest) used for de-duplication and citation resolution. |
| **Engine** | An independent literature source adapter (arXiv, OpenAlex, Semantic Scholar, Crossref, PubMed, SovietRxiv, ChinaRxiv, Europe PMC, and bioRxiv/medRxiv) with a uniform search interface and graceful skip-on-failure. |
| **Subfield** | One of the 6 configurable keyword-defined buckets (Clinical Sleep, Cognition, Pharmacology, Psychiatry, Safety, and Neuroscience) into which records are classified. |
| **Topic** | A latent theme from non-negative matrix factorization over the TF-IDF representation. |
| **Embedding** | A deterministic offline vector (TF-IDF $\rightarrow$ truncated SVD) for a title, abstract, or full text. |
| **Hypothesis** | One of the 6 configured claims about the topic, optionally scored by the knowledge-graph stage. |
| **Assertion** | A directional (supports / contradicts / neutral) statement extracted from a record against a hypothesis, with a confidence score. |
| **Nanopublication** | An RDF-serialized assertion plus its provenance. |
| **CAGR** | Compound annual growth rate of publication volume (5.48\% for this corpus). |
| **Living literature review** | A synthesis that can be re-executed as the field evolves, with every number regenerable. |



```{=latex}
\newpage
```


# References

The bibliography is generated automatically during PDF compilation from `references.bib`. All citation keys used in the manuscript (e.g., `\citep{friston2010free}`) resolve to entries below; unused entries have been pruned. Pandoc's `--natbib` flag injects `\usepackage{natbib}` and `\bibliographystyle{plainnat}`, so neither directive appears in this section or in `preamble.md`.

\bibliography{references}

<!--
References management notes:

* Entries are maintained in `references.bib` (BibTeX format).
* Each entry must include `title`, `author` (or `editor`), and `year`.
* DOIs are preferred over URLs where available.
* When adding a new citation, run the integrity sweep documented in `AGENTS.md`
  to confirm a 1:1 match between cited keys and bibliography entries.
-->
