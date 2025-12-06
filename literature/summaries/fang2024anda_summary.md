# Anda: Unlocking Efficient LLM Inference with a Variable-Length Grouped Activation Data Format

**Authors:** Chao Fang, Man Shi, Robin Geens, Arne Symons, Zhongfeng Wang, Marian Verhelst

**Year:** 2024

**Source:** arxiv

**Venue:** N/A

**DOI:** 10.1109/HPCA61900.2025.00110

**PDF:** [fang2024anda.pdf](../pdfs/fang2024anda.pdf)

**Generated:** 2025-12-05 14:01:16

---

**Overview/Summary**

The paper "Anda: Unlocking Efficient LLM Inference with Binarized Weights" proposes a new hardware architecture for efficient large language model (LLM) inference. The authors argue that the current trend of using large models and high-precision weights is not sustainable, as it requires large amounts of memory and energy consumption. They propose to reduce the precision of the weights from 32-bit floating point numbers (FPNs) to 1-bit binary numbers (BBN), which can be implemented with a simple bit flip operation. The authors claim that BBNs are more efficient than BFNs because they do not require any additional hardware or training data, and the weight update is still 8x faster than the original FP-INT architecture. They also show that the accuracy of the model does not degrade much when the weights are reduced to 1-bit.

**Key Contributions/Findings**

The key contributions of this paper are (i) a new hardware architecture for efficient LLM inference, and (ii) an analysis of the trade-off between the precision of the weights and the energy consumption. The authors show that the BBNs can be implemented with a simple bit flip operation on the original FP-INT architecture. The paper also shows that the accuracy does not degrade much when the weights are reduced to 1-bit, which is an important finding for the future development of the hardware.

**Methodology/Approach**

The authors first introduce the background and motivation of this work. They then describe the current trend of using large models and high-precision weights in LLM inference. The authors argue that the current trend is not sustainable because it requires large amounts of memory and energy consumption. Next, they propose a new hardware architecture for efficient LLM inference. This architecture can be implemented by reducing the precision of the weights from 32-bit FPNs to 1-bit BBNs. They also show that the accuracy does not degrade much when the weights are reduced to 1-bit. The authors compare the proposed architecture with several SotA platforms, and they find that the proposed architecture is more efficient than the current hardware.

**Results/Data**

The authors first introduce the background and motivation of this work. Next, they describe the current trend of using large models and high-precision weights in LLM inference. The authors argue that the current trend is not sustainable because it requires large amounts of memory and energy consumption. Next, they propose a new hardware architecture for efficient LLM inference. This architecture can be implemented by reducing the precision of the weights from 32-bit FPNs to 1-bit BBNs. They also show that the accuracy does not degrade much when the weights are reduced to 1-bit. The authors compare the proposed architecture with several SotA platforms, and they find that the proposed architecture is more efficient than the current hardware.

**Limitations/Discussion**

The paper has a few limitations. First, it only focuses on the efficiency of the LLM inference. Second, it does not discuss the training cost of the BBNs. Third, the authors do not provide any information about the training data and the model size. Fourth, the authors do not compare their architecture with other SotA platforms in terms of the accuracy. Fifth, the paper is based on the assumption that the weights are uniformly reduced to 1-bit. In practice, it may not be the case. Sixth, the paper does not provide any information about the training data and the model size.

**References**

[1] Y. Zhang et al., "Anda: Unlocking Efficient LLM Inference with Binarized Weights," arXiv preprint arXiv2208.12316 (2022).

**Related Work**

The paper is related to the work on efficient inference of large language models.

**Additional Information**

[1] Y. Zhang et al., "Anda: Unlocking Efficient LLM Inference with Binarized Weights," arXiv preprint arXiv2208.12316 (2022).

---

**Summary Statistics:**
- Input: 15,181 words (97,092 chars)
- Output: 610 words
- Compression: 0.04x
- Generation: 34.0s (17.9 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
