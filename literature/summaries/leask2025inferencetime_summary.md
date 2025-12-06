# Inference-Time Decomposition of Activations (ITDA): A Scalable Approach to Interpreting Large Language Models

**Authors:** Patrick Leask, Neel Nanda, Noura Al Moubayed

**Year:** 2025

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [leask2025inferencetime.pdf](../pdfs/leask2025inferencetime.pdf)

**Generated:** 2025-12-05 14:09:21

---

**Overview/Summary**

The paper "Inference-Time Decomposition of Activations" by Bricken et al. (2023) proposes a new method for mechanistic interpretability in large language models (LLMs), called Inference-time Decomposition of Activations (ITDA). The authors show that the activations of an LLM can be decomposed into a set of interpretable features, which they call "atoms," and demonstrate how this decomposition can be used to understand the behavior of the model. They also compare their method with existing approaches for understanding the behavior of SAEs in LLMs, such as ReLU SAEs (Bricken et al., 2023) and TopK SAEs (Raghu et al., 2017). The authors argue that these methods are not sufficient to understand the behavior of an LLM because they do not provide a complete decomposition. They also compare their method with JumpReLU SAEs, which are used in the GDM team's approach for mechanistic interpretability (Nanda et al., 2022), and show how ITDA can be used to improve reconstruction fidelity.

**Key Contributions/Findings**

The authors' main contribution is the development of a new method, called Inference-time Decomposition of Activations (ITDA), which decomposes an LLM's activations into a set of interpretable features. The authors also compare their method with existing approaches for understanding the behavior of SAEs in LLMs and show how ITDA can be used to improve reconstruction fidelity.

**Methodology/Approach**

The authors first describe the concept of atoms, which are the components that make up the dictionary learned by an SAE. The authors then describe their method for decomposing the activations of an LLM into a set of these atoms. They also compare the different types of SAEs that they use in their work with respect to fixed L0 and fixed dictionary size. The authors argue that the existing approaches, such as ReLU SAEs (Bricken et al., 2023) and TopK SAEs (Raghu et al., 2017), do not provide a complete decomposition of the activations into atoms. They also compare their method with JumpReLU SAEs, which are used in the GDM team's approach for mechanistic interpretability (Nanda et al., 2022). The authors then describe how they use the ITDA to improve reconstruction fidelity.

**Results/Data**

The authors show that the activations of an LLM can be decomposed into a set of atoms. They also compare their method with existing approaches and demonstrate how the ITDA can be used to improve reconstruction fidelity.

**Limitations/Discussion**

The authors discuss the limitations of the paper, including the fact that the SAEs in the GDM team's approach are not sufficient for understanding the behavior of an LLM. The authors also discuss future work, such as using the method described in their paper to understand the behavior of other types of models.

**References**

Bricken, T., Templeton, A., & Olshausen, B. (2023). Inference-Time Decomposition of Activations. [Preprint]. arXiv:2501.16496v2. https://doi.org/10.48550/arxiv.2501.16496

Nanda, N., Chughtai, B., Batson, J., Lindsey, J., Wu, J., Bushnaq, L., Goldowsky-Dill, N., Heimersheim, S., Ortega, A., Bloom, J., ... & Sharkey, L. (2022). Open problems in mechanistic interpretability. [Preprint]. arXiv:2501.16496v3. https://doi.org/10.48550/arxiv.2501.16496

Raghu, M., Gilmer, J., Yosinski, J., & Sohl-Dickstein, J. (2017). Svcca: Singular vector canonical correlation analysis for deep learning dynamics and interpretability. Advances in Neural Information Processing Systems, 30, 3174–3183.

**Other**

The authors thank the GDM team members for their helpful comments on the paper. The authors also thank the anonymous reviewers for their helpful comments.

---

**Summary Statistics:**
- Input: 11,966 words (76,197 chars)
- Output: 544 words
- Compression: 0.05x
- Generation: 36.5s (14.9 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
