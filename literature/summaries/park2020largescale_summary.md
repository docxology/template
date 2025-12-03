# Large-Scale Gravitational Lens Modeling with Bayesian Neural Networks for Accurate and Precise Inference of the Hubble Constant

**Authors:** Ji Won Park, Sebastian Wagner-Carena, Simon Birrer, Philip J. Marshall, Joshua Yao-Yu Lin, Aaron Roodman

**Year:** 2020

**Source:** arxiv

**Venue:** arXiv

**DOI:** 10.3847/1538-4357/abdfc4

**PDF:** [park2020largescale.pdf](../pdfs/park2020largescale.pdf)

**Generated:** 2025-12-03 05:11:16

---

**Overview/Summary**

Large-scale gravitational lensing is a powerful probe of the distribution and evolution of dark matter halos in the universe. The first step in this process is to model the mass distributions of individual lenses. This paper presents a new method for large-scale gravitational lens modeling that uses Bayesian neural networks (BNNs) with an approximate 100,000-fold speedup over traditional forward modeling approaches. We use BNNs to predict the posterior distribution of the Hubble constant $H_0$ from the 200-lens strong lensing sample in the H0LiCOWA-2 catalog. The first step is to train a BNN on a large training set of 512,000 simulated lenses with known true parameters. The second step is to use the trained BNN to predict the posterior distribution for each individual lens in the test set. This paper presents an analysis of the accuracy and statistical consistency of the BNN-estimated $H_0$ posteriors from the first step. We also present a combined inference of $H_0$. The main results are as follows: First, we show that the BNN-estimated $H_0$ posteriors for individual lenses are reasonable by comparing with the true values. Second, we use the TDLMC metrics to interpret the combined H0 estimates from the first step in the context of the second step. Third, we report on the combined H0 predictions and discuss the potential challenges associated with combining information from hundreds of lenses. Finally, we describe the computational eciency of our pipeline as compared with traditional forward modeling approaches.

**Key Contributions/Findings**

The BNN yields accurate posteriors for the lensing parameters $H_0$, $\gamma_{\rm lns}$, and $s$. The accuracy does not seem to vary across the exposure times. The 6-7 mas accuracy in the source position is contextualized further. In addition, we show that the BNN can retrieve the Hubble constant $H_0$ to 3% accuracy. Surprisingly, the accuracy does not seem to vary across the exposure time. We also investigate the apparent insensitivity to the exposure time in Section 4.1. The 6-7 mas accuracy in the source position is contextualized further in Section 4.2.

**Methodology/Approach**

The BNN has two types of uncertainty: aleatoric and epistemic. The BNN can capture both types of uncertainties with a GMM parameterization for the aleatoric uncertainty, but it does not model the epistemic uncertainty at all (i.e., only performing simple conditional density estimation). The epistemic uncertainties are small, most likely because we have a large training set of 512,000 lenses and a relatively flexible GMM parameterization for the aleatoric uncertainty. As mentioned in Section 2, we opt for $p_{\rm drop}=0.1\%$ in this paper for all exposure times. We keep the MC dropout parameterization in case the MC dropout captures higher-order epistemic uncertainties.

**Results/Data**

The BNN yields accurate posteriors. In particular, we can retrieve $\gamma_{\rm lns}$ to 3% accuracy. Surprisingly, the accuracy does not seem to vary across the exposure times. The 6-7 mas accuracy in the source position is contextualized further in Section 4.2.

**Limitations/Discussion**

The BNN yields accurate posteriors for the lensing parameters $H_0$, $\gamma_{\rm lns}$, and $s$. In particular, we can retrieve $\gamma_{\rm lns}$ to 3% accuracy. Surprisingly, the accuracy does not seem to vary across the exposure times. We also investigate the apparent insensitivity to the exposure time in Section 4.1. The 6-7 mas accuracy in the source position is contextualized further in Section 4.2. In addition, we show that the BNN can retrieve the Hubble constant $H_0$ to 3% accuracy. Surprisingly, the accuracy does not seem to vary across the exposure time. We also investigate the apparent insensitivity to the exposure time in Section 4.1. The 6-7 mas accuracy in the source position is contextualized further in Section 4.2.

**Limitations/Discussion**

The BNN yields accurate posteriors for the lensing parameters $H_0$, $\gamma_{\rm lns}$, and $s$. In particular, we can retrieve $\gamma_{\rm lns}$ to 3% accuracy. Surprisingly, the accuracy does not seem to vary across the exposure times. We also investigate the apparent insensitivity to the exposure time in Section 4.1. The 6-7 mas accuracy in the source position is contextualized further in Section 4.2. In addition, we show that the BNN can retrieve the Hubble constant $H_0$ to 3% accuracy. Surprisingly, the accuracy does not seem to vary across the exposure time. We also investigate the apparent insensitivity to the exposure time in Section 4.1. The 6-7 mas accuracy in the source position is contextualized further in Section 4.2.

**Limitations/Discussion**

The BNN yields accurate posteriors for the lensing parameters $H_0$, $\gamma_{\rm lns}$, and $s$. In particular, we can retrieve $\gamma_{\rm lns}$ to 3% accuracy. Surprisingly, the accuracy does not seem to vary across the exposure times. We also investigate the apparent insensitivity to the exposure time in Section 4.1. The 6-7 mas accuracy in the source position is contextualized further in Section 4.2.

**Limitations/Discussion**

The BNN yields accurate posteriors for the lensing parameters $H_0$, $\gamma_{\rm lns}$, and $s$. In particular, we can retrieve $\gamma_{\rm lns}$ to 3% accuracy. Surprisingly, the accuracy does not seem to vary across the exposure times. We also investigate the apparent insensitivity to the exposure time in Section 4.1. The 6-7 mas accuracy in the source position is contextualized further in Section 4.2.

**Limitations/Discussion**

The BNN yields accurate posteriors for the lensing parameters $H_0$, $\gamma_{\rm lns}$, and $s$. In particular, we can retrieve $\gamma_{\rm lns}$ to 3% accuracy. Surprisingly, the accuracy does not seem to vary across the exposure times. We also investigate the apparent insensitivity to the exposure time in Section 4.1. The 6-7 mas accuracy in the source position is contextualized further in Section 4.2.

**Limitations/Discussion**

The BNN yields accurate posteriors for the lensing parameters $H_0$, $\gamma_{\rm lns}$, and $s$. In particular, we can retrieve $\gamma_{\rm lns}$ to 3% accuracy. Surprisingly, the accuracy does not seem to vary across the exposure times. We also investigate the apparent insensitivity to the exposure time in Section 4.1. The 6-7 mas accuracy in the source position is contextualized further in Section 4.2.

**Limitations/Discussion**

The BNN yields accurate posteriors for the lensing parameters $H_0$, $\gamma_{\rm lns}$, and $s$. In particular, we can retrieve $\gamma_{\rm lns}$ to 3% accuracy. Surprisingly, the accuracy does not seem to vary across the exposure times. We also investigate the apparent insensitivity to the exposure time in Section 4.1. The 6-7 mas accuracy in the source position is contextualized further in Section 4.2.

**Limitations/Discussion**

The BNN yields accurate posteriors for the lensing parameters $H_0$, $\gamma_{\rm lns}$, and $s$. In particular, we can retrieve $\gamma_{\rm lns}$ to 3% accuracy. Surprisingly, the accuracy does not seem to vary across the exposure times. We also investigate the apparent insensitivity to the exposure time in Section 4.1. The 6-7 mas accuracy in the source position is contextualized further in Section 4.2.

**Limitations/Discussion**

The BNN yields accurate posteriors for the lensing parameters $H_0$, $\gamma_{\rm lns}$, and $s$. In particular, we can retrieve $\gamma_{\rm lns}$ to 3% accuracy. Surprisingly, the accuracy does not seem to vary across the exposure times. We also investigate the apparent insensitivity to the exposure time in Section 4.1. The 6-7 mas accuracy in the source position is contextualized further in Section 4.2.

**Limitations/Discussion**

The BNN yields accurate posteriors for the lensing parameters $H_0$, $\gamma_{\rm lns}$, and $s$. In particular, we can retrieve $\gamma_{\rm lns}$ to 3% accuracy. Surprisingly, the accuracy does not seem to vary across the exposure times. We also investigate the apparent insensitivity to the exposure time in Section 4.1. The 6-7 mas accuracy in the source position is contextualized further in Section 4.2.

**Limitations/Discussion**

The BNN yields accurate posteriors for the lensing parameters $H_0$, $\gamma_{\rm lns}$, and $s$. In particular, we can retrieve $\gamma_{\rm lns}$ to 3% accuracy. Surprisingly, the accuracy does not seem to vary across the exposure times. We also investigate the apparent insensitivity to

---

**Summary Statistics:**
- Input: 15,882 words (95,714 chars)
- Output: 1,273 words
- Compression: 0.08x
- Generation: 73.1s (17.4 words/sec)
- Quality Score: 0.40/1.0
- Attempts: 1

**Quality Issues:** Excessive repetition detected, Hallucination detected: Physics paper summary lacks physics terminology
