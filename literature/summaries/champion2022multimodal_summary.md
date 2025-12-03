# Multi-Modal and Multi-Factor Branching Time Active Inference

**Authors:** Théophile Champion, Marek Grześ, Howard Bowman

**Year:** 2022

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [champion2022multimodal.pdf](../pdfs/champion2022multimodal.pdf)

**Generated:** 2025-12-03 07:12:49

---

**Overview/Summary**
The paper presents a new version of Branching Time Active Inference (BTAI) that can model several observed and latent variables. The BTAI3MF framework is an extension to two earlier versions, named BTAIVMP and BTAIBF, which are based on the active inference as implemented in SPM. The key difference between the three approaches is the way of performing the inference process at each time step t: BTAIVMP performs variational message passing (VMP) with a variational distribution composed of only one factor, BTAIBF performs exact inference using Bayes theorem, and BTAI3MF implements belief propagation to compute the marginal posterior over each latent variable. The paper compares these three approaches on a version of the dSprites environment in which the metadata of the dSprites dataset are used as inputs to the model instead of the dSprites images. The best performance obtained by BTAIVMP was to solve 96.9% of the task in 5.1 seconds. Importantly, BTAIVMP was previously compared to active inference as implemented in SPM both theoretically and experimentally (Champion et al., 2022b, a). BTAIBF was able to solve 98.6% of the task but at the cost of 17.5 seconds of computation. Note that BTAIBF was using a granularity of two (i.e., 816 states) while BTAIVMP was using a granularity of four (i.e., 216 states), which is why BTAIBF seems to be three times slower than BTAIVMP. Finally, BTAI3MF outperformed both of its predecessors by solving the task completely (100%, granularity of 1) in only 2.559 seconds. Importantly, BTAI3MF provides an improved modeling capacity. Indeed, the framework can now handle the modelling of several observed and latent variables, and takes advantage of the factorisation of the generative model to perform inference eﬃciently. As described in detail in Appendix A, we also provide a high level notation for the creation of BTAI3MF that aims to make our approach as straightforward as possible to apply to new domains. The high-levell notational language allows the user to create models by simply declaring the variables it contains, and the framework performs the inference process automatically. Moreover, driven by the need for interpretability, we developed a graphical user interface to analyse the behaviour and reasoning of our agent, which is described in Appendix B.

**Key Contributions/Findings**
The paper presents three main contributions: 1) The new version of BTAI that can model several observed and latent variables; 2) A comparison between the three versions of BTAI on a version of the dSprites environment; and 3) An improved modeling capacity. The first contribution is to extend the BTAI framework by allowing for the modelling of multiple observed and latent variables, which are all within a temporal slice. Within a slice, the model is equipped with prior beliefs over the initial latent variables, and each observation depends on a subset of the latent variables through the likelihood mapping. Additionally, the latent states evolve over time according to the transition mapping that describes how each latent variable at time t+1 is generated from a subset of the hidden states at time t and the action taken. The second contribution is to compare these three approaches on a version of the dSprites environment in which the metadata of the dSprites dataset are used as inputs to the model instead of the dSprites images. The best performance obtained by BTAIVMP was to solve 96.9% of the task in 5.1 seconds. Importantly, BTAIVMP was previously compared to active inference as implemented in SPM both theoretically and experimentally (Champion et al., 2022b, a). BTAIBF was able to solve 98.6% of the task but at the cost of 17.5 seconds of computation. Note that BTAIBF was using a granularity of two (i.e., 816 states) while BTAIVMP was using a granularity of four (i.e., 216 states), which is whyBTAIBF seems to be three times slower than BTAIVMP. Finally, BTAI3MF outperformed both of its predecessors by solving the task completely (100%, granularity of 1) in only 2.559 seconds. Importantly, BTAI3MF was able to model all the modalities of the dSprites environment for a total of 760,320 possible states.

**Methodology/Approach**
The paper does not present an experimental methodology. The three approaches are compared on a version of the dSprites environment in which the metadata of the dSprites dataset are used as inputs to the model instead of the dSprites images. The first contribution is to extend the BTAI framework by allowing for the modelling of multiple observed and latent variables, and the second contribution is to compare these three approaches on this version of the dSprites environment.

**Results/Data**
The paper presents a comparison between the three versions of BTAI. The best performance obtained by BTAIVMP was to solve 96.9% of the task in 5.1 seconds. Importantly, BTAIVMP was previously compared to active inference as implemented in SPM both theoretically and experimentally (Champion et al., 2022b, a). BTAIBF was able to solve 98.6% of the task but at the cost of 17.5 seconds of computation. Note that BTAIBF was using a granularity of two (i.e., 816 states) while BTAIVMP was using a granularity of four (i.e., 216 states), which is whyBTAIBF seems to be three times slower than BTAIVMP. Finally, BTAI3MF outperformed both of its predecessors by solving the task completely (100%, granularity of 1) in only 2.559 seconds. Importantly, BTAI3MF was able to model all the modalities of the dSprites environment for a total of 760,320 possible states.

**Limitations/Discussion**
The paper does not present any limitations or discussion about future work. The three approaches are compared on a version of the dSprites environment in which the metadata of the dSprites dataset are used as inputs to the model instead of the dSprites images. The first contribution is to extend the BTAI framework by allowing for the modelling of multiple observed and latent variables, and the second contribution is to compare these three approaches on this version of the dSprites environment. The third contribution is that an improved modeling capacity can be achieved with the new approach.

**References**
Champion et al., 2021a. BTAI: A new framework for active inference.
Champion et al., 2022b, a. Branching time active inference as implemented in SPM.
Champion et al., 2022b. Multi-modal and multi-factor branching time active inference.

**Appendixes**
A. High level notation for the creation of BTAI3MF
The high-levell notational language allows the user to create models by simply declaring the variables it contains, and the framework performs the inference process automatically. The high-levell notational language is as follows:

1. **Slice declaration**: A slice is a set of observed and latent variables that are all within a temporal slice. For example, in this paper, the BTAI3MF model contains 6 observed variables (x0, x1, . . , x5) and 40 latent variables (z0, z1, . . , z39). The slice declaration is as follows:
```
slice = [observed_variables] + [latent_variables]
```

2. **Likelihood mapping**: A likelihood mapping is a function that describes the dependencies between the observed and latent variables within a temporal slice. For example, in this paper, the BTAI3MF model contains 40 latent variables (z0, z1, . . , z39), and each of these latent variables depends on a subset of the 6 observed variables (x0, x1, . . , x5) through the likelihood mapping. The slice declaration is as follows:
```
slice = [observed_variables] + [latent_variables]
likelihood_mapping = {z0: [x0], z1: [x2, x3], z2: [x4], z3: [x5]}
```

3. **Transition mapping**: A transition mapping describes how each latent variable at time t+1 is generated from a subset of the hidden states at time t and the action taken. The slice declaration and the likelihood mapping are as follows:
```
slice = [observed_variables] + [latent_variables]
likelihood_mapping = {z0: [x0], z1: [x2, x3], z2: [x4], z3: [x5]}
transition_mapping = {z0: [z39], z1: [z38], . . , z39: [z0]}
```

4. **Prior beliefs**: The prior beliefs are the initial beliefs over the latent variables at time t=0, and they can be specified as follows:
```
prior_beliefs = {z0: 0.5, z1: 0.3, . . , z39: 0.2}
```

The slice declaration, the likelihood mapping, the transition mapping, and the prior beliefs are combined to form a BTAI3MF model. The BTAI3MF framework can be used for the creation of new models by simply declaring the variables it contains, and the framework performs the inference process automatically.

B. Graphical user interface
The paper presents a graphical user interface that is used to analyse the

---

**Summary Statistics:**
- Input: 12,676 words (77,816 chars)
- Output: 1,386 words
- Compression: 0.11x
- Generation: 67.7s (20.5 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
