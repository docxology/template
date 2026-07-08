# infrastructure/search/connectors/impl/ — Connector implementations

Shared base classes and concrete connector adapters invoked by
`infrastructure.search.connectors` and opt-in pipeline stage
`scripts/pipeline/stage_08_connector_search.py`.

| Module | Role |
| --- | --- |
| `base.py` | Connector protocol and shared helpers |
| `arxiv.py` | `ArxivConnector` — queries the unauthenticated arXiv Atom/OpenSearch API for physics/math/CS/quantitative-biology preprints; parses the Atom feed into `ConnectorHit`s and fetches single records by id. |
| `biorxiv.py` | `BiorxivConnector` — queries the bioRxiv/medRxiv details API over a date window and filters by title/abstract terms (the API lacks full-text search); covers life-science and medical preprints. |
| `crossref.py` | `CrossrefConnector` — queries the Crossref REST `/works` DOI registry (polite-pool `mailto`) for journal articles, books, and conference papers; fetches single works by DOI. |
| `europepmc.py` | `EuropePMCConnector` — queries the Europe PMC REST `/search` endpoint for life-sciences literature from PubMed Central and partner repositories, with `PUB_YEAR` filters and fetch-by-external-id. |
| `openalex.py` | `OpenAlexConnector` — queries the OpenAlex `/works` catalog of scholarly works (polite `mailto`) and reconstructs abstracts from OpenAlex's inverted-index format. |
| `pdb.py` | `PDBConnector` — full-text search against the RCSB PDB search API for 3-D macromolecular structures; fetches entry metadata from the RCSB data API. |
| `semantic_scholar.py` | `SemanticScholarConnector` — queries the Semantic Scholar Graph API paper search (optional `x-api-key`), returning citation-graph metadata and a score derived from citation count and rank. |
| `uniprot.py` | `UniProtConnector` — queries the UniProtKB REST search for protein sequences, function, and taxonomy; fetches single entries by accession. |

## See also

- [`../AGENTS.md`](../AGENTS.md) (parent package)
- [`README.md`](README.md)
