# Results: Citation Network

## RQ4: Citation Geometry

Resolving each record's references against the corpus yields an intra-corpus citation
graph (built and analyzed with NetworkX [@hagberg2008exploring]) of 46
nodes and 48 edges across 10 connected components,
with a graph density of 2.32\% and a mean in-degree of
1.0. Of 96 total outgoing references,
50.0\% resolve to another record inside the corpus. This
resolution rate describes how self-contained the retrieved slice is; it is not an
estimate of the underlying citation density of any individual work.

The citation network has 15 communities (detected by modularity
optimization), a maximum in-degree of 6 (the most-cited paper
within the corpus), and a maximum out-degree of 4 (the paper
that cites the most other corpus members).

## Centrality Analysis

Centrality scores (PageRank [@page1999pagerank] and HITS) and modularity-based community
detection [@clauset2004finding] are rounded and ranked with a stable tiebreaker so the
reported hub and authority rankings are byte-reproducible across runs despite the
floating-point non-associativity of the underlying iterative solvers.

**Table 4. Top 5 papers by PageRank.**

| Rank | DOI | PageRank |
| --- | --- | --- |
| 1 | 10.5555/exoplanet atmospheres.0000 | 0.100386 |
| 2 | 10.5555/exoplanet atmospheres.0005 | 0.094693 |
| 3 | 10.5555/exoplanet atmospheres.0008 | 0.089991 |
| 4 | 10.5555/exoplanet atmospheres.0010 | 0.080374 |
| 5 | 10.5555/exoplanet atmospheres.0015 | 0.044154 |

**Table 5. Top 5 authority papers (HITS).**

| Rank | DOI | Authority |
| --- | --- | --- |
| 1 | 10.5555/exoplanet atmospheres.0010 | 0.328136 |
| 2 | 10.5555/exoplanet atmospheres.0016 | 0.117442 |
| 3 | 10.5555/exoplanet atmospheres.0047 | 0.097992 |
| 4 | 10.5555/exoplanet atmospheres.0009 | 0.080540 |
| 5 | 10.5555/exoplanet atmospheres.0015 | 0.076253 |

**Table 6. Top 5 hub papers (HITS).**

| Rank | DOI | Hub |
| --- | --- | --- |
| 1 | 10.5555/exoplanet atmospheres.0057 | 0.126454 |
| 2 | 10.5555/exoplanet atmospheres.0018 | 0.121085 |
| 3 | 10.5555/exoplanet atmospheres.0078 | 0.115800 |
| 4 | 10.5555/exoplanet atmospheres.0056 | 0.111057 |
| 5 | 10.5555/exoplanet atmospheres.0015 | 0.089171 |

The highest-ranked paper by PageRank (DOI 10.5555/exoplanet atmospheres.0000) is a central node in the
retained citation graph. Its score indicates relative centrality within this graph, not
scientific importance or causal influence. Hub papers cite many corpus members and may
connect threads of the retrieved literature, but their role should be checked against
their source type and content.

<!-- FIGURE: citation_network.png -->
![Citation network for Exoplanet Atmospheres. Nodes represent papers; directed edges represent citation links. Node colours indicate community membership (15 communities detected by modularity optimization). Layout uses a spring-based algorithm with a fixed seed for reproducibility.](../output/figures/citation_network.png "Citation Network"){#fig:citation_network}

<!-- FIGURE: degree_distribution.png -->
![Degree distribution for the Exoplanet Atmospheres citation network. The histogram shows the frequency of each in-degree value on a log-linear scale, revealing the heavy-tailed structure characteristic of citation networks.](../output/figures/degree_distribution.png "Degree Distribution"){#fig:degree_distribution}

The heavy-tailed degree distribution is characteristic of citation networks: a small
number of highly-cited papers anchor the structure, while the long tail of low-degree
nodes represents newer or peripheral works. The low graph density
(2.32\%) reflects the sparsity of intra-corpus citation links.
Many papers may cite works outside the retrieved slice, especially under a capped
retrieval design.

## Advanced Network Metrics

Beyond PageRank and HITS, the network analysis computes betweenness centrality (which
papers bridge different communities), closeness centrality (which papers are near all
others), degree assortativity (do highly-cited papers cite other highly-cited papers?),
and average clustering coefficient (how tightly knit are local neighborhoods).

The degree assortativity coefficient is -0.0325, and the average
clustering coefficient is 0.0601. A negative assortativity indicates that
highly-cited papers tend to cite less-cited papers (dissortative mixing), which is
typical of citation networks where review papers (high in-degree) cite many primary
studies (low in-degree).

**Table 7. Top 5 papers by betweenness centrality.**

| Rank | DOI | Betweenness |
| --- | --- | --- |
| 1 | 10.5555/exoplanet atmospheres.0010 | 0.021717 |
| 2 | 10.5555/exoplanet atmospheres.0008 | 0.016667 |
| 3 | 10.5555/exoplanet atmospheres.0015 | 0.012879 |
| 4 | 10.5555/exoplanet atmospheres.0005 | 0.010606 |
| 5 | 10.5555/exoplanet atmospheres.0017 | 0.005051 |

Papers with high betweenness centrality occupy shortest paths between communities in
the retained graph. Removing one may alter connectivity, but that graph operation does
not by itself establish that the paper is a review or methodological bridge in the
scientific field. Source-type and content review are required for that interpretation.
