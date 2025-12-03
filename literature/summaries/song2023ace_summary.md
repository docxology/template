# ACE: Active Learning for Causal Inference with Expensive Experiments

**Authors:** Difan Song, Simon Mak, C. F. Jeff Wu

**Year:** 2023

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [song2023ace.pdf](../pdfs/song2023ace.pdf)

**Generated:** 2025-12-03 05:43:51

---

**Overview/Summary**

The paper "ACE: Active Learning for Causal Inference with Expensive Experiments" proposes an active learning method called ACE (Active Causal Estimation) to learn the causal effect of a treatment in the presence of confounding variables. The authors consider the case where the number of experiments is limited and the cost per experiment is high, which is common in many real-world applications such as clinical trials or online controlled experiments. They propose an algorithm that can efficiently select the most informative data to learn about the causal effect and make a decision based on the selected data. The proposed ACE method uses a combination of two strategies: (1) selecting the most informative data from the existing data, and (2) using the selected data to make a decision. The first strategy is called "data twinning" which is an optimal method for splitting data into training and test sets. The second strategy is based on the idea that the causal effect can be estimated by balancing the covariates via the propensity score weighting. They also propose a new algorithm, called "ACE", to make the decision based on the selected data. In this paper, the authors provide a theoretical analysis of the proposed ACE method and evaluate its performance using both synthetic and real-world datasets.

**Key Contributions/Findings**

The main contributions of the paper are: (1) proposing an optimal strategy for splitting data into training and test sets called "data twinning", and (2) providing a theoretical analysis of the proposed ACE algorithm. The authors also provide an empirical evaluation of the proposed ACE method using both synthetic and real-world datasets.

**Methodology/Approach**

The authors first propose a new strategy to split the existing data into training and test sets, which is called "data twinning". This strategy can be used in any active learning problems where the number of experiments is limited. The main idea behind this strategy is that it should select the most informative data from the existing data to learn about the causal effect. Then, they propose an algorithm called ACE based on the selected data. The proposed ACE method uses a combination of two strategies: (1) selecting the most informative data from the existing data, and (2) using the selected data to make a decision. The first strategy is called "data twinning" which is an optimal method for splitting data into training and test sets. The second strategy is based on the idea that the causal effect can be estimated by balancing the covariates via the propensity score weighting. They also propose a new algorithm, called ACE, to make the decision based on the selected data.

**Results/Data**

The authors provide an empirical evaluation of the proposed ACE method using both synthetic and real-world datasets. The results show that the proposed ACE method is effective in making decisions with limited experiments.

**Limitations/Discussion**

One limitation of the paper is that it only considers a simple case where the treatment effect is linear. In this case, the propensity score is also linear. However, in many applications, the propensity score can be non-linear and the treatment effect may not be linear. The authors do not discuss how to extend their method to these cases. Another limitation of the paper is that it only considers a simple case where there are no hidden confounders. In this case, the authors assume that all the covariates are observed. However, in many applications, some of the covariates may be unobserved. The authors do not discuss how to extend their method to these cases.

**References**

The paper does not have any references.

---

**Summary Statistics:**
- Input: 5,649 words (35,718 chars)
- Output: 591 words
- Compression: 0.10x
- Generation: 32.2s (18.3 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
