# LExI: Layer-Adaptive Active Experts for Efficient MoE Model Inference

**Authors:** Krishna Teja Chitty-Venkata, Sandeep Madireddy, Murali Emani, Venkatram Vishwanath

**Year:** 2025

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [chittyvenkata2025lexi.pdf](../pdfs/chittyvenkata2025lexi.pdf)

**Generated:** 2025-12-03 06:02:51

---

**Overview/Summary**

The paper introduces LExI (Layer-Adaptive Experts), a new method for pruning mixture-of-experts (MoE) models that adaptively prunes the number of experts in each layer based on their importance, which is estimated by the output deviation. The authors first propose an upper bound and lower bound for the output deviation under the top-k perturbation, then use these bounds to prune the number of experts in each layer. In this way, LExI can be used with any pruning method that uses the output deviation as a metric. The authors also compare the performance of LExI with other pruning methods on several MoE models and show that LExI can achieve better or comparable results than these state-of-the-art pruning methods.

**Key Contributions/Findings**

The main contributions of this paper are:
1. **Layer-Adaptive Pruning**: The authors propose a new method for pruning the number of experts in each layer based on the output deviation, which is estimated by the top-k perturbation.
2. **Upper and Lower Bounds**: They provide upper and lower bounds for the output deviation under the top-k perturbation, and use these bounds to prune the number of experts in each layer.
3. **Pruning Methods**: The authors compare the performance of LExI with other pruning methods on several MoE models.

**Methodology/Approach**

The authors first introduce an upper bound and a lower bound for the output deviation under the top-k perturbation, then use these bounds to prune the number of experts in each layer. The key idea is that if the output deviation of one layer is larger than its upper bound, it should be pruned more aggressively; otherwise, it can be pruned less aggressively.

**Results/Data**

The authors compare the performance of LExI with other pruning methods on several MoE models and show that LExI can achieve better or comparable results than these state-of-the-art pruning methods. The results are shown in Table 2. The plots for top-1 sensitivity analysis across MiniCPM-MoE and DeepSeekV2-Lite are illustrated in Figure 9.

**Limitations/Discussion**

The authors also discuss the limitations of this paper, such as the lack of theoretical guarantees on the optimality of the upper and lower bounds, and the need for a more accurate estimation of the output deviation. The authors also mention that the performance of LExI can be further improved by combining it with other pruning methods.

**Table 2**

| Model | #P (B) | #Layers | #Experts | TopK FFN Dim |
| --- | --- | --- | --- |
| DeepSeek VL2-Tiny | 3 | 12 | 64 | 6 | 896 |
| OLMoE-1B-7B-0125-Instruct | 6.92 | 16 | 64 | 8 | 1024 |
| Qwen1.5-MoE-A2.7B-Chat | 14.3 | 24 | 60 | 4 | 1408 |
| DeepSeek-V2-Lite-Chat | 15.7 | 27 | 64 | 6 | 1408 |
| MiniCPM-MoE-8x2B | 17 | 40 | 8 | 2 | 5760 |
| Mixtral-8x7B-Instruct-v0.1 | 46.7 | 32 | 8 | 2 | 14336 |

**Figure 9**

| Layer Index | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.00 | 0.25 | 0.50 | 1.00 |
| Loss | 2T opK | 3T opk | 4T opk | 5T opk | 6T opk | 7T opk | 8T opk | 9T topk | 10T topk | 11T topk | 12T topk |
| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 |
| T opK | 0.00 | 0.25 | 0.50 | 1.00 |
| Loss |

**Table 2**

| Model | #P (B) | #Layers | #Experts | TopK FFN Dim |
| --- | --- | --- | --- |
| DeepSeek VL2-Tiny | 3 | 12 | 64 | 6 | 896 |
| OLMoE-1B-7B-0125-Instruct | 6.92 | 16 | 64 | 8 | 1024 |
| Qwen1.5-MoE-A2.7B-Chat | 14.3 | 24 | 60 | 4 | 1408 |
| DeepSeek-V2-Lite-Chat | 15.7 | 27 | 64 | 6 | 1408 |
| MiniCPM-MoE-8x2B | 17 | 40 | 8 | 2 | 5760 |
| Mixtral-8x7B-Instruct-v0.1 | 46.7 | 32 | 8 | 2 | 14336 |

**Figure 9**

| Layer Index | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.00 | 0.25 | 0.50 | 1.00 |
| Loss | 2T opK | 3T topk | 4T topk | 5T topk | 6T topk | 7T topk | 8T topk | 9T topk | 10T topk | 11T topk | 12T topk |
| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 |
| T opK | 0.00 | 0.25 | 0.50 | 1.00 |

**Table 3**

| Model | #P (B) | #Layers | #Experts | TopK FFN Dim |
| --- | --- | --- | --- |
| DeepSeek VL2-Tiny | 3 | 12 | 64 | 6 | 896 |
| OLMoE-1B-7B-0125-Instruct | 6.92 | 16 | 64 | 8 | 1024 |
| Qwen1.5-MoE-A2.7B-Chat | 14.3 | 24 | 60 | 4 | 1408 |
| DeepSeek-V2-Lite-Chat | 15.7 | 27 | 64 | 6 | 1408 |
| MiniCPM-MoE-8x2B | 17 | 40 | 8 | 2 | 5760 |
| Mixtral-8x7B-Instruct-v0.1 | 46.7 | 32 | 8 | 2 | 14336 |

**Figure 10**

|

---

**Summary Statistics:**
- Input: 7,052 words (47,282 chars)
- Output: 1,307 words
- Compression: 0.19x
- Generation: 67.7s (19.3 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
