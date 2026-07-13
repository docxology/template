# Retrieval and De-duplication

Retrieval dispatches the configured query across {{N_ENGINES}} independent literature
engines ({{ENGINE_LIST}}). Each engine is an isolated adapter exposing a uniform
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
two engines under case/format-variant DOIs merges. For this run, {{DOI_COUNT}} records
carry DOIs, {{OPENALEX_ID_COUNT}} carry OpenAlex IDs, and {{ARXIV_ID_COUNT}} carry arXiv
IDs. The de-duplicated corpus for this run holds $N = {{CORPUS_SIZE}}$ records published
across {{YEAR_START}}--{{YEAR_END}}.

## Relevance Filtering

After de-duplication, a relevance filter drops papers whose title and abstract contain
none of the configured relevance keywords ({{KEYWORDS_RELEVANCE}}). Keywords are matched
case-insensitively; an empty keyword list is treated as no filter to avoid silently
wiping the corpus. A year filter then excludes papers published before the configured
start year ({{YEAR_START}}).
