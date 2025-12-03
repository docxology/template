# R-Sparse: Rank-Aware Activation Sparsity for Efficient LLM Inference

**Authors:** Zhenyu Zhang, Zechun Liu, Yuandong Tian, Harshit Khaitan, Zhangyang Wang, Steven Li

**Year:** 2025

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [zhang2025rsparse.pdf](../pdfs/zhang2025rsparse.pdf)

**Generated:** 2025-12-03 06:25:45

---

**Overview/Summary**
The paper "R-Sparse: Rank-Aware Activation Sparsity" presents a new approach for improving the efficiency of pre-trained large language models (LLMs) during generation. The authors introduce R-Sparse, an efficient and adaptive method that can be used with any LLMs to reduce their computational cost while preserving their performance. In this paper, they first analyze the importance of each input channel in a given prompt for the task of text generation. They then propose a new rank-aware activation sparsity (RAS) training strategy based on the analysis and apply it to the GRIFFIN model, which is a state-of-the-art method for generating text from a given prompt while controlling the number of generated tokens. The R-Sparse approach improves the efficiency of GRIFFIN by 2-3x with minimal loss in performance.

**Key Contributions/Findings**
The authors first analyze the importance of each input channel and singular value across different numbers of training samples. They find that the importance patterns are remarkably similar across different datasets, which demonstrates the generalization capability of the R-Sparse approach. The analysis also shows that the importance of each input channel is highly correlated with its corresponding singular value. The authors then apply two strategies to scale up the model-level sparsity ratios: (i)MLP, where they directly increase the sparsity ratios within the MLP blocks and report the resulting model-level sparsity; and (ii) All, where they extend the strategy to include attention blocks. In this case, they use the same metrics to identify important channels based on the activations during the prefilling stage and determine the corresponding active channels during the decoding stage. The results are presented in Figure 7 where the MLP strategy is significantly better than the All. Thus in the main context, the authors report the results of MLP strategy for GRIFFIN.

**Methodology/Approach**
The R-Sparse approach can be applied to any LLMs and does not require any additional training. The authors first analyze the importance of each input channel based on the activations during the prefilling stage. They then apply two strategies to scale up the model-level sparsity ratios: (i)MLP, where they directly increase the sparsity ratios within the MLP blocks and report the resulting model-level sparsity; and (ii) All, where they extend the strategy to include attention blocks. In this case, they use the same metrics to identify important channels based on the activations during the prefilling stage and determine the corresponding active channels during the decoding stage. The results are presented in Figure 7 where the MLP strategy is significantly better than the All. Thus in the main context, the authors report the results of MLP strategy for GRIFFIN.

**Results/Data**
The R-Sparse approach can be applied to any LLMs and does not require any additional training. The authors first analyze the importance of each input channel based on the activations during the prefilling stage. They then apply two strategies to scale up the model-level sparsity ratios: (i)MLP, where they directly increase the sparsity ratios within the MLP blocks and report the resulting model-level sparsity; and (ii) All, where they extend the strategy to include attention blocks. In this case, they use the same metrics to identify important channels based on the activations during the prefilling stage and determine the corresponding active channels during the decoding stage. The results are presented in Figure 7 where the MLP strategy is significantly better than the All. Thus in the main context, the authors report the results of MLP strategy for GRIFFIN.

**Limitations/Discussion**
The paper does not discuss any limitations or future work.

---

**Summary Statistics:**
- Input: 7,598 words (50,162 chars)
- Output: 581 words
- Compression: 0.08x
- Generation: 33.8s (17.2 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
