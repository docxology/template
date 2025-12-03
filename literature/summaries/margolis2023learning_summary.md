# Learning to See Physical Properties with Active Sensing Motor Policies

**Authors:** Gabriel B. Margolis, Xiang Fu, Yandong Ji, Pulkit Agrawal

**Year:** 2023

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [margolis2023learning.pdf](../pdfs/margolis2023learning.pdf)

**Generated:** 2025-12-03 04:20:25

---

Overview/Summary:
The paper introduces a new learning paradigm called Active Sensing Motor Policies (ASMP) for sim-to-real transfer of visual perception in legged robots. The authors propose to train the visual module on proprioceptive data, which is more readily available and less expensive than real-world data, by using an active policy that actively selects the next state based on the current observation. They show that this approach can be used to learn a better visual model for sim-to-real transfer of friction inference from color images.

Key Contributions/Findings:
The main contributions are in two parts: (1) they propose ASMP, and (2) they demonstrate its effectiveness for sim-to-real transfer of visual perception. The first part is the introduction of ASMP, which is a new learning paradigm that trains the visual module on proprioceptive data by using an active policy. The second part is the demonstration of the effectiveness of the proposed approach.

Methodology/Approach:
The authors start with the observation that in sim-to-real transfer, the performance gap between simulation and real-world is mainly due to the difference in the sensing modality (color image vs. proprioceptive data) rather than the difference in the policy. They propose ASMP by using an active policy to train a visual module on proprioceptive data. The basic idea of the proposed approach is that the visual module can be trained with the help of the proprioceptive data, which is more readily available and less expensive than real-world data, by using an active policy. In this paper, they use the A∗ algorithm for path planning.

Results/Data:
The authors first demonstrate the effectiveness of ASMP in a simulated environment. They collect one minute of simulated data from policies trained with and without active state estimation and compare the resulting visual inference result against the ground truth. The results show that the visual module trained on data from the proposed approach is better than the baseline. Then, they use the proposed approach to train the visual module for sim-to-real transfer of friction inference from color images in a real-world environment. They collect 5 minutes of data and compare the resulting visual inference result against the ground truth. The results show that the ASMP can be used to learn a better visual model for the sim-to-real transfer of friction inference.

Limitations/Discussion:
The authors point out some limitations of their work, which are mainly related to the experimental setup. For example, they only use one robot and do not test the proposed approach on other robots. They also mention that the ground truth is not available in the real-world environment. The authors believe that the proposed approach can be used for more complex tasks such as learning the visual model for the whole-body motion.

Additional Information:
The paper does not provide any additional information beyond what is already written above.

---

**Summary Statistics:**
- Input: 7,350 words (47,595 chars)
- Output: 465 words
- Compression: 0.06x
- Generation: 26.3s (17.7 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
