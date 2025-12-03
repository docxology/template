# Bayesian data assimilation for estimating epidemic evolution: a COVID-19 study

**Authors:** Xian Yang, Shuo Wang, Yuting Xing, Ling Li, Richard Yi Da Xu, Karl J. Friston, Yike Guo

**Year:** 2020

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [yang2020bayesian.pdf](../pdfs/yang2020bayesian.pdf)

**Generated:** 2025-12-02 07:47:36

---

**Overview/Summary**

The paper proposes a Bayesian data assimilation method for estimating the evolution of an epidemic over time. The authors consider the case where the number of infected individuals is observed at different times and locations, but the exact location of each observation is not known. This problem is formulated as a hierarchical state-space model with a renewal process, which is used to describe the conditional independence between the observations and the underlying latent variables. The transition probability in this model is defined based on the underlying renewal process. A particle filter method is adopted for the inference of the time-varying latent state, which updates the posterior estimation using the latest observations following the Bayes rule. The filtering estimates would be accurate if all related infections are fully observed. However, this is certainly not the case due to observation delay. To reduce the uncertainty from forward filtering, a Bayesian backward smoothing technique is adopted for estimating the latent state at a time retrospectively, given all observations available till that time.

**Key Contributions/Findings**

The key contributions of the paper include the following: 1) The authors propose a new hierarchical state-space model with a renewal process to describe the conditional independence between the observations and the underlying latent variables. This is different from the traditional Markov chain models in which the transition probability is defined based on the underlying stochastic process. 2) A particle filter method is adopted for the inference of the time-varying latent state, which updates the posterior estimation using the latest observations following the Bayes rule. The filtering estimates would be accurate if all related infections are fully observed. However, this is certainly not the case due to observation delay. To reduce the uncertainty from forward filtering, a Bayesian backward smoothing technique is adopted for estimating the latent state at a time retrospectively, given all observations available till that time.

**Methodology/Approach**

The authors formulate the inference of the latent state with the observations as within a data assimilation framework. A sequential Bayesian filtering approach is adopted to infer the time-varying latent state, which updates the posterior estimation using the latest observations following the Bayes rule. This approach differs from the fixed prior in the Bayesian inference of static parameters. The filtering mechanism computes the posterior distribution of the latent state by assimilating the forecast from the forward transition model with the information from the new epidemiological observations. For the implementation of this Bayesian updating process, a particle filter method is adopted to efficiently approximate the posterior distribution through Sequential Monte Carlo (SMC) sampling. This eschews any fixed- form assumptions for the posterior – of the sort used in variational filtering and dynamic causal modelling[38]. The likelihood function is assumed to follow a Gaussian distribution with an estimated variance, which is calculated empirically. The authors also show that using this Gaussian likelihood function can reduce the fluctuation of the estimation results from forward filtering. This is demonstrated by the simulation results of using Poisson likelihood without considering the observation noise. Results can be found in Supplementary Figure 2, where the estimations fluctuate dramatically under noisy observation.

**Results/Data**

The paper uses a renewal process to describe the conditional independence between the observations and the underlying latent variables. The transition probability is defined based on this renewal process. A particle filter method is adopted for the inference of the time-varying latent state, which updates the posterior estimation using the latest observations following the Bayes rule. The filtering estimates would be accurate if all related infections are fully observed. However, this is certainly not the case due to observation delay. To reduce the uncertainty from forward filtering, a Bayesian backward smoothing technique is adopted for estimating the latent state at a time retrospectively, given all observations available till that time.

**Limitations/Discussion**

The paper does not discuss any limitations or future work.

---

**Summary Statistics:**
- Input: 13,277 words (93,453 chars)
- Output: 638 words
- Compression: 0.05x
- Generation: 36.8s (17.3 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
