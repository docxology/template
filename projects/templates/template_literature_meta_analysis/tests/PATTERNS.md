# Test Patterns

This suite follows the repository **no-mocks** policy: every test runs real code on
real data. There are no `unittest.mock`, `MagicMock`, or `mocker.patch` calls.

## How each boundary is exercised for real

| Boundary | Pattern | Example test class |
| --- | --- | --- |
| HTTP engine APIs (arXiv, OpenAlex, Semantic Scholar, Crossref, PubMed) | `pytest-httpserver` serves real fixture payloads; the client makes a real request to `httpserver.url_for(...)` | `TestSearchArxiv`, `TestSearchOpenalex`, `TestSearchSemanticScholar`, `TestParsePubMedArticle` |
| Full-text resolve/download | `pytest-httpserver` serves a fake Unpaywall JSON + PDF bytes; a real `requests` GET writes a real file to `tmp_path` | `tests/literature/test_fulltext_download.py` |
| Pure parsing | Hand-built API JSON/XML → assert exact `Paper` fields against an independently reasoned reference | `TestParseArxivResponse`, `TestReconstructAbstract` |
| Record model & de-dup | Construct real `Paper`/`Corpus` objects; assert canonical-id priority and merge behaviour | `TestPaperCanonicalId`, `TestCorpusAdd`, `TestCorpusMerge` |
| Statistics / bibliometrics | Small hand-built corpus with KNOWN values; assert every statistic against a hand-computed reference (Gini against a brute-force double loop — never green-by-construction) | `TestDescriptiveStats`, `TestCitationDistribution`, `TestAuthorProductivity`, `TestBuildMetaReport` |
| Embeddings | Real `scikit-learn` TF-IDF→SVD; assert determinism (`embed_texts(x) == embed_texts(x)`) and a reasoned nearest-neighbour ordering | `tests/analysis/test_embeddings.py` |
| Entities / language | Real regex extraction on strings with KNOWN entities/acronyms | `TestExtractEntities`, `TestExtractKeyphrases`, `TestCorpusEntities` |
| Figures | Headless matplotlib (`MPLBACKEND=Agg`) renders to `tmp_path`; assert the file exists and is non-empty | `TestCitationPlots`, `TestTemporalPlots`, `TestFieldOverview` |
| File I/O | Real temp files via the `tmp_path` fixture; JSONL save/load round-trips | `TestCorpusPersistence`, `TestJSONLSerialization` |
| Scripts | Executed as real modules; assert produced artifacts | `TestLiteratureSearchScript`, `TestMetaAnalysisPipelineScript`, `TestGenerateFiguresScript` |

## Determinism

Every randomized path is seeded (`config.DEFAULT_SEED = 42`): NMF topic init, the
synthetic fixture corpus, and embedding SVD/KMeans. The same inputs always produce
byte-identical outputs, which is what makes the offline pipeline idempotent.

## Adding a test

1. Pick the smallest real input that demonstrates the behaviour.
2. Compute the expected result independently (by hand or a second algorithm) — do not
   assert a value the function trivially returns.
3. For network code, serve a fixture with `pytest-httpserver`; never reach the real
   internet.
4. Keep `src/` coverage ≥ 90 %.
