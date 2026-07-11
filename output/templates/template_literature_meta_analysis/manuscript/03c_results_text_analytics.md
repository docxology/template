# Results: Language, Topics, and Embeddings

## RQ3: Topical and Linguistic Structure

Text analysis operates over titles, abstracts, and (when available) full text. A TF-IDF
representation over a 500-feature vocabulary feeds non-negative matrix
factorization, which extracts 5 latent topics cross-cutting the subfield
taxonomy. The top vocabulary terms are: modafinil, treatment, study, effects, patients, results, sleep, used, use, drug, studies, clinical, mg, using, placebo, cognitive, associated, effect, however, disorder.

**Table 3. NMF topics extracted from the corpus.**

| Topic | Top terms |
| --- | --- |
| 0 | cognitive, use, drugs, enhancement, performance, drug, effects, modafinil |
| 1 | adhd, ci, 95, studies, trials, evidence, risk, treatment |
| 2 | modafinil, mg, kg, effects, dose, rats, induced, placebo |
| 3 | sleep, narcolepsy, sleepiness, patients, eds, daytime, excessive, cataplexy |
| 4 | fatigue, patients, placebo, modafinil, scale, depression, treatment, armodafinil |

The topics reveal the thematic structure of the literature: Topic 0 centres on cognitive
enhancement and neuroenhancement; Topic 1 addresses ADHD treatment and clinical evidence;
Topic 2 covers pharmacological dose-response studies (including animal models); Topic 3
focuses on sleep disorders (narcolepsy, excessive daytime sleepiness); and Topic 4
addresses fatigue in psychiatric populations. These topics cross-cut the keyword-based
subfield taxonomy, revealing connections that the explicit classification does not
capture.

<!-- FIGURE: topic_term_bars.png -->
![Topic-term bar charts for Modafinil. Each panel shows the top weighted terms for one of 5 NMF topics, with bar length proportional to the topic-term weight in the $\mathbf{H}$ matrix.](../output/figures/topic_term_bars.png "Topic-Term Weights"){{#fig:topic_term_bars}}

## Document Embeddings

Offline deterministic embeddings (TF-IDF followed by truncated SVD) place every document
in a shared 50-dimensional vector space. Embedding the same text twice yields identical
vectors, so the derived similarity matrix, nearest-neighbour lists, clusters, and
two-dimensional projection are all reproducible.

<!-- FIGURE: pca_embeddings.png -->
![PCA projection of document embeddings for Modafinil. Each point represents one document projected onto the first two principal components of the TF-IDF/SVD embedding. Colours indicate subfield assignment, showing how the topical geography relates to the keyword taxonomy.](../output/figures/pca_embeddings.png "PCA Embeddings"){{#fig:pca_embeddings}}

<!-- FIGURE: dendrogram.png -->
![Hierarchical clustering dendrogram of document embeddings. The tree shows the similarity structure of the corpus: documents that join low in the tree are semantically similar, while high-level splits separate the major topical clusters.](../output/figures/dendrogram.png "Document Dendrogram"){{#fig:dendrogram}}

## Term Analysis

The TF-IDF term heatmap reveals which terms discriminate between subfields: terms with
high between-subfield variance (rather than high global mean) are selected for display.

<!-- FIGURE: term_heatmap.png -->
![Term heatmap for Modafinil. Each cell shows the mean TF-IDF weight of a term within a subfield. Terms are selected by between-subfield variance to highlight discriminative vocabulary rather than globally frequent terms.](../output/figures/term_heatmap.png "Term Heatmap"){{#fig:term_heatmap}}

## Named Entity Analysis

Named entity extraction over the 1277 abstracts identified 30
unique entities. The most frequent entities reflect the clinical and pharmacological
vocabulary of the modafinil literature.

**Table 4. Top named entities in abstracts.**

| Entity | Frequency |
| --- | --- |
| ADHD | 338 |
| CI | 315 |
| EDS | 258 |
| OSA | 236 |
| MOD | 158 |
| RESULTS | 152 |
| DAT | 133 |
| MS | 132 |
| CONCLUSIONS | 130 |
| ESS | 127 |
| SD | 113 |
| METHODS | 102 |
| CE | 101 |
| MD | 97 |
| IH | 88 |

<!-- FIGURE: entity_bar_chart.png -->
![Top named entities for Modafinil. The horizontal bar chart shows the 20 most frequently extracted named entities from abstracts, revealing the dominant drugs, conditions, and concepts in the literature.](../output/figures/entity_bar_chart.png "Named Entities"){{#fig:entity_bar_chart}}

**Table 5. Top keyphrases by TF-IDF score.**

| Keyphrase | Score |
| --- | --- |
| available | 0.3333 |
| abstract | 0.3333 |
| abstract available | 0.3333 |
| content | 0.1053 |
| access | 0.1053 |
| md | 0.0870 |
| jama | 0.0826 |
| cleveland | 0.0763 |
| modafinil | 0.0741 |
| depression | 0.0741 |
| substance | 0.0694 |
| drug | 0.0667 |
| conditions | 0.0667 |
| continuous | 0.0667 |
| continuous flow | 0.0667 |

## Embedding Similarity and Clustering

The TF-IDF/SVD embeddings place every document in a 50-dimensional vector space. K-means
clustering with $k = 5$ clusters partitions the corpus into
topically coherent groups. The top similar document pairs, ranked by cosine similarity,
reveal the most closely related works in the corpus.

**Table 6. Top 10 most similar document pairs.**

| Paper A | Paper B | Similarity |
| --- | --- | --- |
| doi:10.1176/appi.ajp.163.12.21 | doi:10.1176/ajp.2006.163.12.21 | 1.0000 |
| doi:10.1176/ajp.2006.163.12.21 | doi:10.1176/appi.ajp.163.12.21 | 1.0000 |
| doi:10.1197/j.aem.2005.08.013 | doi:10.1111/j.1553-2712.2006.t | 1.0000 |
| doi:10.1345/aph.1h302 | doi:10.1136/bcr.08.2011.4652 | 0.9687 |
| doi:10.4088/jcp.09m05900gry | doi:10.1186/s40345-015-0034-0 | 0.9628 |
| doi:10.1016/s2215-0366(18)3026 | doi:10.1016/s2215-0366(25)0006 | 0.9621 |
| doi:10.1345/aph.1h302 | doi:10.1017/neu.2023.6 | 0.9598 |
| doi:10.1111/j.1365-2869.2008.0 | doi:10.3109/07420528.2011.6352 | 0.9538 |
| doi:10.1513/annalsats.202006-6 | doi:10.3760/cma.j.cn112147-202 | 0.9532 |
| doi:10.1345/aph.1h302 | doi:10.1192/bjo.2024.75 | 0.9517 |

<!-- FIGURE: similarity_heatmap.png -->
![Document similarity for Modafinil. The horizontal bar chart shows the 15 most similar document pairs ranked by cosine similarity of their TF-IDF/SVD embeddings. High-similarity pairs share topical and lexical content.](../output/figures/similarity_heatmap.png "Similar Document Pairs"){{#fig:similarity_heatmap}}

<!-- FIGURE: word_cloud.png -->
![Term cloud for Modafinil. Term sizes are proportional to their TF-IDF weights across the corpus, providing a visual summary of the dominant vocabulary.](../output/figures/word_cloud.png "Term Cloud"){{#fig:word_cloud}}

<!-- FIGURE: cooccurrence_matrix.png -->
![Term co-occurrence matrix for Modafinil. Each cell shows the normalized co-occurrence frequency of two terms within the same document, revealing which concepts tend to appear together in the literature.](../output/figures/cooccurrence_matrix.png "Term Co-occurrence"){{#fig:cooccurrence_matrix}}

These embeddings support semantic retrieval over the corpus and the visual map of the
literature's topical geography.
