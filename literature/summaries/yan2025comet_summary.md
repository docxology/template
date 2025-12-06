# Comet: Accelerating Private Inference for Large Language Model by Predicting Activation Sparsity

**Authors:** Guang Yan, Yuhui Zhang, Zimu Guo, Lutan Zhao, Xiaojun Chen, Chen Wang, Wenhao Wang, Dan Meng, Rui Hou

**Year:** 2025

**Source:** arxiv

**Venue:** N/A

**DOI:** 10.1109/SP61157.2025.00182

**PDF:** [yan2025comet.pdf](../pdfs/yan2025comet.pdf)

**Generated:** 2025-12-05 12:56:40

---

**Overview/Summary**

The paper introduces Comet, a novel private inference system for large language models (LLMs) that accelerates end-to-end performance of existing MPC-based systems by 2-5x and reduces the communication cost by 4-6x. The authors propose three key contributions: an activation sparsity predictor to reduce the number of linear layers in the model, a novel oblivious shuffle protocol for private data shuffling, and a new SIMM protocol that accelerates the computation of the non-linear layer. Comet is designed as a drop-in replacement for existing MPC-based LLM inference systems without modifying the underlying model architecture.

**Key Contributions/Findings**

The first contribution is an activation sparsity predictor that can predict whether a linear layer will be activated or not, based on which a subset of the input data will be sent to the server. The authors use a simple yet effective approach by using the output of the previous layer as the input for the current layer's activation sparsity prediction. This is because the activation of the current layer can only depend on the output of the previous layer, and the output of the previous layer is the input of the current layer. Therefore, the authors can predict the activation of the current layer based on the output of the previous layer. The second contribution is an oblivious shuffle protocol that can be used for both linear and non-linear layers. In the oblivious shuffle protocol, the server first receives a token vector from the user, then it shuffles the input data according to the token vector. The authors use the same token vector for all the input data in the current inference task, which is different from the existing protocols that generate a new random token for each input data. This can reduce the communication cost by 2-3x. In addition, the server only needs to receive one token vector per inference task, and it does not need to shuffle the data for the same token in different inference tasks. The third contribution is a novel SIMM protocol that accelerates the computation of the non-linear layer. The authors use a new oblivious shuffle protocol for the input data and a novel SIMM protocol for the output data. In the new SIMM protocol, the server first receives an output token vector from the user, then it shuffles the output data according to the output token vector. This is different from the existing protocols that generate a random token for each output data. The authors use the same output token vector for all the output data in the current inference task, which can also reduce the communication cost by 2-3x. In addition, the server only needs to receive one output token vector per inference task and it does not need to shuffle the data for the same token in different inference tasks.

**Methodology/Approach**

The paper first proposes an activation sparsity predictor that can predict whether a linear layer will be activated or not. The authors use a simple yet effective approach by using the output of the previous layer as the input for the current layer's activation sparsity prediction. This is because the activation of the current layer can only depend on the output of the previous layer, and the output of the previous layer is the input of the current layer. Therefore, the authors can predict the activation of the current layer based on the output of the previous layer. The second contribution is an oblivious shuffle protocol that can be used for both linear and non-linear layers. In the oblivious shuffle protocol, the server first receives a token vector from the user, then it shuffles the input data according to the token vector. The authors use the same token vector for all the input data in the current inference task, which is different from the existing protocols that generate a new random token for each input data. This can reduce the communication cost by 2-3x. In addition, the server only needs to receive one token vector per inference task and it does not need to shuffle the data for the same token in different inference tasks. The third contribution is a novel SIMM protocol that accelerates the computation of the non-linear layer. The authors use a new oblivious shuffle protocol for the input data and a new SIMM protocol for the output data. In the new SIMM protocol, the server first receives an output token vector from the user, then it shuffles the output data according to the output token vector. This is different from the existing protocols that generate a random token for each output data. The authors use the same output token vector for all the output data in the current inference task, which can also reduce the communication cost by 2-3x. In addition, the server only needs to receive one output token vector per inference task and it does not need to shuffle the data for the same token in different inference tasks.

**Results/Data**

The authors evaluate the end-to-end performance of Comet on three cloud servers with two servers for MPC computation node and one for user node. Each server is equipped with an Intel 8458P@2.7GHz CPU, an NVIDIA A100 GPU, and 256GB of memory. The bandwidth between the servers is 5Gbps. The authors select five mainstream Transformer private inference systems as baselines for comparison with Comet. Two systems, Iron [35] and Bolt [68], use hybrid protocols that combine homomorphic encryption (HE) for linear layers and MPC for non-linear layers. Since HE is slower than MPC, the authors ensure a fair comparison by using their non- linear layer implementations, while keeping the linear layer implementation consistent with Comet. The other three baselines, MPCFormer [47], SecFormer [59], and Puma [30], rely solely on MPC. The authors provide detailed descriptions of the baselines in Appendix D.

**Limitations/Discussion**

The paper does not discuss any limitations or future work.

---

**Summary Statistics:**
- Input: 15,767 words (98,871 chars)
- Output: 973 words
- Compression: 0.06x
- Generation: 43.1s (22.6 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
