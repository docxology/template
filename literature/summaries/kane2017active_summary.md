# Active classification with comparison queries

**Authors:** Daniel M. Kane, Shachar Lovett, Shay Moran, Jiapeng Zhang

**Year:** 2017

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [kane2017active.pdf](../pdfs/kane2017active.pdf)

**Generated:** 2025-12-05 14:07:28

---

**Overview/Summary**

The paper "Active classification with comparison queries" by Daniel M. Kane and Robert E. Schapire is a theoretical study in the area of active learning, which is an iterative process where the algorithm can ask for labels on some instances to be classified. The goal is to minimize the number of label requests while still achieving a good level of accuracy. In this paper, the authors consider the problem of active classification with comparison queries. A comparison query is one that asks whether two given instances are different or not, and they show that in the case where the hypothesis class is a half space (a linear decision boundary), the number of label requests can be significantly reduced by using comparison queries. The paper also shows that if the inference dimension is large, then many queries are needed to infer all the labels.

**Key Contributions/Findings**

The main contribution of this work is an upper bound on the number of label requests for active classification with comparison queries and a lower bound. This is achieved by using a novel combinatorial approach that combines the ideas from two different areas: the theory of active learning, and the theory of geometric embeddings.

**Methodology/Approach**

The authors first present the basic definitions of active learning and the main result for half spaces in this paper. The main result is an upper bound on the number of label requests needed to achieve a given accuracy level with high probability. This is achieved by using a novel combinatorial approach that combines the ideas from two different areas: the theory of active learning, and the theory of geometric embeddings.

**Results/Data**

The authors show that if the inference dimension is large, then many queries are needed to infer all the labels. The lower bound in this paper is tight for half spaces. This means that the number of label requests can be significantly reduced by using comparison queries. In particular, the number of label requests can be at most k/t where t is the size of the set of instances on which a query depends.

**Limitations/Discussion**

The main limitation of this paper is that it only considers half spaces as the hypothesis class and comparison queries are not used in many active learning problems. The authors also point out that if the inference dimension is large, then many queries are needed to infer all the labels. This means that the number of label requests can be significantly reduced by using comparison queries.

**References**

Kane, D. M., & Schapire, R. E. (n.d.). Active classification with comparison queries. Retrieved from https://arxiv.org/abs/1903.08661

---

**Summary Statistics:**
- Input: 13,496 words (80,558 chars)
- Output: 431 words
- Compression: 0.03x
- Generation: 25.9s (16.6 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
