# Literature Review Prompt

You are performing a systematic literature review as part of the SURVEY stage
of the research workflow.

## Objectives

1. Retrieve relevant papers from multiple scientific databases.
2. Normalise retrieved records into a consistent schema.
3. De-duplicate across sources.
4. Assess relevance and assign scores.
5. Produce a final corpus file.

## Step-by-Step Process

### Step 1: Formulate Search Queries

Given the research question from `domain_profile.yaml`:

- Extract 3–5 key terms.
- Create Boolean queries appropriate for each database.
  - arXiv: `all:<term>` or `ti:<term> AND abs:<term>`
  - OpenAlex: natural-language search
  - Semantic Scholar: keyword search
  - Crossref: `query=<term>`
  - Europe PMC: `<term> AND SRC:MED`

### Step 2: Execute Searches

For each database connector:
- Use `search_connector(name, query, max_results=20)`.
- Capture and log any errors (do not let a single failure abort the survey).
- Collect raw `ConnectorHit` objects.

### Step 3: Normalise Records

Convert each `ConnectorHit` to a normalised record:
- Assign a stable `id` (prefer DOI, then arXiv ID, then source:title).
- Fill `title`, `authors`, `year`, `abstract`, `doi`, `url`.
- Set `source` to the connector name.
- Score by relevance (connector-provided, or heuristic).

### Step 4: De-duplicate

Merge records with matching:
1. DOI (case-insensitive).
2. arXiv ID.
3. Normalised (title, year) — case-insensitive, punctuation-stripped.

Keep the higher-scored copy; fill missing fields from the lower-scored copy.

### Step 5: Assess Relevance

For each remaining record:
- Flag records where title or abstract does not contain any search terms.
- Mark low-relevance records (`score < 0.3`) as advisory rather than primary.
- Keep all records in the corpus; use `relevant: true/false` metadata.

### Step 6: Save Corpus

Write `output/literature/corpus.json`:

```json
{
  "query": "<the research question>",
  "sources": ["openalex", "arxiv", "semantic_scholar"],
  "total": 42,
  "papers": [
    {
      "id": "doi:10.xxxx/...",
      "title": "...",
      "authors": ["..."],
      "year": 2023,
      "abstract": "...",
      "source": "openalex",
      "score": 0.87
    }
  ]
}
```

## Quality Thresholds

| Check | Threshold |
|---|---|
| Minimum unique records | 5 |
| Minimum sources queried | 2 |
| Records with abstracts | ≥ 50% |
| Year range coverage | within last 10 years |

## Output

A `SearchResult`-compatible corpus at `output/literature/corpus.json`.  Feed
this corpus into the HYPOTHESISE stage.
