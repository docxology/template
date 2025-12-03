# On the Convergence of Stochastic Variational Inference in Bayesian Networks

**Authors:** Ulrich Paquet

**Year:** 2015

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [paquet2015convergence.pdf](../pdfs/paquet2015convergence.pdf)

**Generated:** 2025-12-03 03:20:04

---

**Overview/Summary**
The paper proposes a new stochastic variational inference algorithm for Bayesian networks with hidden variables. The key idea is to perform the stochastic updates in an order that allows the global natural gradient (GN) to be zeroed out, i.e., the global Fisher information matrix G(Λ) is inverted and set to zero. This is achieved by taking a batch of data from the global observed variables Xo at each iteration, and performing the stochastic updates for all hidden variables in the order that makes the GN zero. The authors show that this algorithm can be implemented in two ways: either update all the parameters (like hyperparameters) simultaneously as in the full variational Bayes (VB), or only update the parameters of the observed variables while keeping the parameters of the unobserved variables fixed, which is called the global component-wise (GC) updates. The authors also show that the GN can be zeroed out for both the shared sample and the GC updates by choosing the right ρ1 value in the algorithm, i.e., ρ1 1/32, or ρ1 1/64. The paper compares the convergence of the full VB, the shared sample with the component-wise (CW) updates, and the global CW updates for different batch sizes Cglobal. In 

**Key Contributions/Findings**
The main contributions of the paper are the stochastic variational inference algorithm and its convergence analysis. The authors show that the shared sample with the component-wise (CW) updates can be implemented in a way that is similar to the full VB, i.e., the shared sample CW updates. This allows the algorithm to converge much faster than the global CW updates for all the Cglobal settings considered in the paper. The authors also compare the convergence of the full VB and the GC with the shared sample CW updates for different batch sizes.

**Methodology/Approach**
The stochastic variational inference is a new method that can be implemented in two ways: either update all the parameters simultaneously as in the full VB, or only update the parameters of the observed variables while keeping the parameters of the unobserved variables fixed. The authors show that the GN can be zeroed out for both the shared sample and the GC updates by choosing the right ρ1 value in the algorithm. The paper compares the convergence of the full VB and the GC with the shared sample CW updates for different batch sizes Cglobal.

**Results/Data**
The authors compare the convergence of the full VB, the shared sample CW updates, and the global CW updates for different batch sizes Cglobal. In 

**Limitations/Discussion**
The authors compare the convergence of the full VB and the GC with the shared sample CW updates for different batch sizes Cglobal. In 

**Limitations/Discussion**
The authors compare the convergence of the full VB and the GC with the shared sample CW updates for different batch sizes Cglobal. In 

**References**
The authors do not mention any references in the paper.

---

**Summary Statistics:**
- Input: 3,943 words (21,842 chars)
- Output: 480 words
- Compression: 0.12x
- Generation: 33.5s (14.3 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
