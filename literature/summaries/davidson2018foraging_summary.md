# Foraging as an evidence accumulation process

**Authors:** Jacob D. Davidson, Ahmed El Hady

**Year:** 2018

**Source:** arxiv

**Venue:** N/A

**DOI:** 10.1371/journal.pcbi.1007060

**PDF:** [davidson2018foraging.pdf](../pdfs/davidson2018foraging.pdf)

**Generated:** 2025-12-05 11:34:31

---

**Overview/Summary**

The paper "Foraging as an evidence accumulation process" by J.D. Dyer and A.E. Hanks provides a mathematical model of the foraging behavior in animals, which is inspired by the models used in systems neuroscience. The authors consider an agent that calculates a moving average of the available energy in the environment and makes noisy patch decisions according to the receipt of food rewards and a decision "strategy", which can be adapted to optimize for the characteristics of the foraging environment. This work provides a step towards establishing a unifying framework tying concepts from systems neuroscience, ecology, and behavioral economics to study naturalistic decision making.

**Key Contributions/Findings**

The main contributions in this paper are the development of the mathematical model and the results of the simulations that demonstrate the behavior of the forager with different strategies. The authors show that the density-adaptive strategy is optimal when the environment is predictable, but sub-optimal when it is uncertain. They also provide a step towards establishing a unifying framework tying concepts from systems neuroscience, ecology, and behavioral economics to study naturalistic decision making.

**Methodology/Approach**

The authors use the drift-diffusion modeling (FDDM) framework that has been used in systems neuroscience. The FDDM is based on the idea of an agent that makes a series of decisions about whether or not to stay at a patch, and the receipt of food rewards provides information about the environment. The forager has memory of its previous foraging experience through the estimate of available energy. A related question is how foraging decisions are affected when the environment changes over time, which for example can lead to biases from contrast eﬀects. The speed of environmental fluctuations aﬀects which strategy is optimal, and the relative importance of taking diﬀerent adaptive strategies depends on the dynamics and predictability of the environment.

**Results/Data**

The authors show that the density-adaptive strategy is optimal when the foraging environment is predictable, but sub-optimal when it is uncertain. They also provide a step towards establishing a unifying framework tying concepts from systems neuroscience, ecology, and behavioral economics to study naturalistic decision making. The drift-diffusion modeling (FDDM) has been extended to represent coupled decision-makers who share information to collectively reach a decision.

**Limitations/Discussion**

The authors consider that the forager knows the average patch food density  and the average patch size , and uses these to set an optimal decision "strategy" by choosing values of the drift rate  and the threshold . Other models have considered the process of learning about the environment during foraging using reinforcement learning. Reinforcement learning is a framework to represent how an agent that receives information about the state of the world along with a scalar valued reward signal learns to select actions which maximize the long run accrued reward. Kolling and Akam  reframed the MVT rule as an average reward RL algorithm, which estimates relative values of staying and leaving using a particular assumption about the patch's reward rate dynamics. To incorporate RL into the FDDM, one possibility is that the agent has to learn the patch characteristics , and then uses these learned values to set . Another possibility is that the agent could adjust  and  directly, based on feedback from the amount of reward received.

**References**

[1] Carlos D Brody and Timothy D Hanks. Neural underpinnings of the evidence accumulator. Current opinion in neurobiology, 37:149–157, 2016.
[2] Timothy D Hanks and Christopher Summerfield. Perceptual decision making in rodents, monkeys, and humans. Neuron, 93(1):15–31, 2017.
[3] Ian Krajbich, Dingchao Lu, Colin Camerer, and Antonio Rangel. The attentional drift-diﬀusion model extends to simple purchasing decisions. Frontiers in psychology, 3:193, 2012.
[4] William T Newsome, Kenneth H Britten, and J Anthony Movshon. Neuronal correlates of a perceptual decision. Nature, 341(6237):52, 1989.
[5] Sebastian Gluth, J¨ org Rieskamp, and Christian B¨ chel. Deciding when to decide: time-variant sequential sampling models explain the emergence of value-based decisions in the human brain. Journal of Neuroscience, 32(31):10686–10698, 2012.
[6] Jerome R Busemeyer and James T Townsend. 

**END OF SUMMARY**

Please let me know if you need any further assistance!

---

**Summary Statistics:**
- Input: 14,758 words (89,749 chars)
- Output: 672 words
- Compression: 0.05x
- Generation: 37.9s (17.7 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
