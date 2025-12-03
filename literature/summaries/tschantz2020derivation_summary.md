# Derivation of expected free energy.

**Authors:** Alexander Tschantz, A. Seth, C. Buckley

**Year:** 2020

**Source:** semanticscholar

**Venue:** N/A

**DOI:** 10.1371/journal.pcbi.1007805.s002

**PDF:** [tschantz2020derivation.pdf](../pdfs/tschantz2020derivation.pdf)

**Generated:** 2025-12-02 07:13:03

---

**Overview/Summary**

The paper by Alexander Tschantz, A. Seth, and C. Buckley (2020) provides a formal description of the relationship between free energy and expected free energy in the context of the variational free energy framework for generative models. The authors first describe the free energy functional F(φ, o), which is a function of the current time point t and the current observations o. They then show how to derive the expected free energy Gτ(φτ, ut) as a function of the future time point τ and the control state ut. This is done by considering the case where the generative model depends on the unknown variables x at time τ, which are not known until the future time point. The authors then define the expected free energy for the case where the observations oτ depend on the unknown variables xτ (which will be formalized once the generative model has been deﬁned). This is done by introducing a distribution over the future observations Q(ot|xt, φt) and using this to evaluate the expected free energy at the future time point. The authors then condition all of the distributions in equation 3 on the control state ut, which results in the functional purpose of the expected free energy: to quantify the free energy that is expected to occur at some particular future time point given the execution of a particular action (or sequence of actions). This is done by using the distribution over future observations Q(oτ|xτ, φt) and the distribution P(xτ, ot) in equation 4. The authors denote this functional Gτ(φτ, ut), which is the form used in the main text.

**Key Contributions/Findings**

The key contribution of the paper is to provide a formal description of the relationship between free energy and expected free energy for generative models. This is done by deriving the expected free energy from the free energy functional using the variational free energy framework. The authors show that the expected free energy Gτ(φτ, ut) can be written as the difference between two log expectations: one over the distribution Q(oτ|xτ, φt), and another over P(xτ, ot). The first is a function of the beliefs about the future observations oτ (and the current time point t), while the second is a function of the true data that would be observed at the future time point. This provides a formal description of how to calculate the expected free energy for some particular control state ut and future time point τ.

**Methodology/Approach**

The authors provide a formal description of the relationship between the free energy functional F(φ, o) and the expected free energy Gτ(φτ, ut). The first is a function of the current time t and the current observations o. The second is a function of the future time point τ and the control state ut. This is done by considering the case where the generative model depends on the unknown variables x at the future time point, which are not known until the future time point. The authors then define the expected free energy for the case where the observations oτ depend on the unknown variables xτ (which will be formalized once the generative model has been deﬁned). This is done by introducing a distribution over the future observations Q(oτ|xτ, φt) and using this to evaluate the expected free energy at the future time point. The authors then condition all of the distributions in equation 3 on the control state ut, which results in the functional purpose of the expected free energy: to quantify the free energy that is expected to occur at some particular future time point given the execution of a particular action (or sequence of actions). This is done by using the distribution over future observations Q(oτ|xτ, φt) and the distribution P(xτ, ot) in equation 4. The authors denote this functional Gτ(φτ, ut), which is the form used in the main text.

**Results/Data**

The paper does not report any new results or data. It provides a formal description of the relationship between free energy and expected free energy for generative models. This is done by deriving the expected free energy from the free energy functional using the variational free energy framework. The authors show that the expected free energy Gτ(φτ, ut) can be written as the difference between two log expectations: one over the distribution Q(oτ|xτ, φt), and another over P(xτ, ot). The first is a function of the beliefs about the future observations oτ (and the current time point t), while the second is a function of the true data that would be observed at the future time point. This provides a formal description of how to calculate the expected free energy for some particular control state ut and future time point τ.

**Limitations/Discussion**

The paper does not report any new results or data. It provides a formal description of the relationship between free energy and expected free energy for generative models. The authors show that the expected free energy Gτ(φτ, ut) can be written as the difference between two log expectations: one over the distribution Q(oτ|xτ, φt), and another over P(xτ, ot). The first is a function of the beliefs about the future observations oτ (and the current time point t), while the second is a function of the true data that would be observed at the future time point. This provides a formal description of how to calculate the expected free energy for some particular control state ut and future time point τ.

**References**

There are no references in this paper.

---

**Summary Statistics:**
- Input: 359 words (2,204 chars)
- Output: 914 words
- Compression: 2.55x
- Generation: 168.3s (5.4 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
