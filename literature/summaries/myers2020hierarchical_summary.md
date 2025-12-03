# A Hierarchical Approach to Scaling Batch Active Search Over Structured Data

**Authors:** Vivek Myers, Peyton Greenside

**Year:** 2020

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [myers2020hierarchical.pdf](../pdfs/myers2020hierarchical.pdf)

**Generated:** 2025-12-02 13:49:42

---

**Overview/Summary**

The paper proposes a hierarchical approach to scaling batch active search (HAS) for accelerating the exploration of chemical space in the context of molecular optimization. The authors argue that the existing methods are not scalable and do not provide an efficient way to balance the trade-off between exploration and exploitation, which is critical for the success of the parallelized Bayesian optimization. In this paper, the authors introduce a novel approach by combining the local penalization with the batched Gaussian process (GP) framework. The HAS method can be used in a variety of settings where the objective function is expensive to evaluate but the surrogate model is cheap and can be used for both exploration and exploitation.

**Key Contributions/Findings**

The authors show that the proposed approach outperforms the existing methods by a large margin, especially when the number of parallel machines is small. The HAS method can also be applied in other settings where the objective function is expensive to evaluate but the surrogate model is cheap and can be used for both exploration and exploitation.

**Methodology/Approach**

The authors first introduce the batched GP (BG) framework that can be used for both exploration and exploitation. Then, the authors propose a novel approach called HAS by combining the local penalization with the BG framework. The HAS method is based on a hierarchical Bayesian model where the hyperparameters of the surrogate model are updated in two stages. In the first stage, the authors use the batched GP to update the hyperparameters and then use the obtained hyperparameters to update the GP. The authors also propose an algorithm that can be used for the parallelized Bayesian optimization.

**Results/Data**

The authors evaluate the performance of the proposed approach on a large-scale molecular optimization problem. The results show that the HAS method outperforms the existing methods by a large margin, especially when the number of parallel machines is small. The authors also compare the performance of the HAS method with the batched GP and the penalized GP (PG) method. The results show that the PG method can be used for the exploration but not for the exploitation. The authors also compare the performance of the HAS method with the batched GP and the BG methods in the case where the number of parallel machines is large.

**Limitations/Discussion**

The authors point out some limitations of the proposed approach. For example, the authors do not discuss how to choose the hyperparameters for the surrogate model. The authors also do not compare the performance of the HAS method with the batched GP and the PG methods in the case where the number of parallel machines is large.

**References**

The paper references 23 other papers.

---

**Summary Statistics:**
- Input: 3,997 words (25,740 chars)
- Output: 446 words
- Compression: 0.11x
- Generation: 26.1s (17.1 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
