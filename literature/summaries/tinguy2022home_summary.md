# Home Run: Finding Your Way Home by Imagining Trajectories

**Authors:** Daria de Tinguy, Pietro Mazzaglia, Tim Verbelen, Bart Dhoedt

**Year:** 2022

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [tinguy2022home.pdf](../pdfs/tinguy2022home.pdf)

**Generated:** 2025-12-03 06:47:21

---

**Overview/Summary**

The paper "Home Run: Finding Your Way Home by Imagining" is a research work in the field of artificial intelligence and robotics that proposes a new approach for an agent to learn how to navigate in a grid world. The authors use a novel idea called "home run" where the agent imagines its way home from any location in the environment, which is different from the traditional method of learning a map by moving around. In this paper, the authors first train a low-level perception model that can reconstruct an image based on the current state and action taken. Then they use a high-level topological graph representation to represent the agent's experience during the interaction with the environment. The key contributions of the work are the design of the low level perception model and the high level topological map, which is used for the agent to imagine its way home.

**Key Contributions/Findings**

The main contribution of this paper is that it proposes a new approach for an agent to learn how to navigate in a grid world. The authors first train a low-level perception model that can reconstruct an image based on the current state and action taken. Then they use a high-level topological graph representation, linking pose and hidden state representation to a location in the map. In this paper, the authors use a novel idea called "home run" where the agent imagines its way home from any location in the environment, which is different from the traditional method of learning a map by moving around. The key findings are that the agent can learn how to navigate in the grid world using the proposed approach and this new approach has some advantages over the traditional one.

**Methodology/Approach**

The authors first train a low-level perception model that can reconstruct an image based on the current state and action taken. Then they use a high-level topological graph representation, linking pose and hidden state representation to a location in the map. The detailed parameters of the models are listed in Table 2. The training data is composed of sequences of action-observation pairs which were collected by human demonstrations of interaction with the environment. The agent was made to move around from rooms to room, circle around and turn randomly. About 12000 steps were recorded in 39 randomly created environments having different room size, number of rooms, open door emplacements and floor colors, as well as the agent having a random starting pose and orientation. 2/3 of the data were used for training and 1/3 for validation. Then a fully novel environment was used for testing.

**Results/Data**

The low level perception pipeline was trained end to end on time sequences of 10 steps using stochastic gradient descent with the minimization of the free energy loss function: FE = ∑[DKL[Q(st|st−1,at−1,ot)||P(st|st−1,at−1)] −EQ(st)[log P(ot|st)]. The loss consists of a negative log likelihood part penalizing the error on reconstruction, and a KL-divergence between the posterior and the prior distributions on a training sequence. We trained the model for 300 epochs using the ADAM optimizer with a learning rate of 1·10–4.

**Limitations/Discussion**

The authors point out that the agent can learn how to navigate in the grid world using the proposed approach, which is different from the traditional one. The new approach has some advantages over the traditional one. However, there are also some limitations and future work. For example, the training of the low level perception model needs a large amount of data, and the agent can only imagine its way home in a fully novel environment. In addition, the authors do not provide an evaluation on the performance of the high-level topological map.

**References**

[1] M. Chevalier-Boisvert, L. Willems, and S. Pal, "Minimalistic grid world environment for openai gym," https://github.com/maximecb/gym-minigrid, 2018.
[2] M. Milford, A. Jacobson, Z. Chen, and G. Wyeth, RatSLAM: Using Models of Rodent Hippocampus for Robot Navigation and Beyond. Cham: Springer International Publishing, 2016, pp. 467–485.

[3] M. Chevalier-Boisvert, L. Willems, and S. Pal, "Minimalistic grid world environment for openai gym," https://github.com/ maximecb/gym-minigrid, 2018.
[4] V. Edvardsen, A. Bicanski, and N. Burgess, "Navigating with grid and place cells in cluttered environments," Hippocampus, vol. 30, pp. 220–232, 03 2012.

[5] P. Mazzaglia, T. Verbelen, and B. Dhoedt, "Contrastive active inference," in Advances in Neural Information Processing Systems, A. Beygelzimer, Y. Dauphin, P. Liang, and J. W. Vaughan, Eds., 2021.

[6] M. Milford, A. Jacobson, Z. Chen, and G. Wyeth, RatSLAM: Using Models of Rodent Hippocampus for Robot Navigation and Beyond. Cham: Springer International Publishing, 2016, pp. 467–485.
[7] D. P. Kingma and J. Ba, "Adam: A method for stochastic optimization." [Online]. Available: https://arxiv.org/abs/1412.6980

**Additional Details**

The low level perception pipeline was trained end to end on time sequences of 10 steps using the ADAM optimizer with a learning rate of 1·10–4. The high level topological map is implemented as a topological graph representation, linking pose and hidden state representation to a location in the map. Here we reuse the LatentSLAM implementation [6] consisting of pose cells, local view cells and an experience map. The detailed parameters are listed in Table 2.

The low level perception pipeline was trained end to end on time sequences of 10 steps using stochastic gradient descent with the minimization of the free energy loss function: FE = ∑[DKL[Q(st|st−1,at−1,ot)||P(st|st−1,at−1)] −EQ(st)[log P(ot|st)]. The loss consists of a negative log likelihood part penalizing the error on reconstruction, and a KL-divergence between the posterior and the prior distributions on a training sequence. We trained the model for 300 epochs using the ADAM optimizer with a learning rate of 1·10–4.

The high level topological map is implemented as a topological graph representation, linking pose and hidden state representation to a location in the map. Here we reuse the LatentSLAM implementation [6] consisting of pose cells, local view cells and an experience map. The detailed parameters are listed in Table 2.

The authors point out that the agent can learn how to navigate in the grid world using the proposed approach, which is different from the traditional one. The new approach has some advantages over the traditional one. However, there are also some limitations and future work. For example, the training of the low level perception model needs a large amount of data, and the agent can only imagine its way home in a fully novel environment. In addition, the authors do not provide an evaluation on the performance of the high-level topological map.

**References**

[1] M. Chevalier-Boisvert, L. Willems, and S. Pal, "Minimalistic grid world environment for openai gym," https://github.com/ maximecb/gym-minigrid, 2018.
[2] M. Milford, A. Jacobson, Z. Chen, and G. Wyeth, RatSLAM: Using Models of Rodent Hippocampus for Robot Navigation and Beyond. Cham: Springer International Publishing, 2016, pp. 467–485.

[3] M. Chevalier-Boisvert, L. Willems, and S. Pal, "Minimalistic grid world environment for openai gym," https://github.com/ maximecb/gym-minigrid, 2018.
[4] V. Edvardsen, A. Bicanski, and N. Burgess, "Navigating with grid and place cells in cluttered environments," Hippocampus, vol. 30, pp. 220–232, 03 2012.

[5] P. Mazzaglia, T. Verbelen, and B. Dhoedt, "Contrastive active inference," in Advances in Neural Information Processing Systems, A. Beygelzimer, Y. Dauphin, P. Liang, and J. W. Vaughan, Eds., 2021.

[6] M. Milford, A. Jacobson, Z. Chen, and G. Wyeth, RatSLAM: Using Models of Rodent Hippocampus for Robot Navigation and Beyond. Cham: Springer International Publishing, 2016, pp. 467–485.
[7] D. P. Kingma and J. Ba, "Adam: A method for stochastic optimization." [Online]. Available: https://arxiv.org/abs/1412.6980

---

**Summary Statistics:**
- Input: 4,407 words (27,971 chars)
- Output: 1,234 words
- Compression: 0.28x
- Generation: 64.9s (19.0 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
