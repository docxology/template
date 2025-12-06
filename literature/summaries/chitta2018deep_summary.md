# Deep Probabilistic Ensembles: Approximate Variational Inference through KL Regularization

**Authors:** Kashyap Chitta, Jose M. Alvarez, Adam Lesnikowski

**Year:** 2018

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [chitta2018deep.pdf](../pdfs/chitta2018deep.pdf)

**Generated:** 2025-12-05 13:54:34

---

**Overview/Summary**

The paper introduces a new approach for training deep neural networks with Bayesian inference, which is called Deep Probabilistic Ensembles (DPEs). The authors argue that the current methods of Bayesian inference in deep learning are not scalable to large models and datasets. They propose DPEs as an alternative method by approximating variational inference for Bayesian Neural Networks (BNNs) using a novel KL regularization term. The key idea is to train ensembles with this new KL regularization term, which allows the use of BNNs in existing frameworks without impacting performance.

**Key Contributions/Findings**

The authors show that DPEs improve performance on active learning tasks over baselines and state-of-the-art active learning techniques on two image classification datasets. The results are consistent across different annotation budgets, with the gap to the corresponding upper bound growing as the annotation budget increases. The paper also compares the proposed approach to state-of-the-art active learning techniques on the CIFAR-10 dataset using 20% of the labeled training data. The authors show that DPEs outperform all the others, not only achieving higher accuracy with limited training data but also reducing the gap to the corresponding upper bound.

**Methodology/Approach**

The proposed method is based on a novel KL regularization term for Bayesian inference in BNNs. The key idea is to train ensembles with this new KL regularization term, which allows the use of BNNs in existing frameworks without impacting performance. This paper shows that DPEs improve performance on active learning tasks over baselines and state-of-the-art active learning techniques on two image classification datasets. The results are consistent across different annotation budgets, with the gap to the corresponding upper bound growing as the annotation budget increases. The paper also compares the proposed approach to state-of-the-art active learning techniques on the CIFAR-10 dataset using 20% of the labeled training data. The authors show that DPEs outperform all the others, not only achieving higher accuracy with limited training data but also reducing the gap to the corresponding upper bound.

**Results/Data**

The results are shown in Tables 1 and 2. Table 1 shows the mean accuracy of 3 experimental trials. As shown, active learning with DPEs clearly outperforms random baselines, and consistently provides better results compared to ensemble based active learning methods. Further, though the gap is small, it typically grows as the annotation budget (size of the labeled dataset) increases, which is a particularly appealing property for large-scale labeling projects. The paper also compares the proposed approach to state-of-the-art active learning techniques on the CIFAR-10 dataset using 20% of the labeled training data. The authors show that DPEs outperform all the others, not only achieving higher accuracy with limited training data but also reducing the gap to the corresponding upper bound.

**Limitations/Discussion**

The paper does not discuss any limitations or future work.

---

**Summary Statistics:**
- Input: 2,582 words (15,657 chars)
- Output: 459 words
- Compression: 0.18x
- Generation: 26.7s (17.2 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
