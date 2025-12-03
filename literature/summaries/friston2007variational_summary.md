# Variational free energy and the Laplace approximation

**Authors:** Karl J. Friston, J. Mattout, N. Trujillo-Barreto, J. Ashburner, W. Penny

**Year:** 2007

**Source:** semanticscholar

**Venue:** NeuroImage

**DOI:** 10.1016/j.neuroimage.2006.08.035

**PDF:** [friston2007variational.pdf](../pdfs/friston2007variational.pdf)

**Generated:** 2025-12-02 08:09:53

---

**Overview/Summary**

The paper presents a comprehensive study on the variational free energy and the Laplace approximation in statistical inference. The authors first review the classical Reversible Jump MCMC (RJMCMC) algorithm and its various applications, but also point out that the RJMCMC may not be suitable for all cases because it is sensitive to the choice of the initial state and the reversible jump moves. Then they propose a new variational free energy framework based on the idea of approximating the true posterior distribution by a sequence of distributions with a decreasing number of parameters, which can avoid the sensitivity problem in RJMCMC. The authors also discuss the Laplace approximation and its relation to the variational free energy. Finally, the authors propose an automatic model selection (AMS) method for the AMS algorithm based on the idea that the optimal model is the one with the largest log-evidence.

**Key Contributions/Findings**

The main contributions of this paper are the new variational free energy framework and the AMS method. The variational free energy framework can be used to find an optimal model from a set of models by maximizing the log-evidence, which is the same as the objective function for finding the variational parameters. This means that the inversion of an over-parameterized model will automatically select the optimal model. The authors also propose an AMS method based on the idea that the optimal model is the one with the largest log-evidence.

**Methodology/Approach**

The paper first reviews the classical RJMCMC algorithm and its various applications, but also point out that the RJMCMC may not be suitable for all cases because it is sensitive to the choice of the initial state and the reversible jump moves. Then they propose a new variational free energy framework based on the idea of approximating the true posterior distribution by a sequence of distributions with a decreasing number of parameters, which can avoid the sensitivity problem in RJMCMC. The authors also discuss the Laplace approximation and its relation to the variational free energy. Finally, the authors propose an AMS method for the AMS algorithm based on the idea that the optimal model is the one with the largest log-evidence.

**Results/Data**

The paper does not present any new data or results in the classical sense. The paper presents a theoretical study and the main findings are the proposed variational free energy framework, the relation between the Laplace approximation and the variational free energy, and the AMS method.

**Limitations/Discussion**

The authors point out that the RJMCMC is sensitive to the choice of the initial state and the reversible jump moves. The paper also points out that the classical 5 ReML may not be suitable for all cases because it can only switch off the redundant parameters, but cannot switch off the redundant covariance components. The AMS method can avoid this problem by using the log- normal hyperpriors on the scale parameters. The authors also point out that the inversion of an over-parameterized model will automatically select the optimal model.

**Limitations/Discussion**

The paper does not present any new data or results in the classical sense. The paper presents a theoretical study and the main findings are the proposed variational free energy framework, the relation between the Laplace approximation and the variational free energy, and the AMS method. The authors point out that the inversion of an over-parameterized model will automatically select the optimal model.

**References**

The paper does not have any references.

---

**Summary Statistics:**
- Input: 11,247 words (71,114 chars)
- Output: 569 words
- Compression: 0.05x
- Generation: 30.7s (18.5 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
