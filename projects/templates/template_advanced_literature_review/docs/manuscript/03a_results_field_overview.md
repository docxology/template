# Results: Field Overview

The de-duplicated corpus for **{{SEARCH_TERM_TITLE}}** contains $N = {{CORPUS_SIZE}}$
records spanning {{YEAR_START}}--{{YEAR_END}} ({{YEAR_SPAN}} years). Publication volume
grows at a compound annual rate of {{CAGR_PCT}}\% (mean year-over-year growth
{{MEAN_YOY_GROWTH_PCT}}\%, doubling time {{DOUBLING_TIME}} years), peaking in {{PEAK_YEAR}}
with {{PEAK_YEAR_PUBS}} records that year. The growth curve is a first-order descriptive
summary of the retained corpus; it is not a field-wide estimate of research activity.

<!-- FIGURE: growth_curve.png -->
![Publication growth curve for {{SEARCH_TERM_TITLE}}. Annual publication counts (bars) and cumulative total (line) show sustained growth from {{YEAR_START}} through {{YEAR_END}}, peaking in {{PEAK_YEAR}}.](../output/figures/growth_curve.png "Publication Growth Curve"){#fig:growth_curve}

## RQ1: Field Size and Growth

The temporal analysis describes a retained literature slice spanning {{YEAR_SPAN}}
years. The compound annual growth rate of {{CAGR_PCT}}\% implies a corpus doubling time
of approximately {{DOUBLING_TIME}} years under the configured retrieval and indexing
conditions. The peak year {{PEAK_YEAR}} contains {{PEAK_YEAR_PUBS}} retained records;
that count may reflect both publication activity and delays or differences in source
indexing, so it should not be interpreted as a causal trend without a live coverage audit.

**Table 1. Top publication years.**

{{YEAR_COUNT_TABLE}}

## RQ2: Subfield Composition

Records distribute across the {{N_SUBFIELDS}} configured subfields as shown in Table 2,
with **{{TOP_SUBFIELD}}** the largest bucket at {{TOP_SUBFIELD_PCT}}\% of the classified
corpus. The dominance of {{TOP_SUBFIELD}} is a property of the configured taxonomy and
retained corpus. It is not a domain prevalence estimate without a live, source-backed
review and a documented coverage assessment.

**Table 2. Subfield distribution.**

{{SUBFIELD_TABLE}}

<!-- FIGURE: field_summary.png -->
![Field summary dashboard for {{SEARCH_TERM_TITLE}}. The dashboard combines corpus size, temporal range, subfield distribution, and key bibliometric indicators in a single overview panel.](../output/figures/field_summary.png "Field Summary"){#fig:field_summary}

<!-- FIGURE: subfield_distribution.png -->
![Subfield distribution for {{SEARCH_TERM_TITLE}}. The {{N_SUBFIELDS}}-bucket taxonomy shows the relative weight of each configured sub-area, with {{TOP_SUBFIELD}} dominant at {{TOP_SUBFIELD_PCT}}\%.](../output/figures/subfield_distribution.png "Subfield Distribution"){#fig:subfield_distribution}

\newpage

<!-- FIGURE: subfield_timeline.png -->
![Subfield timeline for {{SEARCH_TERM_TITLE}}. Stacked annual publication counts by subfield show how each sub-area has evolved over time, revealing emerging and declining research threads.](../output/figures/subfield_timeline.png "Subfield Timeline"){#fig:subfield_timeline}

## Identifier and Full-Text Coverage

The corpus has measurable identifier coverage: {{DOI_COUNT}} of {{CORPUS_SIZE}} records
({{PCT_WITH_DOI}}\%) carry DOIs, supporting cross-engine de-duplication.
OpenAlex IDs are present for {{OPENALEX_ID_COUNT}} records. Abstract coverage stands at
{{ABSTRACT_COVERAGE_PCT}}\% ({{ABSTRACT_COUNT}} records), which limits the text analytics
to that subset. Open-access status is confirmed for {{OA_PCT}}\% of records, and
{{PDF_AVAIL_PCT}}\% have a direct PDF link.

## Descriptive Bibliometrics

The corpus spans {{UNIQUE_AUTHORS}} unique authors across {{CORPUS_SIZE}} papers, yielding
a mean of {{PAPERS_PER_AUTHOR_MEAN}} papers per author. Citation counts range from zero to
{{CITATION_MAX}} (mean {{CITATION_MEAN}}, median {{CITATION_MEDIAN}}), with a total of
{{CITATION_TOTAL}} citations across the corpus. The Gini coefficient of citation
concentration is {{GINI_COEFFICIENT}}. This statistic describes concentration within
the retained corpus and should not be generalized to citation behavior in the field.

**Table 3. Citation count distribution.**

{{CITATION_DIST_TABLE}}

<!-- FIGURE: citation_distribution.png -->
![Citation distribution for {{SEARCH_TERM_TITLE}}. The histogram shows the number of papers in each citation-count bucket, with the Gini coefficient annotated. The distribution is a descriptive property of the retained corpus.](../output/figures/citation_distribution.png "Citation Distribution"){#fig:citation_distribution}

\newpage

**Table 4. Top publication venues.**

{{TOP_VENUES_TABLE}}

<!-- FIGURE: top_venues.png -->
![Top publication venues for {{SEARCH_TERM_TITLE}}. The horizontal bar chart shows the venues with the most retained records; it describes this corpus rather than the complete field.](../output/figures/top_venues.png "Top Venues"){#fig:top_venues}

**Table 5. Top authors by publication count.**

{{TOP_AUTHORS_TABLE}}

<!-- FIGURE: author_productivity.png -->
![Author productivity for {{SEARCH_TERM_TITLE}}. The horizontal bar chart shows authors with the most retained records; names and counts depend on source coverage and deduplication.](../output/figures/author_productivity.png "Author Productivity"){#fig:author_productivity}
