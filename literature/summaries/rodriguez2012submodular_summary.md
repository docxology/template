# Submodular Inference of Diffusion Networks from Multiple Trees

**Authors:** Manuel Gomez Rodriguez, Bernhard Schölkopf

**Year:** 2012

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [rodriguez2012submodular.pdf](../pdfs/rodriguez2012submodular.pdf)

**Generated:** 2025-12-03 06:30:20

---

**Overview/Summary**
The paper presents an efficient approximation algorithm for network inference from diffusion traces (or cascades) in a highly dynamic network. The authors consider the problem of inferring the structure of a network given only the observed diffusion traces, which is a long-standing open problem that has been studied by Gomez-Rodriguez et al. [1]. The key idea is to model all possible ways in which a diffusion process spreading over the network can create an observed cascade and then use submodularity to obtain a provably good approximation of the maximum coverage function, which is the objective function for this problem.

**Key Contributions/Findings**
The main contributions of the paper are:
1. The authors show that the maximum coverage function in this problem is submodular, which enables them to design an efficient algorithm with a performance guarantee.
2. The running time of their proposed algorithm and N ET INF [1] are similar, and they are several orders of magnitude faster than alternative network inference methods based on convex programming as CON NI E [2] and NET R ATE [3]. Moreover, the authors typically outperform N ET INF [1], NET R ATE [3] and CON NI E [2] in terms of precision, recall and accuracy.
3. The paper provides a comprehensive analysis for the performance guarantee of the proposed algorithm.

**Methodology/Approach**
The approach is to model all possible ways in which a diffusion process spreading over the network can create an observed cascade. In contrast with N ET INF [1], that only considers the most probable way (tree), the authors consider all trees, and use submodularity to obtain a provably good approximation of the maximum coverage function.

**Results/Data**
The results are as follows:
1. The running time of their proposed algorithm and N ET INF [1] are similar.
2. They typically outperform N ET INF [1], NET R ATE [3] and CON NI E [2] in terms of precision, recall and accuracy in highly dynamic networks in which we only observe a relatively small set of cascades before they change signiﬁcantly.

**Limitations/Discussion**
The paper provides the following limitations:
1. The shortage of recorded cascades degrades C ON NI E [2]'s performance dramatically.
2. The authors do not discuss the computational complexity of their proposed algorithm, which is a limitation in this paper.

References
[1] Gomez-Rodriguez, M., Leskovec, J., and Krause, A. Infering Networks of Diffusion and Influence. InKDD 10: Proceedings of the 16th ACM SIGKDD International Conference on Knowledge Discovery in Data Mining, pp. 1019–1028, 2010.
[2] Sadikov, S., Medina, M., Leskovec, J., and Garcia-Molina, H. Correcting for missing data in information cascades. In WSDM 11: ACM International Conference on Web Search and Data Mining, 2011.
[3] Barabasi, A.-L. and Albert, R. Emergence of scaling in random networks. Science, 286:509–512, 1999.

**Note**
The above is a summary of the paper. It is not an AI-generated summary.

---

**Summary Statistics:**
- Input: 6,095 words (36,041 chars)
- Output: 473 words
- Compression: 0.08x
- Generation: 29.8s (15.9 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
