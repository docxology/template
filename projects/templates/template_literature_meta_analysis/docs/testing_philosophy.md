# Testing Philosophy

The suite enforces the repository **no-mocks** rule: real code runs on real data,
HTTP is served locally by `pytest-httpserver`, and file I/O uses real temp files.
`src/` coverage is gated at **≥ 90 %**. See [`../tests/PATTERNS.md`](../tests/PATTERNS.md)
for the concrete per-boundary patterns.

## Why no mocks

A mock asserts that you *called* something; this template asserts what the code
*computed*. Bibliometric statistics, de-duplication, embeddings, and parsers all have
checkable outputs, so every test binds to an independently derived expected value
rather than a stubbed return. A green suite therefore means the math is right, not
merely that the wiring was invoked.

## What each layer tests

| Layer | Representative test classes |
| --- | --- |
| Record model & de-duplication | `TestPaperCanonicalId`, `TestPaperSerialization`, `TestCorpusAdd`, `TestCorpusMerge`, `TestCorpusPersistence` |
| Retrieval engines (real HTTP via `pytest-httpserver`) | `TestSearchArxiv`, `TestParseArxivResponse`, `TestSearchOpenalex`, `TestSearchSemanticScholar`, `TestParsePubMedArticle` |
| Multi-engine dispatch & filtering | `TestLiteratureSearchScript`, `TestClassifyCorpus`, `TestClassifyPaper` |
| Descriptive stats & meta-report | `TestDescriptiveStats`, `TestCitationDistribution`, `TestAuthorProductivity`, `TestBuildMetaReport`, `TestSaveMetaReport` |
| Language & entities | `TestExtractEntities`, `TestExtractKeyphrases`, `TestCorpusEntities`, `TestTokenize`, `TestRemoveStopwords` |
| Embeddings & topics | `TestBuildTfidfMatrix`, `TestFitNMFTopics`, `TestGetDocumentTopics` |
| Bibliometrics | `TestBuildCitationGraph`, `TestComputeNetworkMetrics`, `TestComputeTemporalMetrics`, `TestEstimateGrowthRate` |
| Knowledge graph (optional, LLM-gated) | `TestStandardHypotheses`, `TestScoreHypothesis`, `TestCreateNanopub`, `TestNanopubRDF` |
| Figures (headless matplotlib) | `TestCitationPlots`, `TestTemporalPlots`, `TestFieldOverview`, `TestHypothesisCharts` |
| Manuscript variables | `TestComputeVariables`, `TestInjectVariables`, `TestLatexNumber` |

## Determinism

All randomness is seeded (`config.DEFAULT_SEED = 42`). The synthetic fixture corpus,
NMF initialisation, and the embedding SVD/KMeans are reproducible, so re-running the
offline pipeline produces byte-identical artifacts — the property the idempotency
tests rely on.

## Error paths

Network clients and the figure runner degrade gracefully: a failed engine, malformed
payload, or non-convergent graph algorithm is caught at a justified safety-net handler
and turned into an empty/`skipped` result rather than an exception. Tests drive those
paths with real fixtures (HTTP errors, malformed JSON/XML, empty corpora) — see the
error-path tests in `tests/literature/` and `tests/analysis/`.
