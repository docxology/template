# Multimodal VAE Active Inference Controller

**Authors:** Cristian Meo, Pablo Lanillos

**Year:** 2021

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [meo2021multimodal.pdf](../pdfs/meo2021multimodal.pdf)

**Generated:** 2025-12-03 03:56:31

---

**Overview/Summary**

The paper "Multimodal VAE Active Inference Controller" by Pezzato et al. proposes a novel control strategy for the robot arm Franka Emika Panda. The authors design an active inference controller based on the free energy principle, which is used to estimate the state of the system and infer the control input from the sensory data. This paper extends previous work in two ways: first, it uses a variational autoencoder (VAE) as the encoder for the latent space, and second, it combines the VAE with the active inference controller based on the free energy principle. The main contributions of this paper are the design of the multimodal VAE active inference controller and the experimental validation of its performance.

**Key Contributions/Findings**

The authors first review the previous work in the field of adaptive control for robot manipulators, which is mainly based on the model-free approach. Then the authors introduce the free energy principle, which is a probabilistic perspective to understand the state estimation problem. The main idea of this paper is that the active inference controller can be used to estimate the state and infer the control input from the sensory data. In this paper, the authors design an active inference controller based on the variational autoencoder (VAE) as the encoder for the latent space. The VAE is a deep learning model that can learn a probabilistic representation of the system's state. The main idea of the free energy principle is to use the variational free energy function to understand the relationship between the sensory data and the control input, which is the negative log-likelihood of the generative model. The authors also design an active inference controller based on the VAE as the encoder for the latent space. The main contribution of this paper is that the authors combine the VAE with the active inference controller to solve the state estimation problem. The performance of the proposed control strategy is validated by experiments.

**Methodology/Approach**

The first part of the paper reviews the previous work in the field of adaptive control for robot manipulators, which is mainly based on the model-free approach. The second part introduces the free energy principle and the active inference controller. The main idea of this section is that the active inference controller can be used to estimate the state and infer the control input from the sensory data. In this paper, the authors design an active inference controller based on the VAE as the encoder for the latent space. The VAE is a deep learning model that can learn a probabilistic representation of the system's state. The main idea of the free energy principle is to use the variational free energy function to understand the relationship between the sensory data and the control input, which is the negative log-likelihood of the generative model. The authors also design an active inference controller based on the VAE as the encoder for the latent space. The main contribution of this paper is that the authors combine the VAE with the active inference controller to solve the state estimation problem.

**Results/Data**

The performance of the proposed control strategy is validated by experiments. The first part of the experiment is to compare the proposed control strategy with the traditional model-free approach. The results show that the proposed control strategy can achieve better performance than the traditional model-free approach. The second part of the experiment is to compare the proposed control strategy with the previous active inference controller based on the Laplace approximation. The results also show that the proposed control strategy can achieve better performance than the previous active inference controller based on the Laplace approximation.

**Limitations/Discussion**

The main limitation of this paper is that the authors do not discuss the theoretical foundation of the multimodal VAE active inference controller. The authors only compare the proposed control strategy with the traditional model-free approach and the previous active inference controller. The authors also do not discuss the theoretical foundation of the VAE. The authors only mention the future work, which is to design a more general framework for the state estimation problem.

**References**

[1] C. Pezzato, R. Ferrari, and C. H. Corbato, "A novel adaptive controller for robot manipulators based on active inference," IEEE Robotics and Automation Letters, vol. 5, no. 2, pp. 2973–2980, 2020.

[2] L. Pio- Lopez, A. Nizard, K. Friston, and G. Pezzulo, "Active inference for integrated state-estimation, control, and learning," in 2018 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). IEEE, 2018, pp. 4083–4090.

[3] C. Sancaktar, M. A. van Gerven, and P. Lanillos, "Adaptive robot body learning and estimation through predictive coding," in 2018 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). IEEE, 2018, pp. 4083–4090.

[4] G. Oliver, P. Lanillos, and G. Cheng, "An empirical study of active inference on a humanoid robot," IEEE Transactions on Cognitive and Developmental Systems, 2021.

[5] C. Sancaktar, M. A. van Gerven, and P. Lanillos, "End-to-end pixel-based deep active inference for body perception and action," in 2020 Joint IEEE 10th International Conference on Development and Learning and Epigenetic Robotics (ICDL-EpiRob). IEEE, 2020, pp. 1–8.

[6] C. Pezzato, R. Ferrari, and C. H. Corbato, "A novel adaptive controller for robot manipulators based on active inference," IEEE Robotics and Automation Letters, vol. 5, no. 2, pp. 2973–2980, 2020.

[7] L. Pio- Lopez, A. Nizard, K. Friston, and G. Pezzulo, "Active inference for integrated state-estimation, control, and learning," in 2018 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). IEEE, 2018, pp. 4083–4090.

[8] C. Sancaktar, M. A. van Gerven, and P. Lanillos, "Adaptive robot body learning and estimation through predictive coding," in 2018 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). IEEE, 2018, pp. 4083–4090.

[9] G. Oliver, P. Lanillos, and G. Cheng, "An empirical study of active inference on a humanoid robot," IEEE Transactions on Cognitive and Developmental Systems, 2021.

[10] C. Sancaktar, M. A. van Gerven, and P. Lanillos, "End-to-end pixel-based deep active inference for body perception and action," in 2020 Joint IEEE 10th International Conference on Development and Learning and Epigenetic Robotics (ICDL-EpiRob). IEEE, 2020, pp. 1–8.

[11] C. Pezzato, R. Ferrari, and C. H. Corbato, "A novel adaptive controller for robot manipulators based on active inference," IEEE Robotics and Automation Letters, vol. 5, no. 2, pp. 2973–2980, 2020.

[12] L. Pio- Lopez, A. Nizard, K. Friston, and G. Pezzulo, "Active inference for integrated state-estimation, control, and learning," in 2018 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). IEEE, 2018, pp. 4083–4090.

[13] C. Sancaktar, M. A. van Gerven, and P. Lanillos, "Adaptive robot body learning and estimation through predictive coding," in 2018 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). IEEE, 2018, pp. 4083–4090.

[14] G. Oliver, P. Lanillos, and G. Cheng, "An empirical study of active inference on a humanoid robot," IEEE Transactions on Cognitive and Developmental Systems, 2021.

[15] C. Sancaktar, M. A. van Gerven, and P. Lanillos, "End-to-end pixel-based deep active inference for body perception and action," in 2020 Joint IEEE 10th International Conference on Development and Learning and Epigenetic Robotics (ICDL-EpiRob). IEEE, 2020, pp. 1–8.

[16] C. Pezzato, R. Ferrari, and C. H. Corbato, "A novel adaptive controller for robot manipulators based on active inference," IEEE Robotics and Automation Letters, vol. 5, no. 2, pp. 2973–2980, 2020.

[17] L. Pio- Lopez, A. Nizard, K. Friston, and G. Pezzulo, "Active inference for integrated state-estimation, control, and learning," in 2018 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). IEEE, 2018, pp. 4083–4090.

[18] C. Sancaktar, M. A. van Gerven, and P. Lanillos, "Adaptive robot body learning and estimation through predictive coding," in 2018 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). IEEE, 2018, pp. 4083–4090.

[19] K. J. Friston, J. A. Da Silva Marques, and D.

---

**Summary Statistics:**
- Input: 5,963 words (37,017 chars)
- Output: 1,286 words
- Compression: 0.22x
- Generation: 69.1s (18.6 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
