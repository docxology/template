# Results: Citation Network

Resolving each record's references against the corpus yields an intra-corpus citation
graph (built and analyzed with NetworkX [@hagberg2008exploring]) of {{CITATION_NODES}}
nodes and {{CITATION_EDGES}} edges across
{{CITATION_COMPONENTS}} connected component(s), with a graph density of
{{CITATION_DENSITY_PCT}}\% and a mean in-degree of {{MEAN_IN_DEGREE}}. Of
{{CITATION_TOTAL_REFS}} total outgoing references, {{CITATION_RESOLUTION_PCT}}\% resolve
to another record inside the corpus — a resolution rate that reflects how self-contained
the retrieved slice of the literature is rather than the underlying citation density of
any single work.

Centrality scores (PageRank [@page1999pagerank] and HITS) and modularity-based community
detection [@clauset2004finding] are rounded and ranked with a stable tiebreaker so
the reported hub and authority rankings are byte-reproducible across runs despite the
floating-point non-associativity of the underlying iterative solvers.
