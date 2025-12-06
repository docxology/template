# Efficient search of active inference policy spaces using k-means

**Authors:** Alex B. Kiefer, Mahault Albarracin

**Year:** 2022

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [kiefer2022efficient.pdf](../pdfs/kiefer2022efficient.pdf)

**Generated:** 2025-12-05 12:11:03

---

**Overview/Summary**

The paper presents a novel approach for efficient search of active inference policy spaces in the context of graph-based generative models. In this setting, an agent is given a set of policies and must select one to execute at each time step based on its current state and observation. The authors propose two new methods: (1) k-means clustering with a novel embedding construction that can be used for both global and local active inference; and (2) sample-based hierarchical policy selection, which is an alternative to the standard greedy search algorithm. In addition, they compare these two approaches to the standard greedy search in terms of optimality and efficiency. The authors use a graph as the generative model and define the variables as follows: states are edges, observations are tuples (edge, weight) representing edge weights, control states are actions for local transitions, A is an identity mapping from states to observations, B is the state transition matrix that encodes deterministic knowledge of action-conditioned state transitions, C is a preference matrix that distributes probability mass equally over all edges that end on the agent's destination node, and D is the prior over initial location states. The authors use the standard procedure for selecting policies with one exception: the expected free energy has an additional term which is the dot product of the posterior distribution over states (locations) with the associated edge weights. They combine this with the standard EFE calculation using a free hyperparameter λ.

**Key Contributions/Findings**

The main contributions of the paper are two-fold. First, the authors propose a novel embedding construction for k-means clustering that can be used for both global and local active inference. Second, they compare the new methods to the standard greedy search in terms of optimality and efficiency. The authors use the standard procedure for selecting policies with one exception: the expected free energy has an additional term which is the dot product of the posterior distribution over states (locations) with the associated edge weights. They combine this with the standard EFE calculation using a free hyperparameter λ.

**Methodology/Approach**

The authors' generative model is based on a graph, where the agent's state is an edge and its observation is a tuple (edge, weight) representing edge weights. The control states are actions for local transitions. A is the agent's ‘A’ or likelihood matrix, which in this case is simply an identity mapping from states to observations. B is the state transition matrix that encodes deterministic knowledge of action-conditioned state transitions. C is a preference matrix that distributes probability mass equally over all edges that end on the agent's destination node. There is also implicitly a preference against high edge weights, but to simplify the representation they incorporate this directly within the expected free energy calculation (see Appendix B). The authors use the standard procedure for selecting policies with one exception: the expected free energy has an additional term which is the dot product of the posterior distribution over states (locations) with the associated edge weights. They combine this with the standard EFE calculation using a free hyperparameter λ.

**Results/Data**

The authors compare their two new methods to the standard greedy search in terms of optimality and efficiency. The authors use the standard procedure for selecting policies with one exception: the expected free energy has an additional term which is the dot product of the posterior distribution over states (locations) with the associated edge weights. They combine this with the standard EFE calculation using a free hyperparameter λ.

**Limitations/Discussion**

The paper does not discuss the following limitations and future work:
    - The authors do not compare their methods to other existing policy search techniques in the literature.
    - The authors do not evaluate the optimality of the proposed methods for different values of the hyperparameter λ. In particular, they only report the results with a fixed value of λ. It is unclear how sensitive the optimality and efficiency are to the choice of this hyperparameter.

**Additional Results**

The paper presents some additional experimental results. Figure 4 plots the combined embedding construction and k-means clustering times for each embedding type. Table 1 below shows the full set of optimality results they obtained, averaged across trials (i.e. across particular graphs in each category). Here, "None" denotes standard policy selection. Best embedding results for each graph size are bolded.

**Figures**

Figure 4. Left: Time taken to construct embeddings and perform k-means clustering on the resulting embeddings. The increased times for both construction and clustering for the EDM representation are due to the relatively much larger dimensionality of the EDM embedding: one dimension for each policy, rather than one for each vertex and edge, as in the BOE and aBOE representations. Right:  ‘detail’ plot of the construction times by graph size for the BOE and aBOE embeddings.

**Tables**

Table 1. Percent of solutions optimal
Graph size 3 4 5
Scope Embedding k n
Global None — — 100.0 97.5 97.4
BOE 6 1 70.0 65.0 56.4
3 77.5 62.5 46.1
12 1 60.0 87.5 59.0
3 77.5 62.5 51.3
EDM 6 1 70.0 67.5 48.7
3 80.0 72.5 56.4
12 1 67.5 72.5 64.1
3 80.0 72.5 61.5
aBOE 6 1 82.5 85.0 66.7
3 87.5 85.0 61.5
12 1 85.0 67.5 35.9
3 75.0 92.5 79.5
Local None — — 100.0 97.5 97.5
BOE 6 1 17.5 37.5 48.7
3 52.5 55.0 61.5
12 1 42.5 47.5 41.0
3 82.5 42.5 25.6
EDM 6 1 5.0 52.5 45.0
3 50.0 65.0 35.0
12 1 50.0 60.0 40.0
3 97.5 32.5 15.4
aBOE 6 1 15.0 12.5 5.1
3 35.0 12.5 5.1
12 1 5.0 22.5 12.8
3 70.0 20.0 12.8

=== END PAPER CONTENT ===

---

**Summary Statistics:**
- Input: 5,406 words (36,034 chars)
- Output: 945 words
- Compression: 0.17x
- Generation: 49.9s (18.9 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
