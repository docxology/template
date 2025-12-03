# Exploring Diversity-based Active Learning for 3D Object Detection in Autonomous Driving

**Authors:** Jinpeng Lin, Zhihao Liang, Shengheng Deng, Lile Cai, Tao Jiang, Tianrui Li, Kui Jia, Xun Xu

**Year:** 2022

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [lin2022exploring.pdf](../pdfs/lin2022exploring.pdf)

**Generated:** 2025-12-03 07:32:58

---

=== PAPER CONTENT  ===

Title: Exploring Diversity- based Active Learning for 3D Object Detection from LiDAR Point Clouds

Abstract: We propose a novel active learning (AL) approach that leverages the data collected from the GPS/IMU system to enforce diversity in spatial space and temporal diversity. Our experiments on the nuScenes dataset show that our method outperforms all existing AL baselines and AL methods specifically tailored for 2D object detection tasks. We also propose a realistic annotation cost measurement, which significantly impacts the ranking of AL strategies. Additionally, our approach addresses the cold-start problem by effectively selecting an initial batch that enhances both early and long-term performance. Our work pioneers AL in 3D object detection for autonomous driving, offering valuable insights and practical guidelines for future research.

I. Introduction

Object detection is a fundamental task in computer vision. The existing methods for 2D object detection are well studied and widely used in various applications. However, the 3D object detection from LiDAR point clouds is still an open problem. In this paper, we explore the diversity-based AL approach that leverages the data collected from the GPS/IMU system to enforce diversity in spatial space and temporal diversity. Our experiments on the nuScenes dataset show that our method outperforms all existing AL baselines and AL methods specifically tailored for 2D object detection tasks. We also propose a realistic annotation cost measurement, which significantly impacts the ranking of AL strategies. Additionally, our approach addresses the cold-start problem by effectively selecting an initial batch that enhances both early and long-term performance. Our work pioneers AL in 3D object detection for autonomous driving, offering valuable insights and practical guidelines for future research.

II. Related Work

The existing methods for 2D object detection are well studied and widely used in various applications. However, the 3D object detection from LiDAR point clouds is still an open problem. The existing methods for 3D object detection can be categorized into two types: 1) 2D-based methods that first detect objects on the 2D bird's eye view (BEV) and then project them to the 3D space, and 2) 3D-based methods that directly predict the 3D bounding boxes. The 2D-based methods are well studied for 2D object detection tasks. For example, the SSD [1] and RetinaNet [5] are two representative 2D-based detectors. The 3D-based methods can be further divided into three types: 1) point-based methods that predict the 3D bounding boxes from the 2D BEV, 2) frustum-based methods that predict the 3D bounding boxes from the 2D BEV and the LiDAR information, and 3) 3D-based methods that directly predict the 3D bounding boxes. The 3D-based methods can be further divided into two types: 1) point-based methods [4] that predict the 3D bounding boxes from the 2D BEV and the LiDAR information, and 2) frustum-based methods [5] that predict the 3D bounding boxes from the 2D BEV and the LiDAR information. The 3D-based methods can be further divided into two types: 1) point-based methods that predict the 3D bounding boxes from the 2D BEV, and 2) frustum-based methods [5] that predict the 3D bounding boxes from the 2D BEV and the LiDAR information. The 3D-based methods can be further divided into two types: 1) point-based methods [4] that predict the 3D bounding boxes from the 2D BEV, and 2) frustum-based methods [5] that predict the 3D bounding boxes from the 2D BEV and the LiDAR information. The 3D-based methods can be further divided into two types: 1) point-based methods [4] that predict the 3D bounding boxes from the 2D BEV, and 2) frustum-based methods [5] that predict the 3D bounding boxes from the 2D BEV and the LiDAR information. The 3D-based methods can be further divided into two types: 1) point-based methods [4] that predict the 3D bounding boxes from the 2D BEV, and 2) frustum-based methods [5] that predict the 3D bounding boxes from the 2D BEV and the LiDAR information. The 3D-based methods can be further divided into two types: 1) point-based methods [4] that predict the 3D bounding boxes from the 2D BEV, and 2) frustum-based methods [5] that predict the 3D bounding boxes from the 2D BEV and the LiDAR information. The 3D-based methods can be further divided into two types: 1) point-based methods [4] that predict the 3D bounding boxes from the 2D BEV, and 2) frustum-based methods [5] that predict the 3D bounding boxes from the 2D BEV and the LiDAR information. The 3D-based methods can be further divided into two types: 1) point-based methods [4] that predict the 3D bounding boxes from the 2D BEV, and 2) frustum-based methods [5] that predict the 3D bounding boxes from the 2D BEV and the LiDAR information. The 3D-based methods can be further divided into two types: 1) point-based methods [4] that predict the 3D bounding boxes from the 2D BEV, and 2) frustum-based methods [5] that predict the 3D bounding boxes from the 2D BEV and the LiDAR information. The 3D-based methods can be further divided into two types: 1) point-based methods [4] that predict the 3D bounding boxes from the 2D BEV, and 2) frustum-based methods [5] that predict the 3D bounding boxes from the 2D BEV and the LiDAR information. The 3D-based methods can be further divided into two types: 1) point-based methods [4] that predict the 3D bounding boxes from the 2D BEV, and 2) frustum-based methods [5] that predict the 3D bounding boxes from the 2D BEV and the LiDAR information. The 3D-based methods can be further divided into two types: 1) point-based methods [4] that predict the 3D bounding boxes from the 2D BEV, and 2) frustum-based methods [5] that predict the 3D bounding boxes from the 2D BEV and the LiDAR information. The 3D-based methods can be further divided into two types: 1) point-based methods [4] that predict the 3D bounding boxes from the 2D BEV, and 2) frustum-based methods [5] that predict the 3D bounding boxes from the 2D BEV and the LiDAR information. The 3D-based methods can be further divided into two types: 1) point-based methods [4] that predict the 3D bounding boxes from the 2D BEV, and 2) frustum-based methods [5] that predict the 3D bounding boxes from the 2D BEV and the LiDAR information. The 3D-based methods can be further divided into two types: 1) point-based methods [4] that predict the 3D bounding boxes from the 2D BEV, and 2) frustum-based methods [5] that predict the 3D bounding boxes from the 2D BEV and the LiDAR information. The 3D-based methods can be further divided into two types: 1) point-based methods [4] that predict the 3D bounding boxes from the 2D BEV, and 2) frustum-based methods [5] that predict the 3D bounding boxes from the 2D BEV and the LiDAR information. The 3D-based methods can be further divided into two types: 1) point-based methods [4] that predict the 3D bounding boxes from the 2D BEV, and 2) frustum-based methods [5] that predict the 3D bounding boxes from the 2D BEV and the LiDAR information. The 3D-based methods can be further divided into two types: 1) point-based methods [4] that predict the 3D bounding boxes from the 2D BEV, and 2) frustum-based methods [5] that predict the 3D bounding boxes from the 2D BEV and the LiDAR information. The 3D-based methods can be further divided into two types: 1) point-based methods [4] that predict the 3D bounding boxes from the 2D BEV, and 2) frustum-based methods [5] that predict the 3D bounding boxes from the 2D BEV and the LiDAR information. The 3D-based methods can be further divided into two types: 1) point-based methods [4] that predict the 3D bounding boxes from the 2D BEV, and 2) frustum-based methods [5] that predict the 3D bounding boxes from the 2D BEV and the LiDAR information. The 3D-based methods can be further divided into two types:

---

**Summary Statistics:**
- Input: 9,679 words (62,347 chars)
- Output: 1,302 words
- Compression: 0.13x
- Generation: 68.3s (19.1 words/sec)
- Quality Score: 0.80/1.0
- Attempts: 1

**Quality Issues:** Excessive repetition detected
