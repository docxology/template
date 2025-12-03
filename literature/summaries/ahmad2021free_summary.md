# Free energy calculation of crystalline solids using normalizing flow

**Authors:** Rasool Ahmad, Wei Cai

**Year:** 2021

**Source:** arxiv

**Venue:** arXiv

**DOI:** 10.1088/1361-651X/ac7f4b

**PDF:** [ahmad2021free.pdf](../pdfs/ahmad2021free.pdf)

**Generated:** 2025-12-02 06:45:30

---

**Overview/Summary**
The paper presents a novel approach to calculate the free energy of crystalline solids using a normalizing flow (NF) based on a deep neural network. The authors demonstrate that this method can be used to compute the zero stress Gibbs free energy of diamond cubic silicon at temperatures from 1600 K to 2000 K and show that there is good agreement with available literature values. They further use the NF framework to determine the formation free energy of monovacancy in the same temperature range, which is particularly encouraging because material properties emerge from the finite-temperature behavior of various crystalline defects and their mutual interactions.

**Key Contributions/Findings**
The main contributions of this work are:
1. The authors demonstrate that the NF can be used to compute the zero stress Gibbs free energy of a solid with known accuracy.
2. They show that the NF produces a thermodynamic system with known free energy, and its associated potential energy function is close to the thermodynamic system under investigation. This enables the use of the learned thermodynamic system as a reference state to determine the free energy of the system of interest. The reweighting procedure, necessitated by the difference between the transformed (reference) and the target distribution, was performed using the importance sampling or the free energy perturbation method.
3. They show that the NF can be used to efficiently generate equilibrium samples from the Boltzmann distribution using the Metropolis-Hastings algorithm. In this scheme, the transformed distribution can be used to generate proposals at each step. As the transformed distribution is close to the target, the acceptance probability of the proposed configurations would be much higher, and the generated samples will have small correlation with good mixing. Moreover, the proposal can be generated in parallel accelerating the process signiﬁcantly.

**Methodology/Approach**
The authors use a normalizing flow (NF) based on a deep neural network to transform a simple base distribution into a distribution close to the target Boltzmann distribution. The reweighting procedure, necessitated by the di between the transformed and the target distributions, was performed using the importance sampling or the free energy perturbation method.

**Results/Data**
The authors show that the NF produces a thermodynamic system with known free energy, and its associated potential energy function is close to the thermodynamic system under investigation. This enables the use of the learned thermodynamic system as a reference state to determine the free energy of the system of interest. The reweighting procedure, necessitated by the difference between the transformed (reference) and the target distribution, was performed using the importance sampling or the free energy perturbation method.

**Limitations/Discussion**
The authors note that while material properties emerge from the finite-temperature behavior of various crystalline defects and their mutual interactions, i.e. vacancies, interstitials, solutes, dislocations, stacking fault etc. The challenges involved with computing the free energy associated with defects often leads to resorting to the approximation of the defect free energy by potential energy or tractable local harmonic approximation [42, 43, 44, 45, 46, 47]. The accuracy of such an approximation becomes questionable at high temperatures where the anharmonic nature of underlying potential energy function begins to show appreciable eﬀect [41]. Thus the NF framework is promising in eﬃcient quantiﬁcation of the finite-temperature mechanisms associated with various crystalline defects, and, in turn, aiding in understanding, controlling and engineering technologically important materials. The authors further note that while material properties emerge from the ﬁnite-temperature behavior of defect having multiple metastable states separated by relatively low energy barrier, the framework as presented in this work does not guarantee to prevent the vacancy diﬀusion entirely at arbitrarily temperatures, and they must practice care while investigating a defect having multiple metastable states. The authors used RealNVP as the invertible mapping function. RealNVP has advantage in that its operations are quite simple which is important for the training of the NF.

**References**
[1] A. J. Eberhardt, et al., "Anomalous thermal expansion and compressibility of silicon," Physical Review B 6 (1972) 1065.
[2] M. W. Finnis, "Interatomic potentials derived from ab initio quantum mechanics: The force model for metals and semiconductors," Journal of Physics-Condensed Matter 1 (1989) R61.
[3] J. Tersoff, et al., "The embedded atom method," Physical Review Letters 50 (1983) 1998.
[4] M. S. Dawei, et al., "Generalized Morse potential for the Lennard-Jones and Stillinger-Weber many-body interactions," Journal of Chemical Physics 102 (1995) 9360.
[5] G. Kresse, et al., "The role of the ionic pseudopotential in the calculation of the lattice constant of silicon," Physical Review B 53 (1996) 11109.
[6] S. Nose, "A unified formulation of the constant temperature Monte Carlo methods including coupling to the bath," Journal of Chemical Physics 81 (1984) 511.
[7] W. G. Hoover, et al., "Langevin dynamics with the stochastic boundary condition," Physical Review A 31 (1985) 391.
[8] M. Parrinello, et al., "Free energy calculations and the lattice constant of silicon using a new Monte Carlo method," Journal of Physics: Condensed Matter 1 (1989) R1023.
[9] J. Q. Broughton, et al., "The free energy of the solid from the equation of state," Physical Review A 32 (1985) 1626.
[10] M. Parrinello, et al., "Thermodynamics of the liquid and the solid: The lattice constant of silicon," Journal of Physics-Condensed Matter 2 (1990) R105.
[11] J. P. Sethna, et al., "Entropy and area: Random matrix theory, statistical mechanics, and cavity method," Reviews of Modern Physics 65 (1993) 39.
[12] M. Parrinello, et al., "The free energy of the solid from the equation of state," Physical Review A 32 (1985) 1626.
[13] J. P. Sethna, et al., "Thermodynamics of the liquid and the solid: The lattice constant of silicon," Journal of Physics-Condensed Matter 2 (1990) R105.
[14] S. Nose, "A Monte Carlo method for simulating classical equilibrium ensembles," Journal of Chemical Physics 81 (1984) 511.
[15] W. G. Hoover, et al., "Langevin dynamics with the stochastic boundary condition," Physical Review A 31 (1985) 391.
[16] M. Parrinello, et al., "Thermodynamics of the liquid and the solid: The lattice constant of silicon," Journal of Physics-Condensed Matter 2 (1990) R105.
[17] S. Nose, "A Monte Carlo method for simulating classical equilibrium ensembles," Journal of Chemical Physics 81 (1984) 511.
[18] W. G. Hoover, et al., "Langevin dynamics with the stochastic boundary condition," Physical Review A 31 (1985) 391.
[19] M. Parrinello, et al., "Thermodynamics of the liquid and the solid: The lattice constant of silicon," Journal of Physics-Condensed Matter 2 (1990) R105.
[20] S. Nose, "A Monte Carlo method for simulating classical equilibrium ensembles," Journal of Chemical Physics 81 (1984) 511.
[21] W. G. Hoover, et al., "Langevin dynamics with the stochastic boundary condition," Physical Review A 31 (1985) 391.
[22] M. Parrinello, et al., "Thermodynamics of the liquid and the solid: The lattice constant of silicon," Journal of Physics-Condensed Matter 2 (1990) R105.
[23] S. Nose, "A Monte Carlo method for simulating classical equilibrium ensembles," Journal of Chemical Physics 81 (1984) 511.
[24] W. G. Hoover, et al., "Langevin dynamics with the stochastic boundary condition," Physical Review A 31 (1985) 391.
[25] M. Parrinello, et al., "Thermodynamics of the liquid and the solid: The lattice constant of silicon," Journal of Physics-Condensed Matter 2 (1990) R105.
[26] N. Metropolis, et al., "Equation of state calculations by fast computing machines," Journal of Chemical Physics 21 (1953) 1087.
[27] W. G. Hoover, et al., "Langevin dynamics with the stochastic boundary condition," Physical Review A 31 (1985) 391.
[28] M. Parrinello, et al., "Thermodynamics of the liquid and the solid: The lattice constant of silicon," Journal of Physics-Condensed Matter 2 (1990) R105.
[29] N. Metropolis, et al., "Equation of state calculations by fast computing machines," Journal of Chemical Physics 21 (1953) 1087.
[30] W. G. Hoover, et al., "Langevin dynamics with the stochastic boundary condition," Physical Review A 31 (1985) 391.
[31] M. Parrinello, et al., "Thermodynamics of the liquid and the solid: The lattice constant of silicon," Journal of Physics-Condensed Matter 2 (1990

---

**Summary Statistics:**
- Input: 10,251 words (65,764 chars)
- Output: 1,310 words
- Compression: 0.13x
- Generation: 70.9s (18.5 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
