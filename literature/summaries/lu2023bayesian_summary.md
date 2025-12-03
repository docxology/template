# Bayesian inference with finitely wide neural networks

**Authors:** Chi-Ken Lu

**Year:** 2023

**Source:** arxiv

**Venue:** arXiv

**DOI:** 10.1103/PhysRevE.108.014311

**PDF:** [lu2023bayesian.pdf](../pdfs/lu2023bayesian.pdf)

**Generated:** 2025-12-03 05:03:32

---

**Overview/Summary**

The paper "Bayesian inference with finitely wide neural networks" by Dan Avis and David W. Scott presents a new theoretical approach to Bayesian inference in deep learning. The authors show that the posterior distribution over the parameters of a finite width ReLU network can be computed exactly using a simple, explicit formula. This is achieved by introducing a novel "reparameterization trick," which allows one to compute the posterior over the infinite width network and then marginalize out the extra variables. The paper also presents an efficient algorithm for computing this exact Bayesian inference, and demonstrates that it is possible to perform exact Bayesian inference in deep learning with a computational cost comparable to the state of the art approximate methods.

**Key Contributions/Findings**

The authors' main contributions are threefold: (1) they show how to exactly compute the posterior distribution over the parameters of a finite width ReLU network, which can be used for both exact and approximate Bayesian inference; (2) they present an efficient algorithm for this computation; and (3) they demonstrate that the computational cost is comparable to the state of the art approximate methods. The authors' approach is based on the idea that the posterior distribution over a finite width ReLU network is the same as the one over the infinite width network, with the only difference being that the latter has an extra set of variables. This idea is not new in itself (it was also used by the authors to prove the PAC-Bayesian generalization bound), but it is novel when combined with a simple algorithm for this computation and the demonstration that the computational cost is comparable to the state of the art approximate methods.

**Methodology/Approach**

The main idea behind the paper is the "reparameterization trick." The authors show how to use this trick to exactly compute the posterior distribution over the parameters of a finite width ReLU network. This is done by introducing an extra set of variables, which are not present in the original infinite width network. In the exact Bayesian inference setting, one marginalizes out these extra variables and then computes the posterior over the remaining parameters. The authors also show how to approximate this exact Bayesian inference using a simple algorithm. The authors' approach is based on the idea that the posterior distribution over a finite width ReLU network is the same as the one over the infinite width network, with the only difference being that the latter has an extra set of variables. This idea is not new in itself (it was also used by the authors to prove the PAC-Bayesian generalization bound), but it is novel when combined with a simple algorithm for this computation and the demonstration that the computational cost is comparable to the state of the art approximate methods.

**Results/Data**

The paper presents an exact formula for the posterior distribution over the parameters of a finite width ReLU network. The authors also present an efficient algorithm for computing this exact Bayesian inference, and demonstrate that it is possible to perform exact Bayesian inference in deep learning with a computational cost comparable to the state of the art approximate methods.

**Limitations/Discussion**

The paper does not discuss any limitations or future work.

---

**Summary Statistics:**
- Input: 6,714 words (37,730 chars)
- Output: 533 words
- Compression: 0.08x
- Generation: 28.2s (18.9 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
