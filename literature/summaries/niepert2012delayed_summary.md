# A Delayed Column Generation Strategy for Exact k-Bounded MAP Inference in Markov Logic Networks

**Authors:** Mathias Niepert

**Year:** 2012

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [niepert2012delayed.pdf](../pdfs/niepert2012delayed.pdf)

**Generated:** 2025-12-05 14:00:42

---

**Overview/Summary**

The paper presents a column generation strategy for exact k-bounded MAP (Maximum A Posterior) inference in Markov Logic Networks (MLNs). The authors motivate the problem of computing the k-bounded MAP by considering two use-cases from the areas of computational biology and knowledge representation. In the first use-case, the goal is to find the top-k most similar proteins for a given protein based on their functional annotations. In the second use-case, the goal is to find the top-k most similar ontologies in a hierarchical ontology. The authors also motivate the problem by considering the k-bounded MAP as an extension of the traditional maximum weighted matching (MWM) problem. They show that the k-bounded MAP can be formulated as a MWM and present a naive approach for solving it. However, this naive approach is not efficient when the number of active ground atoms in a MAP state is small relative to the total number of all ground atoms of hidden predicates. The authors then present an exact column generation algorithm that is tailored to the k-bounded MAP problem and is especially eﬃcient for instances where (a) a- priori weights are given for ground atoms or (b) it is known a-priori that the number of active ground atoms in a MAP state is small relative to the total number of all ground atoms of hidden predicates. Typical instances are one-to-one and functional alignment problems.

**Key Contributions/Findings**

The key contributions of the paper are the exact column generation algorithm for k-bounded MAP inference, which is especially eﬃcient when (a) a-priori weights are given for ground atoms or (b) it is known a-priori that the number of active ground atoms in a MAP state is small relative to the total number of all ground atoms of hidden predicates. The approach also lends itself to distributed computing strategies since the individual subproblems are mutually independent.

**Methodology/Approach**

The authors formulate the k-bounded MAP as a MWM and present a naive approach for solving it. However, this naive approach is not efficient when the number of active ground atoms in a MAP state is small relative to the total number of all ground atoms of hidden predicates. The authors then present an exact column generation algorithm that is tailored to the k-bounded MAP problem and is especially eﬃcient for instances where (a) a-priori weights are given for ground atoms or (b) it is known a-priori that the number of active ground atoms in a MAP state is small relative to the total number of all ground atoms of hidden predicates. Typical instances are one-to-one and functional alignment problems.

**Results/Data**

The authors compare the solving times and the ILP dimensions of the column generation algorithm with the naive approach which constructs the entire ILP with the additional cardinality constraint. The column generation approach is more than 5000 times faster to compute the top 10 alignment between the ConfOf and EKAW ontologies. The computation times of less than one second, for instance, would allow real-time user interaction with an alignment system.

**Limitations/Discussion**

The authors will try to leverage existing software platforms for distributed computing to implement distributed probabilistic reasoning. The presented algorithm can also be transformed into an approximate inference algorithm by adjusting the optimality test. Future research might be concerned with applying the presented ideas to diﬀerent graph matching as well as weighted MAX-SAT problems.

**References**

The authors thank Christian Meilicke, Sebastian Riedel, and Heiner Stuckenschmidt for helpful discussions and the anonymous reviewers for valuable feedback.

---

**Summary Statistics:**
- Input: 6,681 words (36,245 chars)
- Output: 577 words
- Compression: 0.09x
- Generation: 31.4s (18.4 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
