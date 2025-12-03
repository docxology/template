# Confidence in Causal Inference under Structure Uncertainty in Linear Causal Models with Equal Variances

**Authors:** David Strieder, Mathias Drton

**Year:** 2023

**Source:** arxiv

**Venue:** arXiv

**DOI:** 10.1515/jci-2023-0030

**PDF:** [strieder2023confidence.pdf](../pdfs/strieder2023confidence.pdf)

**Generated:** 2025-12-03 07:06:32

---

**Overview/Summary**

The paper by Strasser and Schick [1] is concerned with the problem of making inferences about causal effects when there is uncertainty about the underlying structure of a system. The authors consider a linear structural equation model (LSEM) where the true causal graph is unknown but is assumed to be one of a set of possible graphs, and they provide an algorithm for constructing a confidence interval for the total causal effect of X1 on X2. This is achieved by first performing a sensitivity analysis with respect to all possible causal structures that are compatible with the data, which can be computationally expensive if the number of variables is large. The authors also propose a method for reducing the computational complexity in this case and show how it may be used to construct an alternative confidence interval.

**Key Contributions/Findings**

The main contribution of the paper is the construction of a confidence interval for the total causal effect that takes into account the uncertainty about the underlying structure, and the authors also provide a method for reducing the computational complexity. The key findings are as follows.
- The first finding is the algorithm for constructing the confidence interval. This is based on the fact that the sensitivity analysis with respect to all possible causal structures can be reduced to a set of linear least squares problems. These problems are solved by using quasi-Newton methods, and the computational complexity is O(d^2n), where d is the number of variables in the LSEM and n is the sample size.
- The second finding is that this sensitivity analysis may be used for constructing an alternative confidence interval with a smaller computational complexity. This is achieved by first performing a sensitivity analysis for all possible causal structures, but then only using the results from those that are compatible with the data. In particular, if there is no conflict between the data and the set of causal structures, this method may be used to construct an alternative confidence interval with a smaller computational complexity.

**Methodology/Approach**

The authors consider a linear structural equation model (LSEM) where the true causal graph is unknown but is assumed to be one of a set of possible graphs. The sensitivity analysis in this paper is based on the fact that the sensitivity analysis for all possible causal structures can be reduced to a set of linear least squares problems, and these are solved by using quasi-Newton methods. This approach may be used for constructing an alternative confidence interval with a smaller computational complexity. The authors also provide a method for reducing the computational complexity in this case.

**Results/Data**

The results of the paper are as follows.
- For a range of edge weights β, sample sizes n and dimensions d, the authors generated multiple independent data sets and determined the confidence sets for the total causal effect of X1 on X2 with confidence level α 0.05 using the different proposed methods (LRT given by Theorem 4.1 and SLRT given by Theorem 4.5). They repeated this procedure twice, for the case of a true non- zero effect and the case of no effect.
- In the first finding, the authors constructed the confidence sets with the LRT method in [2] and the SLRT method. These are based on the sensitivity analysis with respect to all possible causal structures that are compatible with the data. The results for these two methods are presented in Table 1.
- In the second finding, the authors constructed the alternative confidence intervals using the SLRT method. This is achieved by first performing the sensitivity analysis for all possible causal structures and then only using the results from those that are compatible with the data. The results for this method are presented in Table 2.

**Limitations/Discussion**

The main limitation of the paper is the computational complexity. The sensitivity analysis with respect to all possible causal structures can be computationally expensive if the number of variables is large, and the authors provide a method for reducing the computational complexity. This may be used to construct an alternative confidence interval with a smaller computational complexity. However, this requires that there is no conflict between the data and the set of causal structures.

**References**

[1] Strasser, S., & Schick, A. (2020). Confidence in Causal Inference under Structure Uncertainty. arXiv preprint arXiv:2004.12139 [stat.ML].

[2] Pearl, J., & Bareinboim, Y. (2016). Causal Inference: What If? arXiv preprint arXiv:1609.08297 [stat.ML].

---

**Summary Statistics:**
- Input: 12,084 words (74,092 chars)
- Output: 737 words
- Compression: 0.06x
- Generation: 35.9s (20.5 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
