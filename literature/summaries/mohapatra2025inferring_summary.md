# Inferring activity from the flow field around active colloidal particles using deep learning

**Authors:** Aditya Mohapatra, Aditya Kumar, Mayurakshi Deb, Siddharth Dhomkar, Rajesh Singh

**Year:** 2025

**Source:** arxiv

**Venue:** arXiv

**DOI:** 10.1017/jfm.2025.10502

**PDF:** [mohapatra2025inferring.pdf](../pdfs/mohapatra2025inferring.pdf)

**Generated:** 2025-12-03 06:20:09

---

**Overview/Summary**
The paper "Learning hydrodynamic equations for active matter from particle simulations and experiments" by Supekar et al. (2023) is a machine learning approach that uses a physics-informed neural network to predict the velocity field around individual particles in an experimentally accessible, two-dimensional flow. The authors' goal is to use this method as a first step towards developing a general-purpose, data-driven hydrodynamic solver for active matter. In particular, they focus on the case of a dilute suspension of microorganisms that are driven by a global force field and which can be represented in the long-wavelength limit as an incompressible fluid with a non-zero Reynolds number. The paper is divided into three main parts: the first part presents the physics-informed neural network (PINN) approach, the second part discusses the results of using this method to predict the velocity fields around individual particles in experiments and simulations, and the third part discusses the limitations of the current work.

**Key Contributions/Findings**
The authors use a PINN to learn the hydrodynamic equations for active matter. The PINN is a neural network that is trained on a dataset of particle image velocimetry (PIV) data from a well-controlled experiment, and which uses a set of physics-based constraints in its loss function. This allows the learned model to be used as an input-output mapping, but also provides a set of equations for the velocity field around individual particles that can be solved using the forward Euler method. The authors use this approach to learn the hydrodynamic equations from both experimental and simulation data. They find that the PINN is able to predict the velocity fields in the experiments with high accuracy. The authors' results also show that the learned model is not as good at predicting the velocity fields around individual particles in a simulation, which they attribute to the fact that the PIV dataset does not contain any information about the global force field. They find that the PINN can be used to predict the hydrodynamic equations for active matter with high accuracy and that it is able to learn the same physics from both experimental and simulation data.

**Methodology/Approach**
The authors use a PINN to learn the hydrodynamic equations, which is a neural network that uses a set of physical constraints in its loss function. The authors' approach is based on the idea that if the PIV data contains information about the global force field, then the learned model should be able to predict the velocity fields around individual particles in both experimental and simulation data with high accuracy. The authors use this method to learn the hydrodynamic equations from both experimental and simulation data. They find that the PINN is able to predict the velocity fields in the experiments with high accuracy. The authors' results also show that the learned model is not as good at predicting the velocity fields around individual particles in a simulation, which they attribute to the fact that the PIV dataset does not contain any information about the global force field.

**Results/Data**
The authors use the PINN to learn the hydrodynamic equations from both experimental and simulation data. The authors find that the PINN is able to predict the velocity fields in the experiments with high accuracy. The authors' results also show that the learned model is not as good at predicting the velocity fields around individual particles in a simulation, which they attribute to the fact that the PIV dataset does not contain any information about the global force field.

**Limitations/Discussion**
The authors find that the PINN can be used to predict the hydrodynamic equations for active matter with high accuracy and that it is able to learn the same physics from both experimental and simulation data. The authors' results also show that the learned model is not as good at predicting the velocity fields around individual particles in a simulation, which they attribute to the fact that the PIV dataset does not contain any information about the global force field.

**References**
Supekar, R., Song, B., Hastewell, A., Choi, G. P. T., Mietke, A., Dunkel, J. (2023). Learning hydrodynamic equations for active matter from particle simulations and experiments. Proc. Natl. Acad. Sci. 120(7), e2206994120.

**Additional Comments**
The authors' approach is an interesting first step towards developing a general-purpose, data-driven hydrodynamic solver for active matter. The authors' results show that the PINN can be used to predict the velocity fields in the experiments with high accuracy and that it is able to learn the same physics from both experimental and simulation data. The authors' results also show that the learned model is not as good at predicting the velocity fields around individual particles in a simulation, which they attribute to the fact that the PIV dataset does not contain any information about the global force field.

---

**Summary Statistics:**
- Input: 5,467 words (33,945 chars)
- Output: 797 words
- Compression: 0.15x
- Generation: 37.4s (21.3 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
