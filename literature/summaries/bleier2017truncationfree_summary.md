# Truncation-free Hybrid Inference for DPMM

**Authors:** Arnim Bleier

**Year:** 2017

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [bleier2017truncationfree.pdf](../pdfs/bleier2017truncationfree.pdf)

**Generated:** 2025-12-02 11:00:08

---

**Overview/Summary**
The paper presents a novel hybrid inference for Bayesian non-parametric models. The authors propose to use the full variational distribution in most of the updates while sampling for the introduction of new components. This approach is easy to implement and improves the predictive performance over state-of-the-art methods for single- as well as mixed-membership models at little additional computational cost.

**Key Contributions/Findings**
The main contributions of this paper are: (1) a novel type of hybridization that efficiently uses the full variational distribution while sampling for the introduction of new components; and (2) an early empirical evaluation of the proposed updates. The authors establish some favorable properties of the updates, such as the sum of the explanatory power of the existing K dimensions will exceed the explanatory power of introducing a new dimension E[ξ1] >E[ξ2] for most data points, supporting the use of the more informative variational distribution ζ1 in most of the updates. The authors also find predictive performance improvements over state-of-the-art methods for single- as well as mixed-membership models at little additional computational cost.

**Methodology/Approach**
The paper is organized into 5 sections: Introduction, Paper Content, Critical Instructions, References and END PAPER CONTENT ===

**Results/Data**

The authors used two text data sets to evaluate the proposed updates. The first one was the Associated Press corpus consisting of 2,250 documents, where they used a vocabulary of 10,932 distinct terms occurring over a total of 398k tokens. The second one was the larger New York Times corpus consisting of 1,8 million articles, from which they extracted 153 million tokens using a vocabulary of 77,928 distinct terms.

**Limitations/Discussion**
The current limitations of this work are two-fold. While we have established some favorable properties of the updates and found predictive performance improvements, we rely on approximations and have only limited theoretical arguments legitimizing our approach. The other limitation of this work is its scope. Next to a more thorough experimental evaluation and further formalization, an adaption of the hybrid updates to Wang et al.'s [8] Chinese restaurant process based variational inference for the HDP could potentially be a promising direction for future work.

**References**
[1] Arthur Asuncion, Max Welling, Padhraic Smyth, and Yee Whye Teh. On smoothing and inference for topic models. In Proceedings of the 25th Conference on Uncertainty in Artificial Intelligence, 2009.
[2] Arnim Bleier. Practical collapsed stochastic variational inference for the hdp. InNIPS Workshop on Topic Models: Computation, Application, and Evaluation, 2013.
[3] James Foulds, Levi Boyles, Christopher DuBois, Padhraic Smyth, and Max Welling. Stochastic collapsed variational bayesian inference for latent dirichlet allocation. In Proceedings of the 19th ACM SIGKDD international conference on Knowledge discovery and data mining, 2013.
[4] Kenichi Kurihara, Max Welling, and Yee Whye Teh. Collapsed variational dirichlet process mixture models. In IJCAI, volume 7, 2007.
[5] Dahua Lin. Online learning of nonparametric mixture models via sequential variational approximation. In Advances in Neural Information Processing Systems, 2013.
[6] Issei Sato, Kenichi Kurihara, and Hiroshi Nakagawa. Practical collapsed variational bayes inference for hierarchical dirichlet process. In Proceedings of the 18th ACM SIGKDD international conference on Knowledge discovery and data mining, 2012.
[7] Chong Wang and David M Blei. Truncation-free online variational inference for bayesian non-parametric models. In Advances in neural information processing systems, 2012.
[8] Chong Wang, John William Paisley, and David M Blei. Online variational inference for the hierarchical dirichlet process. In AISTATS, 2011.

**END PAPER CONTENT ===**

Let's begin our summary now!

---

**Summary Statistics:**
- Input: 1,998 words (12,614 chars)
- Output: 565 words
- Compression: 0.28x
- Generation: 88.6s (6.4 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
