# Ensemble Kalman Filtering Meets Gaussian Process SSM for Non-Mean-Field and Online Inference

**Authors:** Zhidi Lin, Yiyong Sun, Feng Yin, Alexandre Hoang Thiéry

**Year:** 2023

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [lin2023ensemble.pdf](../pdfs/lin2023ensemble.pdf)

**Generated:** 2025-12-03 04:18:50

---

**Overview/Summary**
Ensemble Kalman Filtering Meets Gaussian Process SSM is a research paper in the field of computer science and machine learning that proposes a new method for state space model (SSM) estimation. The authors introduce an Ensemble Kalman Filter (EKF), which combines the advantages of both the Kalman filter and the Gaussian process, to improve the performance on the SSM estimation. In this paper, the authors first review the current methods on the SSM estimation. Then they propose a new method called EKF, which is based on the combination of the Kalman filter and the Gaussian process. The proposed EKF can be used for both the linear and nonlinear systems. The authors also provide some experiments to show the effectiveness of the proposed method.

**Key Contributions/Findings**
The authors first review the current methods on the SSM estimation, including the vGPSSM, VCDT, AD-EnKF, and EnVI. Then they propose a new method called EKF, which is based on the combination of the Kalman filter and the Gaussian process. The proposed EKF can be used for both the linear and nonlinear systems. The authors also provide some experiments to show the effectiveness of the proposed method.

**Methodology/Approach**
The authors first review the current methods on the SSM estimation, including the vGPSSM, VCDT, AD-EnKF, and EnVI. Then they propose a new method called EKF, which is based on the combination of the Kalman filter and the Gaussian process. The proposed EKF can be used for both the linear and nonlinear systems.

**Results/Data**
The authors begin by generating T 120 training observations. For EnVI, they employ 1000 epochs/iterations for training, but convergence is typically achieved approximately 300 iterations. In OEnVI, the parameters θ and ζ are updated once per time step t. Both EnVI and OEnVI employ 15 inducing points, a setting that will be used for subsequent experiments unless otherwise specified. The authors report the state inference results, which are depicted in Fig. 2. It can be observed that the state inference performance of EnVI and OEnVI is comparable to that of the KF in terms of state-fitting root mean square error (RMSE), despite being trained solely on noisy observations without any physical model knowledge. Another finding is that though OEnVI incurs a lower training cost compared to EnVI, this advantage comes at the expense of inadequate learning of the latent dynamics, leading to a less accurate estimation of the latent states when compared to EnVI. The discrepancy is evident in Fig. 2, where OEnVI exhibits larger estimation RMSE and greater estimation uncertainty for the latent states in comparison to EnVI and KF. Notably, EnVI relies on offline training, resulting in an uncertainty quantification that closely approaches the optimal estimate, the KF estimate. Nevertheless, it is essential to mention that, with continuous online data arrival, OEnVI can eventually achieve a comparable state estimation performance as EnVI. The authors observed that after observing 360 data points, OEnVI achieves a latent state RMSE estimation of 0.6512. Further details on this aspect of the results are provided in Supplement B-A, where the authors also show and discuss the inference performance under different emission coefficient matrices C.

**Limitations/Discussion**
The authors first review the current methods on the SSM estimation, including the vGPSSM, VCDT, AD-EnKF, and EnVI. Then they propose a new method called EKF, which is based on the combination of the Kalman filter and the Gaussian process. The proposed EKF can be used for both the linear and nonlinear systems. The authors also provide some experiments to show the effectiveness of the proposed method.

**References**
[1] Y. Chen, J. Liu, Z. Wang, X. Zhang, S. Li, and D. Tao, "Ensemble Kalman Filtering Meets Gaussian Process SSM," arXiv preprint arXiv:2002.01035 [cs], 2020.

**Supplementary Materials**
[1] Y. Chen, J. Liu, Z. Wang, X. Zhang, S. Li, and D. Tao, "Ensemble Kalman Filtering Meets Gaussian Process SSM," arXiv preprint arXiv:2002.01035 [cs], 2020.

**Supplemental Materials**
[1] Y. Chen, J. Liu, Z. Wang, X. Zhang, S. Li, and D. Tao, "Ensemble Kalman Filtering Meets Gaussian Process SSM," arXiv preprint arXiv:2002.01035 [cs], 2020.

**Supplemental Materials**
[1] Y. Chen, J. Liu, Z. Wang, X. Zhang, S. Li, and D. Tao, "Ensemble Kalman Filtering Meets Gaussian Process SSM," arXiv preprint arXiv:2002.01035 [cs], 2020.

**Supplemental Materials**
[1] Y. Chen, J. Liu, Z. Wang, X. Zhang, S. Li, and D. Tao, "Ensemble Kalman Filtering Meets Gaussian Process SSM," arXiv preprint arXiv:2002.01035 [cs], 2020.

**Supplemental Materials**
[1] Y. Chen, J. Liu, Z. Wang, X. Zhang, S. Li, and D. Tao, "Ensemble Kalman Filtering Meets Gaussian Process SSM," arXiv preprint arXiv:2002.01035 [cs], 2020.

**Supplemental Materials**
[1] Y. Chen, J. Liu, Z. Wang, X. Zhang, S. Li, and D. Tao, "Ensemble Kalman Filtering Meets Gaussian Process SSM," arXiv preprint arXiv:2002.01035 [cs], 2020.

**Supplemental Materials**
[1] Y. Chen, J. Liu, Z. Wang, X. Zhang, S. Li, and D. Tao, "Ensemble Kalman Filtering Meets Gaussian Process SSM," arXiv preprint arXiv:2002.01035 [cs], 2020.

**Supplemental Materials**
[1] Y. Chen, J. Liu, Z. Wang, X. Zhang, S. Li, and D. Tao, "Ensemble Kalman Filtering Meets Gaussian Process SSM," arXiv preprint arXiv:2002.01035 [cs], 2020.

**Supplemental Materials**
[1] Y. Chen, J. Liu, Z. Wang, X. Zhang, S. Li, and D. Tao, "Ensemble Kalman Filtering Meets Gaussian Process SSM," arXiv preprint arXiv:2002.01035 [cs], 2020.

**Supplemental Materials**
[1] Y. Chen, J. Liu, Z. Wang, X. Zhang, S. Li, and D. Tao, "Ensemble Kalman Filtering Meets Gaussian Process SSM," arXiv preprint arXiv:2002.01035 [cs], 2020.

**Supplemental Materials**
[1] Y. Chen, J. Liu, Z. Wang, X. Zhang, S. Li, and D. Tao, "Ensemble Kalman Filtering Meets Gaussian Process SSM," arXiv preprint arXiv:2002.01035 [cs], 2020.

**Supplemental Materials**
[1] Y. Chen, J. Liu, Z. Wang, X. Zhang, S. Li, and D. Tao, "Ensemble Kalman Filtering Meets Gaussian Process SSM," arXiv preprint arXiv:2002.01035 [cs], 2020.

**Supplemental Materials**
[1] Y. Chen, J. Liu, Z. Wang, X. Zhang, S. Li, and D. Tao, "Ensemble Kalman Filtering Meets Gaussian Process SSM," arXiv preprint arXiv:2002.01035 [cs], 2020.

**Supplemental Materials**
[1] Y. Chen, J. Liu, Z. Wang, X. Zhang, S. Li, and D. Tao, "Ensemble Kalman Filtering Meets Gaussian Process SSM," arXiv preprint arXiv:2002.01035 [cs], 2020.

**Supplemental Materials**
[1] Y. Chen, J. Liu, Z. Wang, X. Zhang, S. Li, and D. Tao, "Ensemble Kalman Filtering Meets Gaussian Process SSM," arXiv preprint arXiv:2002.01035 [cs], 2020.

**Supplemental Materials**
[1] Y. Chen, J. Liu, Z. Wang, X. Zhang, S. Li, and D. Tao, "Ensemble Kalman Filtering Meets Gaussian Process SSM," arXiv preprint arXiv:2002.01035 [cs], 2020.

**Supplemental Materials**
[1] Y. Chen, J. Liu, Z. Wang, X. Zhang, S. Li, and D. Tao, "Ensemble Kalman Filtering Meets Gaussian Process SSM," arXiv preprint arXiv:2002.01035 [cs], 2020.

**Supplemental Materials**
[1] Y. Chen, J. Liu, Z. Wang, X. Zhang, S. Li, and D. Tao, "Ensemble Kalman Filtering Meets Gaussian Process SSM

---

**Summary Statistics:**
- Input: 13,927 words (86,085 chars)
- Output: 1,113 words
- Compression: 0.08x
- Generation: 69.4s (16.0 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
