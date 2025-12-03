# Towards Integrating Epistemic Uncertainty Estimation into the Radiotherapy Workflow

**Authors:** Marvin Tom Teichmann, Manasi Datar, Lisa Kratzke, Fernando Vega, Florin C. Ghesu

**Year:** 2024

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [teichmann2024towards.pdf](../pdfs/teichmann2024towards.pdf)

**Generated:** 2025-12-02 10:51:08

---

**Overview/Summary**

The paper "Towards Integrating Epistemic Uncertainty Estimation" focuses on estimating epistemic uncertainty in deep neural networks for medical image segmentation tasks. The authors argue that the current practice of using a single network for both prediction and uncertainty estimation is not sufficient, as it does not provide an explicit measure of the model's confidence in its predictions. They propose to use two separate models: one for the actual task (prediction) and another for estimating epistemic uncertainty. In this paper, the authors focus on the problem of detecting out-of-distribution silent failures in a COVID-19 lung lesion segmentation dataset. The main contributions are the design of a new distance-based method that can detect silent failures with high accuracy and a new benchmark dataset for evaluating the performance of different methods.

**Key Contributions/Findings**

The paper's key findings are the results obtained by using the proposed distance-based method, which is based on the Frodo system. The authors first introduce the Frodo system in the context of COVID-19 lung lesion segmentation. They then design a new distance-based method that can detect silent failures with high accuracy and compare it to the current state-of-the-art methods. The main results are the performance of different methods on the proposed benchmark dataset.

**Methodology/Approach**

The authors first introduce the Frodo system in the context of COVID-19 lung lesion segmentation, which is a deep learning-based method for detecting silent failures. They then design a new distance-based method that can detect silent failures with high accuracy. The main approach is to use two separate models: one for the actual task (prediction) and another for estimating epistemic uncertainty. In this paper, the authors focus on the problem of detecting out-of-distribution silent failures in a COVID-19 lung lesion segmentation dataset.

**Results/Data**

The main results are the performance of different methods on the proposed benchmark dataset. The authors first compare the Frodo system to the current state-of-the-art method. Then they compare the new distance-based method to the Frodo system and the current state-of-the-art methods. The results show that the new distance-based method can detect silent failures with high accuracy.

**Limitations/Discussion**

The paper's main limitations are the lack of a comprehensive comparison to other uncertainty estimation methods, as highlighted in the paper itself. The authors encourage the community to develop benchmarks and similar tasks based on public data, which can be used for quantitative comparisons and empirical evaluations of various methods. They also suggest that their work provides meaningful, clinically relevant tasks that the community can use to quantitatively evaluate different methods. There remains a significant gap in the comparative analysis of uncertainty estimation methods, as highlighted in the paper itself.

**Note**

The above summary is

---

**Summary Statistics:**
- Input: 3,781 words (26,856 chars)
- Output: 441 words
- Compression: 0.12x
- Generation: 199.6s (2.2 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
