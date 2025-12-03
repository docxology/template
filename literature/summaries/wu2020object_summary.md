# Object SLAM-Based Active Mapping and Robotic Grasping

**Authors:** Yanmin Wu, Yunzhou Zhang, Delong Zhu, Xin Chen, Sonya Coleman, Wenkai Sun, Xinggang Hu, Zhiqiang Deng

**Year:** 2020

**Source:** arxiv

**Venue:** arXiv

**DOI:** 10.1109/3DV53792.2021.00144

**PDF:** [wu2020object.pdf](../pdfs/wu2020object.pdf)

**Generated:** 2025-12-03 07:00:08

---

**Overview/Summary**

The paper presents a novel approach to active mapping and robotic grasping of household objects in cluttered environments. The authors propose an object SLAM (Simultaneous Localization And Mapping) based method that leverages the 6D pose estimation of objects from RGB-D images for semantic mapping and robotic manipulation. Active mapping is a challenging problem due to the lack of prior knowledge about the environment, which makes it hard to use traditional methods such as SLAM. The authors claim that their approach can be used in real-world scenarios with cluttered environments and various types of household objects.

**Key Contributions/Findings**

The main contributions of this paper are: 
1. A novel active mapping method based on the object 6D pose estimation from RGB-D images for semantic mapping.
2. An end-to-end learning framework that can be used to learn a SLAM-based active mapping system in a simulated environment and then adapt it to real-world scenarios.

**Methodology/Approach**

The authors first propose an end-to-end learning framework that can be used to train the active mapping system. The training process is divided into two stages: (1) training the object 6D pose estimation module, and (2) training the SLAM-based active mapping system. In the first stage, the authors use a simulated environment for training the 6D pose estimation module. They propose an approach that uses a novel dataset named Sapien, which is a simulated part-based interactive environment. The Sapien dataset contains 30 objects and 3000 RGB-D images with object poses in various scenes. In the second stage, the authors use the trained 6D pose estimation module to train the SLAM-based active mapping system. The training process of the SLAM-based active mapping system is divided into two sub-stages: (1) training the SLAM module and (2) training the robot manipulation module. For the first sub-stage, the authors propose a novel approach that uses an ensemble data association method to train the SLAM module. In the second sub-stage, the authors use the trained 6D pose estimation module to train the SLAM-based active mapping system. The Sapien dataset is used for training the robot manipulation module.

**Results/Data**

The paper presents several results and findings. 
1. The authors show that the proposed approach can be used in real-world scenarios with cluttered environments and various types of household objects.
2. The authors compare their method with a state-of-the-art SLAM-based active mapping system named Cubeslam, which is trained using only point cloud data. They claim that the proposed approach outperforms the Cubeslam by 11.5% in terms of the accuracy of the semantic map and 13.6% in terms of the time to build a complete map.
3. The authors show that the proposed approach can be used for real-world scenarios with cluttered environments and various types of household objects.

**Limitations/Discussion**

The limitations of this paper are: 
1. The Sapien dataset is not publicly available, which makes it hard to use the method in real-world scenarios.
2. The authors do not show how to train the 6D pose estimation module using a real environment and only provide training data from a simulated environment.
3. The authors do not compare their approach with other state-of-the-art SLAM-based active mapping methods, such as the one proposed by Zeng et al. [30]. 
4. The authors do not show how to adapt the trained 6D pose estimation module and the SLAM-based active mapping system from a simulated environment to real-world scenarios.
5. The paper does not discuss the potential applications of this method in other fields, such as online shopping or autonomous driving.

**Summary**

The paper proposes an object SLAM based approach for active mapping and robotic grasping of household objects. The authors first propose an end-to-end learning framework that can be used to train the 6D pose estimation module and then adapt it to a real environment. Then, the trained 6D pose estimation module is used to train the SLAM-based active mapping system. The Sapien dataset is used for training the SLAM based active mapping system. The authors compare their approach with a state-of-the-art SLAM based active mapping system named Cubeslam and claim that the proposed approach outperforms the Cubeslam by 11.5% in terms of the accuracy of the semantic map and 13.6% in terms of the time to build a complete map. The authors show that the proposed approach can be used for real-world scenarios with cluttered environments and various types of household objects.

**References**

[30] Zeng, Z., R ¨ofer, A., & Jenkins, O. C. (2020). Semantics linking maps for active visual object search. In 2020 IEEE International Conference on Robotics and Automation (ICRA), pages 1984–1990.

---

**Summary Statistics:**
- Input: 6,881 words (43,394 chars)
- Output: 756 words
- Compression: 0.11x
- Generation: 38.5s (19.6 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
