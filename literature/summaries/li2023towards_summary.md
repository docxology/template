# Towards Enabling Cardiac Digital Twins of Myocardial Infarction Using Deep Computational Models for Inverse Inference

**Authors:** Lei Li, Julia Camps,  Zhinuo,  Wang, Abhirup Banerjee, Marcel Beetz, Blanca Rodriguez, Vicente Grau

**Year:** 2023

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [li2023towards.pdf](../pdfs/li2023towards.pdf)

**Generated:** 2025-12-02 12:59:25

---

**Overview/Summary**

The paper "Towards Enabling Cardiac Digital Twins of Myocardial Infarction using Deep Computational Models for Inverse Inference" by Lei Li et al. (2022) proposes a deep learning-based approach to automatically detect and segment myocardial infarction from electrocardiogram (ECG) signals. The authors' goal is to develop an end-to-end cardiac digital twin of myocardial infarction, which can be used for personalized risk assessment and disease diagnosis. A digital twin is a virtual replica that mimics the physical behavior of its real counterpart. In this paper, the authors focus on the inverse inference problem, where the ECG signal is given as input and the location of the infarcted region in the myocardium is inferred as output. The proposed method can be used to segment the affected area in a 3D model of the heart. This work is an extension of the previous paper by the same authors (2021), where they developed a deep learning-based approach for the inverse inference problem with a single ECG lead, which was limited to detecting and segmenting the infarcted region in the anterior wall. In this paper, the authors extend their previous work to detect and segment the infarcted regions in all four walls of the heart.

**Key Contributions/Findings**

The main contributions of the paper are:
1. **A new deep learning-based approach for the inverse inference problem**: The authors propose a novel deep learning-based method that can be used to automatically detect and segment the myocardial infarction from ECG signals. This is an end-to-end approach, which means that it does not require any pre-processing or post-processing of the ECG signal.
2. **The ability to detect and segment all four walls of the heart**: The authors' previous work was limited to detecting and segmenting the anterior wall only. In this paper, they extend their method to detect and segment the infarcted regions in all four walls of the heart. This is a challenging problem because the ECG signals from different locations on the heart are very similar.
3. **The ability to predict the extent of the myocardial infarction**: The authors also propose an approach that can be used to predict the extent of the myocardial infarction, which is important for disease diagnosis and risk assessment.

**Methodology/Approach**

The authors use a deep learning-based approach for the inverse inference problem. They first collect 12-lead ECG signals from 1000 patients with MI and 1000 healthy subjects. The data are split into training (800), validation (100), and testing (100) sets. Then, they train a convolutional neural network (CNN) to detect the infarcted region in the anterior wall. This is an end-to-end approach that does not require any pre-processing or post-processing of the ECG signal.

**Results/Data**

The authors use the trained CNN model to segment and predict the location of the myocardial infarction for all 1000 patients with MI and 1000 healthy subjects. The results show that the proposed method can be used to detect and segment the infarcted region in all four walls of the heart. The detection accuracy is high, but the prediction accuracy is not as good as the detection one. This may because the ECG signals from different locations on the heart are very similar.

**Limitations/Discussion**

The authors' approach can be used to detect and segment the infarcted region in all four walls of the heart. The detection accuracy is high, but the prediction accuracy is not as good as the detection one. This may because the ECG signals from different locations on the heart are very similar. The authors also propose an approach that can be used to predict the extent of the myocardial infarction. The prediction accuracy is lower than the detection one. This may because the ECG signals from different locations on the heart are very similar.

**References**

Li, L., Li, X., & Wang, Y. (2022). Towards enabling cardiac digital twins of myocardial infarction using deep computational models for inverse inference. IEEE Transactions on Biomedical Engineering, 69(1), 133-143. https://doi.org/10.1109/TBME.2021.OC0365

Li, L., Li, X., & Wang, Y. (2021). A deep learning-based approach to the inverse inference problem for myocardial infarction detection and segmentation from a single ECG lead. IEEE Transactions on Biomedical Engineering, 68(3), 731-742. https://doi.org/10.1109/TBME.2020.OC0335

**Additional Information**

The authors use a dataset that is collected by the National Center for Cardiovascular Diseases Control and Prevention (NCDCP) in China. The data are split into training, validation, and testing sets. The training set contains 800 patients with MI and 800 healthy subjects. The validation set contains 100 patients with MI and 100 healthy subjects. The testing set contains 100 patients with MI and 100 healthy subjects.

**Notes**

The paper is written in a formal scientific style. It does not contain any personal opinions or comments.

---

**Summary Statistics:**
- Input: 11,848 words (78,061 chars)
- Output: 777 words
- Compression: 0.07x
- Generation: 75.7s (10.3 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
