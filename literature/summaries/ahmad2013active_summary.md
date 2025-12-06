# Active Sensing as Bayes-Optimal Sequential Decision Making

**Authors:** Sheeraz Ahmad, Angela J. Yu

**Year:** 2013

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [ahmad2013active.pdf](../pdfs/ahmad2013active.pdf)

**Generated:** 2025-12-05 13:31:08

---

**Overview/Summary**

The paper discusses active sensing, which is a problem of sequential decision making in partially observable Markov decision processes (POMDPs) where the goal is to maximize the expected cumulative reward over an infinite horizon. The authors consider an agent that can observe its environment and choose actions from a finite set. The agent's objective is to maximize the long-run average reward, but it does not know the parameters of the POMDP in advance. They assume that the agent knows the probability distribution of the initial state and the transition probabilities for all states. The authors also assume that there are no costs or penalties associated with taking an action.

**Key Contributions/Findings**

The main contribution of this paper is to show that active sensing can be formulated as a Bayesian problem of sequential decision making in POMDPs, where the goal is to maximize the expected cumulative reward over an infinite horizon. The authors also provide a new algorithm for solving these problems and compare it with existing algorithms.

**Methodology/Approach**

The authors first formulate the active sensing problem as a POMDP. They then show that this problem can be solved by using a point-based value iteration (PBVI) algorithm, which is an anytime algorithm. The PBVI algorithm is based on the idea of approximating the optimal policy for the original POMDP with a set of points and then using these points to approximate the optimal policy. The authors also compare their algorithm with existing algorithms.

**Results/Data**

The authors show that the PBVI algorithm can be used to solve the active sensing problem. They provide numerical results in the paper, which are based on experiments conducted by the authors. These results demonstrate the effectiveness of the PBVI algorithm. The authors also compare the performance of the PBVI algorithm with existing algorithms.

**Limitations/Discussion**

The authors discuss the limitations and future work of this research. One limitation is that the PBVI algorithm does not have a polynomial time complexity, which may be considered as one of the weaknesses of the paper. Another limitation is that the numerical results are based on experiments conducted by the authors. The authors also mention some possible future directions for this problem.

**References**

The references in the paper include 14 papers and 1 book.

---

**Summary Statistics:**
- Input: 7,149 words (44,580 chars)
- Output: 374 words
- Compression: 0.05x
- Generation: 22.8s (16.4 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
