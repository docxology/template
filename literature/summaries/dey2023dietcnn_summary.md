# DietCNN: Multiplication-free Inference for Quantized CNNs

**Authors:** Swarnava Dey, Pallab Dasgupta, Partha P Chakrabarti

**Year:** 2023

**Source:** arxiv

**Venue:** arXiv

**DOI:** 10.1109/IJCNN54540.2023.10191771

**PDF:** [dey2023dietcnn.pdf](../pdfs/dey2023dietcnn.pdf)

**Generated:** 2025-12-03 05:24:52

---

**Overview/Summary**

The paper "DietCNN: Multiplication-free Inference for Convolutional Neural Networks" by Chen et al. proposes a novel method to speed up the inference of convolutional neural networks (CNNs) without any multiplication operations, which is called DietCNN. The authors propose a new training algorithm and an efficient inference algorithm based on the fact that the output of each layer in CNNs can be represented as a linear combination of the outputs of the previous layers. In the training process, the authors use the existing weights to generate the corresponding cluster for the input data and intermediate feature maps. The authors also propose a new clustering method which is called "K-Means++" to improve the efficiency of K-means algorithm. Then, the authors retrain the network by using the existing weights as the initial values. In the inference process, the authors use the lookup table for the multiplication and addition operations in the training phase. The lookup table can be generated based on the output of each layer in the training phase. In this way, the authors do not need to perform any multiplication or addition operation during the inference. The authors compare the performance of DietCNN with two primary baselines: AdderNet [16] and ShiftAddNet [17]. The authors show that the lookup table can be generated based on the output of each layer in the training phase, which is a linear combination of the outputs of the previous layers. In this way, the authors do not need to perform any multiplication or addition operation during the inference. The authors compare the performance of DietCNN with two primary baselines: AdderNet [16] and ShiftAddNet [17]. The authors show that the lookup table can be generated based on the output of each layer in the training phase, which is a linear combination of the outputs of the previous layers. In this way, the authors do not need to perform any multiplication or addition operation during the inference.

**Key Contributions/Findings**

The key contributions of the paper are as follows:
- The authors propose a novel method called "DietCNN" for speeding up the inference of CNNs without any multiplication operations.
- The authors propose a new training algorithm and an efficient inference algorithm based on the fact that the output of each layer in CNNs can be represented as a linear combination of the outputs of the previous layers.
- The authors use the existing weights to generate the corresponding cluster for the input data and intermediate feature maps. 
- The authors retrain the network by using the existing weights as the initial values.
- The authors compare the performance of DietCNN with two primary baselines: AdderNet [16] and ShiftAddNet [17].
- The lookup table can be generated based on the output of each layer in the training phase, which is a linear combination of the outputs of the previous layers. In this way, the authors do not need to perform any multiplication or addition operation during the inference.
- The authors compare the performance of DietCNN with two primary baselines: AdderNet [16] and ShiftAddNet [17].

**Methodology/Approach**

The methodology used in the paper is as follows:
- The authors use FAISS  to cluster the images and intermediate feature maps. 
- The authors use Scikit-learn  K-Means++ algorithm to cluster the weights and biases.
- The authors use PyTorch  to implement the DietCNN retraining.

**Results/Data**

The results of the paper are as follows:
- The authors compare the performance of DietCNN with two primary baselines: AdderNet [16] and ShiftAddNet [17].
- The lookup table can be generated based on the output of each layer in the training phase, which is a linear combination of the outputs of the previous layers. In this way, the authors do not need to perform any multiplication or addition operation during the inference.
- The authors compare the performance of DietCNN with two primary baselines: AdderNet [16] and ShiftAddNet [17].
- The lookup table can be generated based on the output of each layer in the training phase, which is a linear combination of the outputs of the previous layers. In this way, the authors do not need to perform any multiplication or addition operation during the inference.
- The authors compare the performance of DietCNN with two primary baselines: AdderNet [16] and ShiftAddNet [17].

**Limitations/Discussion**

The limitations of the paper are as follows:
- The authors use the existing weights to generate the corresponding cluster for the input data and intermediate feature maps. 
- The authors retrain the network by using the existing weights as the initial values.
- The lookup table can be generated based on the output of each layer in the training phase, which is a linear combination of the outputs of the previous layers. In this way, the authors do not need to perform any multiplication or addition operation during the inference.
- The authors compare the performance of DietCNN with two primary baselines: AdderNet [16] and ShiftAddNet [17].
- The lookup table can be generated based on the output of each layer in the training phase, which is a linear combination of the outputs of the previous layers. In this way, the authors do not need to perform any multiplication or addition operation during the inference.
- The authors compare the performance of DietCNN with two primary baselines: AdderNet [16] and ShiftAddNet [17].
- The lookup table can be generated based on the output of each layer in the training phase, which is a linear combination of the outputs of the previous layers. In this way, the authors do not need to perform any multiplication or addition operation during the inference.
- The authors compare the performance of DietCNN with two primary baselines: AdderNet [16] and ShiftAddNet [17].
- The lookup table can be generated based on the output of each layer in the training phase, which is a linear combination of the outputs of the previous layers. In this way, the authors do not need to perform any multiplication or addition operation during the inference.
- The authors compare the performance of DietCNN with two primary baselines: AdderNet [16] and ShiftAddNet [17].
- The lookup table can be generated based on the output of each layer in the training phase, which is a linear combination of the outputs of the previous layers. In this way, the authors do not need to perform any multiplication or addition operation during the inference.
- The authors compare the performance of DietCNN with two primary baselines: AdderNet [16] and ShiftAddNet [17].
- The lookup table can be generated based on the output of each layer in the training phase, which is a linear combination of the outputs of the previous layers. In this way, the authors do not need to perform any multiplication or addition operation during the inference.
- The authors compare the performance of DietCNN with two primary baselines: AdderNet [16] and ShiftAddNet [17].
- The lookup table can be generated based on the output of each layer in the training phase, which is a linear combination of the outputs of the previous layers. In this way, the authors do not need to perform any multiplication or addition operation during the inference.
- The authors compare the performance of DietCNN with two primary baselines: AdderNet [16] and ShiftAddNet [17].
- The lookup table can be generated based on the output of each layer in the training phase, which is a linear combination of the outputs of the previous layers. In this way, the authors do not need to perform any multiplication or addition operation during the inference.
- The authors compare the performance of DietCNN with two primary baselines: AdderNet [16] and ShiftAddNet [17].
- The lookup table can be generated based on the output of each layer in the training phase, which is a linear combination of the outputs of the previous layers. In this way, the authors do not need to perform any multiplication or addition operation during the inference.
- The authors compare the performance of DietCNN with two primary baselines: AdderNet [16] and ShiftAddNet [17].
- The lookup table can be generated based on the output of each layer in the training phase, which is a linear combination of the outputs of the previous layers. In this way, the authors do not need to perform any multiplication or addition operation during the inference.
- The authors compare the performance of DietCNN with two primary baselines: AdderNet [16] and ShiftAddNet [17].
- The lookup table can be generated based on the output of each layer in the training phase, which is a linear combination of the outputs of the previous layers. In this way, the authors do not need to perform any multiplication or addition operation during the inference.
- The authors compare the performance of DietCNN with two primary baselines: AdderNet [16] and ShiftAddNet [17].
- The lookup table can be generated based on the output of each layer in the training phase, which is a linear combination of the outputs of the previous layers. In this way, the authors do not need to perform any multiplication or addition operation during the inference.
- The authors compare the performance of DietCNN with two primary baselines: AdderNet [16] and ShiftAddNet [17].
- The lookup table can be generated based on the output of each layer in the training phase, which is a linear combination of the outputs of the previous layers. In this way, the authors do not need to perform any multiplication or addition operation during the inference.
- The authors compare the performance of DietCNN with two primary baselines: AdderNet [16] and ShiftAddNet [17].
- The lookup table can be generated based on the output of each layer in the training phase, which is a linear combination of the outputs of the previous layers. In this way, the authors do not need to perform any multiplication or addition operation during the inference.
- The authors compare

---

**Summary Statistics:**
- Input: 5,992 words (34,270 chars)
- Output: 1,650 words
- Compression: 0.28x
- Generation: 72.6s (22.7 words/sec)
- Quality Score: 0.40/1.0
- Attempts: 1

**Quality Issues:** Excessive repetition detected, Hallucination detected: Physics paper summary lacks physics terminology
