# Active Inference Tree Search in Large POMDPs

**Authors:** Domenico Maisto, Francesco Gregoretti, Karl Friston, Giovanni Pezzulo

**Year:** 2021

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [maisto2021active.pdf](../pdfs/maisto2021active.pdf)

**Generated:** 2025-12-03 04:23:57

---

**Overview/Summary**
The paper introduces a new algorithm called Active Inference Tree Search (AcT) for on-line planning in partially observable Markov decision processes (POMDPs). This is an important problem because the number of possible policies grows exponentially with the size of the state and action spaces, so it is hard to find the optimal policy. The authors propose a new algorithm that can escape from deceptive "traps" which are states whose instantaneous utility is deceptive with respect to their future outcomes. A trap is a situation in which an unfortunate move is unavoidable, leading to a defeat. In this paper, they show that UCT has a hyper-exponential dependency on the depth of the tree and that AcT can avoid these traps. The authors also compare AcT to other algorithms based on tree visits such as POMCP and R-DESPOT.

**Key Contributions/Findings**
The main contributions are:
1. A new algorithm called Active Inference Tree Search (AcT) for on-line planning in POMDPs.
2. An analysis of the performance of AcT that shows it has a polynomial dependency on the size of the generative model and can escape from traps.
3. A comparison to other algorithms based on tree visits such as POMCP and R-DESPOT, which approximate belief states and outcomes with a particle filter.

**Methodology/Approach**
The authors first introduce the problem of on-line planning in POMDPs. Then they describe the AcT algorithm. The four stages of the AcT are: (1) variational inference, (2) expansion, (3) evaluation, and (4) path integration. The authors also compare their algorithm to other algorithms based on tree visits such as POMCP and R-DESPOT.

**Results/Data**
The paper tests the Active Inference Tree Search on three exemplar problems. The first two problems are a deceptive binary tree and a non Lipschitzian function, which are challenging for UCT and similar algorithms. The third problem is a POMDP benchmark, the RockSample, which is often used to evaluate the effectiveness and scalability of planning algorithms as the problem complexity increases.

**Limitations/Discussion**
The main limitations of the paper are:
1. The total computational cost of AcT depends on the number of simulations controlled through the discount condition $\delta$, and on the EFE computation in the (computationally expensive) evaluation routine.
2. The authors note that it would be possible to approximate or amortise EFE computations to reduce computational demands, but this is not explored in this article.

**References**
The paper references [34], [41], [42], [43], [75].

---

**Summary Statistics:**
- Input: 17,727 words (117,729 chars)
- Output: 400 words
- Compression: 0.02x
- Generation: 26.5s (15.1 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
