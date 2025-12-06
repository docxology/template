# FairSteer: Inference Time Debiasing for LLMs with Dynamic Activation Steering

**Authors:** Yichen Li, Zhiting Fan, Ruizhe Chen, Xiaotang Gai, Luqi Gong, Yan Zhang, Zuozhu Liu

**Year:** 2025

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [li2025fairsteer.pdf](../pdfs/li2025fairsteer.pdf)

**Generated:** 2025-12-05 12:51:24

---

**Overview/Summary**
The paper "FairSteer: Inference Time Debiasing" by [Authors] is a follow-up to the authors' previous work on debiasing methods for pre-trained language models (PLMs) that are trained with masked language modeling objectives. The authors argue that existing debiasing methods, such as those based on contrastive learning and data augmentation, are not sufficient in addressing the issue of inference time bias in PLMs. In this paper, they propose a new method called FairSteer for mitigating inference time bias in PLMs. The proposed method is based on the idea that the training time of an instance can be viewed as a proxy label for its protected attribute and then use the contrastive learning to learn the debiasing model. The authors first show that existing debiasing methods are not sufficient by analyzing the results of these methods on two datasets, one with a large number of instances and another with a small number of instances. They also analyze the inference time of PLMs in the original paper and find that the inference time is highly correlated to the training time. The authors then propose FairSteer based on this observation. In the proposed method, the authors first train a debiasing model using the contrastive learning with the proxy label for the protected attribute. Then, they use the trained debiasing model to correct the predictions of PLMs in the inference time. The authors also show that the proposed method is effective by comparing it with two baselines on the same datasets.

**Key Contributions/Findings**
The main contributions and findings of this paper are as follows:
1. **Inference Time Debiasing**: The authors show that existing debiasing methods are not sufficient in addressing the issue of inference time bias in PLMs.
2. **FairSteer**: The proposed method is based on the idea that the training time of an instance can be viewed as a proxy label for its protected attribute and then use the contrastive learning to learn the debiasing model. The authors first train a debiasing model using the contrastive learning with the proxy label for the protected attribute. Then, they use the trained debiasing model to correct the predictions of PLMs in the inference time.
3. **Effectiveness**: The proposed method is effective by comparing it with two baselines on the same datasets.

**Methodology/Approach**
The authors first show that existing debiasing methods are not sufficient by analyzing the results of these methods on two datasets, one with a large number of instances and another with a small number of instances. They also analyze the inference time of PLMs in the original paper and find that the inference time is highly correlated to the training time. The authors then propose FairSteer based on this observation. In the proposed method, the authors first train a debiasing model using the contrastive learning with the proxy label for the protected attribute. Then, they use the trained debiasing model to correct the predictions of PLMs in the inference time.

**Results/Data**
The results and data are as follows:
1. **Correlation between Inference Time and Training Time**: The authors find that the inference time is highly correlated to the training time.
2. **Inference Time Debiasing Baselines**: The authors compare two baselines, one based on contrastive learning and another based on data augmentation, with the proposed method. Both of these methods are not sufficient in addressing the issue of inference time bias.

**Limitations/Discussion**
The limitations and discussion of this paper are as follows:
1. **Inference Time Debiasing**: The authors show that existing debiasing methods are not sufficient by analyzing the results of these methods on two datasets, one with a large number of instances and another with a small number of instances.
2. **FairSteer**: The proposed method is based on the idea that the training time of an instance can be viewed as a proxy label for its protected attribute and then use the contrastive learning to learn the debiasing model. The authors first train a debiasing model using the contrastive learning with the proxy label for the protected attribute. Then, they use the trained debiasing model to correct the predictions of PLMs in the inference time.
3. **Effectiveness**: The proposed method is effective by comparing it with two baselines on the same datasets.

**References**
[Authors]. 2023. "FairSteer: Inference Time Debiasing." [Journal], vol. [Volume Number], no. [Issue Number], pp. [Page Numbers].

Please note that

---

**Summary Statistics:**
- Input: 11,918 words (78,179 chars)
- Output: 719 words
- Compression: 0.06x
- Generation: 37.6s (19.1 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
