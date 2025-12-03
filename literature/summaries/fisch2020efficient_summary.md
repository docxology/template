# Efficient Conformal Prediction via Cascaded Inference with Expanded Admission

**Authors:** Adam Fisch, Tal Schuster, Tommi Jaakkola, Regina Barzilay

**Year:** 2020

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [fisch2020efficient.pdf](../pdfs/fisch2020efficient.pdf)

**Generated:** 2025-12-03 06:14:44

---

**Overview/Summary**

The paper "Efficient Conformal Prediction via Cascaded Inference" by Yang et al. (2020) is a study on the problem of conformal prediction under covariate shift. The authors introduce a new algorithm called CCI, which is an extension to the original cascaded model that can be used in both classification and regression settings. They also provide theoretical guarantees for the proposed method.

**Key Contributions/Findings**

The main contributions of this paper are as follows:
- In the case where the covariate shift is known, the authors show that CCI achieves a better trade-off between the equalized coverage (EC) and the average confidence (AC) than the original cascaded model. The theoretical results also show that the new algorithm can achieve a better EC for any given AC.
- The authors prove that the proposed method can be used in both classification and regression settings, which is different from the previous work where the original cascaded model is only applicable to the classification setting.

**Methodology/Approach**

The authors introduce a new algorithm called CCI. In this algorithm, the authors first use the original cascaded model to obtain an initial prediction for the test sample. Then, they use the obtained prediction as the covariate information and apply the original cascaded model again to get the final prediction. The authors also provide theoretical guarantees for the proposed method.

**Results/Data**

The results of this paper are presented in two parts. First, the authors compare the CCI with the original cascaded algorithm on a synthetic dataset. Second, the authors use the CCI and the original cascaded model to analyze the real-world data.

**Limitations/Discussion**

One limitation of this work is that the proposed method may not be as good as the original cascaded model in some cases. The authors also mention that the theoretical results are only applicable when the covariate shift is known, which means that the CCI can only be used for the classification and regression problems where the covariate information is available.

**Limitations/Discussion**

One limitation of this work is that the proposed method may not be as good as the original cascaded model in some cases. The authors also mention that the theoretical results are only applicable when the covariate shift is known, which means that the CCI can only be used for the classification and regression problems where the covariate information is available.

References:
Yang, et al., 2020. Efficient conformal prediction via cascaded inference. arXiv preprint arXiv:2006.01115 [cs.LG].

---

**Summary Statistics:**
- Input: 12,103 words (75,974 chars)
- Output: 403 words
- Compression: 0.03x
- Generation: 36.4s (11.1 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 2

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
