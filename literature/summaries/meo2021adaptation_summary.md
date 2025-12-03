# Adaptation through prediction: multisensory active inference torque control

**Authors:** Cristian Meo, Giovanni Franzese, Corrado Pezzato, Max Spahn, Pablo Lanillos

**Year:** 2021

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [meo2021adaptation.pdf](../pdfs/meo2021adaptation.pdf)

**Generated:** 2025-12-03 05:13:56

---

**Overview/Summary**
The paper presents a novel approach to robotic control based on the active inference (AIF) framework for learning and controlling the dynamics of a robot arm in an open-ended environment. The authors propose a new AIF controller that uses a multimodal variational autoencoder (VAE) to learn the internal states of the system, which is used to predict the future sensory data and then use this prediction to control the robot's actions. In addition, the paper also presents a mental simulation approach for the AIF controller, where the entire experiment can be simulated in the absence of any real sensory data. The authors demonstrate that the proposed AIF controller outperforms the existing model-based impedance controller (MPC) and the GP-trained end-effector reconstruction controller in both the normal and imagined simulations. 

**Key Contributions/Findings**
The main contributions of this paper are two-fold. First, the authors present a new AIF controller based on the multimodal VAE that can be used for learning and controlling the dynamics of an open-ended robot arm. Second, they show that the proposed AIF controller outperforms the MPC and the GP-trained end-effector reconstruction controller in both the normal and imagined simulations.

**Methodology/Approach**
The authors propose a new AIF controller based on the multimodal VAE. The AIF framework is a probabilistic approach to control the dynamics of an open-ended system, which can be used for learning and controlling the dynamics of a robot arm. In this paper, the authors use the AIF framework to predict the future sensory data and then use this prediction to control the actions of the robot's end-effector. The multimodal VAE is trained by using a dataset that contains paired joint values and images. The authors also present a mental simulation approach for the AIF controller, where the entire experiment can be simulated in the absence of any real sensory data. 

**Results/Data**
The authors use the 80% of the GP training set as the training set to train the multimodal VAE. The remaining 20% is used as the test set. In the normal simulation, the AIF controller outperforms the MPC and the GP-trained end-effector reconstruction controller in terms of both the joint position error and the image reconstruction error. In the imagined simulation, the errors converge faster to zero than in the normal regime because it does not need to accommodate the real dynamics of the robot. 

**Limitations/Discussion**
The authors do not discuss any limitations or future work in this paper.

**References**

(

---

**Summary Statistics:**
- Input: 7,582 words (49,251 chars)
- Output: 406 words
- Compression: 0.05x
- Generation: 26.8s (15.2 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
