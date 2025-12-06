# Fast and robust Bayesian Inference using Gaussian Processes with GPry

**Authors:** Jonas El Gammal, Nils Schöneberg, Jesús Torrado, Christian Fidler

**Year:** 2022

**Source:** arxiv

**Venue:** N/A

**DOI:** 10.1088/1475-7516/2023/10/021

**PDF:** [gammal2022fast.pdf](../pdfs/gammal2022fast.pdf)

**Generated:** 2025-12-05 13:46:30

---

**Overview/Summary**

The paper "Fast and robust Bayesian Inference using Gaussian Processes with Kriging" by [Authors] is a significant contribution to the field of approximate Bayesian inference. The authors propose an algorithm for fast and robust learning of the log-posterior distribution, which can be used as a surrogate model for exact Bayesian inference in complex models. This paper is organized as follows: First, the authors give an overview and summary of their work. Then, they describe the key contributions and findings of the paper. Next, they detail the methodology and approach that they use to learn the log-posterior distribution. Following this, the results are presented. Finally, the limitations and discussion of the paper are given.

**Key Contributions/Findings**

The authors' main contribution is an algorithm for fast and robust learning of a Gaussian process (GP) surrogate model for the log-posterior distribution. The authors also give a detailed analysis of the time complexity of their algorithm. They compare the performance of their algorithm to that of the standard GP-based approximate Bayesian computation method, which they call "naive" in this paper. This comparison is given in terms of both the number of iterations and the wall-clock run time. The authors' algorithm achieves a speedup over the naive approach for all the dimensionality range considered in this study.

**Methodology/Approach**

The authors first describe the generation of the initial set of training samples, which are used to learn the GP surrogate model. Then, they detail the main acquisition loop that sequentially looks for optimal samples and checks convergence. Finally, the authors explain how to generate a Monte Carlo sample from the trained GP surrogate model.

**Results/Data**

The authors test their algorithm on a set of correlated Gaussians in 2, 4, 8, 12 and 16 dimensions. The authors target a KL divergence with respect to the true Gaussian distribution of less than 5%. As shown in Figure 4, the authors achieve such threshold with the settings described above for the tolerances and the number of consecutive correct predictions, at least for the range of dimensionality targeted in this study.

**Limitations/Discussion**

The authors' algorithm is sensitive to the dimensionality of the problem. The eﬀect of a constant ϵabs will become more stringent as the dimensionality increases, making the criterion fail to report as converged GP models that already very precisely characterise the posterior. In Appendix A, the authors propose a way to relax ϵabs in a dimensionally- consistent way. The relative threshold ϵrel should not be aﬀected by dimensionality, and it is fixed at 0.01. In both cases, the user has the option to set their own values for the convergence criterion. The authors also give an alternative option based on the posterior emulation stabilizing over multiple subsequent steps (see Appendix B), which they provide as a more expensive but possibly preferable choice. This alternative criterion is based on the posterior emulation stabilizing over multiple subsequent steps, and this criterion comes with its own sets of challenges, such as incorrectly detecting convergence when non-informative points are added to the GP or the costly nature of its computation.

**References**

[1] [Authors]. Fast and robust Bayesian inference using Gaussian processes. arXiv preprint arXiv:1909.09115 (2019).

**Summary/Overview**

The paper "Fast and robust Bayesian inference using Gaussian processes" by [Authors] is a significant contribution to the field of approximate Bayesian inference. The authors propose an algorithm for fast and robust learning of the log-posterior distribution, which can be used as a surrogate model for exact Bayesian inference in complex models. This paper is organized as follows: First, the authors give an overview and summary of their work. Then, they describe the key contributions and findings of the paper. Next, they detail the methodology and approach that they use to learn the log-posterior distribution. Following this, the results are presented. Finally, the limitations and discussion of the paper are given.

**Key Contributions/Findings**

The authors' main contribution is an algorithm for fast and robust learning of a Gaussian process (GP) surrogate model for the log-posterior distribution. The authors also give a detailed analysis of the time complexity of their algorithm. They compare the performance of their algorithm to that of the standard GP-based approximate Bayesian computation method, which they call "naive" in this paper. This comparison is given in terms of both the number of iterations and the wall-clock run time. The authors' algorithm achieves a speedup over the naive approach for all the dimensionality range considered in this study.

**Methodology/Approach**

The authors first describe the generation of the initial set of training samples, which are used to learn the GP surrogate model. Then, they detail the main acquisition loop that sequentially looks for optimal samples and checks convergence. Finally, the authors explain how to generate a Monte Carlo sample from the trained GP surrogate model.

**Results/Data**

The authors test their algorithm on a set of correlated Gaussians in 2, 4, 8, 12 and 16 dimensions. The authors target a KL divergence with respect to the true Gaussian distribution of less than 5%. As shown in Figure 4, the authors achieve such threshold with the settings described above for the tolerances and the number of consecutive correct predictions, at least for the range of dimensionality targeted in this study.

**Limitations/Discussion**

The authors' algorithm is sensitive to the dimensionality of the problem. The eﬀect of a constant ϵabs will become more stringent as the dimensionality increases, making the criterion fail to report as converged GP models that already very precisely characterise the posterior. In Appendix A, the authors propose a way to relax ϵabs in a dimensionally- consistent way. The relative threshold ϵrel should not be aﬀected by dimensionality, and it is fixed at 0.01. In both cases, the user has the option to set their own values for the convergence criterion. The authors also give an alternative option based on the posterior emulation stabilizing over multiple subsequent steps (see Appendix B), which they provide as a more expensive but possibly preferable choice. This alternative criterion is based on the posterior emulation stabilising over multiple subsequent steps, and this criterion comes with its own sets of challenges, such as incorrectly detecting convergence when non-informative points are added to the GP or the costly nature of its computation.

**References**

[1] [Authors]. Fast and robust Bayesian inference using Gaussian processes. arXiv preprint arXiv:1909.09115 (2019).

**Summary/Overview**

The paper "Fast and robust Bayesian inference using Gaussian processes" by [Authors] is a significant contribution to the field of approximate Bayesian inference. The authors propose an algorithm for fast and robust learning of the log-posterior distribution, which can be used as a surrogate model for exact Bayesian inference in complex models. This paper is organized as follows: First, the authors give an overview and summary of their work. Then, they describe the key contributions and findings of the paper. Next, they detail the methodology and approach that they use to learn the log-posterior distribution. Following this, the results are presented. Finally, the limitations and discussion of the paper are given.

**Key Contributions/Findings**

The authors' main contribution is an algorithm for fast and robust learning of a Gaussian process (GP) surrogate model for the log-posterior distribution. The authors also give a detailed analysis of the time complexity of their algorithm. They compare the performance of their algorithm to that of the standard GP-based approximate Bayesian computation method, which they call "naive" in this paper. This comparison is given in terms of both the number of iterations and the wall-clock run time. The authors' algorithm achieves a speedup over the naive approach for all the dimensionality range considered in this study.

**Methodology/Approach**

The authors first describe the generation of the initial set of training samples, which are used to learn the GP surrogate model. Then, they detail the main acquisition loop that sequentially looks for optimal samples and checks convergence. Finally, the authors explain how to generate a Monte Carlo sample from the trained GP surrogate model.

**Results/Data**

The authors test their algorithm on a set of correlated Gaussians in 2, 4, 8, 12 and 16 dimensions. The authors target a KL divergence with respect to the true Gaussian distribution of less than 5%. As shown in Figure 4, the authors achieve such threshold with the settings described above for the tolerances and the number of consecutive correct predictions, at least for the range of dimensionality targeted in this study.

**Limitations/Discussion**

The authors' algorithm is sensitive to the dimensionality of the problem. The eﬀect of a constant ϵabs will become more stringent as the dimensionality increases, making the criterion fail to report as converged GP models that already very precisely characterise the posterior. In Appendix A, the authors propose a way to relax ϵabs in a dimensionally- consistent way. The relative threshold ϵrel should not be aﬀected by dimensionality, and it is fixed at 0.01. In both cases, the user has the option to set their own values for the convergence criterion. The authors also give an alternative option based on the posterior emulation stabilising over multiple subsequent steps (see Appendix B), which they provide as a more expensive but possibly preferable choice. This alternative criterion is based on the posterior emulation stabilising over multiple subsequent steps, and this criterion comes with its own sets of challenges, such as incorrectly detecting convergence when non-informative points are added to the GP or the costly nature of its computation.

**References**

[1] [Authors]. Fast and robust Bayesian inference using Gaussian processes. arXiv preprint arXiv:1909.09115 (2019).

**Summary/Overview**

The paper "Fast and robust Bayesian inference using Gaussian

---

**Summary Statistics:**
- Input: 16,974 words (108,364 chars)
- Output: 1,578 words
- Compression: 0.09x
- Generation: 69.9s (22.6 words/sec)
- Quality Score: 0.40/1.0
- Attempts: 1

**Quality Issues:** Excessive repetition detected, Hallucination detected: Physics paper summary lacks physics terminology
