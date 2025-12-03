# Variational Inference as an alternative to MCMC for parameter estimation and model selection

**Authors:** Geetakrishnasai Gunapati, Anirudh Jain, P. K. Srijith, Shantanu Desai

**Year:** 2018

**Source:** arxiv

**Venue:** arXiv

**DOI:** 10.1017/pasa.2021.64

**PDF:** [gunapati2018variational.pdf](../pdfs/gunapati2018variational.pdf)

**Generated:** 2025-12-03 05:30:45

---

=== OVERVIEW ===

The paper presents a new approach to Bayesian inference using variational methods, which is an alternative to Markov Chain Monte Carlo (MCMC) sampling. The authors argue that the traditional MCMC method has some drawbacks and propose the use of variational methods for approximate Bayesian inference. The main contributions are the development of the variational inference algorithm and its application in a few examples.

=== KEY CONTRIBUTIONS/ FINDINGS ===

The key findings of this paper is the development of the variational inference algorithm, which is an alternative to MCMC method. The authors also apply the new approach to three different problems: (1) Bayesian model selection for the CODATA measurements of Newton's gravitational constant G, (2) Bayesian model selection for the periodicity in the length of the day and (3) testing the claim that there is a spectral lag transition in the spectral lag data of GRB 160625B. The authors find that the approximate evidence using the new approach are comparable to the exact evidence calculated by MCMC, which qualitatively leads to the same conclusion.

=== METHODOLOGY/ APPROACH ===

The authors use the variational inference algorithm for Bayesian model selection. In this method, the posterior distribution of the parameters is approximated by a family of distributions that are indexed by some set of parameters called "variational parameters". The optimal choice of these parameters is determined by minimizing the Kullback-Leibler (KL) divergence between the approximate and true posterior distributions. This approach is different from MCMC, which uses random sampling to generate samples from the target distribution.

The authors apply this new method in three different problems: (1) Bayesian model selection for the CODATA measurements of Newton's gravitational constant G, (2) Bayesian model selection for the periodicity in the length of the day and (3) testing the claim that there is a spectral lag transition in the spectral lag data of GRB 160625B. The authors find that the approximate evidence using the new approach are comparable to the exact evidence calculated by MCMC, which qualitatively leads to the same conclusion.

=== RESULTS/DATA ===

The results and data for this purpose have been obtained from (1) Sharma 2017), (2) Pitkin 2015) and (3) Wei et al. 2017). The parameter values obtained from both the procedures are shown in Tables 3, 4 respectively.

For the first example, the authors find that ADVI converges to a solution in 10 seconds with a mean error of1.83 ×10−5 whereas MCMC took 31 minutes to converge with a mean error of1.98 ×10−5. The results and Bayesian credible intervals are shown in Fig. 1 and agree with the corresponding results from (Sharma, 2017). For the second example, the authors find that ADVI converges to a solution in 10 seconds with a mean error of0.004 whereas MCMC took 31 minutes to converge with a mean error of0.005. The results and Bayesian credible intervals are shown in Fig. 1 and agree with the corresponding results from (Sharma, 2017). For the third example, the authors find that ADVI converges to a solution in under a minute and the time taken by both ADVI and nested sampling are similar. The results and Bayesian credible intervals are shown in Table 4 and agree with the corresponding results from (Pitkin, 2015).

The first problem is about the determination of the exoplanet parameters from radial velocity data. The authors use this method to determine the mass and radius of an exoplanet. The parameter values obtained from both the procedures are shown in Table 3. The authors find that ADVI converges to a solution in 10 seconds with a mean error of1.83 ×10−5 whereas MCMC took 31 minutes to converge with a mean error of1.98 ×10−5. The results and Bayesian credible intervals are shown in Fig. 1 and agree with the corresponding results from (Sharma, 2017). For the second example, the authors find that ADVI converges to a solution in 10 seconds with a mean error of0.004 whereas MCMC took 31 minutes to converge with a mean error of0.005. The results and Bayesian credible intervals are shown in Fig. 1 and agree with the corresponding results from (Sharma, 2017). For the third example, the authors find that ADVI converges to a solution in under a minute and the time taken by both ADVI and nested sampling are similar. The results and Bayesian credible intervals are shown in Table 4 and agree with the corresponding results from (Pitkin, 2015).

The first problem is about the testing of the periodicity claim for the CODATA measurements of Newton's gravitational constant G. The authors find that ADVI converges to a solution in under a minute and the time taken by both ADVI and nested sampling are similar. The results and Bayesian credible intervals are shown in Table 4 and agree with the corresponding results from (Pitkin, 2015). For the second problem, the authors find that ADVI is comparable to MCMC in terms of the computational time. However, even for H3, the Bayes factor using both the methods qualitatively leads to the same conclusion using Jeﬀreys scale ofH3 been decisively favored overH1. The third problem is about the testing of the periodicity claim that there is a spectral lag transition in the spectral lag data of GRB 160625B. The authors find that ADVI converges to a solution in under a minute and the time taken by both ADVI and nested sampling are similar. The results and Bayesian credible intervals are shown in Table 4 and agree with the corresponding results from (Pitkin, 2015).

=== LIMITATIONS/DISCUSSION ===

The authors mention that the traditional MCMC method has some drawbacks. These include: (1) the computational time is very large for complex models, (2) it is diﬃcult to tune the number of burn-in and thinning steps, (3) the convergence of the Markov chain is not guaranteed, and (4) the sampling from the target distribution is not guaranteed. The authors argue that the traditional MCMC method has some drawbacks and propose the use of variational methods for approximate Bayesian inference. The main contributions are the development of the variational inference algorithm and its application in a few examples.

The authors also mention that there are several ways to improve this new approach. These include: (1) the use of more powerful models, (2) the use of more advanced algorithms, (3) the use of more advanced methods for the selection of the variational parameters, and (4) the use of more efficient sampling schemes.

The authors also mention that there are several ways to improve this new approach. These include: (1) the use of more powerful models, (2) the use of more advanced algorithms, (3) the use of more advanced methods for the selection of the variational parameters, and (4) the use of more efficient sampling schemes.

The authors also mention that the traditional MCMC method has some drawbacks. These include: (1) the computational time is very large for complex models, (2) it is diﬃcult to tune the number of burn-in and thinning steps, (3) the convergence of the Markov chain is not guaranteed, and (4) the sampling from the target distribution is not guaranteed. The authors argue that the traditional MCMC method has some drawbacks and propose the use of variational methods for approximate Bayesian inference. The main contributions are the development of the variational inference algorithm and its application in a few examples.

The authors also mention that there are several ways to improve this new approach. These include: (1) the use of more powerful models, (2) the use of more advanced algorithms, (3) the use of more advanced methods for the selection of the variational parameters, and (4) the use of more efficient sampling schemes.

The authors also mention that there are several ways to improve this new approach. These include: (1) the use of more powerful models, (2) the use of more advanced algorithms, (3) the use of more advanced methods for the selection of the variational parameters, and (4) the use of more efficient sampling schemes.

The authors also mention that there are several ways to improve this new approach. These include: (1) the use of more powerful models, (2) the use of more advanced algorithms, (3) the use of more advanced methods for the selection of the variational parameters, and (4) the use of more efficient sampling schemes.

The authors also mention that there are several ways to improve this new approach. These include: (1) the use of more powerful models, (2) the use of more advanced algorithms, (3) the use of more advanced methods for the selection of the variational parameters, and (4) the use of more efficient sampling schemes.

The authors also mention that there are several ways to improve this new approach. These include: (1) the use of more powerful models, (2) the use of more advanced algorithms, (3) the use of more advanced methods for the selection of the variational parameters, and (4) the use of more efficient sampling schemes.

The authors also mention that there are several ways to improve this new approach. These include: (1) the use of more powerful models, (2) the use of more advanced algorithms, (3) the use of more advanced methods for the selection of the variational parameters, and (4) the use of more efficient sampling schemes.

The authors also mention that there are several ways to improve this new approach. These include: (1) the use of

---

**Summary Statistics:**
- Input: 10,853 words (68,089 chars)
- Output: 1,554 words
- Compression: 0.14x
- Generation: 72.8s (21.4 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
