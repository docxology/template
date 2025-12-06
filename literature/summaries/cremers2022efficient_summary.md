# Efficient Methods for Approximating the Shapley Value for Asset Sharing in Energy Communities

**Authors:** Sho Cremers, Valentin Robu, Peter Zhang, Merlinda Andoni, Sonam Norbu, David Flynn

**Year:** 2022

**Source:** arxiv

**Venue:** N/A

**DOI:** 10.1016/j.apenergy.2022.120328

**PDF:** [cremers2022efficient.pdf](../pdfs/cremers2022efficient.pdf)

**Generated:** 2025-12-05 11:13:39

---

**Overview/Summary**

The paper proposes a new approach for computing the Shapley value in a community of agents with different demand profiles. The authors consider a scenario where there are K classes and each class has Nk unique half-hourly demands, such that every agent belongs to one class and all the agents in the same class have the same demand profile. This is a common assumption in the literature on Shapley value computation for large communities. In this case, the number of possible subcoalitions is (N1  + 1) ×...×(NK  + 1), which can be represented as a hyperrectangle with K dimensions and size N1 ×...×NK. The authors show that the time complexity to compute the Shapley value in such a community is significantly reduced if the number of classes is limited, and they provide an efficient algorithm for this case.

**Key Contributions/Findings**

The main contribution of the paper is the development of two approximation methods with low computational complexities when the number of classes K is small. The authors also propose an exact method to compute the Shapley value in a community of K classes, which can be used as a reference for evaluating the performance of the proposed approximation methods.

**Methodology/Approach**

The paper starts by describing the two existing algorithms for computing the Shapley value: the original algorithm and the O'Brien's algorithm. The authors then propose an efficient method to compute the Shapley value in a community with K classes, which is based on the idea that the time complexity can be significantly reduced if the number of classes is limited. This is because the cost function c(·) has to run through one year of half-hourly demands datapoints every time it is called, and the energy costs of all possible subcoalitions may be used multiple times in Shapley calculation. The authors also provide an efficient algorithm for this case, which can save a lot of computation time by storing the values in a table with size (N1  + 1) ×...×(NK+1). This is important because the cost function c(·) is the most computationally expensive part of computing the Shapley value. The authors also propose an efficient method to compute the Shapley value in a community with K classes, which can be used as a reference for evaluating the performance of the proposed approximation methods.

**Results/Data**

The paper provides an exact computation algorithm for the case where there are K classes and each class has Nk unique half-hourly demands. The authors also provide two approximation algorithms: one is based on the idea that the time complexity can be significantly reduced if the number of classes is limited, and the other is based on a Monte Carlo method.

**Limitations/Discussion**

The paper does not discuss any limitations or future work for this research.

---

**Summary Statistics:**
- Input: 18,477 words (117,870 chars)
- Output: 459 words
- Compression: 0.02x
- Generation: 26.5s (17.3 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
