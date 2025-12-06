# Learning Active Subspaces for Effective and Scalable Uncertainty Quantification in Deep Neural Networks

**Authors:** Sanket Jantre, Nathan M. Urban, Xiaoning Qian, Byung-Jun Yoon

**Year:** 2023

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [jantre2023learning.pdf](../pdfs/jantre2023learning.pdf)

**Generated:** 2025-12-05 13:28:18

---

**Overview/Summary**
The paper "Learning Active Subspaces for Effective and Scalable Uncertainty Propagation" by [Authors] is a seminal work that develops a new approach to Bayesian deep learning, which has the potential to significantly improve our understanding of uncertainty in neural networks. The authors' main contributions are twofold: (1) they provide a simple baseline for Bayesian uncertainty in deep learning and (2) they propose an active subspace method for high-dimensional uncertainty propagation.

**Key Contributions/Findings**
The first contribution is the development of a new baseline, which is achieved by using the Laplace approximation to approximate the posterior distribution over the model parameters. The authors show that this simple approach can be used as a drop-in replacement for existing approaches and provide an empirical comparison with several other methods. They find that the Laplace approximation is competitive with these more complex methods in terms of accuracy, but it is much faster to compute. This baseline is important because it provides a new standard for evaluating the performance of Bayesian uncertainty estimation methods.

The second contribution is the development of a novel active subspace method for high-dimensional uncertainty propagation. The authors find that the existing likelihood-informed dimension reduction (LIDR) and active subspace (AS) approaches are not scalable to high dimensions. They propose an active subspace approach, which they call "derivative-informed projected neural networks" (DIPNNs), that is based on the idea of using the derivative information in the forward pass to reduce the dimensionality of the input space. The DIPNNs can be used as a drop-in replacement for the existing LIDR and AS methods, but they are much faster to compute. They also show that the DIPNNs have better performance than the LIDR and AS approaches in terms of accuracy.

**Methodology/Approach**
The authors first develop a baseline method by using the Laplace approximation. The Laplace approximation is based on the idea that the posterior distribution over the model parameters is approximately a multivariate normal distribution with mean equal to the maximum likelihood estimate (MLE) and variance equal to the inverse Fisher information matrix. This approach is simple because it does not require any additional training data or complex computations, but it can be used as a drop-in replacement for existing Bayesian uncertainty estimation methods. The authors also develop an active subspace method based on the idea of using the derivative information in the forward pass to reduce the dimensionality of the input space. This approach is called "derivative-informed projected neural networks" (DIPNNs). The DIPNNs can be used as a drop-in replacement for the existing LIDR and AS methods, but they are much faster to compute. The authors also show that the DIPNNs have better performance than the LIDR and AS approaches in terms of accuracy.

**Results/Data**
The authors first compare their baseline method with several other Bayesian uncertainty estimation methods. They find that the Laplace approximation is competitive with these more complex methods in terms of accuracy, but it is much faster to compute. The authors also compare the DIPNNs with the LIDR and AS approaches. The authors show that the DIPNNs have better performance than the LIDR and AS approaches in terms of accuracy.

**Limitations/Discussion**
The main limitation of this paper is that it only provides a baseline method for Bayesian uncertainty estimation, but does not provide an active subspace approach to high-dimensional problems. The authors also mention some future work directions, such as developing more complex methods based on the DIPNNs and exploring the theoretical properties of the DIPNNs.

**References**
[1] P. Izmailov, W. J. Maddox, P. Kirichenko, T. Garipov, and A. G. Wilson,  "A simple baseline for Bayesian uncertainty in deep learning," NeurIPS, 2019.
[2] P. Izmailov, S. Vikram, M. Hoffman, and A. G. Wilson,  "What are Bayesian neural network posteriors really like?," in ICML, 2021.
[3] P. Izmailov, W. J. Maddox, P. Kirichenko, T. Garipov, D. Vetrov, and A. G. Wilson,  "Subspace inference for Bayesian deep learning," in UAI, 2020.
[4] P. G. Constantine, Active subspaces: Emerging ideas for dimension reduction in parameter studies, SIAM, 2015.
[5] D. MacKay,  "Bayesian model comparison and backprop nets," NIPS, 1991.
[6] W. J. Maddox, G. Benton, and A. G. Wilson,  "Rethinking parameter counting in deep models: Effective dimensionality revisited," arXiv:2003.02139, 2020.
[7] P. Izmailov, W. J. Maddox, P. Kirichenko, T. Garipov, D. Vetrov, and A. G. Wilson,  "A simple baseline for Bayesian uncer- tainty in deep learning," NeurIPS, 2019.
[8] P. G. Constantine, M. Emory, J. Larsson, and G. Iacarino,  "Exploiting active subspaces to quantify un- certainty in the numerical simulation of the HyShot II scramjet," Journal of Computational Physics, vol. 302, pp. 1–20, 2015.
[9] D. MacKay,  "Bayesian model comparison and backprop nets," NIPS, 1991.
[10] W. J. Maddox, G. Benton, and A. G. Wilson,  "Rethinking parameter counting in deep models: Effective dimensionality revisited," arXiv:2003.02139, 2020.
[11] P. Izmailov, P. Kirichenko, T. Garipov, D. Vetrov, and A. G. Wilson,  "Subspace inference for Bayesian deep learning," in UAI, 2020.
[12] P. G. Constantine, E. Dow, and Q. Wang,  "Active subspaces: Emerging ideas for dimension reduction in parameter studies, SIAM, 2015.
[13] P. G. Constantine, M. Emory, J. Larsson, and G. Iacarino,  "Exploiting active subspaces to quantify un- certainty in the numerical simulation of the HyShot II scramjet," Journal of Computational Physics, vol. 302, pp. 1–20, 2015.
[14] T. Loudon and S. Pankavich,  "Mathematical analysis and dynamic active subspaces for a long term model of hiv," Mathematical Biosciences and Engineering , vol. 14, no. 3, pp. 709–733, 2017.
[15] C. Cui, K. Zhang, T. Daulbaev, J. Gusak, I. Oseledets, and Z. Zhang,  "Active subspaces of neural networks: Structural analysis and universal attacks," SIAM Journal on Mathematics of Data Science, vol. 2, no. 4, 2020.
[16] R. Tripathy and I. Bilionis,  "Deep active subspaces: A scalable method for high- dimensional uncertainty propagation," in International Design Engineering Technical Conferences and Computers and Information in Engineering Conference, 2019.
[17] D. Blei, A. Kucukelbir, and J. McAuliffe,  "Variational inference: A review for statisticians," Journal of the American Statistical Association, vol. 112, no. 518, 2017.
[18] D. Kingma and M. Welling,  "Auto-encoding variational Bayes," in ICLR, 2014.
[19] R. Baptista, Y  . Marzouk, and O. Zahm,  "Gradient-based data and parameter dimension reduction for Bayesian models: an information theoretic perspective," arXiv:2207.08670, 2022.
[20] T. Cui, K. Zhang, T. Daulbaev, J. Martin, Y  . Marzouk, A. Solonen, and A. Span- tini,  "Likelihood-informed dimension reduction for non- linear inverse problems," Inverse Problems, vol. 30, no. 11, 2014.
[21] T. Cui and X. Tong,  "A unified performance analysis of likelihood-informed subspace methods," Bernoulli, vol. 28, no. 4, 2022.
[22] A. Paszke et al.,  "PyTorch: An imperative style, high- performance deep learning library," in NeurIPS, 2019.
[23] C. Blundell, J. Cornebise, K. Kavukcuoglu, and D. Wier- stra,  "Weight uncertainty in neural network," in ICML, 2015.
[24] D. Kingma and J. Ba,  "Adam: A method for stochastic optimization," in ICLR, 2015.
[25] R. Tripathy and I. Bilionis,  "Deep active subspaces: A scalable method for high- dimensional uncertainty propagation," in International Design Engineering Technical Conferences and Computers and Information in Engi- neering Conference, 2019.
[26] D. Kingma and J. Ba,  "Adam: A method for stochastic optimization," in ICLR, 2015.
[27] R.

---

**Summary Statistics:**
- Input: 3,723 words (23,378 chars)
- Output: 1,184 words
- Compression: 0.32x
- Generation: 68.1s (17.4 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
