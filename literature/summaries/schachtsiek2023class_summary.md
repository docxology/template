# Class Balanced Dynamic Acquisition for Domain Adaptive Semantic Segmentation using Active Learning

**Authors:** Marc Schachtsiek, Simone Rossi, Thomas Hannagan

**Year:** 2023

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [schachtsiek2023class.pdf](../pdfs/schachtsiek2023class.pdf)

**Generated:** 2025-12-03 03:46:20

---

**Overview/Summary**
The paper "Class Balanced Dynamic Acquisition for Domain Adaptive Semantic Segmentation" is a research work in the field of computer vision that proposes an active learning method to improve the performance of domain adaptive semantic segmentation. The authors present a new approach called Class Balanced Dynamic Acquisition (CBDA) and compare it with several other methods including the baseline, class balancing, dynamic acquisition, and their combination. The paper starts by discussing the importance of domain adaptation in the field of computer vision. Domain adaptation is the ability to improve the performance of an image segmentation model on a target domain without any additional data from that domain. This problem is challenging because there are large differences between the source and the target domains. The authors also discuss the current state-of-the-art methods for this problem, including the baseline, class balancing, and dynamic acquisition.

**Key Contributions/Findings**
The main contribution of the paper is the proposal of a new active learning method called Class Balanced Dynamic Acquisition (CBDA). This approach can improve the performance of domain adaptive semantic segmentation. The authors also compare CBDA with several other methods to show its effectiveness. The authors first introduce the baseline, which is the current state-of-the-art method for this problem. The baseline is based on a simple random sampling strategy that does not consider the class distribution in the source and target domains. However, it is found that the performance of the baseline is very low because the random selection may not select the pixels that are most useful to improve the model. To solve this problem, the authors propose two other methods: class balancing and dynamic acquisition. The first one is a simple method that balances the number of samples from different classes in the source domain. This approach can reduce the imbalance between the classes in the target domain. However, it does not consider the class distribution in the target domain. The second one is based on an active learning strategy that selects the most useful pixels to label. It uses a dynamic acquisition strategy and a class balancing method to improve the performance of the model. This approach can select more representative samples than the baseline. In addition, the authors compare the combination of the two methods with the baseline.

**Methodology/Approach**
The first part is the introduction of the baseline. The authors then introduce the dynamic acquisition strategy and the class balancing method. These two strategies are used to improve the performance of the model. The authors also describe the combination of the two strategies, which is called CBDA. The main idea of this approach is that it can balance the class distribution in the target domain while using a dynamic acquisition strategy. This approach can select more representative samples than the baseline and the class balancing method.

**Results/Data**
The paper first compares the performance of the baseline with the two other methods: class balancing and dynamic acquisition. The results show that the performance of the baseline is very low because it does not consider the class distribution in the source and target domains. The authors also compare the combination of the two strategies, which is called CBDA, with the baseline. The results show that the performance of the baseline is lower than the other three methods. This result shows that both the dynamic acquisition strategy and the class balancing method can improve the performance of the model. In addition, the results show that the class balancing method can improve the performance of the model more than the dynamic acquisition strategy. However, it is found that the performance of the baseline is higher than the combination of the two strategies. This result shows that the class balancing method may limit the selection of high-scoring indices in the RA regime with a not adequately converged model. The authors also compare the performance of the CBDA with the baseline and the other three methods. The results show that the performance of the CBDA is the best among all the four approaches.

**Limitations/Discussion**
The paper does not discuss any limitations or future work.

---

**Summary Statistics:**
- Input: 5,248 words (32,515 chars)
- Output: 677 words
- Compression: 0.13x
- Generation: 32.5s (20.8 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
