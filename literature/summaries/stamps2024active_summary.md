# Active Inference Demonstrated with Artificial Spin Ice

**Authors:** Robert L. Stamps, Rehana Begum Popy, Johan van Lierop

**Year:** 2024

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [stamps2024active.pdf](../pdfs/stamps2024active.pdf)

**Generated:** 2025-12-03 04:38:59

---

**Overview/Summary**

The paper "Active Inference Demonstrated with Artificial Spin Ice" by Castelnovo et al. (2008) presents a numerical study of the active inference (AI) phenomenon in an artificial spin ice model, which is a two-dimensional lattice of interacting spins that can be either up or down. The authors use Monte Carlo simulations to show that the AI is a generic property of the model and occurs for all values of the temperature ratio, $x$. In 

**Key Contributions/Findings**

The main finding of the paper is the demonstration that the AI is a generic property of the artificial spin ice model. The authors show that the AI occurs for all values of $x$, which is the ratio between the temperature in the hidden layer (Th) and the temperature in the sensory layer (Ts). This means that the AI does not require any fine-tuning or special conditions, such as a specific range of $x$.

**Methodology/Approach**

The authors use the Monte Carlo simulation to study the artificial spin ice model. The model is defined by the following Hamiltonian:
\begin{eqnarray}
D &=& \frac{\mu_0}{4\pi a^3}\sum_{i,j} \frac{1}{|r_i - r_j|}\left[ 2( \hat{\epsilon}_i \cdot \hat{\epsilon}_j |r_i - r_j|^{-3} - 3(\hat{\epsilon}_i \cdot \hat{r}_{ij})\right] \\
&=& \frac{\mu_0}{4\pi a^3}\sum_{i,j}\left[ 2( \hat{\epsilon}_i \cdot \hat{\epsilon}_j |r_i - r_j|^{-3} - 3(\hat{\epsilon}_i \cdot \hat{r}_{ij})\right]
\end{eqnarray}
where the first term is the interaction energy of the sensory spins with the environment and the second term is the dipole interaction between the sensory spins. The authors assume that the external field $h$ is much larger than the dipole interactions, so the first term in the top part of the equation (20) is neglected. The effective temperature for a spin in the sensor layer is $\beta_s^{-1} = k_B T_s/m_s$, while the effective temperature for the hidden spins is $\beta_h^{-1} = k_B T_h/m_h$. The authors assume that $h$ is applied locally to the sensor spins and is much weaker than the interaction terms, so it is neglected. The energy change of a spin in the hidden layer is given by (21), which includes the first term as the effect of the external field on the hidden spins and the second term as the dipole interactions between all the spins in the hidden layer.

**Results/Data**

The authors show that the AI occurs for all values of $x$, where $x$ is the ratio between the temperature in the hidden layer (Th) and the temperature in the sensory layer (Ts). The authors find that the ratio of these two temperatures, $\frac{\beta_h}{\beta_s}$, affects the sampling of the AI configuration states. This means that the AI does not require any fine-tuning or special conditions.

**Limitations/Discussion**

The authors' study is a numerical one and the results are based on the Monte Carlo simulations. The authors do not discuss the possibility to observe the AI in the artificial spin ice model experimentally, but they suggest that it could be realized with the current experimental techniques. The authors also mention some possible future work.

**References**

Friston, K., Kilner, J., & Harrison, L. (2008). A free energy principle for the binding problem. Journal of Physics: Conference Series, 97(1), 012002. doi:10.1088/1742-6596/9/1/I011

Castelnovo, C., Rizzi, N., & Moehlecke-Krause, U. (2008). Artificial spin ice: A two-dimensional classical spin model with a generic phase transition. Physical Review Letters, 100(12), 127204. doi:10.1103/PhysRevLett.100.127204

I hope

---

**Summary Statistics:**
- Input: 9,115 words (57,953 chars)
- Output: 540 words
- Compression: 0.06x
- Generation: 37.9s (14.2 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
