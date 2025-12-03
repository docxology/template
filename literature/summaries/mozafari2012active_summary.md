# Active Learning for Crowd-Sourced Databases

**Authors:** Barzan Mozafari, Purnamrita Sarkar, Michael J. Franklin, Michael I. Jordan, Samuel Madden

**Year:** 2012

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [mozafari2012active.pdf](../pdfs/mozafari2012active.pdf)

**Generated:** 2025-12-03 06:47:45

---

**Overview/Summary**

The paper "Active Learning for Crowd-Sourced Databases" presents a new approach to active learning in the context of crowd-sourced databases. The authors propose two algorithms that can be used to select which data points should be labeled by a human annotator, and they compare these algorithms with a baseline algorithm. In 

**Key Contributions/Findings**

The main contribution is an active learning algorithm called MinExpError, which is based on the idea that the best way to select data points for labeling is by choosing those that are most likely to be misclassified. The authors also compare this algorithm with two other algorithms: Uncertainty and Greedy. The key findings of the paper include the following:

* **MinExpError** is a new active learning algorithm, which can be used in the context of crowd-sourced databases.
* **Uncertainty** is an existing active learning algorithm that chooses data points based on their uncertainty. This algorithm is not optimal for the problem at hand and it is also not guaranteed to converge.
* **Greedy** is another baseline algorithm that always selects the most uncertain data point, which can be used as a starting point for other algorithms.
* **The proposed MinExpError algorithm outperforms both Uncertainty and Greedy on the gold datasets.**
* **The authors show that their active learning algorithm can improve the balance of the questions asked about different classes.**

**Methodology/Approach**

The paper is based on an existing active learning algorithm called Uncertainty, which chooses data points for labeling based on their uncertainty. The authors also compare this algorithm with a baseline algorithm called Greedy. The key idea in the proposed MinExpError algorithm is that it can be used to select those data points that are most likely to be misclassified. This algorithm is not guaranteed to converge and it is not optimal for the problem at hand, but it outperforms both Uncertainty and Greedy on the gold datasets.

**Results/Data**

The authors compare their proposed MinExpError algorithm with two other algorithms: Uncertainty and Greedy. The results show that the proposed algorithm can improve the balance of the questions asked about different classes. The authors also evaluate how to decide when to stop asking for labels, and they find that this method provides more reliable estimates than relying on a small amount of gold data.

**Limitations/Discussion**

The paper does not discuss any limitations or future work.

---

**Summary Statistics:**
- Input: 14,874 words (93,125 chars)
- Output: 389 words
- Compression: 0.03x
- Generation: 24.2s (16.0 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
