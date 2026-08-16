# Results: Language, Topics, and Embeddings

## RQ3: Topical and Linguistic Structure

Text analysis operates over titles, abstracts, and (when available) full text. A TF-IDF
representation over a 137-feature vocabulary feeds non-negative matrix
factorization, which extracts 5 latent topics cross-cutting the subfield
taxonomy. The top vocabulary terms are: atmospheric, uncertainty, spectra, temperature, abundance, analysis, assumptions, opacity, retrievals, sources, stellar, coverage, evaluated, observed, across, composition, models, provide, competing, retrieval.

**Table 3. NMF topics extracted from the corpus.**

| Topic | Top terms |
| --- | --- |
| 0 | atmospheric, cloud, retrieved, species, changes, structure, models, explore |
| 1 | prior, methane, depend, spectral, dioxide, simulated, carbon, constrained |
| 2 | contributions, separate, resolution, planetary, high, systematics, modelled, instrument |
| 3 | population, reporting, studies, preprocessing, require, harmonized, separates, specific |
| 4 | model, intervals, misspecification, noise, quantify, effect, record, dependencies |

The topic labels are computed from the retained corpus and are not hand-assigned. Their
interpretation should be checked against the generated topic-term weights and the
configured subfield taxonomy; fixture-derived topics describe synthetic text patterns,
not the scientific field.

<!-- FIGURE: topic_term_bars.png -->
![Topic-term bar charts for Exoplanet Atmospheres. Each panel shows the top weighted terms for one of 5 NMF topics, with bar length proportional to the topic-term weight in the $\mathbf{H}$ matrix.](../output/figures/topic_term_bars.png "Topic-Term Weights"){#fig:topic_term_bars}

## Document Embeddings

Offline deterministic embeddings (TF-IDF followed by truncated SVD) place every document
in a shared 50-dimensional vector space. Embedding the same text twice yields identical
vectors, so the derived similarity matrix, nearest-neighbour lists, clusters, and
two-dimensional projection are all reproducible.

<!-- FIGURE: pca_embeddings.png -->
![PCA projection of document embeddings for Exoplanet Atmospheres. Each point represents one document projected onto the first two principal components of the TF-IDF/SVD embedding. Colours indicate subfield assignment, showing how the topical geography relates to the keyword taxonomy.](../output/figures/pca_embeddings.png "PCA Embeddings"){#fig:pca_embeddings}

<!-- FIGURE: dendrogram.png -->
![Hierarchical clustering dendrogram of document embeddings. The tree shows the similarity structure of the corpus: documents that join low in the tree are semantically similar, while high-level splits separate the major topical clusters.](../output/figures/dendrogram.png "Document Dendrogram"){#fig:dendrogram}

## Term Analysis

The TF-IDF term heatmap reveals which terms discriminate between subfields: terms with
high between-subfield variance (rather than high global mean) are selected for display.

<!-- FIGURE: term_heatmap.png -->
![Term heatmap for Exoplanet Atmospheres. Each cell shows the mean TF-IDF weight of a term within a subfield. Terms are selected by between-subfield variance to highlight discriminative vocabulary rather than globally frequent terms.](../output/figures/term_heatmap.png "Term Heatmap"){#fig:term_heatmap}

\newpage

## Named Entity Analysis

Named entity extraction over the 80 abstracts identified 1
unique entities. The most frequent entities reflect the retained corpus and the
configured extraction rules; source coverage and fixture status determine how they may
be interpreted.

**Table 4. Top named entities in abstracts.**

| Entity | Frequency |
| --- | --- |
| JWST | 17 |

<!-- FIGURE: entity_bar_chart.png -->
![Top named entities for Exoplanet Atmospheres. The horizontal bar chart shows the 20 most frequently extracted entities from abstracts, revealing recurring objects, instruments, methods, and concepts in the retained corpus.](../output/figures/entity_bar_chart.png "Named Entities"){#fig:entity_bar_chart}

\clearpage

**Table 5. Top keyphrases by TF-IDF score.**

| Keyphrase | Score |
| --- | --- |
| jwst | 0.0714 |
| population | 0.0556 |
| analyses | 0.0435 |
| calibration | 0.0435 |
| calibration choices | 0.0435 |
| choices | 0.0435 |
| combined | 0.0435 |
| jwst analyses | 0.0435 |
| models | 0.0435 |
| models calibration | 0.0435 |
| models calibration choices | 0.0435 |
| model | 0.0400 |
| atmospheric | 0.0392 |
| abundance | 0.0385 |
| assumptions | 0.0385 |

## Embedding Similarity and Clustering

The TF-IDF/SVD embeddings place every document in a 50-dimensional vector space. K-means
clustering with $k = 5$ clusters partitions the corpus into
topically coherent groups. The top similar document pairs, ranked by cosine similarity,
reveal the most closely related works in the corpus.

**Table 6. Top 10 most similar document pairs.**

| Paper A | Paper B | Similarity |
| --- | --- | --- |
| doi:10.5555/exoplanet atmosphe | doi:10.5555/exoplanet atmosphe | 1.0000 |
| doi:10.5555/exoplanet atmosphe | doi:10.5555/exoplanet atmosphe | 1.0000 |
| doi:10.5555/exoplanet atmosphe | doi:10.5555/exoplanet atmosphe | 1.0000 |
| doi:10.5555/exoplanet atmosphe | doi:10.5555/exoplanet atmosphe | 1.0000 |
| doi:10.5555/exoplanet atmosphe | doi:10.5555/exoplanet atmosphe | 1.0000 |
| doi:10.5555/exoplanet atmosphe | doi:10.5555/exoplanet atmosphe | 1.0000 |
| doi:10.5555/exoplanet atmosphe | doi:10.5555/exoplanet atmosphe | 1.0000 |
| doi:10.5555/exoplanet atmosphe | doi:10.5555/exoplanet atmosphe | 1.0000 |
| doi:10.5555/exoplanet atmosphe | doi:10.5555/exoplanet atmosphe | 1.0000 |
| doi:10.5555/exoplanet atmosphe | doi:10.5555/exoplanet atmosphe | 1.0000 |

<!-- FIGURE: similarity_heatmap.png -->
![Document similarity for Exoplanet Atmospheres. The horizontal bar chart shows the 15 most similar document pairs ranked by cosine similarity of their TF-IDF/SVD embeddings. High-similarity pairs share topical and lexical content.](../output/figures/similarity_heatmap.png "Similar Document Pairs"){#fig:similarity_heatmap}

<!-- FIGURE: word_cloud.png -->
![Term cloud for Exoplanet Atmospheres. Term sizes are proportional to their TF-IDF weights across the corpus, providing a visual summary of the dominant vocabulary.](../output/figures/word_cloud.png "Term Cloud"){#fig:word_cloud}

<!-- FIGURE: cooccurrence_matrix.png -->
![Term co-occurrence matrix for Exoplanet Atmospheres. Each cell shows the normalized co-occurrence frequency of two terms within the same document, revealing which concepts tend to appear together in the literature.](../output/figures/cooccurrence_matrix.png "Term Co-occurrence"){#fig:cooccurrence_matrix}

These embeddings support semantic retrieval over the corpus and the visual map of the
literature's topical geography.
