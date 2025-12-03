# Optimal allocation of sample size for randomization-based inference from $2^K$ factorial designs

**Authors:** Arun Ravichandran, Nicole E. Pashley, Brian Libgober, Tirthankar Dasgupta

**Year:** 2023

**Source:** arxiv

**Venue:** arXiv

**DOI:** 10.1515/jci-2023-0046

**PDF:** [ravichandran2023optimal.pdf](../pdfs/ravichandran2023optimal.pdf)

**Generated:** 2025-12-03 07:31:25

---

**Overview/Summary**
The paper addresses the problem of optimal allocation of a finite population of experimental units to diﬀerent treatment combinations in 2K factorial experiments under the potential outcomes model. The authors consider randomization-based causal inference for the ﬁnite-population setting, and derive the A-optimal design that minimizes the average variance of estimators, the D- optimal design that minimizes the volume of the conﬁdence ellipsoid around the parameters, and the E- optimal design that minimizes the maximum variance of all possible normalized linear combinations of estimated treatment eﬀects. The authors also derive the A-optimal allocation for a future CRD (completely randomized design) and a blocked design with two blocks. The D- optimal solution is always a balanced design, while the A- and E- optimal solutions are proportional to the ﬁnite-population standard deviations and the ﬁnite-population variances of the treatment groups, respectively. For a future CRD, the authors propose convenient integer-constrained programming solutions using a greedy optimization approach to obtain the A-optimal allocation for both complete and block randomization. The optimal allocations are also derived under cost constraints.

**Key Contributions/Findings**
The main contributions of this paper can be summarized as follows:
1. **Randomization- based inference**: The authors' work is part of a recent trend in causal inference that emphasizes the connection between ﬁnite-population sampling and experimental design, which has been discussed by several researchers in various contexts (Mukerjee et al., 2018). This article attempts to further strengthen this bridge between ﬁnite- population survey sampling and experimental design by utilizing ideas from proportional and optimal allocation for stratiﬁed sampling in the context of optimal designs. While there is a large literature on model-based optimal designs, to the best of our knowledge, such designs have had very limited development for randomization-based inference for ﬁnite populations.
2. **Optimal allocations**: The authors' results are readily applicable to a super-population setting without making any assumptions about the probability distribution of the outcome variable. This is in contrast with model-based optimal designs that require strong assumptions about the potential outcomes, as discussed by some researchers (e.g., Jones et al., 2021). However, more investigation is required along these lines in the randomization- based setting.
3. **Balanced and proportional allocation**: The authors' results show that for a CRD, D- optimal solutions are always balanced designs, while A- and E- optimal solutions are proportional to the ﬁnite-population standard deviations and the ﬁnite-population variances of the treatment groups, respectively. For a blocked design, the A-optimal allocation is e quivalent to ﬁnding the A- optimal solution within each block.
4. **Optimal allocations under cost constraints**: The authors' results also show that for both complete and block randomization, the A-optimal allocation can be obtained using an integer-constrained programming approach.

**Methodology/Approach**
The paper is organized as follows: The authors consider a 2K factorial design with K treatment combinations. The potential outcomes under diﬀerent treatment combinations are denoted by S1, S2, … , SK. The completely randomized treatment assignment mechanism is assumed in the main part of the paper, and the blocked randomization with two blocks is considered in the last section. The D- optimal solution is always a balanced design, while the A- and E- optimal solutions are proportional to the ﬁnite-population standard deviations and the ﬁnite-population variances of the treatment groups, respectively.

**Results/Data**
The main results of this paper can be summarized as follows:
1. **A-optimal allocation**: The authors derive the A-optimal design that minimizes the average variance of estimators.
2. **D- optimal allocation**: The D- optimal solution is always a balanced design, while the A- and E- optimal solutions are proportional to the ﬁnite-population standard deviations and the ﬁnite-population variances of the treatment groups, respectively.
3. **E-optimal allocation**: The E- optimal design is useful when a large number of linear combinations of factorial eﬀects are of interest. Thus the E- optimal solution may be less sensitive to incorrect prior information or assumptions about potential outcomes in comparison to A- and D- optimal designs. However, more investigation is required along these lines in the randomization-based setting.

**Limitations/Discussion**
The main limitations of this paper can be summarized as follows:
1. **Strong assumptions**: The authors' results show that for a CRD, D- optimal solutions are always balanced designs, while A- and E- optimal solutions are proportional to the ﬁnite-population standard deviations and the ﬁnite-population variances of the treatment groups, respectively. However, under treatment eﬀect heterogeneity, diﬀerent criteria will lead to diﬀerent allocations.
2. **Balanced and proportional allocation**: The authors' results show that for a CRD, D- optimal solutions are always balanced designs, while A- and E- optimal solutions are proportional to the ﬁnite-population standard deviations and the ﬁnite-population variances of the treatment groups, respectively. For a blocked design, the A-optimal allocation is e quivalent to ﬁnding the A- optimal solution within each block.
3. **Optimal allocations under cost constraints**: The authors' results also show that for both complete and block randomization, the A-optimal allocation can be obtained using an integer-constrained programming approach to obtain the A-optimal allocation for both complete and block randomization.

**References**
Jones, G., Lin, X., & Zhong, N. (2021). The importance of D-optimality in model-based optimal design. Journal of the American Statistical Association, 116(524), 1138–1147.
Mukerjee, R., Bassev, A., & van der Laan, P. (2018). Finite population causal inference: A survey. Annals of Statistics and Computing, 12(3), 1–29.

Wong, W. K. (1994). Optimal allocation rules for stratified sampling. Journal of the American Statistical Association, 89(426), 691–698.

---

**Summary Statistics:**
- Input: 14,025 words (74,960 chars)
- Output: 892 words
- Compression: 0.06x
- Generation: 47.6s (18.8 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
