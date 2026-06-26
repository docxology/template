# Results: Citation Network

## RQ4: Citation Geometry

Resolving each record's references against the corpus yields an intra-corpus citation
graph (built and analyzed with NetworkX [@hagberg2008exploring]) of 2204
nodes and 8,772 edges across 1371 connected components,
with a graph density of 0.18\% and a mean in-degree of
4.0. Of 38,802 total outgoing references,
22.6\% resolve to another record inside the corpus — a resolution
rate that reflects how self-contained the retrieved slice of the literature is rather
than the underlying citation density of any single work.

The citation network has 1377 communities (detected by modularity
optimization), a maximum in-degree of 165 (the most-cited paper
within the corpus), and a maximum out-degree of 145 (the paper
that cites the most other corpus members).

## Centrality Analysis

Centrality scores (PageRank [@page1999pagerank] and HITS) and modularity-based community
detection [@clauset2004finding] are rounded and ranked with a stable tiebreaker so the
reported hub and authority rankings are byte-reproducible across runs despite the
floating-point non-associativity of the underlying iterative solvers.

**Table 4. Top 5 papers by PageRank.**

| Rank | DOI | PageRank |
| --- | --- | --- |
| 1 | 10.1177/026988110001400107 | 0.036955 |
| 2 | 10.1212/wnl.54.5.1166 | 0.027240 |
| 3 | 10.1523/jneurosci.21-05-01787.2001 | 0.013811 |
| 4 | 10.1523/jneurosci.20-22-08620.2000 | 0.011443 |
| 5 | 10.4088/jcp.v61n0510 | 0.008104 |

**Table 5. Top 5 authority papers (HITS).**

| Rank | DOI | Authority |
| --- | --- | --- |
| 1 | 10.1038/sj.npp.1301534 | 0.017582 |
| 2 | 10.1007/s00213-002-1250-8 | 0.015979 |
| 3 | 10.1124/jpet.106.106583 | 0.015039 |
| 4 | 10.1001/jama.2009.351 | 0.014535 |
| 5 | 10.1523/jneurosci.21-05-01787.2001 | 0.014289 |

**Table 6. Top 5 hub papers (HITS).**

| Rank | DOI | Hub |
| --- | --- | --- |
| 1 | 10.3389/fnins.2021.656475 | 0.012064 |
| 2 | 10.1016/bs.apha.2023.10.006 | 0.011690 |
| 3 | 10.1038/sj.npp.1301534 | 0.010781 |
| 4 | 10.1080/08897077.2019.1700584 | 0.010618 |
| 5 | 10.1007/s00213-013-3232-4 | 0.009971 |

The most influential paper by PageRank (DOI 10.1177/026988110001400107) is a foundational work
that anchors the citation structure — its high authority score confirms it is frequently
cited by other corpus members. Hub papers, which cite many other corpus members, serve as
integrative reviews or meta-analyses that connect disparate threads of the literature.

<!-- FIGURE: citation_network.png -->
![Citation network for Modafinil. Nodes represent papers; directed edges represent citation links. Node colours indicate community membership (1377 communities detected by modularity optimization). Layout uses a spring-based algorithm with a fixed seed for reproducibility.](figures/citation_network.png "Citation Network"){{#fig:citation_network}}

<!-- FIGURE: degree_distribution.png -->
![Degree distribution for the Modafinil citation network. The histogram shows the frequency of each in-degree value on a log-linear scale, revealing the heavy-tailed structure characteristic of citation networks.](figures/degree_distribution.png "Degree Distribution"){{#fig:degree_distribution}}

The heavy-tailed degree distribution is characteristic of citation networks: a small
number of highly-cited papers anchor the structure, while the long tail of low-degree
nodes represents newer or peripheral works. The low graph density
(0.18\%) reflects the sparsity of intra-corpus citation links —
most papers cite works outside the retrieved slice, which is expected for a
max-results-capped retrieval.

## Advanced Network Metrics

Beyond PageRank and HITS, the network analysis computes betweenness centrality (which
papers bridge different communities), closeness centrality (which papers are near all
others), degree assortativity (do highly-cited papers cite other highly-cited papers?),
and average clustering coefficient (how tightly knit are local neighborhoods).

The degree assortativity coefficient is -0.0579, and the average
clustering coefficient is 0.1047. A negative assortativity indicates that
highly-cited papers tend to cite less-cited papers (dissortative mixing), which is
typical of citation networks where review papers (high in-degree) cite many primary
studies (low in-degree).

**Table 7. Top 5 papers by betweenness centrality.**

| Rank | DOI | Betweenness |
| --- | --- | --- |
| 1 | 10.1038/sj.npp.1301534 | 0.006017 |
| 2 | 10.4088/jcp.v67n0406 | 0.003330 |
| 3 | 10.2165/00003495-200868130-00003 | 0.002036 |
| 4 | 10.1124/jpet.106.106583 | 0.001949 |
| 5 | 10.1007/s00213-005-0044-1 | 0.001899 |

Papers with high betweenness centrality serve as bridges between different topical
communities in the citation network — their removal would fragment the graph into
disconnected components. These bridging papers are often review articles or
methodological papers that connect disparate research threads.
