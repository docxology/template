# Multigrid methods for total variation

**Authors:** Felipe Guerra, Tuomo Valkonen

**Year:** 2025

**Source:** arxiv

**Venue:** arXiv

**DOI:** 10.1007/978-3-031-92369-2_1

**PDF:** [guerra2025multigrid.pdf](../pdfs/guerra2025multigrid.pdf)

**Generated:** 2025-12-02 08:03:07

---

**Overview/Summary**
The paper presents a novel multigrid proximal gradient (MGPG) method for solving the total variation (TV) minimization problem with a strongly convex regularizer. The authors' main goal is to design an efficient algorithm that can be used in a wide range of applications, including image denoising and deblurring, where the TV term is often used as a regularization term. This is achieved by using a forward-backward (FB) proximal gradient method with an adaptive restriction strategy for strongly convex optimization. The FB method is well known to be efficient for the smooth problem in the coarse grid, but it does not work well for the nonsmooth TV problem in the fine grid. In this paper, the authors propose a new MGPG algorithm that can overcome the difficulty of the FB method and improve the performance. 

**Key Contributions/Findings**
The main contributions of the paper are threefold. First, the authors develop an adaptive restriction strategy for the strongly convex optimization problem with a nonsmooth objective function. The key idea is to adaptively choose the step size in the coarse grid based on the smoothness of the iterates obtained from the FB method and the proximity of the current iterate to the solution in the fine grid. The new MGPG algorithm can be used for both the smooth problem and the nonsmooth TV problem, but it is particularly efficient for the nonsmooth TV problem. Second, the authors prove that the MGPG algorithm converges under some conditions. Third, the authors apply the proposed MGPG method to two applications: image denoising and deblurring. The numerical results show that the new MGPG method can be more efficient than the existing methods for the nonsmooth TV problem.

**Methodology/Approach**
The paper is organized as follows. In Section 1, the authors first introduce the FB method with an adaptive restriction strategy. Then in Section 2, they prove the convergence of the proposed MGPG algorithm under some conditions. Finally, in Section 3, the authors apply the proposed MGPG method to two applications: image denoising and deblurring.

**Results/Data**
The numerical results show that the new MGPG method can be more efficient than the existing methods for the nonsmooth TV problem. The paper also compares the performance of the FB and FBMG algorithms in the image denoising and deblurring applications. 

**Limitations/Discussion**
The situation is comparable to [12], who do deblurring directly with the primal problem. This requires proximal map of total variation to be solved numerically (as a denoising problem) on each fine-grid step, while in the coarse grid they avoid this by using a smooth problem and gradient steps. For multigrid optimisation methods to be meaningful, it therefore appears that the coarse-grid problems have to be significantly cheaper than the fine-grid problems. The paper also discusses the limitations of the proposed MGPG method.

**References**
[1] A. Ang, H. De Sterck, and S. Vavasis, MGProx: A nonsmooth multigrid proximal gradient method with adaptive restriction for strongly convex optimization, SIAM J. Optim. 34 (2024), 2788–2820.
[2] M. A. Belzunce, High-Resolution Heterogeneous Digital PET [18F]FDG Brain Phantom based on the BigBrain Atlas, 2018, doi:10.5281/zenodo.1190598.
[3] W. L. Briggs, V. E. Henson, and S. F. McCormick, A multigrid tutorial , SIAM, 2000.
[4] A. Chambolle, An algorithm for total variation minimization and applications, Journal of Mathe- matical imaging and vision 20 (2004), 89–97.
[5] C. Clason and T. Valkonen, Introduction to Nonsmooth Analysis and Optimization  (2020), arXiv: 2001.00216.
[6] F. Guerra and T. Valkonen, Codes for “Multigrid methods for total variation”, 2025, doi:10.5281/zenodo.14927401. Software.
[7] E. F. Guerra Urgiles, Algoritmo forward-backward multimalla con aplicación al problema de supre- sión de ruido en una imagen , Master’ s thesis, Escuela Politécnica Nacional, Quito, Ecuador, 2023, http://bibdigital.epn.edu.ec/handle/15000/23675.
[8] S. Karimi and S. Vavasis, IMRO: A proximal quasi-Newton method for solving ℓ1-regularized least squares problems, SIAM J. Optim. 27 (2017), 583–615.
[9] R. Kornhuber, Monotone multigrid methods for elliptic variational inequalities I, Numerische Mathematik 69 (1994), 167–184.
[10] P. L. Lions and B. Mercier, Splitting algorithms for the sum of two nonlinear operators, SIAM J. Numer. Anal. 16 (1979), 964–979.
[11] S. G. Nash, A multigrid approach to discretized optimization problems, Optim. Methods. Software 14 (2000), 99–116.
[12] P. Parpas, A multilevel proximal gradient algorithm for a class of composite optimization problems, SIAM J. Optim. 39 (2017), 681–701.

Please let me know if you need any further assistance!

---

**Summary Statistics:**
- Input: 4,791 words (27,312 chars)
- Output: 720 words
- Compression: 0.15x
- Generation: 47.8s (15.1 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
