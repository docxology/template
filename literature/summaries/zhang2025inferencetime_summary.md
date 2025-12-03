# Inference-time Scaling of Diffusion Models through Classical Search

**Authors:** Xiangcheng Zhang, Haowei Lin, Haotian Ye, James Zou, Jianzhu Ma, Yitao Liang, Yilun Du

**Year:** 2025

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [zhang2025inferencetime.pdf](../pdfs/zhang2025inferencetime.pdf)

**Generated:** 2025-12-03 04:15:14

---

**Overview/Summary**

The paper "A General Framework for Inference-Time Scaling and Steering of Diffusion Models" by Raghav Singhal et al. (2025) presents a novel framework that enables inference-time scaling and steering of diffusion models, which are generative models that have been widely used in various applications such as image synthesis, text-to-image generation, and data augmentation. The authors propose a unified approach for the inference-time scaling problem, which is to find an optimal function $f$ that maps the input parameters $\boldsymbol{\theta}$ of the diffusion model to the number of steps $t$ required to produce a sample from the target distribution. They also provide a general framework that allows the user to steer the output of the diffusion model by optimizing the objective function with respect to the inference-time scaling function $f$. The proposed approach is based on the understanding that the inference-time scaling problem can be viewed as an optimization problem in the space of measures, and the original formulation of the problem is a special case of this general framework. The authors show that the optimal $f$ for the inference-time scaling problem is the one that minimizes the Kullback-Leibler (KL) divergence between the target distribution and the output distribution of the diffusion model. They also provide several ways to optimize the objective function, including gradient-based optimization and score- or loss-guided methods. The authors demonstrate the effectiveness of their approach by comparing it with a number of existing approaches on various datasets.

**Key Contributions/Findings**

The main contributions of the paper are:

1. **Unified framework**: The authors propose a unified framework for the inference-time scaling problem, which is to find an optimal function $f$ that maps the input parameters $\boldsymbol{\theta}$ of the diffusion model to the number of steps $t$ required to produce a sample from the target distribution. This general formulation can be applied to various existing approaches and also leads to a new approach for inference-time scaling.
2. **Optimal $f$**: The authors show that the optimal $f$ is the one that minimizes the Kullback-Leibler (KL) divergence between the target distribution and the output distribution of the diffusion model. This result provides a theoretical foundation for the inference-time scaling problem, which can be used to guide the design of new approaches.
3. **General framework**: The authors also provide a general formulation that allows the user to steer the output of the diffusion model by optimizing the objective function with respect to the inference-time scaling function $f$. This general framework is based on the understanding that the inference-time scaling problem can be viewed as an optimization problem in the space of measures, and the original formulation of the problem is a special case of this general framework. The authors show that the optimal $f$ for the inference-time scaling problem is the one that minimizes the Kullback-Leibler (KL) divergence between the target distribution and the output distribution of the diffusion model.
4. **Optimization methods**: The authors provide several ways to optimize the objective function, including gradient-based optimization and score- or loss-guided methods.

**Methodology/Approach**

The inference-time scaling problem is the following: Given a set of input parameters $\boldsymbol{\theta}$ for the diffusion model, find an optimal function $f$ that maps the input $\boldsymbol{\theta}$ to the number of steps $t$, and the output distribution of the diffusion model with the input $\boldsymbol{\theta}$ is $p_t$. The authors show that the original formulation of the problem can be viewed as a special case of this general framework. In the general framework, the objective function is $L(f)$, which is the KL divergence between the target distribution and the output distribution of the diffusion model with the input $f(\boldsymbol{\theta})$. The authors also provide several ways to optimize the objective function, including gradient-based optimization and score- or loss-guided methods. The authors use the example of training-free inference-time scaling as an illustration for the general framework.

**Results/Data**

The paper does not report any new results. Instead, it provides a theoretical analysis that can be used to guide the design of new approaches for the inference-time scaling problem and also compares several existing approaches with their proposed approach on various datasets.

**Limitations/Discussion**

The authors do not mention any limitations or future work in the paper.

---

**Summary Statistics:**
- Input: 14,629 words (95,714 chars)
- Output: 691 words
- Compression: 0.05x
- Generation: 36.2s (19.1 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
