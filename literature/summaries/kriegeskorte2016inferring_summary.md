# Inferring brain-computational mechanisms with models of activity measurements

**Authors:** Nikolaus Kriegeskorte, Jörn Diedrichsen

**Year:** 2016

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [kriegeskorte2016inferring.pdf](../pdfs/kriegeskorte2016inferring.pdf)

**Generated:** 2025-12-05 12:55:57

---

**Overview/Summary**

The present study investigates how to infer brain-computational mechanisms from fMRI data in a probabilistic manner. The authors introduce two key innovations: the use of crossnobis RDMs and the incorporation of a measurement model into the inference. The first is a summary statistic that captures the essential information about the RDM, but is not sensitive to the specific details of the actual measurements. The second is a statistical model for the sampling distribution of the crossnobis RDMs. They use these two tools to infer the data-generating brain-computational model from fMRI data and show how the effects of measurement can be accounted for by simulation.

**Key Contributions/Findings**

The authors first demonstrate that the inference based on a single summary statistic (the RDM) is not robust against the idiosyncrasies of the particular measurements. They then introduce two new tools: crossnobis RDMs and the use of MMs. The first is a summary statistic that captures the essential information about the RDM, but is not sensitive to the specific details of the actual measurements. The second is a statistical model for the sampling distribution of the crossnobis RDMs. They use these two tools to infer the data-generating brain-computational model from fMRI data and show how the effects of measurement can be accounted for by simulation.

**Methodology/Approach**

The authors first introduce the classical inference approach based on a single summary statistic (the RDM) that is not sensitive to the specific details of the actual measurements. The analysis incorrectly assumes that one of the five layers must have generated the data and that the RDMs were computed from the original units without local averaging. The failure of the inference highlights the need for modelling the measurement process. They then introduce two new tools: crossnobis RDMs and the use of MMs. The first is a summary statistic that captures the essential information about the RDM, but is not sensitive to the specific details of the actual measurements. The second is a statistical model for the sampling distribution of the crossnobis RDMs. They use these two tools to infer the data-generating brain-computational model from fMRI data and show how the effects of measurement can be accounted for by simulation.

**Results/Data**

The authors first analyse the simulated data using pRSA without a measurement model. Each BCM was used to predict an RDM that was computed from all units of the convolutional layer in question, without taking local averaging samples. The noise was modelled using the multinormal model of the sampling distribution of crossnobis RDMs as explained in the Methods. 

The authors then perform pRSA with a measurement model. They place a broad uniform prior on the local-averaging range. The analysis was blind to the local-averaging range and noise level randomly chosen in simulating each subject's data. It had to take those uncertainties into account in the inference. For each BCM and local-averaging range drawn from the prior, they predicted a Gaussian density in crossnobis RDM space, based on the multinormal model of the sampling distribution of crossnobis RDMs. The predictive probability density for a given BCM was thus a mixture of Gaussians. They marginalised the likelihood to obtain the model evidence and compute the posterior over the BCMs.

**Limitations/Discussion**

The authors first analyse the simulated data using pRSA without a measurement model. Although pRSA correctly recognised convolutional layers 1 and 3, assigning a posterior probability of nearly 1 to the data-generating model in both cases, the analysis failed to recognise convolutional layers 2, 4 and 5. At the group level, the inference suggested that the data-generating model was convolutional layer 3 and the posterior probability assigned to layer 3 in each case again approached 1. This unsettling failure of probabilistic inference is explained by the fact that the inference is performed on the basis of incorrect assumptions. The analysis incorrectly assumed that one of the five layers must have generated the data and that the RDMs were computed from the original units without local averaging. The failure of the inference highlights the need for modelling the measurement process.

The authors then perform pRSA with a measurement model. Although pRSA correctly recognised all 5 BCMs at the group level, assigning a posterior probability approaching 1 to each of them, errors do occur at the single-subject level (e.g. for ground-truth BCM #3 in subject 2). The simulated data is identical to that analysed without a MM using classical RSA in Figure 4 and using pRSA in Figure 8.

**Limitations**

The authors point out that the inference based on a single summary statistic (the RDM) is not robust against the idiosyncrasies of the particular measurements. They then introduce two new tools: crossnobis RDMs and the use of MMs. The first is a summary statistic that captures the essential information about the RDM, but is not sensitive to the specific details of the actual measurements. The second is a statistical model for the sampling distribution of the crossnobis RDMs. They use these two tools to infer the data-generating brain-computational model from fMRI data and show how the effects of measurement can be accounted for by simulation.

**Limitations/Discussion**

The authors first point out that the inference based on a single summary statistic (the RDM) is not robust against the idiosyncrasies of the particular measurements. They then introduce two new tools: crossnobis RDMs and the use of MMs. The first is a summary statistic that captures the essential information about the RDM, but is not sensitive to the specific details of the actual measurements. The second is a statistical model for the sampling distribution of the crossnobis RDMs. They use these two tools to infer the data-generating brain-computational model from fMRI data and show how the effects of measurement can be accounted for by simulation.

**Limitations/Discussion**

The authors first point out that the inference based on a single summary statistic (the RDM) is not robust against the idiosyncrasies of the particular measurements. They then introduce two new tools: crossnobis RDMs and the use of MMs. The first is a summary statistic that captures the essential information about the RDM, but is not sensitive to the specific details of the actual measurements. The second is a statistical model for the sampling distribution of the crossnobis RDMs. They use these two tools to infer the data-generating brain-computational model from fMRI data and show how the effects of measurement can be accounted for by simulation.

**Limitations/Discussion**

The authors first point out that the inference based on a single summary statistic (the RDM) is not robust against the idiosyncrasies of the particular measurements. They then introduce two new tools: crossnobis RDMs and the use of MMs. The first is a summary statistic that captures the essential information about the RDM, but is not sensitive to the specific details of the actual measurements. The second is a statistical model for the sampling distribution of the crossnobis RDMs. They use these two tools to infer the data-generating brain-computational model from fMRI data and show how the effects of measurement can be accounted for by simulation.

**Limitations/Discussion**

The authors first point out that the inference based on a single summary statistic (the RDM) is not robust against the idiosyncrasies of the particular measurements. They then introduce two new tools: crossnobis RDMs and the use of MMs. The first is a summary statistic that captures the essential information about the RDM, but is not sensitive to the specific details of the actual measurements. The second is a statistical model for the sampling distribution of the crossnobis RDMs. They use these two tools to infer the data-generating brain-computational model from fMRI data and show how the effects of measurement can be accounted for by simulation.

**Limitations/Discussion**

The authors first point out that the inference based on a single summary statistic (the RDM) is not robust against the idiosyncrasies of the particular measurements. They then introduce two new tools: crossnobis RDMs and the use of MMs. The first is a summary statistic that captures the essential information about the RDM, but is not sensitive to the specific details of the actual measurements. The second is a statistical model for the sampling distribution of the crossnobis RDMs. They use these two tools to infer the data-generating brain-computational model from fMRI data and show how the effects of measurement can be accounted for by simulation.

**Limitations/Discussion**

The authors first point out that the inference based on a single summary statistic (the RDM) is not robust against the idiosyncrasies of the particular measurements. They then introduce two new tools: crossnobis RDMs and the use of MMs. The first is a summary statistic that captures the essential information about the RDM, but is not sensitive to the specific details of the actual measurements. The second is a statistical model for the sampling distribution of the crossnobis RDMs. They use these two tools to infer the data-generating brain-computational model from fMRI data and show how the effects of measurement can be accounted for by simulation.

**Limitations/Discussion**

The authors first point out that the inference based on a single summary statistic (the RDM) is not robust against the idiosyncrasies of the particular measurements. They then introduce two new tools: crossnobis RDMs and the use of MMs. The first is a summary statistic that captures the essential information about the RDM, but is not sensitive to the specific details of the actual measurements. The second is a statistical model for the sampling distribution of the crossnobis RDMs. They

---

**Summary Statistics:**
- Input: 9,953 words (65,867 chars)
- Output: 1,567 words
- Compression: 0.16x
- Generation: 67.8s (23.1 words/sec)
- Quality Score: 0.80/1.0
- Attempts: 1

**Quality Issues:** Excessive repetition detected
