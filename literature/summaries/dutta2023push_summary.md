# Push to know! -- Visuo-Tactile based Active Object Parameter Inference with Dual Differentiable Filtering

**Authors:** Anirvan Dutta, Etienne Burdet, Mohsen Kaboli

**Year:** 2023

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [dutta2023push.pdf](../pdfs/dutta2023push.pdf)

**Generated:** 2025-12-05 12:21:08

---

**Overview/Summary**
The paper presents a new approach to estimating an object's inertial parameters by using visuo-tactile sensing and few-shot learning from a large-scale simulation dataset. The authors leverage the fact that for many objects, the inertial parameters are not known in advance but can be learned through the process of robotic pushing. They first introduce a novel 2D Gaussian model to describe the uncertainty of the contact point's position in the image frame and then propose an end-to-end learning framework based on differentiable physics simulations. The authors use a large-scale simulation dataset for planar manipulation, which is collected by using a high-fidelity robotic arm with a large range of motion, and a few-shot learning strategy to learn the model from this dataset. They show that their approach can be used to estimate the inertial parameters of an object in real-world scenarios.

**Key Contributions/Findings**
The authors make two main contributions. The first is the 2D Gaussian model for describing the uncertainty of the contact point's position in the image frame, which is a new way to represent the uncertainty of the pushing process. The second is the end-to-end learning framework based on differentiable physics simulations, which can be used to estimate an object's inertial parameters from a few demonstrations. The authors show that their approach can be used to estimate the inertial parameters of an object in real-world scenarios.

**Methodology/Approach**
The authors first introduce a novel 2D Gaussian model for describing the uncertainty of the contact point's position in the image frame, which is a new way to represent the uncertainty of the pushing process. The 2D Gaussian can be 
px = pixelx
pixely

,K =  cos2(pd)
2v2  + sin2(pd)
sin(2pd)
4v2 − sin(2pd)
4
sin2(pd)
2v2  + cos2(pd)
2

The authors then propose an end-to-end learning framework based on differentiable physics simulations. The approach is to use a few demonstrations of the pushing process and learn the model from this dataset. The authors show that their approach can be used to estimate the inertial parameters of an object in real-world scenarios.

**Results/Data**
The authors first introduce a large-scale simulation dataset for planar manipulation, which is collected by using a high-fidelity robotic arm with a large range of motion. This dataset contains 1,000,000 demonstrations and each demonstration includes 10,000 frames. The authors then use this dataset to train the model. They show that their approach can be used to estimate the inertial parameters of an object in real-world scenarios.

**Limitations/Discussion**
The authors point out two limitations. The first is that the current differentiable physics simulator only supports 2D planar pushing, and the second is that the current dataset does not contain any demonstrations with a large amount of force or motion. They suggest that these limitations can be addressed in future work.

**Additional Information**

1. **Dataset**: The authors use the MCube push dataset to train their model. This dataset contains 1,000,000 demonstrations and each demonstration includes 10,000 frames.
2. **Simulation**: The authors use a high-fidelity robotic arm with a large range of motion to collect this dataset. The robot is equipped with a force sensor that can measure the force applied by the human operator during the pushing process.

**References**

1. Coumans, E., & Bai, Y. (2016). Pybullet, a python module for physics simulation for games, robotics and machine learning.
2.  "The mcube lab - push dataset." https://mcube.mit.edu/push-dataset/, (Accessed on 03/02/2023).
3.  "Optitrack - motion capture systems," https://optitrack.com/, (Accessed on 03/02/2023).
4. Haarnoja, T., & al., e. (2016). Backprop kf: Learning discriminative deterministic state estimators.
5. Kloss, A., & al., e. (2018). How to train your differentiable filter.
6. Lambert, A. S., & al., e. (2019). Joint inference of kinematic and force trajectories with visuo-tactile sensing.
7. Liu, J., & West, M. (2018). Realtime state estimation with tactile and visual sensing. application to planar manipulation.
8. Mavrakis, N., & al., e. (2020). Estimating an object's inertial parameters by robotic pushing: a data-driven approach.
9. Simonyan, K., & Zisserman, A. (2014). Very deep convolutional networks for large-scale image recognition.
10. Thrun, S.,  Roussos, A. E., & Dellaert, F. (2002). Probabilistic robotics.
11. W ¨ utrich, M., & al., e. (2016). Robust gaussian filtering using a pseudo measure-ment.

**Appendix**

1. **Constrained Monte Carlo Sampling**: The 2D Gaussian can be 
px = pixelx
pixely

,K =  cos2(pd)
2v2  + sin2(pd)
sin(2pd)
4v2 − sin(2pd)
4
sin2(pd)
2v2  + cos2(pd)
2

Mt = e(−1
2  (px−cpi f  ) K(px−cpi f  )T )

(24)

---

**Summary Statistics:**
- Input: 6,957 words (44,305 chars)
- Output: 740 words
- Compression: 0.11x
- Generation: 44.1s (16.8 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
