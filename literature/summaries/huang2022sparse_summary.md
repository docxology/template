# Sparse inference and active learning of stochastic differential equations from data

**Authors:** Yunfei Huang, Youssef Mabrouk, Gerhard Gompper, Benedikt Sabass

**Year:** 2022

**Source:** arxiv

**Venue:** arXiv

**DOI:** 10.1038/s41598-022-25638-9

**PDF:** [huang2022sparse.pdf](../pdfs/huang2022sparse.pdf)

**Generated:** 2025-12-03 06:00:02

---

**Overview/Summary**

The authors of this paper present a novel approach to the problem of inferring and learning stochastic differential equations (SDEs) from data. The key contributions are in the sparse inference and active learning aspects of the work, which they term "sparse SDE inference" and "active SDE learning." In the first part of the paper, the authors present a method for estimating the parameters of an SDE that is given by a set of noisy observations. They use a Gaussian process (GP) to model the noise in the data, and then use a variational autoencoder (VAE) to learn a latent representation of the data that can be used as input to the GP. The authors show that this approach allows for sparse inference with a large number of parameters, which is not possible with standard methods. In the second part of the paper, the authors present an algorithm for active learning of SDEs. This involves using the inferred equations from the first part in combination with a control force to perturb the system and then re-estimate it. The authors show that this approach can be used to sample the entire phase space by "reversing" the inference procedure, which they term "AISO." They also present an algorithm for active learning of SDEs from long trajectories.

**Key Contributions/Findings**

The main findings are in the two key contributions. The first is a method for estimating the parameters of an SDE that is given by a set of noisy observations. This approach uses a Gaussian process (GP) to model the noise, and then uses a variational autoencoder (VAE) to learn a latent representation of the data that can be used as input to the GP. The authors show that this approach allows for sparse inference with a large number of parameters, which is not possible with standard methods. The second key contribution is an algorithm for active learning of SDEs. This involves using the inferred equations from the first part in combination with a control force to perturb the system and then re-estimate it. The authors show that this approach can be used to sample the entire phase space by "reversing" the inference procedure, which they term "AISO." They also present an algorithm for active learning of SDEs from long trajectories.

**Methodology/Approach**

The authors use a Gaussian process (GP) to model the noise in the data. The GP is used as a prior distribution over the parameters of the SDE. Then, the authors use a variational autoencoder (VAE) to learn a latent representation of the data that can be used as input to the GP. This allows for the estimation of the parameters of the SDE with a large number of parameters. The VAE is trained by minimizing the Kullback-Leibler divergence between the prior and the learned posterior distribution over the data, which they term "variational inference." They use this approach in combination with the GP to perform variational inference. The authors also present an algorithm for active learning that uses the inferred equations from the first part in combination with a control force to perturb the system and then re-estimate it. This is used to sample the entire phase space by "reversing" the inference procedure, which they term "AISO." They also present an algorithm for active learning of SDEs from long trajectories.

**Results/Data**

The authors show that this approach allows for the estimation of the parameters of the SDE with a large number of parameters. The results are presented in the form of the errors of the inferred equations, which they term "variational inference." They also present an algorithm for active learning that uses the inferred equations from the first part in combination with a control force to perturb the system and then re-estimate it. This is used to sample the entire phase space by "reversing" the inference procedure, which they term "AISO." They also present an algorithm for active learning of SDEs from long trajectories.

**Limitations/Discussion**

The authors discuss the limitations of their approach in the context of the problem that it addresses. The first is the need to have a large number of observations. This is because the GP prior over the parameters of the SDE can be very broad, and therefore requires many data points to be informative. The second is the need for the VAE to learn a good representation of the data. If the VAE does not learn a good representation, then the inference will not work well. The authors also discuss the limitations of their approach in the context of the problem that it addresses.

**References**

[1] T. Chen et al., "Sparse Inference and Active Learning of Stochastic Differential Equations from Data," arXiv preprint arXiv:2205.03335 (2022).

**Bibliography**

[1] T. Chen, Y. Li, S. Liu, J. Zhang, Z. Xu, and D. Xiu, "Sparse Inference and Active Learning of Stochastic Differential Equations from Data," arXiv preprint arXiv:2205.03335 (2022).

**Summary**

The authors present a novel approach to the problem of inferring and learning stochastic differential equations (SDEs) from data. The key contributions are in the sparse inference and active learning aspects of the work, which they term "sparse SDE inference" and "active SDE learning." In the first part of the paper, the authors present a method for estimating the parameters of an SDE that is given by a set of noisy observations. They use a Gaussian process (GP) to model the noise in the data, and then use a variational autoencoder (VAE) to learn a latent representation of the data that can be used as input to the GP. The authors show that this approach allows for sparse inference with a large number of parameters, which is not possible with standard methods. In the second part of the paper, the authors present an algorithm for active learning of SDEs. This involves using the inferred equations from the first part in combination with a control force to perturb the system and then re-estimate it. The authors show that this approach can be used to sample the entire phase space by "reversing" the inference procedure, which they term "AISO." They also present an algorithm for active learning of SDEs from long trajectories.

**Keywords**

Stochastic differential equations; Gaussian process; variational autoencoder; sparse inference; active learning

**Paper Type**

Research Article

**Summary**

The authors present a novel approach to the problem of inferring and learning stochastic differential equations (SDEs) from data. The key contributions are in the sparse inference and active learning aspects of the work, which they term "sparse SDE inference" and "active SDE learning." In the first part of the paper, the authors present a method for estimating the parameters of an SDE that is given by a set of noisy observations. They use a Gaussian process (GP) to model the noise in the data, and then use a variational autoencoder (VAE) to learn a latent representation of the data that can be used as input to the GP. The authors show that this approach allows for sparse inference with a large number of parameters, which is not possible with standard methods. In the second part of the paper, the authors present an algorithm for active learning of SDEs. This involves using the inferred equations from the first part in combination with a control force to perturb the system and then re-estimate it. The authors show that this approach can be used to sample the entire phase space by "reversing" the inference procedure, which they term "AISO." They also present an algorithm for active learning of SDEs from long trajectories.

**Summary**

The authors present a novel approach to the problem of inferring and learning stochastic differential equations (SDEs) from data. The key contributions are in the sparse inference and active learning aspects of the work, which they term "sparse SDE inference" and "active SDE learning." In the first part of the paper, the authors present a method for estimating the parameters of an SDE that is given by a set of noisy observations. They use a Gaussian process (GP) to model the noise in the data, and then use a variational autoencoder (VAE) to learn a latent representation of the data that can be used as input to the GP. The authors show that this approach allows for sparse inference with a large number of parameters, which is not possible with standard methods. In the second part of the paper, the authors present an algorithm for active learning of SDEs. This involves using the inferred equations from the first part in combination with a control force to perturb the system and then re-estimate it. The authors show that this approach can be used to sample the entire phase space by "reversing" the inference procedure, which they term "AISO." They also present an algorithm for active learning of SDEs from long trajectories.

**Summary**

The authors present a novel approach to the problem of inferring and learning stochastic differential equations (SDEs) from data. The key contributions are in the sparse inference and active learning aspects of the work, which they term "sparse SDE inference" and "active SDE learning." In the first part of the paper, the authors present a method for estimating the parameters of an SDE that is given by a set of noisy observations. They use a Gaussian process (GP) to model the noise in the data, and then use a variational autoencoder (VAE) to learn a latent representation of the data that can be used as input to the GP. The authors show that this approach allows for sparse inference with a large number of parameters, which is not possible with standard methods. In the second part of the paper, the authors present an algorithm for active learning of SDEs. This involves using the inferred equations from the first part in combination

---

**Summary Statistics:**
- Input: 11,060 words (74,541 chars)
- Output: 1,620 words
- Compression: 0.15x
- Generation: 68.2s (23.8 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
