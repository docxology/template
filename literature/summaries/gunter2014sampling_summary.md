# Sampling for Inference in Probabilistic Models with Fast Bayesian Quadrature

**Authors:** Tom Gunter, Michael A. Osborne, Roman Garnett, Philipp Hennig, Stephen J. Roberts

**Year:** 2014

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [gunter2014sampling.pdf](../pdfs/gunter2014sampling.pdf)

**Generated:** 2025-12-05 13:26:01

---

**Overview/Summary**

This paper introduces a new method for Bayesian quadrature (Bayesian numerical integration), which is an important tool in statistical inference and machine learning. The authors introduce the first fast Bayesian quadrature scheme using a novel warped likelihood model and a novel active sampling scheme. This work demonstrates faster convergence than the state-of-the-art Monte Carlo approach on all test cases, including regression and classification benchmarks.

**Key Contributions/Findings**

The main contributions of this paper are the introduction of the warped likelihood model and the active sampling algorithm. The warped likelihood is a new model for Bayesian numerical integration that can be used in any probabilistic model with the same computational cost as the original likelihood function. This allows the use of existing MCMC algorithms to perform Bayesian quadrature, which was previously only possible by using an annealed importance sampler. The active sampling algorithm is a novel approach to select the next sample in the space of the target distribution that can be used for any probabilistic model with the same computational cost as the original likelihood function. This allows the use of existing MCMC algorithms to perform Bayesian quadrature, which was previously only possible by using an annealed importance sampler.

**Methodology/Approach**

The authors first review previous work on Bayesian numerical integration and introduce the warped likelihood model. The warped likelihood is a new model for Bayesian numerical integration that can be used in any probabilistic model with the same computational cost as the original likelihood function. This allows the use of existing MCMC algorithms to perform Bayesian quadrature, which was previously only possible by using an annealed importance sampler. They then introduce the active sampling algorithm. The active sampling is a novel approach to select the next sample in the space of the target distribution that can be used for any probabilistic model with the same computational cost as the original likelihood function. This allows the use of existing MCMC algorithms to perform Bayesian quadrature, which was previously only possible by using an annealed importance sampler. The authors also compare their approach to previous work.

**Results/Data**

The authors test their method on several test cases, including a synthetic mixture model and two real datasets: a regression problem and a classification problem. They compare the performance of their method with the state-of-the-art Monte Carlo approach. The results show that the authors' method is faster than the state-of-the-art Monte Carlo approach on all test cases.

**Limitations/Discussion**

The authors discuss some possible biases in MCMC convergence diagnostics and how to avoid them. They also mention the possibility of future work, such as developing a more efficient annealing schedule for the importance sampler. The authors do not discuss any limitations of their method.

**References**

The paper references 17 papers.

---

**Summary Statistics:**
- Input: 4,808 words (30,279 chars)
- Output: 454 words
- Compression: 0.09x
- Generation: 27.6s (16.4 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
