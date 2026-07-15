# Results: Field Overview

The de-duplicated corpus for **Modafinil** contains $N = 2334$
records spanning 2000--2026 (26 years). Publication volume
grows at a compound annual rate of 5.48\% (mean year-over-year growth
7.8\%, doubling time 9.2 years), peaking in 2025
with 147 records that year. The growth curve is the first-order signal
that the literature is active rather than dormant.

<!-- FIGURE: growth_curve.png -->
![Publication growth curve for Modafinil. Annual publication counts (bars) and cumulative total (line) show sustained growth from 2000 through 2026, peaking in 2025.](../output/figures/growth_curve.png "Publication Growth Curve"){{#fig:growth_curve}}

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
![Field summary dashboard for Modafinil. The dashboard combines corpus size, temporal range, subfield distribution, and key bibliometric indicators in a single overview panel.](../output/figures/field_summary.png "Field Summary"){{#fig:field_summary}}

<!-- FIGURE: subfield_distribution.png -->
![Subfield distribution for Modafinil. The 6-bucket taxonomy shows the relative weight of each configured sub-area, with Clinical Sleep dominant at 63.0\%.](../output/figures/subfield_distribution.png "Subfield Distribution"){{#fig:subfield_distribution}}

<!-- FIGURE: subfield_timeline.png -->
![Subfield timeline for Modafinil. Stacked annual publication counts by subfield show how each sub-area has evolved over time, revealing emerging and declining research threads.](../output/figures/subfield_timeline.png "Subfield Timeline"){{#fig:subfield_timeline}}

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
![Citation distribution for Modafinil. The histogram shows the number of papers in each citation-count bucket, with the Gini coefficient annotated. The heavy-tailed distribution is characteristic of scientific citation networks.](../output/figures/citation_distribution.png "Citation Distribution"){{#fig:citation_distribution}}

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
![Top publication venues for Modafinil. The horizontal bar chart shows the 15 venues with the most papers in the corpus, revealing where the modafinil literature is published.](../output/figures/top_venues.png "Top Venues"){{#fig:top_venues}}

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
![Author productivity for Modafinil. The horizontal bar chart shows the 20 authors with the most papers in the corpus, revealing the most prolific contributors to the modafinil literature.](../output/figures/author_productivity.png "Author Productivity"){{#fig:author_productivity}}
