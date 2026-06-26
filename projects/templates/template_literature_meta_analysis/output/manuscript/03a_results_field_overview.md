# Results: Field Overview

The de-duplicated corpus for **Modafinil** contains $N = 2302$
records spanning 2000--2026 (26 years). Publication volume
grows at a compound annual rate of 3.45\% (mean year-over-year growth
6.3\%, doubling time 11.3 years), peaking in 2025
with 112 records that year. The growth curve is the first-order signal
that the literature is active rather than dormant.

<!-- FIGURE: growth_curve.png -->
![Publication growth curve for Modafinil. Annual publication counts (bars) and cumulative total (line) show sustained growth from 2000 through 2026, peaking in 2025.](figures/growth_curve.png "Publication Growth Curve"){{#fig:growth_curve}}

## RQ1: Field Size and Growth

The temporal analysis reveals a literature that has grown steadily over 26
years. The compound annual growth rate of 3.45\% means the corpus roughly doubles
every 11.3 years — a pace that exceeds the general biomedical literature
growth rate of approximately 4\% per year. The peak year 2025 with
112 publications likely reflects both genuine research activity and the
lag between publication and indexing in the source databases.

**Table 1. Top publication years.**

| Year | Publications |
| --- | --- |
| 2015 | 101 |
| 2016 | 110 |
| 2017 | 109 |
| 2018 | 101 |
| 2019 | 107 |
| 2020 | 109 |
| 2021 | 106 |
| 2022 | 103 |
| 2024 | 109 |
| 2025 | 112 |

## RQ2: Subfield Composition

Records distribute across the 6 configured subfields as shown in Table 2,
with **Clinical Sleep** the largest bucket at 64.3\% of the classified
corpus. The dominance of Clinical Sleep reflects the clinical primacy of
modafinil as a wakefulness-promoting agent: the largest body of literature addresses
its use in narcolepsy, shift-work disorder, and obstructive sleep apnea.

**Table 2. Subfield distribution.**

| Subfield | Papers | Share |
| --- | --- | --- |
| Clinical Sleep | 1417 | 64.3% |
| Cognition | 233 | 10.6% |
| Pharmacology | 74 | 3.4% |
| Psychiatry | 357 | 16.2% |
| Safety | 82 | 3.7% |
| Neuroscience | 41 | 1.9% |

<!-- FIGURE: field_summary.png -->
![Field summary dashboard for Modafinil. The dashboard combines corpus size, temporal range, subfield distribution, and key bibliometric indicators in a single overview panel.](figures/field_summary.png "Field Summary"){{#fig:field_summary}}

<!-- FIGURE: subfield_distribution.png -->
![Subfield distribution for Modafinil. The 6-bucket taxonomy shows the relative weight of each configured sub-area, with Clinical Sleep dominant at 64.3\%.](figures/subfield_distribution.png "Subfield Distribution"){{#fig:subfield_distribution}}

<!-- FIGURE: subfield_timeline.png -->
![Subfield timeline for Modafinil. Stacked annual publication counts by subfield show how each sub-area has evolved over time, revealing emerging and declining research threads.](figures/subfield_timeline.png "Subfield Timeline"){{#fig:subfield_timeline}}

## Identifier and Full-Text Coverage

The corpus has strong identifier coverage: 2248 of 2302 records
(98.0\%) carry DOIs, enabling robust cross-engine de-duplication.
OpenAlex IDs are present for 932 records. Abstract coverage stands at
55.5\% (1277 records), which limits the text analytics
to that subset. Open-access status is confirmed for 14.4\% of records, and
40.9\% have a direct PDF link.

## Descriptive Bibliometrics

The corpus spans 7259 unique authors across 2302 papers, yielding
a mean of 1.34 papers per author. Citation counts range from zero to
1333 (mean 30.9, median 0.0), with a total of
68,151 citations across the corpus. The Gini coefficient of citation
concentration is 0.812, indicating a highly skewed distribution
characteristic of scientific literature.

**Table 3. Citation count distribution.**

| Citations | Papers |
| --- | --- |
| 0 | 1184 |
| 1-9 | 195 |
| 10-49 | 421 |
| 50-99 | 214 |
| 100-499 | 179 |
| 500+ | 11 |

<!-- FIGURE: citation_distribution.png -->
![Citation distribution for Modafinil. The histogram shows the number of papers in each citation-count bucket, with the Gini coefficient annotated. The heavy-tailed distribution is characteristic of scientific citation networks.](figures/citation_distribution.png "Citation Distribution"){{#fig:citation_distribution}}

**Table 4. Top publication venues.**

| Venue | Papers |
| --- | --- |
| Reactions Weekly | 142 |
| Psychopharmacology | 41 |
| SLEEP | 34 |
| Sleep Medicine | 33 |
| The Journal of Clinical Psychiatry | 31 |
| European Neuropsychopharmacology | 27 |
| Neuropharmacology | 26 |
| Inpharma Weekly | 25 |
| PubMed | 24 |
| American Journal of Psychiatry | 23 |

<!-- FIGURE: top_venues.png -->
![Top publication venues for Modafinil. The horizontal bar chart shows the 15 venues with the most papers in the corpus, revealing where the modafinil literature is published.](figures/top_venues.png "Top Venues"){{#fig:top_venues}}

**Table 5. Top authors by publication count.**

| Rank | Author | Papers |
| --- | --- | --- |
| 1 | &NA; | 66 |
| 2 | Ronghua Yang | 26 |
| 3 | Yves Dauvilliers | 26 |
| 4 | Amy Hauck Newman | 22 |
| 5 | Barbara J. Sahakian | 20 |
| 6 | Edward T. Hellriegel | 17 |
| 7 | Gianluigi Tanda | 16 |
| 8 | Philmore Robertson | 16 |
| 9 | Sanjay Arora | 16 |
| 10 | Gert Lubec | 15 |

<!-- FIGURE: author_productivity.png -->
![Author productivity for Modafinil. The horizontal bar chart shows the 20 authors with the most papers in the corpus, revealing the most prolific contributors to the modafinil literature.](figures/author_productivity.png "Author Productivity"){{#fig:author_productivity}}
