# Retrieval and De-duplication

Retrieval dispatches the configured query across {{N_ENGINES}} independent literature
engines ({{ENGINE_LIST}}). Each engine is an isolated adapter exposing a uniform
`search(query) -> list[Record]` interface; engines that are keyless — arXiv, OpenAlex
[@priem2022openalex], Crossref [@hendricks2020crossref], and PubMed/Entrez
[@sayers2022entrez] — need no credentials, while Semantic Scholar [@kinney2023semantic]
uses a key when present. Optional full-text resolution queries Unpaywall
[@piwowar2018state] for open-access locations. **Multiple
dispatch degrades gracefully**: an engine that is disabled in the configuration, lacks a
required key, or cannot reach the network returns a *skipped* status, and the run
completes from the remaining engines plus the committed offline corpus.

Heterogeneous records are reconciled by a **canonical identifier hierarchy** —
DOI $>$ arXiv ID $>$ Semantic Scholar ID $>$ OpenAlex ID $>$ a stable digest of the
normalized title. When two records share a canonical identifier they are merged, keeping
the version with the most complete metadata. The de-duplicated corpus for this run holds
$N = {{CORPUS_SIZE}}$ records published across {{YEAR_START}}--{{YEAR_END}}.
