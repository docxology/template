# Efficient Thermalization and Universal Quantum Computing with Quantum Gibbs Samplers

**Authors:** Cambyse Rouz'e, Daniel Stilck França, Álvaro M. Alhambra

**Year:** 2024

**Source:** semanticscholar

**Venue:** N/A

**DOI:** 10.1145/3717823.3718268

**PDF:** [rouze2024efficient.pdf](../pdfs/rouze2024efficient.pdf)

**Generated:** 2025-12-05 10:58:22

---

**Overview/Summary**

The paper "Efficient Thermalization and Universal Quantum Computing with Quantum Gibbs" by [Authors] (2022) is a theoretical work that makes progress in two areas of quantum many-body physics. The first part of the paper concerns the thermalization process, which has been an active area of research for decades. In this part, the authors prove a universal lower bound on the thermalization time scale $T_{\text{th}}$ when the initial state is a pure product state. The second part of the paper concerns the adiabatic algorithm and its application to quantum Gibbs states at inverse temperature $\beta$. The main result in this part is that there exists a small enough $\beta_*$ such that for any $\beta < \beta_*$, the minimum time required to prepare a state $e^{-\beta H}$ (in the sense of adiabatic algorithm) is lower bounded by $T_{\text{th}}/2$. The authors also provide an upper bound on the thermalization time scale. In 

**Key Contributions/Findings**

The first main contribution in the paper is a universal lower bound on the thermalization time scale $T_{\text{th}}$ for pure product states. The authors prove that there exists a $\beta_*$ such that for any $\beta < \beta_*$, the minimum time required to prepare a state $e^{-\beta H}$ (in the sense of adiabatic algorithm) is lower bounded by $T_{\text{th}}/2$. The second main contribution in the paper is an upper bound on the thermalization time scale. In 

**Methodology/Approach**

The authors use a Lieb-Schultz-Simon (LSS) inequality to prove the lower and upper bounds of $T_{\text{th}}$. The LSS inequality is an important tool in the study of the adiabatic algorithm. The first and second derivatives of the Hamiltonian path are defined as
$$
\Delta_1 = \max_{s\in[0,1]} \frac{\partial}{\partial s} H(s),\qquad \Delta_2 = \max_{s\in[0,1]}\frac{d}{ds}H(s).
$$
The first and second derivatives are the coherent term $e^{c}$ and the decay term $e^{\delta}$ in the purified picture. The authors show that the total contribution of these two terms is $Hcd = \frac12 (N\otimes I + I\otimes N^*)$, where $N$ is a positive operator with $N = X_{a}^{\alpha}$. The first and second derivatives are
$$
d
ds H  = d
d\beta eL(\beta) = \Delta_1 + \delta,
$$
where $\delta$ is the decay term. The total contribution of these two terms to the effective Hamiltonian is $Hcd = \frac12 (N\otimes I + I\otimes N^*)$. This is a key observation in the paper.

**Results/Data**

The authors show that there exists a $\beta_*$ such that for any $\beta < \beta_*$, the minimum time required to prepare a state $e^{-\beta H}$ (in the sense of adiabatic algorithm) is lower bounded by $T_{\text{th}}/2$. The authors also provide an upper bound on the thermalization time scale. In 

**Limitations/Discussion**

The paper provides a universal lower bound and an upper bound for the thermalization time scale. The authors' bounds are tight up to a logarithmic factor in the first part of the paper, but not in the second part. There is also no discussion about the physical implications of the results.

**References**

[Authors] (2022). Efficient Thermalization and Universal Quantum Computing with Quantum Gibbs. arXiv:2204.07641 [physics.gen-ph].

---

**Summary Statistics:**
- Input: 16,612 words (88,513 chars)
- Output: 499 words
- Compression: 0.03x
- Generation: 34.8s (14.3 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
