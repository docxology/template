# Technical Appendix: Mathematical and Algorithmic Details \label{sec:technical_appendix}

_This appendix collects the formal mathematical definitions, derivations, and algorithmic specifications referenced from the main methodology section._

## A.1 Citation-Weighted Hypothesis Scoring Formula

For each hypothesis $H$, we compute a citation-weighted evidence score aggregating all assertions relevant to $H$:

$$
\text{score}(H) = \frac{\sum_{a \in S(H)} w(a) - \sum_{a \in C(H)} w(a)}{\sum_{a \in A(H)} w(a)}
$$

where $S(H)$ is the set of supporting assertions, $C(H)$ is the set of contradicting assertions, $A(H)$ is all assertions for $H$ (including neutral), and the weight function is:

$$
w(a) = \log(1 + \text{citations}(a)) \cdot \text{confidence}(a)
$$

The logarithmic citation weighting ensures that highly cited papers carry more influence while preventing any single blockbuster paper from dominating the score. The score lies in $[-1, 1]$: values near $+1$ indicate strong supporting evidence, values near $-1$ indicate strong contradicting evidence, and values near $0$ indicate balanced or insufficient evidence.

**Temporal aggregation.** We additionally compute temporal trends by evaluating the cumulative score at each year $t$, using only assertions from papers published in year $\leq t$:

$$
\text{score}(H, t) = \frac{\sum_{a \in S(H,t)} w(a) - \sum_{a \in C(H,t)} w(a)}{\sum_{a \in A(H,t)} w(a)}
$$

This reveals whether support for a hypothesis is growing, declining, or plateauing over time.

## A.2 Non-negative Matrix Factorization (NMF) for Topic Modeling

We apply NMF to the TF-IDF matrix of the corpus to discover latent topics. Given the document-term matrix $V \in \mathbb{R}^{n \times m}_{\geq 0}$, NMF finds factor matrices $W \in \mathbb{R}^{n \times k}_{\geq 0}$ and $H \in \mathbb{R}^{k \times m}_{\geq 0}$ such that $V \approx WH$, where $k$ is the number of topics.

We use multiplicative update rules \citep{lee1999nmf}:

$$H \leftarrow H \odot \frac{W^T V}{W^T W H + \epsilon}, \quad W \leftarrow W \odot \frac{V H^T}{W H H^T + \epsilon}$$

with $\epsilon = 10^{-10}$ for numerical stability and a fixed random seed of 42 for reproducibility.

**Term-Frequency Inverse Document Frequency (TF-IDF).** The document-term matrix is constructed using TF-IDF weighting \citep{salton1975vector}. For term $t$ in document $d$:

$$
\text{TF-IDF}(t, d) = \text{tf}(t, d) \cdot \log\!\left(\frac{N}{\text{df}(t)}\right)
$$

where $\text{tf}(t, d)$ is the term frequency, $N$ is the total number of documents, and $\text{df}(t)$ is the document frequency of term $t$.

## A.3 Field Growth-Rate Estimation

The **mean year-over-year growth rate** $\bar{g}$ is the arithmetic mean of annual growth rates computed only for years where the prior year had non-zero publications:

$$
\bar{g} = \frac{1}{|Y|} \sum_{y \in Y} \frac{n_y - n_{y-1}}{n_{y-1}}
$$

where $Y = \{y : n_{y-1} > 0\}$ and $n_y$ is the number of publications in year $y$.

The **doubling time** $t_d$ is derived from the mean annual growth rate:

$$
t_d = \frac{\ln 2}{\ln(1 + \bar{g})}
$$

The **compound annual growth rate** (CAGR) over the full span $[y_0, y_T]$ is:

$$
\text{CAGR} = \left(\frac{n_{\text{cumulative}}(y_T)}{n_{\text{cumulative}}(y_0)}\right)^{1/(y_T - y_0)} - 1
$$

For the current corpus, CAGR $= 6.63\%$. The more recent growth phase (2010--2025) exhibits substantially higher annualized growth.

## A.4 Advanced Visualization Methods

### PCA of TF-IDF Embeddings

Principal Component Analysis (PCA) is applied to the TF-IDF matrix $V$ to project each document into a 2-D space. The projection preserves the directions of maximum variance, enabling visual inspection of document clustering by domain. Loading arrows overlay the top-variance terms onto the scatter plot, showing which vocabulary drives the principal components.

### Hierarchical Clustering Dendrogram

For each domain $s$, we compute the centroid $\bar{v}_s = \frac{1}{|D_s|} \sum_{d \in D_s} v_d$ where $D_s$ is the set of documents in domain $s$ and $v_d$ is the TF-IDF vector of document $d$. Ward linkage is applied to the centroid matrix to produce a hierarchical clustering dendrogram showing semantic proximity between domains.

### Term Heatmap

For each domain $s$ and term $t$, we compute the mean TF-IDF weight $\bar{w}_{s,t} = \frac{1}{|D_s|} \sum_{d \in D_s} \text{TF-IDF}(t, d)$. The heatmap displays $\bar{w}_{s,t}$ for the top-$k$ terms (by global document frequency) across all domains, with cell intensity proportional to mean weight. This reveals distinctive vocabulary patterns that differentiate domains beyond the keyword-level classification used for subfield assignment.

### Term Co-occurrence Matrix

The co-occurrence matrix $C \in \mathbb{R}^{k \times k}$ counts the number of documents in which two terms appear together. For top-$k$ terms by document frequency, $C_{ij} = |\{d : t_i \in d \land t_j \in d\}|$. The matrix is normalized to $[0, 1]$ by dividing by the maximum entry and visualized as a symmetric heatmap.
