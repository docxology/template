# Parametric dynamic causal modelling

**Authors:** Amirhossein Jafarian, Peter Zeidman, Rob. C Wykes, Matthew Walker, Karl J. Friston

**Year:** 2020

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [jafarian2020parametric.pdf](../pdfs/jafarian2020parametric.pdf)

**Generated:** 2025-12-02 07:46:59

---

**Overview/Summary**
The paper proposes a novel approach called Parametric Dynamic Causal Modelling (P-DCM) to infer the causal effects of slowly changing parameters on the neural activity from multivariate time series data. The authors apply this method to both simulated and real ECoG data, which is a type of brain activity recording.

**Key Contributions/Findings**
The main contributions of the paper are:
1. A new statistical framework for inferring the causal effects of slowly changing parameters on the neural activity from multivariate time series data.
2. The application of P-DCM to both simulated and real ECoG data, which is a type of brain activity recording.

**Methodology/Approach**
The authors first fit the CMC (Computational Model of Cognition) model to the normal activity to establish the prior expectation for the model parameters. Then they epoched the data each of which has 2 seconds duration and estimated key model parameters. They fixed some of the parameters (e.g., noise hyperparameters and sensor gain, which are not likely to vary in this animal model during the experiment) and only allow the rate constant and self-connection of neuronal populations to change during and after seizures. After model inversion, they ran a PEB analysis with a binarized spectral envelope as a regressor (column vector with zero and one entries, where zero and one denotes normal and seizure epochs, respectively). The results are shown in Figure 10 and suggest that disinhibition of deep pyramidal and inhibitory populations best explain the data. Finally, they repeated the above analysis using frequency-specific regressors to characterise the relationship between disinhibition in particular populations and their frequency specific correlates.

**Results/Data**
The authors first fitted the CMC model to the normal activity to  establish the prior expectation for the model parameters. They then epoched the data each of which has  2 seconds duration and estimated key model parameters. They fixed some of the parameters (e.g., noise hyperparameters and sensor gain, which are not likely to vary in this animal model during the experiment) and only allow the rate constant and self-connection of neuronal populations to change during and after seizures. After model inversion, they ran a PEB analysis with a binarized spectral envelope as a regressor (column vector with zero and one entries, where zero and one denotes normal and seizure epochs, respectively). The results are shown in Figure 10 and suggest that disinhibition of deep pyramidal and inhibitory populations was likely to explain the data. Finally, they repeated the above analysis using frequency-specific regressors to characterise the relationship between disinhibition in particular populations and their frequency specific correlates. Here, the regressors of the GLM were the predominant empirical frequencies in the data of 5, 19, and 40 Hz (identified using singular value decomposition of the time frequency data). The PEB results are shown in Figure 11 and suggest that seizures (which are characterised by 3 to 8 Hz activity) were best explained by the reduction in effective membrane time constant of deep pyramidal cells, with interneurons contributing to 19 Hz activity. This is aga

[... truncated for summarization ...]

---

**Summary Statistics:**
- Input: 12,343 words (81,905 chars)
- Output: 504 words
- Compression: 0.04x
- Generation: 31.3s (16.1 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
