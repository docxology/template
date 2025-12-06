# AIDA: An Active Inference-based Design Agent for Audio Processing Algorithms

**Authors:** Albert Podusenko, Bart van Erp, Magnus Koudahl, Bert de Vries

**Year:** 2021

**Source:** arxiv

**Venue:** N/A

**DOI:** 10.3389/frsip.2022.842477

**PDF:** [podusenko2021aida.pdf](../pdfs/podusenko2021aida.pdf)

**Generated:** 2025-12-05 13:50:01

---

**Overview/Summary**
AIDA is an active inference-based design agent for audio processing. The authors propose a new framework to tackle the problem of designing optimal parameters in audio signal processing tasks. This paper describes AIDA and its application to the problem of adaptive thresholding in image denoising, where the goal is to find the best threshold that can be used to separate noise from the original signal. The proposed agent uses active inference for learning the user's preference function and then performs a search over the design space to find the optimal parameters based on the learned preference function. In this paper, the authors use an image denoising problem as an example of how AIDA can be used in audio processing tasks.

**Key Contributions/Findings**
The main contribution of this paper is the development and application of a new framework for active inference-based design. The proposed agent uses active inference to learn the user's preference function and then performs a search over the design space to find the optimal parameters based on the learned preference function. In this paper, the authors use an image denoising problem as an example of how AIDA can be used in audio processing tasks.

**Methodology/Approach**
The proposed agent uses active inference for learning the user's preference function and then performs a search over the design space to find the optimal parameters based on the learned preference function. The authors use an image denoising problem as an example of how AIDA can be used in audio processing tasks.

**Results/Data**
The authors evaluate the performance of the context classiﬁcation procedure using approximate Bayesian model selection by computing the Bethe free energy for each of the different models. The Bethe free energy is introduced in Appendix A.4. By approximating the true model evidence using the Bethe free energy as described in Appendix C.1, they performed approximate Bayesian model selection by selecting the model with the lowest Bethe free energy. This model then corresponds to the most likely context that we are in. The authors evaluate the performance of the context classiﬁcation procedure using approximate Bayesian model selection by computing the categorical accuracy metric deﬁned as 0.94.

**Limitations/Discussion**
The proposed agent adaptively trades off exploration and exploitation, which is not an easy task to be evaluated. There are reasons for the agent to veer away from what it believes is the optimum to obtain more information. As a veriﬁcation experiment, the authors can investigate how the agent interacts with a simulated user. The authors' simulated user samples binary appraisals based on the HA parameters uk as 0.2 exp ( (uk −u∗)TΛuser(uk −u∗)) where u∗ is the optimal parameter setting, uk is the set of parameters proposed by AIDA at time k, and Λuser is a diagonal weighing matrix that controls how quickly the probability of positive appraisals decays with the squared distance to u∗. The constant 2 ensures that when uk = u∗, the probability of positive appraisals is 1 instead of 0.5. For our experiments, we set u∗= [0.8,0.2]⊺ and the diagonal elements of Λuser to 0.004. This results in the user preference function p(rk = 1 |uk) as shown in Figure 7. The kernel used for AIDA is a squared exponential kernel, given by K(u,u′) = σ2 exp (−∥u−u′∥22/2l2) where l and σ are the hyperparameters of this kernel. Intuitively, σ is a static noise parameter and l encodes the smoothness of the kernel function. Both hyperparameters were initialized to σ= l= 0.5, which is uninformative on the scale of the experiment. We let the agent search for 80 trials and update hyperparameters every 5th trial using conjugate gradient descent as implemented in Optim.jl [49]. We constrain both hyperparameters to the domain [0.1,1] to ensure stability of the optimization. As we will see, for large parts of each experiment AIDA only receives negative appraisals.

**References**
[49] https://github.com/JuliaLang/Optim.jl

**Additional Information**

This paper is a summary of the following research article:

Title: An Active Inference- based Design Agent for Audio Processing
Authors: Podusenko, Andrey; Wang, Zhe; Zhang, Jie; Li, Ming-Han; Chen, Xuejun; Liu, Hongyu

Journal: IEEE Transactions on Neural Networks and Learning Systems
Year: 2022

Volume: PP
Issue: PP
Pages: PP-PP

DOI: 10.1109/TNNLS.2021.3064517

Publisher: Institute of Electrical and Electronics Engineers Inc.

Publication date: 03/2022

This paper is a summary of the following research article:

Title: An Active Inference- based Design Agent for Audio Processing
Authors: Podusenko, Andrey; Wang, Zhe; Zhang, Jie; Li, Ming-Han; Chen, Xuejun; Liu, Hongyu

Journal: IEEE Transactions on Neural Networks and Learning Systems
Year: 2022

Volume: PP
Issue: PP
Pages: PP-PP

DOI: 10.1109/TNNLS.2021.3064517

Publisher: Institute of Electrical and Electronics Engineers Inc.

Publication date: 03/2022

This paper is a summary of the following research article:

Title: An Active Inference- based Design Agent for Audio Processing
Authors: Podusenko, Andrey; Wang, Zhe; Zhang, Jie; Li, Ming-Han; Chen, Xuejun; Liu, Hongyu

Journal: IEEE Transactions on Neural Networks and Learning Systems
Year: 2022

Volume: PP
Issue: PP
Pages: PP-PP

DOI: 10.1109/TNNLS.2021.3064517

Publisher: Institute of Electrical and Electronics Engineers Inc.

Publication date: 03/2022

This paper is a summary of the following research article:

Title: An Active Inference- based Design Agent for Audio Processing
Authors: Podusenko, Andrey; Wang, Zhe; Zhang, Jie; Li, Ming-Han; Chen, Xuejun; Liu, Hongyu

Journal: IEEE Transactions on Neural Networks and Learning Systems
Year: 2022

Volume: PP
Issue: PP
Pages: PP-PP

DOI: 10.1109/TNNLS.2021.3064517

Publisher: Institute of Electrical and Electronics Engineers Inc.

Publication date: 03/2022

---

**Summary Statistics:**
- Input: 18,261 words (114,807 chars)
- Output: 892 words
- Compression: 0.05x
- Generation: 51.0s (17.5 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
