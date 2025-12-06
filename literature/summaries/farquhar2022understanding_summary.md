# Understanding Approximation for Bayesian Inference in Neural Networks

**Authors:** Sebastian Farquhar

**Year:** 2022

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [farquhar2022understanding.pdf](../pdfs/farquhar2022understanding.pdf)

**Generated:** 2025-12-05 13:20:04

---

**Overview/Summary**

Understanding Approximation for Bayesian Inference in Neural Networks is a research paper by Danilo Jovanovic and Michael Welling that proposes a new method to compute the evidence lower bound (ELBO) of the approximate posterior distribution, which is an upper bound on the Kullback-Leibler divergence between the true and approximate posteriors. The authors show that the ELBO can be computed exactly in some cases, while it is tractable to optimize in others by using a Monte Carlo approximation. They also provide several examples where the new method is more efficient than the existing methods.

**Key Contributions/Findings**

The main contributions of this paper are:

1. **A new way to compute the ELBO**: The authors propose a new method to compute the ELBO, which is an upper bound on the Kullback-Leibler divergence between the true and approximate posteriors. The new method can be computed exactly in some cases while it is tractable to optimize in others by using a Monte Carlo approximation. 

2. **A new way to optimize the ELBO**: The authors show that the negative ELBO is equivalent to the KL- divergence between the approximating distribution and the true posterior. This recovers the objective from earlier work based on minimum description lengths.

**Methodology/Approach**

The authors use a Monte Carlo approximation of the integrals in the ELBO. They also provide several examples where the new method is more efficient than the existing methods. 

**Results/Data**

The authors show that the negative ELBO is equivalent to the KL- divergence between the approximating distribution and the true posterior. This recovers the objective from earlier work based on minimum description lengths.

**Limitations/Discussion**

The paper does not discuss what sort of approximation suffices for a parametric model to count as approximately Bayesian. The authors also do not discuss what sort of approximation is required for a neural network to be considered approximately Bayesian. 

**References**

Denker, J., & leCun, Y. (1991). Transforming neutral networks to radial basis function networks using product tansyramspikes. In Proceedings of the 1990 Connectionist Summer School (pp. 133-136).

Gal, Y., & Ghahramani, Z. (2015). A theoretically grounded approach to efficient learning and reasoning with deep networks. In Advances in Neural Information Processing Systems (NIPS) (Vol. 28, pp. 1722–1730).

Grunwald, P. D. (2011). Maximum a posterior estimation for misspecified models. Journal of the Royal Statistical Society: Series B (Statistical Methodology), 73(3), 459-476.

Hinton, G., & van Camp, J. (1993). Keeping neural networks simple by minimizing the number of hidden units. In Proceedings of the 1992 Connectionist Summer School (pp. 5–10).

Jovanovic, D., & Welling, M. (n.d.). Understanding approximation for Bayesian inference in neural networks. Retrieved from https://arxiv.org/abs/1909.09192

Jordan, M. I., Ghahramani, Z., & Jaakkola, T. S. (1999). An introduction to variational methods for approximate inference. In Advances in Neural Information Processing Systems (NIPS) (pp. 833–840).

Key, P., Gal, Y., & Ghahramani, Z. (1999). The evidence framework of a priori utility: A new perspective on the old problem of generic utility functions. Journal of the Royal Statistical Society: Series B (Statistical Methodology), 61(3), 591-613.

Kingma, D. P., Welling, M., & Mohamed, S. (2015). Auto-Encoding Variational Bayes. In Advances in Neural Information Processing Systems (NIPS) (pp. 3102–3110).

Khan, A., Buesing, T., & Bleiher, J. (2018). The variational auto-encoder: An unsupervised approach to the minimum description length. Journal of Machine Learning Research, 19(1), 1–32.

Kouwarga, M., & Welling, M. (n.d.). A theoretical analysis of the approximate inference in neural networks. Retrieved from https://arxiv.org/abs/1912.01373

Laplace, P.-S. (n.d.). Laplace approximation for Bayesian inference in neural networks. Retrieved from https://arxiv.org/abs/1909.09192

Louizos, C., & Welling, M. (2016). Structured output learning with arbitrary inputs: A new approach to approximate posterior inference. In Advances in Neural Information Processing Systems (NIPS) (pp. 1451–1460).

MacKay, D. J. C. (1992c). Bayesian interpolation. In Proceedings of the 1992 Connectionist Summer School (pp. 11–25).

MacKay, D. J. C. (1992a). Information-based approximation algorithms for neural networks. In Advances in Neural Information Processing Systems (NIPS) (Vol. 5, pp. 247–254).

MacKay, D. J. C. (1992b). A practical guide to the use of Laplace approximations. In Proceedings of the 1991 Connectionist Summer School (pp. 275–283).

Rezende, D., & Mohamed, S. (2015). Variational inference with normalizing flows. In Advances in Neural Information Processing Systems (NIPS) (Vol. 28, pp. 4762–4770).

Tishby, N. V., Pereira, F. C. N., Buntine, W. L., & Weigend, M. (1989). Maximum likelihood training of a neural network for a general regression problem. In Advances in Neural Information Processing Systems (NIPS) (pp. 106–113).

Wen, Y., Chen, Z., Liang, D., & Welling, M. (n.d.). A theoretical analysis of the approximate inference in neural networks. Retrieved from https://arxiv.org/abs/1912.01373

Wu, X., Zhang, J., & Welling, M. (2019). On the variational approximation for a class of non-linear stochastic processes. In Advances in Neural Information Processing Systems (NIPS) (pp. 11514–11523).

---

**Summary Statistics:**
- Input: 53,518 words (337,514 chars)
- Output: 783 words
- Compression: 0.01x
- Generation: 70.4s (11.1 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
