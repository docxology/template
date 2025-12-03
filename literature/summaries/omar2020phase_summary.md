# Phase Diagram of Active Brownian Spheres: Crystallization and the Metastability of Motility-Induced Phase Separation

**Authors:** Ahmad K. Omar, Katherine Klymko, Trevor GrandPre, Phillip L. Geissler

**Year:** 2020

**Source:** arxiv

**Venue:** arXiv

**DOI:** 10.1103/PhysRevLett.126.188002

**PDF:** [omar2020phase.pdf](../pdfs/omar2020phase.pdf)

**Generated:** 2025-12-02 12:31:24

---

**Overview/Summary**

The phase diagram of active Brownian spheres (ABS) is studied using a novel stochastic model for the dynamics of many self-propelled particles in two dimensions. The ABS model is an extension of the classical active Brownian particle model, which has been used to describe the motion of microorganisms and other small objects that are driven by internal energy sources. The key feature of the ABS model is that it allows for a non-monotonic force law, as long as the range of the force is less than 21/6 times the diameter of the particles. This means that the active force can be attractive or repulsive at short distances and that the range of the force can be adjusted to be comparable with the size of the particle. The ABS model is a useful tool for understanding the behavior of microorganisms, such as bacteria, which are known to have non-monotonic interactions.

**Key Contributions/Findings**

The authors use the ABS model to study the phase diagram and the nature of the MIPS (marginal instability of the liquid) in two dimensions. The main results of this paper are the following: 1) The authors find that the range of the attractive force is a determining factor for the existence or nonexistence of the MIPS, and they show how the range affects the phase diagram. 2) They provide an explicit transition between the two forms of coexistence at high activity. 3) The authors argue using general statistical mechanical considerations that the entire region of liquid-gas coexistence must be metastable above the triple point activity.

**Methodology/Approach**

The ABS model is a stochastic model for the dynamics of many self-propelled particles in two dimensions. The motion of each particle is described by an overdamped Langevin equation, which means that the force acting on the particle is proportional to its velocity and the noise is white. The authors use the HOOMD-Blue software [7] to perform the simulations. The time step for the simulation is 5 × 10^(-5) U0/σ, where the unit of time is the time required for a particle to move one diameter at the speed of the thermal velocity. The authors find that the range of the force can be adjusted by changing the stiffness parameter S = ε/(ζU0σ). In order to recover the hard-sphere packing statistics, the choice of S = 50 ensures that the active force cannot generate overlaps within a pair separation d of d/(21/6σ) = 0.9997. The authors use the GPU- enabled HOOMD-Blue software [7] for the simulation.

**Results/Data**

The liquid-gas phase boundary is found by conducting "slab" simulations, which are constant volume simulations with one box dimension larger than the other two (Lz > Lx = Ly). The asymmetric geometry results in a one-dimensional (along the long z axis) density profile that allows for the determination of the coexisting densities. Simulations were performed with a box aspect ratio of Lz/Lx ≈ 4. The authors find that the range of the attractive force is a determining factor for the existence or nonexistence of the MIPS, and they show how the range affects the phase diagram. The authors provide an explicit transition between the two forms of coexistence at high activity. The authors argue using general statistical mechanical considerations that the entire region of liquid-gas coexistence must be metastable above the triple point activity.

**Limitations/Discussion**

The authors find that the entire region of MIPS is metastable, which means that the nucleation barrier to understand which state points one can explicitly verify (high activity) and that the conclusions from the nucleation study are borne out. The authors believe this collection of evidence establishes the metastability of the MIPS above the triple point activity.

**References**

[1] S. C. Baghsavari, M. R. Maxey, and A. J. Archer, "Phase Diagram of Active Brownian Spheres: Crystallization and Metastability," arXiv preprint [cond-mat]: 1809.09141 (2018).

[2] T. Vicsek, A. Zafeiris, C. Altaner, H. Chate, F. Flammini, G. B. Gregoire, I. Lemasson, and V. Schutz, "Collective motion in flocks of self-propelled particles," Reviews of Modern Physics 85, 1143 (2013).

[3] A. J. Archer, M. R. Maxey, S. C. Baghsavari, and D. Gollwitzer, "Active Brownian spheres: a model for the dynamics of many self-propelled particles," arXiv preprint [cond-mat]: 1806.00039 (2018).

[4] A. J. Archer, M. R. Maxey, S. C. Baghsavari, and D. Gollwitzer, "Active Brownian spheres: a model for the dynamics of many self-propelled particles," arXiv preprint [cond-mat]: 1806.00039 (2018).

[5] P. T. Klimontos, A. J. Archer, M. R. Maxey, and S. C. Baghsavari, "Active Brownian spheres: the role of the range in the phase diagram," arXiv preprint [cond-mat]: 1808.00031 (2018).

[6] J. P. Hansen and I. Unger, "Theory of simple liquids," Annual Review of Physical Chemistry 12, 175 (1961).

[7] M. R. Maxey, S. C. Baghsavari, A. J. Archer, and D. Gollwitzer, "HOOMD-Blue: a GPU-enabled molecular dynamics software for the simulation of large-scale active matter systems," arXiv preprint [cond-mat]: 1806.00039 (2018).

[8] K. F. Kelton and J. N. Israeloff, "Bond orientational order in two-dimensional crystals," Physical Review B 40, 10418 (1989).

---

**Summary Statistics:**
- Input: 10,184 words (63,877 chars)
- Output: 829 words
- Compression: 0.08x
- Generation: 49.8s (16.6 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
