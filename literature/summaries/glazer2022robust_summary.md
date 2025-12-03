# Robust inference for matching under rolling enrollment

**Authors:** Amanda K. Glazer, Samuel D. Pimentel

**Year:** 2022

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [glazer2022robust.pdf](../pdfs/glazer2022robust.pdf)

**Generated:** 2025-12-03 04:16:50

---

**Overview/Summary**

Amanda K. Glazer and Samuel D. Pimentel present a new approach to matching under rolling enrollment settings in their paper "Robust inference for matching under rolling enrollment." The authors focus on the problem of estimating average treatment effects (ATEs) when the data is collected over time, with some units being enrolled at different times. In this setting, the optimal matching algorithm should not only be able to find a good match between treated and control units but also take into account the temporal information in the data. The authors propose a new method called GroupMatch that can do just that. The key advantage of the proposed approach is that it considers and optimizes over matches between units at different time points, which leads to higher quality matches on lagged covariates. However, this advantage comes with a price in additional assumptions, notably the assumption of timepoint agnosticism. In particular, the authors assume that mean potential outcomes under control for any two individual timepoints in the data should be identical; in particular, this rules out time trends of any kind in the outcome model that cannot be explained by covariates in the prior L timepoints.

**Key Contributions/Findings**

The main contributions of the paper are the proposed GroupMatch method and a new test for the assumption of timepoint agnosticism. The authors show that the ATE can be estimated using the GroupMatch algorithm, which is robust to the correlated errors between different time points. In addition, they provide an empirical application of the proposed approach in Section 6.

**Methodology/Approach**

The authors first present a new test for the assumption of timepoint agnosticism. The test is based on control-control time matching: matching control units at di ﬀerent timepoints and testing if the average di ﬀerence in outcomes between the two time point groups, conditional on relevant covariates, is signi ﬁcantly di ﬀerent from zero using a bootstrap test. The authors then present the GroupMatch algorithm that can be used to estimate ATEs under rolling enrollment settings. In particular, the proposed approach does not require the assumption of timepoint agnosticism and it is robust to the correlated errors between different time points.

**Results/Data**

The authors use a simulation study to show the performance of the proposed method. The results are presented in Section 6. The authors also provide an empirical application of the proposed approach in Section 6. The main ﬁndings of the paper are that the ATE can be estimated using the GroupMatch algorithm, which is robust to the correlated errors between different time points.

**Limitations/Discussion**

The authors mention some limitations and future work. In particular, they point out that the proposed approach does not require the assumption of timepoint agnosticism and it is robust to the correlated errors between different time points. However, the authors also assume that mean potential outcomes under control for any two individual timepoints in the data should be identical; in particular, this rules out time trends of any kind in the outcome model that cannot be explained by covariates in the prior L timepoints.

**References**

The paper references 37 papers.

---

**Summary Statistics:**
- Input: 14,260 words (85,358 chars)
- Output: 512 words
- Compression: 0.04x
- Generation: 28.5s (17.9 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
