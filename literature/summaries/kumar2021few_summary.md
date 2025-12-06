# Few Shot Activity Recognition Using Variational Inference

**Authors:** Neeraj Kumar, Siddhansh Narang

**Year:** 2021

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [kumar2021few.pdf](../pdfs/kumar2021few.pdf)

**Generated:** 2025-12-05 13:15:25

---

**Overview/Summary**

The paper "Few Shot Activity Recognition Using Variational Inference" proposes a novel approach for few-shot learning in activity recognition. The authors argue that the current approaches for few-shot learning are not effective when the number of training samples is very small, and they claim that the existing methods do not address the problem of how to learn from only a few examples. They also point out that the existing methods are based on the assumption that there exists a large amount of data in the target domain, which may not be true for some cases.

**Key Contributions/Findings**

The authors propose an approach called Few-shot Activity Recognition (FSAR) using Variational Inference (VI). The main contributions of this paper are: 1) they introduce a new few-shot learning problem and formulate it as a density estimation task, 2) they propose the FSAR-VI method for solving the above problem. The key findings of this paper are that the proposed approach can achieve better performance than the existing methods in the case where only one or two training samples per class is available.

**Methodology/Approach**

The authors first introduce a new few-shot learning problem, which they call few-shot activity recognition (FSAR). In FSR, there are only a few training samples for each class. The authors then formulate this problem as a density estimation task. They argue that the existing methods do not address the problem of how to learn from only a few examples. Then, they propose an approach called FSAR-VI. This is based on the idea of variational inference (VI). In VI, the goal is to find the distribution which maximizes the log-likelihood function with respect to the observed data. The authors first describe the VI method in detail and then apply it to the FSR problem. They also compare their approach with the existing approaches.

**Results/Data**

The authors evaluate their proposed FSAR-VI on two datasets, UCF101 and HMDB51. For the UCF101 dataset, they use 10-fold cross-validation. The results show that the proposed method can achieve better performance than the existing methods in most cases. On the HMDB51 dataset, they compare the accuracy of the different approaches. The results also show that the proposed approach can achieve better performance than the existing methods.

**Limitations/Discussion**

The authors point out some limitations and discuss the future work for this paper. They argue that the proposed method is not effective when there are only a few classes in the target domain, and they claim that the FSR problem is more challenging than the traditional few-shot learning problem. The authors also mention that the existing methods do not address the problem of how to learn from only a few examples.

**References**

The references for this paper are listed at the end of

---

**Summary Statistics:**
- Input: 5,488 words (35,113 chars)
- Output: 454 words
- Compression: 0.08x
- Generation: 26.1s (17.4 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
