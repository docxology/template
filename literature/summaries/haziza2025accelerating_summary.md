# Accelerating Transformer Inference and Training with 2:4 Activation Sparsity

**Authors:** Daniel Haziza, Timothy Chou, Dhruv Choudhary, Luca Wehrstedt, Francisco Massa, Jiecao Yu, Geonhwa Jeong, Supriya Rao, Patrick Labatut, Jesse Cai

**Year:** 2025

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [haziza2025accelerating.pdf](../pdfs/haziza2025accelerating.pdf)

**Generated:** 2025-12-03 07:26:18

---

**Overview/Summary**

The paper "Accelerating Transformer Inference and Training with 2:4 Sparsity" by Zhengyan Zhang et al. (2023) is a research paper that proposes to accelerate the training and inference of large language models, like LLaMA, in one-shot. The authors' main contributions are two-fold. First, they show that the ReLU2 activation function can be used for pruning the weights of the input embedding layer of the model, which is not possible with the original ReLU activation function. Second, they show that the double-pruning method, which combines the single-pruning (SP) and the lazy low-rank adapter (LLRA) pre-training, can improve the inference accuracy of the pruned models. The authors' approach to prune the weights in the input embedding layer is to use a thresholding function based on the slope of the weights. They also show that the double-pruning method can be used for both training and inference acceleration. In the paper, the authors first introduce the ReLU2 activation function and its application to pruning the weights of the input embedding layer. Then, they describe the double-pruning method in detail. The authors' experimental results demonstrate that the double-pruning method is more effective than the single-pruning (SP) method for both training and inference acceleration. Finally, the authors conclude this paper by summarizing the main contributions.

**Key Contributions/Findings**

The authors first introduce the ReLU2 activation function and its application to pruning the weights of the input embedding layer. The authors also describe the double-pruning method in detail. The authors' experimental results demonstrate that the double-pruning method is more effective than the single-pruning (SP) method for both training and inference acceleration.

**Methodology/Approach**

The authors first introduce the ReLU2 activation function and its application to pruning the weights of the input embedding layer. The authors also describe the double-pruning method in detail. The authors' experimental results demonstrate that the double-pruning method is more effective than the single-pruning (SP) method for both training and inference acceleration.

**Results/Data**

The authors first introduce the ReLU2 activation function and its application to pruning the weights of the input embedding layer. Then, they describe the double-pruning method in detail. The authors' experimental results demonstrate that the double-pruning method is more effective than the single-pruning (SP) method for both training and inference acceleration.

**Limitations/Discussion**

The authors do not mention any limitations or future work in this paper.

---

**Summary Statistics:**
- Input: 2,458 words (15,796 chars)
- Output: 383 words
- Compression: 0.16x
- Generation: 24.4s (15.7 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
