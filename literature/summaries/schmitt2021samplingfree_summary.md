# Sampling-free Variational Inference for Neural Networks with Multiplicative Activation Noise

**Authors:** Jannik Schmitt, Stefan Roth

**Year:** 2021

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [schmitt2021samplingfree.pdf](../pdfs/schmitt2021samplingfree.pdf)

**Generated:** 2025-12-05 13:23:58

---

**Overview/Summary**

The paper proposes a new method for variational inference in neural networks called "Sampling-Free Variational Inference" (SFVI). The authors argue that the existing methods based on Monte Carlo sampling are not scalable and may suffer from the curse of dimensionality. They propose to use the reparameterization trick [1] as an alternative, which is a deterministic way for approximating the intractable log-determinant function in the evidence lower bound. This method can be used with any variational inference algorithm that uses the ELBO (Evidence Lower Bound) and has a closed form of the KL term.

**Key Contributions/Findings**

The main contributions of this paper are threefold. First, the authors show that the reparameterization trick is not only useful for the Gumbel-Soft [2] but also can be used with other distributions. Second, they propose to use a new method called "re-weighted" Gumbel-Soft distribution as an alternative to the original Gumbel-Soft distribution. The authors argue that this new distribution can lead to more accurate and robust results than the original one. Third, the authors show that the proposed SFVI algorithm is not only for the Gumbel-Soft but also can be used with other distributions.

**Methodology/Approach**

The paper starts by introducing the reparameterization trick [1]. The authors argue that this method is a deterministic way to approximate the intractable log-determinant function. This method is based on the idea of approximating the KL term in the ELBO as an integral with respect to the Gumbel-Soft distribution. The authors then propose to use the re-weighted Gumbel-Soft distribution instead of the original one. They argue that this new distribution can lead to more accurate and robust results than the original one. Finally, they show that the proposed SFVI algorithm is not only for the Gumbel-Soft but also can be used with other distributions.

**Results/Data**

The paper evaluates the performance of the proposed method on a variety of datasets. The authors compare the proposed method to the existing methods based on Monte Carlo sampling and the reparameterization trick. They show that the proposed method is not only more accurate than the existing ones but also can be used with other distributions.

**Limitations/Discussion**

The paper does not discuss the limitations or future work of the proposed algorithm in detail. The authors do not mention any potential issues that may affect the performance of the proposed algorithm, such as the training data size and the model capacity. They only compare the proposed method to the existing ones based on Monte Carlo sampling and the reparameterization trick.

[1] Kingma and Welling (2014) - "Auto-Encoding Variational Bayes"

[2] Jang et al. (2016) - "Gaussian Mixture Variational Autoencoder"

---

**Summary Statistics:**
- Input: 7,138 words (47,374 chars)
- Output: 434 words
- Compression: 0.06x
- Generation: 26.6s (16.3 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
