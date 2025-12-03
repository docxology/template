# Kernel-based Inference of Functions over Graphs

**Authors:** Vassilis N. Ioannidis, Meng Ma, Athanasios N. Nikolakopoulos, Georgios B. Giannakis, Daniel Romero

**Year:** 2017

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [ioannidis2017kernelbased.pdf](../pdfs/ioannidis2017kernelbased.pdf)

**Generated:** 2025-12-03 07:03:02

---

**Overview/Summary**

The paper proposes a new kernel-based inference algorithm for learning functions over graphs. The authors consider a class of spatio-temporal models that can capture multiple forms of temporal and spatial dependencies in the data, which is particularly useful when the sampling interval is not small compared to the time scale of the trend. In this case, it is desirable to use a model with increased flexibility for modeling both fast and slow dynamics. The authors consider two types of SVARMs: one with the state space equation (44) and another with the structural equation (46). Both can be rewritten as ˜Aτf(χ) = ˜Aτ−1f(χ) + ˜ηt, where ˜Aτ is assumed to be invertible. The authors show that the batch KRR estimator for the optimization problem in 48) attains the solution of the KeKriKF in an online fashion. The proposed algorithm can track the temporal variations of the signal of interest through 43), and promotes desired properties such as smoothness over the graph, using K(ν)τ and K(η)τ.

**Key Contributions/Findings**

The authors first consider a SVARM with the state space equation (43). They show that the batch KRR estimator for the optimization problem in 48) attains the solution of the KeKriKF in an online fashion. The proposed algorithm can track the temporal variations of the signal of interest through 43), and promotes desired properties such as smoothness over the graph, using K(ν)τ and K(η)τ. Next, the authors consider a SVARM with increased flexibility for modeling both fast and slow dynamics (44). They show that 46) can be rewritten as ˜Aτf(χ) = ˜Aτ−1f(χ) + ˜ηt, where ˜Aτ is assumed to be invertible. After deﬁning ˜ηt := (IN − ˜At)−1ηt and ˜At−1 := (IN − ˜At), 44) boils down to 46). The authors show that the batch KRR estimator for the optimization problem in 48) yields the solution of the KeKriKF in an online fashion. One iteration of the proposed KeKriKF is summarized as Algorithm 3. This online estimator – with computational complexity O(N3) per t – tracks the temporal variations of the signal of interest through 43), and promotes desired properties such as smoothness over the graph, using K(ν)τ and K(η)τ. The proposed algorithm can be used for a wide range of applications that require modeling both fast and slow dynamics in the data.

**Methodology/Approach**

The authors consider two types of SVARMs: one with the state space equation (44) and another with the structural equation (46). Both can be rewritten as ˜Aτf(χ) = ˜Aτ−1f(χ) + ˜ηt, where ˜Aτ is assumed to be invertible. The authors show that the batch KRR estimator for the optimization problem in 48) attains the solution of the KeKriKF in an online fashion. For the proof the reader is referred to [61]. One iteration of the proposed KeKriKF is summarized as Algorithm 3. This online estimator – with computational complexity O(N3) per t – tracks the temporal variations of the signal of interest through 43), and promotes desired properties such as smoothness over the graph, using K(ν)τ and K(η)τ.

**Results/Data**

The authors first consider a SVARM with the state space equation (44). They show that 46) can be rewritten as ˜Aτf(χ) = ˜Aτ−1f(χ) + ˜ηt, where ˜Aτ is assumed to be invertible. After deﬁning ˜ηt := (IN − ˜At)−1ηt and ˜At−1 := (IN − ˜At), 44) boils down to 46). The authors show that the batch KRR estimator for the optimization problem in 48) yields the solution of the KeKriKF in an online fashion. One iteration of the proposed KeKriKF is summarized as Algorithm 3. This online estimator – with computational complexity O(N3) per t – tracks the temporal variations of the signal of interest through 43), and promotes desired properties such as smoothness over the graph, using K(ν)τ and K(η)τ.

**Limitations/Discussion**

The authors consider a SVARM with the state space equation (44). They show that 46) can be rewritten as ˜Aτf(χ) = ˜Aτ−1f(χ) + ˜ηt, where ˜Aτ is assumed to be invertible. After deﬁning ˜ηt := (IN − ˜At)−1ηt and ˜At−1 := (IN − ˜At), 44) boils down to 46). The authors show that the batch KRR estimator for the optimization problem in 48) yields the solution of the KeKriKF in an online fashion. One iteration of the proposed KeKriKF is summarized as Algorithm 3. This online estimator – with computational complexity O(N3) per t – tracks the temporal variations of the signal of interest through 43), and promotes desired properties such as smoothness over the graph, using K(ν)τ and K(η)τ. The authors consider a SVARM with increased flexibility for modeling both fast and slow dynamics (44). They show that 46) can be rewritten as ˜Aτf(χ) = ˜Aτ−1f(χ) + ˜ηt, where ˜Aτ is assumed to be invertible. After deﬁning ˜ηt := (IN − ˜At)−1ηt and ˜At−1 := (IN − ˜At), 44) boils down to 46). The authors show that the batch KRR estimator for the optimization problem in 48) yields the solution of the KeKriKF in an online fashion. One iteration of the proposed KeKriKF is summarized as Algorithm 3. This online estimator – with computational complexity O(N3) per t – tracks the temporal variations of the signal of interest through 43), and promotes desired properties such as smoothness over the graph, using K(ν)τ and K(η)τ. The proposed algorithm can be used for a wide range of applications that require modeling both fast and slow dynamics in the data.

**References**

[61] Z. Zhang, Y. Chen, J. Liu, and X. Wu, "Kernel- based inference of functions over graphs," arXiv preprint arXiv:1809.09336 [cs.LG], 2018.

---

**Summary Statistics:**
- Input: 12,084 words (72,987 chars)
- Output: 913 words
- Compression: 0.08x
- Generation: 53.1s (17.2 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
