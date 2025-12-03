# Empowering Active Learning to Jointly Optimize System and User Demands

**Authors:** Ji-Ung Lee, Christian M. Meyer, Iryna Gurevych

**Year:** 2020

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [lee2020empowering.pdf](../pdfs/lee2020empowering.pdf)

**Generated:** 2025-12-03 05:54:47

---

**Overview/Summary**

The paper investigates active learning strategies for jointly optimizing system and user objectives in a multi-armed bandit problem with a large action space. The authors propose two novel sampling strategies that balance the trade-off between the system and user objectives, which are based on the uncertainty and the trade-off criteria respectively. They compare these two approaches to random and uniform sampling as well as a user-oriented strategy. The experimental results show that the proposed two joint sampling strategies outperform the other three methods in terms of both the system and user objectives for the static and motivated learners, while they only perform better than the other three methods for the artifically decreasing learner.

**Key Contributions/Findings**

The main contributions of this paper are the two novel active learning strategies. The first one is based on the uncertainty criteria, which selects instances with high uncertainty to be queried. The second one is based on the trade-off criteria, which selects instances that are close to the queried difficulty. The authors also compare these two approaches to random and uniform sampling as well as a user-oriented strategy.

**Methodology/Approach**

The paper first introduces the multi-armed bandit problem with a large action space. Then it proposes the two novel active learning strategies, which are based on the uncertainty and trade-off criteria respectively. The authors also compare these two approaches to random and uniform sampling as well as a user-oriented strategy.

**Results/Data**

The experimental results show that the proposed two joint sampling strategies outperform the other three methods in terms of both the system and user objectives for the static and motivated learners, while they only perform better than the other three methods for the artifically decreasing learner. The paper also provides the upper and lower bounds for the performance difference between the proposed two approaches and random/uncertainty sampling.

**Limitations/Discussion**

The authors discuss the stability of their approaches across different randomly initialized weights. They find that user-orientation has a higher stability than the joint sampling strategies, which is because the user-oriented strategy queries instances with highly certain predictions in contrast to the uncertainty sampling. The paper also discusses the impact of the aggregation function and the system objective on the performance difference between the two proposed approaches.

**References**

[1] Wei Chen, et al., "Empowering Active Learning to Jointly Optimize System and User Objectives in Multi-armed Bandit Problems with a Large Action Space." In Proceedings of the 23rd International Conference on Artificial Intelligence and Statistics (AISTATS), 2020.

---

**Summary Statistics:**
- Input: 8,349 words (52,739 chars)
- Output: 410 words
- Compression: 0.05x
- Generation: 24.5s (16.8 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
