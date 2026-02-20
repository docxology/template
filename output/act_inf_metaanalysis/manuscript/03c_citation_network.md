# Citation Network Topology \label{sec:citation_network}

The intra-corpus citation network provides a structural view of how Active Inference research is organized, identifying influential hub papers, community structure, and patterns of citation isolation.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.9\textwidth]{figures/citation_network.png}
\caption{Intra-corpus citation network ($N = 1208$ nodes, 2{,}780 edges). Node size reflects PageRank and HITS centrality scores \citep{kleinberg1999authoritative}; highly cited foundational papers serve as nexus points connecting sub-domains.}
\label{fig:citation_network}
\end{figure}

## Network Density and Degree Distribution

The intra-corpus citation network contains 1208 nodes and 2{,}780 edges, with a density of 0.19\% and 700 connected components. The average in-degree of $\approx 2.3$ indicates that most papers receive few intra-corpus citations, consistent with the field's rapid expansion: the majority of recent papers have not yet accumulated citations within the corpus. Only 6.1\% of all references (2{,}780 of 45{,}716) resolve to other papers within the corpus, reflecting cross-source identifier mismatches and the field's engagement with a broad external literature base. Community detection identifies clusters via the Louvain algorithm \citep{blondel2008louvain}.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.7\textwidth]{figures/degree_distribution.png}
\caption{In-degree distribution of the citation network. The power-law tail is characteristic of citation networks, with a small number of highly cited hubs.}
\label{fig:degree_distribution}
\end{figure}

## Connected Components and Citation Isolation

The high number of connected components (700 out of 1208 nodes) reveals that much of the corpus consists of citation-isolated papers—works that neither cite nor are cited by other papers in the collection. This is partially an artifact of cross-source identifier mismatches, but it also reflects the field's pattern of papers engaging with the FEP literature conceptually without building explicit citation chains. PageRank analysis identifies highly influential papers, predominantly Friston's foundational work \citep{friston2010free} and the AIF textbook \citep{parr2022active}, which serve as nexus points linking otherwise disconnected subgraphs.

## Network Summary

| Metric | Value |
| --- | --- |
| Nodes | 1208 |
| Edges | 2{,}780 |
| Reference resolution rate | 6.1\% (2{,}780 / 45{,}716) |
| Connected components | 700 |
| Network density | 0.19\% |
| Mean in-degree | $\approx$ 2.3 |
