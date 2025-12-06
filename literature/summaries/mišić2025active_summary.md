# An Active Inference Model of Covert and Overt Visual Attention

**Authors:** Tin Mišić, Karlo Koledić, Fabio Bonsignorio, Ivan Petrović, Ivan Marković

**Year:** 2025

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [mišić2025active.pdf](../pdfs/mišić2025active.pdf)

**Generated:** 2025-12-05 12:26:03

---

**Overview/Summary**
The paper presents a new computational model of covert and voluntary saccades based on active inference. The authors argue that the traditional view of covert attention as a "spotlight" is not sufficient to explain the variety of phenomena observed in the human brain, and propose an alternative approach using the free energy principle (FEP) [30]. They use this framework to model both covert and voluntary saccades, which are typically considered distinct forms of eye movement. The authors first discuss the FEP as a unified theory for understanding brain function, then describe their new model, and finally present results from an active inference implementation in a simulated environment.

**Key Contributions/Findings**
The main contribution of this paper is the development of a new computational model that can explain both covert and voluntary saccades. The authors show that the FEP provides a framework for understanding how the brain generates its own predictions, which are then compared to the sensory data it receives. They also present an active inference implementation in a simulated environment, which they use to test their model.

**Methodology/Approach**
The authors first discuss the FEP as a unified theory for understanding brain function. The FEP is based on the idea that the brain's goal is to minimize its free energy [29]. They then describe how this framework can be used to understand the generation of predictions in the brain, and finally present an active inference implementation in a simulated environment.

**Results/Data**
The authors first discuss the FEP as a unified theory for understanding brain function. The FEP is based on the idea that the brain's goal is to minimize its free energy [29]. They then describe how this framework can be used to understand the generation of predictions in the brain, and finally present an active inference implementation in a simulated environment.

**Limitations/Discussion**
The authors discuss the limitations of their approach. The main limitation is that the optimization of system dynamics precisions ˜Πµ is left for future work. They also mention that the gradient of the visual generative model is the gradient of the VAE decoder computed by backpropagation, and that the inverse mapping from sensory data to actions is a "hard problem" [35]. However, it is fairly simple in their case: the centroid of the color red is converted into pitch and yaw angles (assuming we know the intrinsic parameters of the camera model). The authors also mention that the optimization of system dynamics precisions ˜Πµ is left for future work, and they are assumed to be constant. They also mention that the gradient of the visual generative model is the gradient of the VAE decoder computed by backpropagation, and that the inverse mapping from sensory data to actions is a "hard problem" [35]. However, it is fairly simple in their case: the centroid of the color red is converted into pitch and yaw angles (assuming we know the intrinsic parameters of the camera model).

**References**
[29] K. Friston, J. Kilner, and L. Harrison, 2006. A free energy principle for the brain. Journal of Physiology-Paris, 100(2), 70–87.
[30] K. Friston, 2010. The free-energy principle: a unified theory? Nature Reviews Neuroscience, 11(2), 127–138.
[35] K. J. Friston, J. Daunizeau, J. Kilner, and S. J. Kiebel, 2010. Action and behavior: a free- energy formulation. Biology Cybernetics, 102(3), 227–260.

**Appendix**
The authors first discuss the implementation of gradients. The gradients with respect to beliefs, action and sensory data given in (11) and (13) depend on the different imple-mentations of system dynamics, generative models, sensory precisions and the type of sensory data: • ∂ ˜f
∂ ˜µ  : The gradient of the system dynamics function defined in (10) w. r. t. the belief µ is fairly simple, seeing as it is defined as an affine transformation of the belief. • ∂˜g
∂ ˜µ  : The gradients of the generative models w. r. t. the belief for the proprioceptive and interoceptive models are simple identity matrices. However, the gradient of the visual generative model is the gradient of the VAE decoder computed by backpropagation. • ∂ ˜Πs
∂ ˜µ  : Since the sensory precision matrix is assumed to be diagonal, this greatly simplifies calculation of the gradients πi
∂µ for each pixel i from the individual precision functions πi(µ, s). The sensory precision gradient ˜Πs
∂ ˜µ
is a tensor of shape L × L × M. • ∂ ˜Πµ
∂ ˜µ  : The optimization of system dynamics precisions ˜Πµ is left for future work, and they are assumed to be constant. Their gradients are therefore zero. • ∂˜s
∂a  : The inverse mapping from sensory data to actions is generally considered a "hard problem" [35]. However, it is fairly simple in their case: the centroid of the color red is converted into pitch and yaw angles (assuming we know the intrinsic parameters of the camera model). • ∂˜s
∂ ˜µ  : The gradient is calculated in a way similar to ˜Πs
∂ ˜µ,
with the gradient being a tensor of shape L × L × L. The authors also mention that the optimization of system dynamics precisions ˜Πµ is left for future work, and they are assumed to be constant. They also mention that the gradient of the visual generative model is the gradient of the VAE decoder computed by backpropagation, and that the inverse mapping from sensory data to actions is a "hard problem" [35]. However, it is fairly simple in their case: the centroid of the color red is converted into pitch and yaw angles (assuming we know the intrinsic parameters of the camera model).

**References**
[29] K. Friston, 2010. The free-energy principle: a unified theory? Nature Reviews Neuroscience, 11(2), 127–138.
[30] K. Friston, J. Kilner, and L. Harrison, 2006. A free energy principle for the brain. Journal of Physiology-Paris, 100(2), 70–87.
[35] K. J. Friston, J. Daunizeau, J. Kilner, and S. J. Kiebel, 2010. Action and behavior: a free-energy formulation. Biology Cybernetics, 102(3), 227–260.

---

**Summary Statistics:**
- Input: 5,761 words (35,346 chars)
- Output: 984 words
- Compression: 0.17x
- Generation: 50.3s (19.6 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
