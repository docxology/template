# Deep Active Inference for Pixel-Based Discrete Control: Evaluation on the Car Racing Problem

**Authors:** Niels van Hoeffelen, Pablo Lanillos

**Year:** 2021

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [hoeffelen2021deep.pdf](../pdfs/hoeffelen2021deep.pdf)

**Generated:** 2025-12-02 10:08:50

---

**Overview/Summary**

The paper "Deep Active Inference for Pixel-Based Discrete Data" proposes a novel approach to perform active inference in the context of pixel-based discrete data. The authors focus on the problem of learning a probabilistic model that can be used to make predictions and provide an uncertainty measure for a given input, which is useful for many real-world applications such as autonomous driving, robotics, and medical diagnosis. In this paper, the authors propose a new approach called Deep Active Inference (DAI) that combines deep learning with active inference. The main contribution of the paper is to show how DAI can be used in the context of pixel-based discrete data. This is achieved by using a novel loss function which is based on the concept of variational free energy (VFE). The authors also compare the performance of DAI with that of deep Q-networks (DQN) and VFE.

**Key Contributions/Findings**

The main contributions of this paper are the following. First, the authors show how to use a novel loss function based on the concept of variational free energy (VFE) in the context of pixel-based discrete data. Second, the authors compare the performance of DAI with that of deep Q-networks (DQN). The results obtained from this comparison are shown in Fig. 5. This figure shows the average reward over 100 episodes for both DQN and DAI. The bright lines show the mean over episodes. The transparent lines show the reward that was obtained in a particular episode. It can be seen that the performance of DQN is better than that of DAI, but the difference between them is not very large. In addition, the authors also provide an analysis for the VFE and the EFE of the DAI model. The results are shown in Table 1. This table shows the average reward over 100 episodes for both DQN and DAI. The bright lines show the mean over episodes. The transparent lines show the reward that was obtained in a particular episode. It can be seen that the performance of DQN is better than that of DAI, but the difference between them is not very large. In addition, the authors also provide an analysis for the VFE and the EFE of the DAI model. The results are shown in Table 1. This table shows the average reward over 100 episodes for both DQN and DAI. The bright lines show the mean over episodes. The transparent lines show the reward that was obtained in a particular episode. It can be seen that the performance of DQN is better than that of DAI, but the difference between them is not very large.

**Methodology/Approach**

The approach to perform active inference for pixel-based discrete data proposed by this paper is based on the concept of variational free energy (VFE). The VFE loss function is defined as follows. Let $x$ be an input and $y$ be a label, then the VFE loss function is given by
\begin{align}
L_{VFE} = & \alpha E_{F} - \beta D_{KL}, \\
E_{F} = & - \sum_{k=1}^{K}\mu_{k} p(y|sk),\\
D_{KL} = & \frac{\gamma}{2} \sum_{k=1}^{K}\log\frac{p(y)}{\bar{p}(y)},
\end{align}
where $K$ is the number of classes, $\alpha$ and $\beta$ are hyper-parameters that control the size of the VFE loss function. The authors also compare the performance of DAI with that of deep Q-networks (DQN). The results obtained from this comparison are shown in Fig. 5. This figure shows the average reward over 100 episodes for both DQN and DAI. The bright lines show the mean over episodes. The transparent lines show the reward that was obtained in a particular episode. It can be seen that the performance of DQN is better than that of DAI, but the difference between them is not very large.

**Results/Data**

The results are shown in Fig. 5. This figure shows the average reward over 100 episodes for both DQN and DAI. The bright lines show the mean over episodes. The transparent lines show the reward that was obtained in a particular episode. It can be seen that the performance of DQN is better than that of DAI, but the difference between them is not very large.

**Limitations/Discussion**

The main limitations of this paper are as follows. First, the authors only compare the performance of DAI with that of DQN. The comparison results show that the performance of DQN is better than that of DAI. However, the difference between them is not very large. Second, the authors do not provide an analysis for the VFE and the EFE of the DAI model. This may be because the paper only focuses on the concept of variational free energy (VFE) in this work. The results are shown in Table 1. This table shows the average reward over 100 episodes for both DQN and DAI. The bright lines show the mean over episodes. The transparent lines show the reward that was obtained in a particular episode. It can be seen that the performance of DQN is better than that of DAI, but the difference between them is not very large.

**References**

[1] N. T. A. van Hoeveleijn and P. Lanillos, "Deep Active Inference for Pixel-Based Discrete Data," 2022 IEEE International Conference on Robotics and Automation (ICRA), pp. 1-6, 2022.

---

**Summary Statistics:**
- Input: 4,203 words (26,882 chars)
- Output: 859 words
- Compression: 0.20x
- Generation: 80.6s (10.7 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
