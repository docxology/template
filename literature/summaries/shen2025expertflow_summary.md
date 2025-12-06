# ExpertFlow: Adaptive Expert Scheduling and Memory Coordination for Efficient MoE Inference

**Authors:** Zixu Shen, Kexin Chu, Yifan Zhang, Dawei Xiang, Runxin Wu, Wei Zhang

**Year:** 2025

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [shen2025expertflow.pdf](../pdfs/shen2025expertflow.pdf)

**Generated:** 2025-12-05 13:59:02

---

**Overview/Summary**

The paper proposes a novel adaptive expert scheduling and memory coordination (AESMC) algorithm for efficient mixture-of-experts (MoE) inference. The authors argue that the existing MoE algorithms are not well-suited to handle the large-scale MoE models, which require a large number of experts. They propose an AESMC algorithm that can be used in conjunction with any MoE training method and is particularly useful for the large-scale MoE models. The proposed algorithm is based on the idea of adaptive expert activation (AEA) and token allocation (TA), which are two key components to optimize the inference speed of the large-scale MoE models. The AEA component dynamically adjusts the number of activated experts according to the input sequence, while the TA component optimizes the memory access pattern for the large-scale MoE models. To verify the effectiveness of the proposed algorithm, the authors conduct a series of experiments on the QWEN-1.5 and QWEN-2 models. The results show that the proposed AESMC algorithm can significantly improve the inference speed of the large-scale MoE models.

**Key Contributions/Findings**

The main contributions of this paper are threefold. First, the authors propose an AEA component to dynamically adjust the number of activated experts according to the input sequence. Second, they propose a TA component to optimize the memory access pattern for the large-scale MoE models. Third, the authors conduct experiments on the QWEN-1.5 and QWEN-2 models and show that the proposed AESMC algorithm can significantly improve the inference speed of the large-scale MoE models.

**Methodology/Approach**

The AEA component is based on the idea of adaptive computation time (ACT). The ACT is a technique to dynamically adjust the number of activated experts according to the input sequence. In this paper, the authors use the QWEN-1.5 and QWEN-2 models as examples for the large-scale MoE models. The AEA component can be used in conjunction with any MoE training method. The authors propose a TA component based on the idea of proactive caching (PC). The PC is an algorithm to proactively cache the frequently accessed data. In this paper, the authors use the QWEN-1.5 and QWEN-2 models as examples for the large-scale MoE models. The proposed AESMC algorithm can be used in conjunction with any MoE training method. The authors propose a TA component based on the idea of proactive caching (PC). The PC is an algorithm to proactively cache the frequently accessed data. In this paper, the authors use the QWEN-1.5 and QWEN-2 models as examples for the large-scale MoE models.

**Results/Data**

The results show that the proposed AESMC algorithm can significantly improve the inference speed of the large-scale MoE models. The authors conduct experiments on the QWEN-1.5 and QWEN-2 models and show that the proposed AESMC algorithm can significantly improve the inference speed of the large-scale MoE models.

**Limitations/Discussion**

The main limitation of this paper is that the authors only use two examples, i.e., the QWEN-1.5 and QWEN-2 models, to verify the effectiveness of the proposed AESMC algorithm. The results show that the proposed AESMC algorithm can significantly improve the inference speed of the large-scale MoE models.

**References**

[... truncated for summarization ...]

=== END PAPER CONTENT ===

Please let me know if you would like me to make any changes!

---

**Summary Statistics:**
- Input: 7,516 words (52,182 chars)
- Output: 531 words
- Compression: 0.07x
- Generation: 30.9s (17.2 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
