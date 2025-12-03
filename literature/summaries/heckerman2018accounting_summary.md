# Accounting for hidden common causes when inferring cause and effect from observational data

**Authors:** David Heckerman

**Year:** 2018

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [heckerman2018accounting.pdf](../pdfs/heckerman2018accounting.pdf)

**Generated:** 2025-12-03 05:13:01

---

Overview/Summary:
The paper "Accounting for hidden common causes when inferring cause and effect from observational data" by David Heckerman is a study on the problem of identifying causal relationships in the presence of hidden common causes. The author considers three approaches to this issue, where the first two are well-known: (1) if there were no hidden common causes of the SNPs, one could distinguish between causal and non-causal SNPs by applying univariate linear regression to assess the correlation between a SNP and trait, producing a P value based on, for example, a likelihood ratio test. The third approach is where there are sufficient clues in the data that hidden common causes can be inferred. In this paper, the author considers an example from genomics, where the goal of a genome-wide association study (GWAS) is to identify which genetic markers known as single nucleotide polymorphism (SNPs) causally influence some trait of interest. The first two approaches are well-known: one could distinguish between causal and non-causal SNPs by applying univariate linear regression to assess the correlation between a SNP and trait, producing a P value based on, for example, a likelihood ratio test. The third approach is where there are sufficient clues in the data that hidden common causes can be inferred.

Key Contributions/Findings:
The main contribution of this paper is that if one can infer the family relatedness from the observed SNPs, then univariate linear regression will not only distinguish between causal and non-causal SNPs but also provide a calibrated P value. The author shows that in the presence of hidden common causes, it is possible to identify them by using the data itself. This is illustrated with an example where the goal is to identify which genetic markers known as single nucleotide polymorphism (SNPs) causally influence some trait of interest.

Methodology/Approach:
The paper describes a method for identifying causal SNPs in the presence of hidden common causes, and this method is applied to the problem of GWAS. The author considers two experiments: one where there are no direct arcs from hto y (h is the hidden family relatedness) and another where there is an arc from hto y. In both cases, the data was generated using a large number of SNPs and 4,000 individuals. For each experiment, three data sets for each possible combination of parameters were generated, yielding 3 x 5 x 6 = 450 data sets. The first set of experiments is taken from [6]. For each data set in both experiments, P values were determined using the distribution (1) as described in the section on regularized multiple linear regression.

Results/Data:
The results are based on two experiments: one where there is no direct arc from hto y and another where there is an arc. In the first experiment, although the data was generated using the similarity matrix of the causal SNPs whereas the data was fit using the similarity matrix of all SNPs, P values were calibrated. Calibration occurred because the two similarity matrices were nearly identical, as they were drawn from the same pattern of family relatedness. In the second experiment, the similarity matrices of all SNPs, the causal observed SNPs, and the causal hidden SNPs were drawn from the same pattern of family relatedness, and again were nearly identical. Thus, the fit to the data remained good, and P values were calibrated. The paper shows that in terms of the causal model, it was possible to infer the family relatedness, in effect inferring h and blocking the d-connections in the model.

Limitations/Discussion:
The author notes that GWAS is a very simple problem in causal inference. We know that SNPs cause traits and not the other way around, so the only real challenge is to identify which SNPs are non-spuriously correlated with the trait. The fact that this seemingly simple problem requires advanced treatment highlights the complexity of the general problem of causal inference in the presence of hidden causes.

References:
[1] Yu, J. et al. A uniﬁed mixed- model method for association mapping that accounts for multiple levels of relatedness. Nat. Genet.38, 203–8 (2006).
[2] Lippert, C. et al. FaST linear mixed models for genome-wide association studies. Nat. Methods8, 833–5 (2011).
[3] Rasmussen, C. E. & Williams, C. K. I. Gaussian Processes for Machine Learning. MIT Press, 2006.
[4] Goddard, M. E., Wray, N., Verbyla, K. & Visscher, P. (2009)Statis. Sci24:517–529.
[5] Kang, H. M. et al. Efﬁcient control of population structure in model organism association mapping. Genetics 178, 1709–23 (2008).
[6] Widmer, C. et al. Further Improvements to Linear Mixed Models for Genome- Wide Association Studies. Sci. Rep. 4, 6874 (2014).

---

**Summary Statistics:**
- Input: 1,982 words (12,027 chars)
- Output: 767 words
- Compression: 0.39x
- Generation: 41.6s (18.4 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
