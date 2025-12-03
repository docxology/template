# Semi-supervised Active Learning for Video Action Detection

**Authors:** Ayush Singh, Aayush J Rana, Akash Kumar, Shruti Vyas, Yogesh Singh Rawat

**Year:** 2023

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [singh2023semisupervised.pdf](../pdfs/singh2023semisupervised.pdf)

**Generated:** 2025-12-03 05:29:32

---

Overview/Summary:
The paper proposes a novel semi-supervised active learning (SSAL) approach for video action detection. The authors argue that while there are many works on video action detection in the literature, most of them focus on supervised learning and only a few work on weakly supervised or unsupervised learning. In this paper, the authors propose to use pseudo-labels as supervision signals which can be obtained from unlabeled data. They also claim that existing methods for semi-supervised active learning are not suitable for video action detection because they do not consider the temporal context of videos.

Key Contributions/Findings:
The main contributions of the paper are the proposed SSAL approach and its application to video action detection. The authors first discuss the challenges in using pseudo-labels as supervision signals, then introduce the proposed SSAL algorithm. They also conduct extensive experiments on four datasets: UCF101, HMDB51, ActivityNet1.2, and AVA. Their results show that the proposed approach outperforms existing state-of-the-art methods.

Methodology/Approach:
The authors first discuss the challenges in using pseudo-labels as supervision signals for video action detection. The main challenge is that there are many classes in video action detection datasets and it is difficult to obtain a good pseudo-label for each class. They also claim that existing methods for semi-supervised active learning are not suitable for video action detection because they do not consider the temporal context of videos. Then, the authors propose to use pseudo-labels as supervision signals which can be obtained from unlabeled data. The proposed method is based on a recently proposed algorithm called FixMatch. In this paper, the authors first introduce the FixMatch and then show how to apply it for video action detection. The authors also discuss the limitations of the existing methods for semi-supervised active learning.

Results/Data:
The results are presented in Section 4. The authors use four datasets: UCF101, HMDB51, ActivityNet1.2, and AVA. They first compare the proposed approach with the baseline method (i.e., FixMatch) on these four datasets. Then, they compare the proposed approach with other existing state-of-the-art methods. The results show that the proposed approach outperforms the baseline method. They also compare the proposed approach with other existing state-of-the-art methods.

Limitations/Discussion:
The authors discuss the limitations of their work in Section 5. The main limitation is that it is difficult to obtain a good pseudo-label for each class. The authors claim that this is the first work that uses pseudo-labels as supervision signals for video action detection. They also claim that existing methods are not suitable for video action detection because they do not consider the temporal context of videos. The authors suggest future directions in Section 6.

---

**Summary Statistics:**
- Input: 7,730 words (48,458 chars)
- Output: 435 words
- Compression: 0.06x
- Generation: 28.3s (15.4 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
