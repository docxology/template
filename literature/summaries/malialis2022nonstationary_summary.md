# Nonstationary data stream classification with online active learning and siamese neural networks

**Authors:** Kleanthis Malialis, Christos G. Panayiotou, Marios M. Polycarpou

**Year:** 2022

**Source:** arxiv

**Venue:** arXiv

**DOI:** 10.1016/j.neucom.2022.09.065

**PDF:** [malialis2022nonstationary.pdf](../pdfs/malialis2022nonstationary.pdf)

**Generated:** 2025-12-03 04:00:30

---

=== OVERVIEW/SUMMARY ===

The paper proposes a novel approach to nonstationary data stream classification with online active learning. The authors first investigate the performance of several existing methods in this area and find that they are not robust enough for real-world applications. Then, they propose an online active learning algorithm based on a multi-queue memory structure. In their proposed method, each queue is used to store the samples from one class and the similarity between the input data and the stored samples is calculated by a Siamese network. The similarity is then used as the confidence score for the current sample in the corresponding queue. The algorithm with the largest confidence score will be selected to update the multi-queue memory. This process is repeated until the budget is exhausted or the classification task is completed. In this way, the samples that are most likely to belong to one class can be classified first and the rest of the samples can be classified later. The authors also propose a Siamese network based on two feed-forward neural networks with shared weights. The similarity between the input data and the stored data in each queue is calculated by the difference between the output of the two networks. The proposed algorithm is compared to several existing methods and the results show that it outperforms them.

=== KEY CONTRIBUTIONS/FOUNDS ===

The main contributions of this paper are:

1. An online active learning algorithm based on a multi-queue memory structure. This method can be used for nonstationary data stream classification.
2. A Siamese network based on two feed-forward neural networks with shared weights. The similarity between the input data and the stored data in each queue is calculated by the difference between the output of the two networks.

=== METHODOLOGY/APPROACH ===

The proposed algorithm first investigates the performance of several existing methods for nonstationary data stream classification. These methods are: (1) Random Sampling, (2) Online Passive Learning, (3) Online Active Learning with a single queue, and (4) Online Active Learning with an ensemble. The authors then propose their online active learning algorithm based on a multi-queue memory structure. In the proposed method, each queue is used to store the samples from one class and the similarity between the input data and the stored samples is calculated by a Siamese network. The similarity is then used as the confidence score for the current sample in the corresponding queue. The algorithm with the largest confidence score will be selected to update the multi-queue memory. This process is repeated until the budget is exhausted or the classification task is completed.

The proposed method is compared to several existing methods and the results show that it outperforms them. In addition, the authors also propose a Siamese network based on two feed-forward neural networks with shared weights. The similarity between the input data and the stored data in each queue is calculated by the difference between the output of the two networks.

=== RESULTS/DATA ===

The results for the synthetic datasets are shown in Figs. 7-10, while the results for the real-world datasets are shown in Figs. 11-12. The active learning budget is set to B=1% unless otherwise stated. In Fig. 7a, ActiSiamese learns signifi-cantly faster than the rest. Given more time, ActiQ and RVSS may equalise ActiSiamese or may even slightly outperform it. In Fig. 7b, the superiority of ActiSiamese is shown. In Fig. 7c both ActiSiamese and ActiQ (to a lesser degree) deal well with abrupt drift; notice how similar this figure with Fig. 7a is. The combination of drift with imbalance in Fig. 7d causes some variation in the performance throughout the experiment's duration. Interestingly, in Fig. 7e, RVSS outperforms the rest.

In Figs. 10a and 10b, ActiSiamese has a superior learning speed; given additional time RVSS and ActiQ equalise its performance in sea and slightly outperform it in circles. In Figs. 10c and 10d ActiSiamese outperforms the rest. The "oscillations" observed in Fig. 10d are due to interchanging nature of drift.

The results for the remaining of the synthetic datasets are shown in Figs. 10a-10e. The active learning is B=10% for circles, sea and Two Patterns, while for the more challenging Inter-changing RBF and Moving Squares datasets it is set to B=30%. In Figs. 10a and 10b, ActiSiamese has a superior learning speed; given additional time RVSS and ActiQ equalise its performance in sea and slightly outperform it in circles. In Figs. 10c and 10d ActiSiamese outperforms the rest.

The results for the real-world datasets are shown in Figs. 11a-11f. The active learning is B=1% unless otherwise stated. In Fig. 7a, given additional time, ActiQ slightly outperforms ActiSiamese. In Fig. 7b, the superiority of ActiSiamese is shown. In Fig. 7c both ActiSiamese and ActiQ (to a lesser degree) deal well with abrupt drift; notice how similar this figure with Fig. 7a is. The combination of drift with imbalance in Fig. 7d causes some variation in the performance throughout the experiment's duration. Interestingly, in Fig. 7e, RVSS outperforms the rest.

Taking everything into account, important remarks are as follows:

1. ActiSiamese, ActiQ, and RVSS that use the multi-queue memory significantly outperform the one-pass learner RVUS in all scenarios.
2. Among the memory-based methods, ActiSiamese learns signifi-cantly faster than the rest. Given more time, ActiQ and RVSS may equalise ActiSiamese or may even slightly outperform it.
3. ActiSiamese is superior under class imbalance.
4. The methods that use the multi-queue memory deal with drift well, and they are robust to it. However, under challenging drift conditions, we had to increase the memory size and/ or active learning budget.

=== LIMITATIONS/DISCUSSION ===

The main limitation of this paper is that the performance of the proposed algorithm may vary after the drift in the data stream. The authors also mention some future work: (1) how to further improve the performance under class imbalance, (2) how to deal with the interchanging nature of drift, and (3) how to combine the multi-queue memory with an ensemble.

=== END PAPER CONTENT ===

---

**Summary Statistics:**
- Input: 11,561 words (74,195 chars)
- Output: 998 words
- Compression: 0.09x
- Generation: 51.7s (19.3 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
