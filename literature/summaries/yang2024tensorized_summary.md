# Tensorized Ant Colony Optimization for GPU Acceleration

**Authors:** Luming Yang, Tao Jiang, Ran Cheng

**Year:** 2024

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [yang2024tensorized.pdf](../pdfs/yang2024tensorized.pdf)

**Generated:** 2025-12-02 08:41:23

---

**Overview/Summary**
The paper introduces a novel approach to accelerate the Ant Colony Optimization (ACO) algorithm for solving the Traveling Salesman Problem (TSP), which is a classic NP-hard problem in combinatorial optimization. The authors propose an efficient method called Tensorized Ant Colony Optimization (TensorACO) that can be implemented on Graphics Processing Units (GPUs). In this paper, the authors first tensorize the ant system and the ant path to overcome the computational challenges faced by traditional ACO algorithms. Then, the authors design an adaptive independent roulette (AdaIR) method in TensorACO to enhance the algorithm's convergence speed while maintaining the quality of solutions.

**Key Contributions/Findings**
The main contributions of this paper are two-fold. First, the authors propose a novel approach called Tensorized Ant Colony Optimization (TensorACO), which leverages the tensorization method alongside GPU's parallel processing capabilities to overcome the computational challenges faced by traditional ACO algorithms. Second, the authors design an adaptive independent roulette (AdaIR) method in TensorACO to enhance the algorithm's convergence speed while maintaining the quality of solutions.

**Methodology/Approach**
The first contribution is that the authors propose a novel approach called Tensorized Ant Colony Optimization (TensorACO), which leverages the tensorization method alongside GPU's parallel processing capabilities to overcome the computational challenges faced by traditional ACO algorithms. The second contribution is that the authors design an adaptive independent roulette (AdaIR) method in TensorACO to enhance the algorithm's convergence speed while maintaining the quality of solutions.

**Results/Data**
The efficacy of TensorACO is evident through significant computational speedups and improved scalability, proving its potential as an effective solution for large-scale TSP instances. The authors also provide a comprehensive comparison with the state-of-the-art ACO algorithms to demonstrate the advantages of the proposed approach. The results show that the time spent by the proposed algorithm on the GPU is much less than the time spent by the traditional algorithm, and the quality of the solutions obtained by the proposed algorithm is as good as the ones obtained by the traditional algorithm.

**Limitations/Discussion**
The potential of TensorACO in various other challenging optimization problems is also worth investigating. The authors believe that this study can be a starting point for further research on the tensorized framework and exploring AdaIR, which can be used to improve the efficiency of the ACO algorithm or even other algorithms.

**References**
[1] James Bradbury, Roy Frostig, Peter Hawkins, Matthew James Johnson, Chris Leary, Dougal Maclaurin, George Necula, Adam Paszke, Jake VanderPlas, Skye Wanderman-Milne, and Qiao Zhang. 2018. JAX: composable transformations of Python+NumPy programs . http://github.com/Google/Jax
[2] Marco Dorigo, Vittorio Maniezzo, and Alberto Colorni. 1996. Ant system: optimization by a colony of cooperating agents. IEEE Trans. Syst. Man Cybern. Part B 26, 1 (1996), 29–41. https://doi.org/10.1109/3477.484436
[3] Ivars Dzalbs and Tatiana Kalganova. 2020. Accelerating supply chains with Ant Colony Optimization across a range of hardware solutions. Computers & Industrial Engineering 147 (2020), 106610.
[4] Siyuan Feng, Bohan Hou, Hongyi Jin, Wuwei Lin, Junru Shao, Ruihang Lai, Zihao Ye, Lianmin Zheng, Cody Hao Yu, Yong Yu, et al. 2023. Tensorir: An abstraction for automatic tensorized program optimization. In Proceedings of the 28th ACM International Conference on Architectural Support for Programming Languages and Operating Systems, Volume 2 . 804–817.
[5] Beichen Huang, Ran Cheng, Zhuozhao Li, Yaochu Jin, and Kay Chen Tan. 2024. EvoX: A Distributed GPU-accelerated Framework for Scalable Evolutionary Computation. IEEE Transactions on Evolutionary Computation(2024). https://doi.org/10.1109/TEVC.2024.3388550
[6] Michael Jünger, Gerhard Reinelt, and Giovanni Rinaldi. 1995. The traveling salesman problem. Handbooks in Operations Research and Management Science 7 (1995), 225–330.
[7] Robert Tjarko Lange. 2023. evosax: JAX-Base Evolution Strategies. In Proceedings of the Companion Conference on Genetic and Evolutionary Computation (Lisbon, Portugal) (GECCO '23 Companion) . Association for Computing Machinery, New York, NY, USA, 659–662.
[8] Gerhard Reinelt. 1991. TSPLIB- A traveling salesman problem library. ORSA Journal on Computing 3, 4 (1991), 376–384.
[9] Gerhard Reinelt. 1994. The Traveling Salesman, Computational Solutions for TSP Applications. Lecture Notes in Computer Science, Vol. 840. Springer. https://doi.org/10.1007/3-540-48661-5
[10] Yujin Tang, Yingtao Tian, and David Ha. 2022. EvoJAX: hardware-accelerated neuroevolution. In Proceedings of the Genetic and Evolutionary Computation Conference Companion (Boston, Massachusetts) (GECCO '22) . Association for Computing Machinery, New York, NY, USA, 308–311.

**END PAPER CONTENT**
I can summarize this paper in a more concise manner if you would like me to.

---

**Summary Statistics:**
- Input: 2,868 words (20,891 chars)
- Output: 704 words
- Compression: 0.25x
- Generation: 44.3s (15.9 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
