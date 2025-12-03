# Mitigating shortage of labeled data using clustering-based active learning with diversity exploration

**Authors:** Xuyang Yan, Shabnam Nazmi, Biniam Gebru, Mohd Anwar, Abdollah Homaifar, Mrinmoy Sarkar, Kishor Datta Gupta

**Year:** 2022

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [yan2022mitigating.pdf](../pdfs/yan2022mitigating.pdf)

**Generated:** 2025-12-03 03:58:28

---

**Overview/Summary**

The paper presents a new active learning (AL) framework called ALCS (Active Learning with Clustering Sampling), which is designed to handle the shortage of labeled data in the absence of prior label information. The main idea is to use the FPS-Clustering procedure to explore the structure of unlabeled data without exhaustive parameter tuning, and then develop a new distance-based sample selection procedure along with an effective diversity exploration strategy to enhance the quality of queried labels. The authors claim that ALCS can be used in datasets where the classes are highly overlapped.

**Key Contributions/Findings**

The main contributions of this paper are:
1. A novel clustering- based AL framework, which is designed to handle the dependency on clustering parameters and offers a promising solution to improve the diversity among queried labels.
2. The bi-cluster boundary selection strategy is developed to enhance the learning performance in datasets where the classes are highly overlapped.

**Methodology/Approach**

The authors first present the FPS-Clustering procedure, which is used to explore the structure of unlabeled data without exhaustive parameter tuning. Then, they develop a new distance-based sample selection procedure with an effective diversity exploration strategy to enhance the quality of queried labels. The main idea is that the clustering parameters are not required in the proposed ALCS framework.

**Results/Data**

The authors compare their method with five other clustering- based AL approaches without tuning the clustering parameters. Experimental results show that ALCS provides better or comparable performance than the five clustering-based AL approaches without tuning the clustering parameters. The main finding is that ALCS can be used to improve the diversity among queried labels in datasets where the classes are highly overlapped.

**Limitations/Discussion**

The authors mention two limitations of their ALCS framework: (i) the imbalance among different class distributions is not considered in ALCS; and (ii) ALCS is currently limited to oﬀine AL problems. Therefore, the future work will focus on addressing these two limitations of the ALCS framework.

**References**

The authors acknowledge support from the Air Force Research Laboratory and the Oﬃce of the Secretary of Defense under agreement number (FA8750-15-2-0116). This work is also partially supported by National Science Foundation under grant number (2000320).

**Acknowledgments**

The authors would like to thank Fan Min for his help in this paper.

---

**Summary Statistics:**
- Input: 2,406 words (16,621 chars)
- Output: 374 words
- Compression: 0.16x
- Generation: 23.8s (15.7 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
