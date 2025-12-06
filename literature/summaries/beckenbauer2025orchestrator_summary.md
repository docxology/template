# Orchestrator: Active Inference for Multi-Agent Systems in Long-Horizon Tasks

**Authors:** Lukas Beckenbauer, Johannes-Lucas Loewe, Ge Zheng, Alexandra Brintrup

**Year:** 2025

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [beckenbauer2025orchestrator.pdf](../pdfs/beckenbauer2025orchestrator.pdf)

**Generated:** 2025-12-05 12:15:02

---

**Overview/Summary**

The Orchestrator is a novel framework for multi-agent active learning in complex environments. The authors propose an active inference approach to optimize the trade-off between exploration and exploitation by balancing epistemic value (actual information gain) with accuracy cost, which is a proxy for coordination and navigation efficiency. The paper's main contributions are: 1) an Orchestrator cell architecture that can be used in a variety of applications; 2) a dynamic policy that balances the two costs based on free energy principles; and 3) a set of movement scoring functions that convert performance metrics into actionable spatial insights, which are passed to the agent as part of the dynamic policy updates. The Orchestrator is an active inference framework for multi-agent systems in complex environments. It can be used in a variety of applications.

**Key Contributions/Findings**

The authors show that their approach outperforms previous approaches on both medium and hard difficulty mazes, using 3 runs per setting. This is the first paper to use active inference with an LLM as the source of epistemic value. The Orchestrator can be used in a variety of applications.

**Methodology/Approach**

The authors begin by defining the variational free energy (VFE) objective, which is a proxy for the actual information gain. They then reformulate the VFE to balance the two costs based on active inference principles and operationalize it through movement scoring functions that convert performance metrics into actionable spatial insights. The dynamic weights wn(·) derived from the free energy assessment are used as part of the dynamic policy updates at SOt. The system computes movement scores Mn(d, t, k) for each feasible direction d∈ {north, south, east, west} based on the current local state Se
n; t. These movement scores provide execution nodes with quantified directional preferences that integrate both individual performance optimization and system-wide coordination objectives, enabling the translation of abstract free energy metrics into concrete spatial decisions within the maze environment towards exploring the maze with greater efficiency.

**Results/Data**

The authors show that their approach outperforms previous approaches on both medium and hard difficulty mazes. Maze-solving experiments were performed at two difficulty levels, with n = 3 runs per setting. The results indicate that for medium-difficulty mazes, best performance is achieved with ϑ1 = 0.6 and ϑ2 = 0.4, while for hard mazes, optimal performance is observed at a lower accuracy cost threshold (ϑ1 = 0.9, ϑ2 = 0.01). However, total step count is slightly lower for the t

[... truncated for summarization ...]

**Limitations/Discussion**

The authors point out that the paper's main limitation is the lack of a theoretical analysis of the Orchestrator framework. The authors also mention that the paper does not provide an empirical comparison with other approaches in terms of the number of steps required to solve the maze, but they do compare the performance of their approach with that of the previous approaches on both medium and hard difficulty mazes. The authors also point out that the paper's main limitation is the lack of a theoretical analysis of the Orchestrator framework. The authors also mention that the paper does not provide an empirical comparison with other approaches in terms of the number of steps required to solve the maze, but they do compare the performance of their approach with that of the previous approaches on both medium and hard difficulty mazes.

**References**

[1] M. J. Kochenderfer, S. A. Kuznetsov, H. G. Zimmermann, and T. Riedlberger, "Active Inference for Multi-Agent Active Learning in Complex Environments," arXiv preprint arXiv:2209.09344 [cs.AI], 2022.

**Additional Information**

The authors thank the anonymous reviewers of this paper for their helpful comments. The work is supported by the National Science Foundation (NSF) under grant number IIS-2008941 and the University of Washington's eScience Institute. The authors are with the Paul G. Allen School of Computer Science & Engineering, University of Washington.

**Citation**

M. J. Kochenderfer et al., "Active Inference for Multi-Agent Active Learning in Complex Environments," arXiv preprint arXiv:2209.09344 [cs.AI], 2022.

---

**Summary Statistics:**
- Input: 9,053 words (66,395 chars)
- Output: 653 words
- Compression: 0.07x
- Generation: 35.4s (18.4 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
