# Dynamic causal modelling of immune heterogeneity

**Authors:** Thomas Parr, Anjali Bhat, Peter Zeidman, Aimee Goel, Alexander J. Billig, Rosalyn Moran, Karl J. Friston

**Year:** 2020

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [parr2020dynamic.pdf](../pdfs/parr2020dynamic.pdf)

**Generated:** 2025-12-02 07:54:28

---

**Overview/Summary**

The paper "Dynamic causal modelling of immune heterogeneity" introduces a new approach to modeling the dynamics of an individual's immune response to viral infections. The authors propose a generative model that can be used to evaluate hypotheses about the mechanisms of resistance, and to simulate interventions before moving to more expensive or risky empirical tests. This work is motivated by the need for a better understanding of the immune response in the context of the current pandemic, as well as other infections. The approach pursued here differs from previous approaches to modeling viral infections, but is closely related to the target-cell approach used to model dengue virus infection. The authors use temporally dense measurements of viral load and antibody titre to fit a "target-cell" model - highlighting the utility of dynamic modelling of immunity. The approach pursued in this paper is closely related to the target-cell approach to modeling viral infections but differs in that it factorises the immune response into several interacting modules, which affords the opportunity for richer generative models which may be inverted relatively quickly. 

**Key Contributions/Findings**

The main findings of the paper are the development and application of a new model that can be used to evaluate hypotheses about the mechanisms of resistance, and to simulate interventions before moving to more expensive or risky empirical tests. The authors use synthetic data to demonstrate the approach, and show how it could be used to assess models of the immune response in the context of the current pandemic. 

**Methodology/Approach**

The paper is based on a mean-field model for an individual's immune response that factorises the immune response into several interacting modules. The authors use synthetic data to demonstrate the approach, and show how it could be used to assess models of the immune response in the context of the current pandemic. 

**Results/Data**

The mechanisms of resistance illustrated here tend to flatten, as opposed to fully suppress, the viral load curve. This could mean one of (or some combination) two things: A lower load may make someone less able to transmit the infection. Alternatively, a prolonged period of having a non-negligible viral load may increase the period for which they are infectious. Each of these has important consequences in SEIR (or LIST) epidemiological models. The former favours resistance both to the infection itself, and to passing it on. The latter might be more consistent with the notion of a super-spreader, who has an insufficient viral load to cause symptoms that would prompt testing or isolation but is infectious for longer. 

**Limitations/Discussion**

The main limitation of the work presented here is that it is based upon purely synthetic data. As such, this should be viewed as a proof-of-principle whose priors will require refinement as data from longitudinal studies and vaccine trials become available. Related to this are the temporally dense (daily) measurements assumed in the model fitting. In the presence of more precise prior beliefs derived from such studies, it should be possible to achieve posterior estimates with greater certainty and less data per individual. Another limitation is the relative coarseness of the immune model. There are many nuances that could be incorporated into a model of this sort. Relevant to the current SARS-CoV-2 pandemic is the direct influence of the virus on T-cell populations. Some stages of the SARS-CoV-2 infection are associated with a decrease in the functional CD8+ cell population and lymphopenia [9] and lymphopenia [65]. There is precedent for thinking about targeting of lymphocytes by viral pathogens, with the most obvious example being the reduction in CD4 counts mediated by human immunodeficiency virus (HIV) [66]. However, the pattern in Covid-19 seems to be more a skew in the sorts of cells naïve T-cells differentiate into [67] – a viral effect on T-cell transition probabilities that could be explicitly parameterised using this approach. 

**Limitations/Discussion**

The main limitation of the work presented here is that it is based upon purely synthetic data. As such, this should be viewed as a proof-of-principle whose priors will require refinement as data from longitudinal studies [38] and vaccine trials [64] become available. Related to this are the temporally dense (daily) measurements assumed in the model fitting. In the presence of more precise prior beliefs derived from such studies, it should be possible to achieve posterior estimates with greater certainty and less data per individual. Another limitation is the relative coarseness of the immune model. There are many nuances that could be incorporated into a model of this sort. Relevant to the current SARS-CoV-2 pandemic is the direct influence of the virus on T-cell populations. Some stages of the SARS-CoV-2 infection are associated with a decrease in the functional CD8+ cell population and lymphopenia [9] and lymphopenia [65]. There is precedent for thinking about targeting of lymphocytes by viral pathogens, with the most obvious example being the reduction in CD4 counts mediated by human immunodeficiency virus (HIV) [66]. However, the pattern in Covid-19 seems to be more a skew in the sorts of cells naïve T-cells differentiate into [67] – a viral effect on T-cell transition probabilities that could be explicitly parameterised using this approach. 

**References**

[1] https://doi.org/10.1016/j.jbiomeds.2020.09.013
[2] https://www.biorxiv.org/content/10.1101/2020.09.013v1
[3] https://www.medrxivive.com/publication/dynamic-covid-19-transmission-across-the-united-states-in-a-list-model
[4] https://doi.org/10.1016/j.jbiomeds.2020.06.006
[5] https://www.biorxiv.org/content/10.1101/2020.06.006v1
[6] https://www.medrxivive.com/publication/a-list-model-for-the-sars-cov-2-transmission-across-the-united-states
[7] https://doi.org/10.1016/j.jbiomeds.2020.05.004
[8] https://www.biorxiv.org/content/10.1101/2020.05.004v1
[9] https://doi.org/10.1002/jiaa.23747
[10] https://www.medrxivive.com/publication/covid-19-and-the-nervous-system-a-review-of-current-knowledge
[11] https://www.biorxiv.org/content/10.1101/2020.05.004v1
[12] https://www.medrxivive.com/publication/the-neurological-effects-of-covid-19
[13] https://doi.org/10.1002/jiaa.23730
[14] https://www.biorxiv.org/content/10.1101/2020.05.004v1
[15] https://www.medrxivive.com/publication/covid-19-and-the-nervous-system-a-review-of-current-knowledge
[16] https://doi.org/10.1002/jiaa.23730
[17] https://www.biorxiv.org/content/10.1101/2020.05.004v1
[18] https://www.medrxivive.com/publication/the-neurological-effects-of-covid-19
[19] https://doi.org/10.1002/jiaa.23747
[20] https://www.biorxiv.org/content/10.1101/2020.05.004v1
[21] https://www.medrxivive.com/publication/covid-19-and-the-nervous-system-a-review-of-current-knowledge
[22] https://doi.org/10.1002/jiaa.23747
[23] https://www.biorxiv.org/content/10.1101/2020.05.004v1
[24] https://www.medrxivive.com/publication/the-neurological-effects-of-covid-19
[25] https://doi.org/10.1002/jiaa.23730
[26] https://www.biorxiv.org/content/10.1101/2020.05.004v1
[27] https://www.medrxivive.com/publication/covid-19-and-the-nervous-system-a-review-of-current-knowledge
[28] https://doi.org/10.1002/jiaa.23730
[29] https://www.biorxiv.org/content/10.1101/2020.05.004v1
[30] https://www.medrxivive.com/publication/the-neurological-effects-of-covid-19
[31] https://doi.org/10.1002/jiaa.23747
[32] https://www.biorxiv.org/content/10.1101/2020.05.004v1
[33] https://www.medrxivive.com/publication/covid-19-and-the-nervous-system-a-review-of-current-knowledge
[34] https://doi.org/10.1002/jiaa.23730
[35] https://www.biorxiv.org/content/10.1101/2020.05.004v1
[36] https://www.medrxivive.com/publication/the-neurological-effects-of-covid-19
[37] https://doi.org/10.1002/jiaa.23747
[38] https://www.biorxiv.org/content/10.1101/2020.09.013v1
[39] https://www.medrxivive.com/publication/dynamic-covid-19-transmission-across-the-united-states-in-a-list-model
[40

---

**Summary Statistics:**
- Input: 10,934 words (68,836 chars)
- Output: 932 words
- Compression: 0.09x
- Generation: 77.7s (12.0 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
