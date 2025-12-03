# Compositional Visual Generation and Inference with Energy Based Models

**Authors:** Yilun Du, Shuang Li, Igor Mordatch

**Year:** 2020

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [du2020compositional.pdf](../pdfs/du2020compositional.pdf)

**Generated:** 2025-12-03 06:04:36

---

**Overview/Summary**
The paper proposes a novel generative model called Energy-Based Model (EBM) for the task of compositional visual generation and inference. Unlike previous works that only focus on generating an image from a single class, EBM can generate an image conditioned on the conjunction or disjunction of two classes. The authors also provide a theoretical analysis on the partition function of the model. They further show that the EBM is able to generalize well to different out-of-distribution datasets and demonstrate its effectiveness in a variety of scenarios.

**Key Contributions/Findings**
The main contributions of this paper are: 1) the introduction of the novel disjunction operator for the conjunction of two probability distributions, which can be used as a building block for the compositionality of visual generation; 2) the design and training of the EBM that is able to generate an image conditioned on the conjunction or disjunction of two classes. The authors also provide a theoretical analysis on the partition function of the model.

**Methodology/Approach**
The authors propose a novel generative model called Energy-Based Model (EBM). The energy-based model is trained with Langevin dynamics and can be used for both generation and inference. The EBM is able to generate an image conditioned on the conjunction or disjunction of two classes. The authors also provide a theoretical analysis on the partition function of the model.

**Results/Data**
The authors use different number of sampling steps in training the EBM. They compare the performance of the EBM with Resnet and PixelCNN. Table 3 shows that the inference in the EBM is able to generalize well to different out-of-distribution datasets such as Color, Light, Size and Type. A large number of sampling steps also improves performance, with a large number of steps of training exhibiting both better training accuracy and generalization performance.

**Limitations/Discussion**
The authors note that in scenarios where the partition functions are different, their deﬁned disjunction operator does not fail drastically. If two unnormalized probability distributions have partition function values of w1 and w2 then models will be sampled with proportion  w1
w1+w2
and  w2
w1+w2
, which is not a dramatic failure in the disjunction. The authors also note that other generative models do not sample well under gradient based MCMC. (a) Samples Generated from Langevin Sampling on PixelCNN++ model from [Salimans et al., 2017]. (b) Samples Generated from Autoregressive Sam-pling on PixelCNN++ model from [Salimans et al., 2017]. Figure A3: Comparison on samples generated from different sampling scenes on PixelCNN++ model from [Salimans et al., 2017]. We note that Langevin sampling, while not making realistic samples, generates higher likelihood samples than those from autoregressive sampling. The authors speculate that EBMs are able to ﬁt the MCMC sampling procedure better than other models since EBMs are trained with MCMC inference and are thus less susceptible to adversarial modes.

**Models**
3x3 conv2d, 64
ResBlock down 64
ResBlock down 128
ResBlock down 256
Global Mean Pooling
Dense →1
(a) The model architecture of EBM used on the Mujoco Scenes Dataset. (b) The model architecture of baseline model for joint generation (section A.1.2). Figure A4: Architecture of models on different datasets.

The authors train two types of EBM, one with the same architecture as Resnet and the other with a similar architecture to PixelCNN++. The architectures are shown in Figure A4a and b. In particular, for the Mujoco Scenes images, the authors use 3x3 conv2d, 64, ResBlock down 64, ResBlock down 128, ResBlock down 256, Global Mean Pooling, Dense →1; for the Celeba 128x128, the authors use 3x3 conv2d, 64, ResBlock down 64, ResBlock down 128, ResBlock down 128, ResBlock up 256, ResBlock up 128, ResBlock up 64, ResBlock up 64, 3x3 conv2d, 3. The EBM is trained with Langevin dynamics and can be used for both generation and inference. The authors also provide a theoretical analysis on the partition function of the model.

**References**
[Du and Mordatch, 2019]
[Oord et al., 2016]
[Salimans et al., 2017]

---

**Summary Statistics:**
- Input: 7,889 words (50,817 chars)
- Output: 652 words
- Compression: 0.08x
- Generation: 36.9s (17.7 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
