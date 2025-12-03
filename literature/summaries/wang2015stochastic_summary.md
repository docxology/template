# Stochastic Collapsed Variational Inference for Sequential Data

**Authors:** Pengyu Wang, Phil Blunsom

**Year:** 2015

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [wang2015stochastic.pdf](../pdfs/wang2015stochastic.pdf)

**Generated:** 2025-12-02 10:40:40

---

**Overview/Summary**

The main goal of this paper is to propose a new inference algorithm for sequential data. The authors are motivated by the fact that many real-world problems can be modeled in terms of Markov chains, and the traditional methods (such as the forward-backward algorithm) do not work well when the number of states is large or the sequence length is long. They also point out that the existing collapsed variational inference (CVI) algorithms are not suitable for sequential data because they only consider the first-order statistics. The authors propose a new method, called stochastic CVI (SCVI), which can be used to do both exact and approximate inference in Markov chains. In this paper, the authors also compare the SCVI with the existing methods.

**Key Contributions/Findings**

The main contributions of the paper are the following:
- The first contribution is that the author proposes a new algorithm called stochastic CVI (SCVI), which can be used to do both exact and approximate inference in Markov chains. This method is based on the idea that the second-order statistics are more informative than the first-order ones for sequential data.
- The second contribution is that the authors compare the SCVI with the existing methods, including the forward-backward algorithm and the CVI. They also show the SCVI can be used to do both exact and approximate inference in Markov chains.

**Methodology/Approach**

The proposed method is based on the idea that the second-order statistics are more informative than the first-order ones for sequential data. The authors use the stochastic expectation, which was introduced by Teh et al. [12], to compute the expected number of tables and the log-expected number of customers in a restaurant. This allows them to do both exact and approximate inference in Markov chains.

**Results/Data**

The results show that the SCVI can be used to do both exact and approximate inference in Markov chains. The authors compare the SCVI with the existing methods, including the forward-backward algorithm and the CVI. They also show the SCVI can be used to do both exact and approximate inference in Markov chains.

**Limitations/Discussion**

The main limitations of this paper are that the proposed method is not suitable for large-scale problems because it uses a batch process, which requires a lot of memory. The authors also point out that the existing methods (such as the forward-backward algorithm) do not work well when the number of states is large or the sequence length is long. They also point out that the CVI algorithms are not suitable for sequential data because they only consider the first-order statistics.

**References**

[12] Y. W. Teh, K. Kurihara, and M. Welling. Collapsed variational inference for HDP. In Advances in Neural Information Processing Systems, volume 20, 2008.

---

**Summary Statistics:**
- Input: 3,036 words (18,401 chars)
- Output: 453 words
- Compression: 0.15x
- Generation: 29.7s (15.2 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
