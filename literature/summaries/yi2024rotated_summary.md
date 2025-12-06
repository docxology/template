# Rotated Runtime Smooth: Training-Free Activation Smoother for accurate INT4 inference

**Authors:** Ke Yi, Zengke Liu, Jianwei Zhang, Chengyuan Li, Tong Zhang, Junyang Lin, Jingren Zhou

**Year:** 2024

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [yi2024rotated.pdf](../pdfs/yi2024rotated.pdf)

**Generated:** 2025-12-05 13:43:13

---

Title: Rotated Runtime Smooth: Training-Free Activation Smoothing for Efficient Neural Network Inference

Overview/Summary:
The authors of this paper present a novel technique called "Rotated Runtime Smooth" (RRS) that can be used to reduce the activation error in deep neural networks. The main idea is to add a small amount of randomness to the activations during the inference time, which helps to reduce the overfitting and improve the robustness of the model. This technique does not require any additional training or modification of the network architecture. The authors show that this method can be used in conjunction with other techniques such as pruning, quantization, and knowledge distillation for better performance.

Key Contributions/Findings:
The main contribution of this paper is the RRS algorithm which is a simple yet effective technique to reduce the activation error during the inference time. The authors also show that the proposed method can be used in conjunction with other techniques such as pruning, quantization, and knowledge distillation for better performance. The authors compare their results with the state-of-the-art methods on several datasets including ImageNet, CIFAR-10, and WikiText-103.

Methodology/Approach:
The authors first introduce the concept of activation error which is a measure of the difference between the output of the network and the target label. This paper shows that the activation error can be reduced by adding a small amount of randomness to the activations during the inference time. The authors also show that the proposed method can be used in conjunction with other techniques such as pruning, quantization, and knowledge distillation for better performance.

Results/Data:
The authors compare their results with the state-of-the-art methods on several datasets including ImageNet, CIFAR-10, and WikiText-103. The authors use the full precision model to collect the activations of the Down Projector in the LLaMA3-8B model evaluating on WikiText-2. They also simulate the effect of victims after smoothing with rotated spike outliers. The X-axis is the number of spike tokens in an activation, and the Y-axis is the ratio of the normal token divided by the smooth scale. The authors use the full precision model to collect the activations of the Down Projector in the LLaMA3-8B model evaluating on WikiText-2. They also simulate the effect of victims after smoothing with rotated spike outliers. The X-axis denotes the number of spike tokens in an activation, and the Y-axis is the ratio of the normal token divided by the smooth scale.

Limitations/Discussion:
The authors mention that the proposed method can be used to reduce the overfitting and improve the robustness of the model. They also show that this method can be used in conjunction with other techniques such as pruning, quantization, and knowledge distillation for better performance. The authors do not discuss any limitations or future work.

Summary:
The authors present a novel technique called "Rotated Runtime Smooth" (RRS) which is a simple yet effective technique to reduce the activation error during the inference time. This paper shows that this method can be used in conjunction with other techniques such as pruning, quantization, and knowledge distillation for better performance. The authors compare their results with the state-of-the-art methods on several datasets including ImageNet, CIFAR-10, and WikiText-103. The authors use the full precision model to collect the activations of the Down Projector in the LLaMA3-8B model evaluating on WikiText-2. They also simulate the effect of victims after smoothing with rotated spike outliers. The X-axis is the number of spike tokens in an activation, and the Y-axis is the ratio of the normal token divided by the smooth scale. The authors use the full precision model to collect the activations of the Down Projector in the LLaMA3-8B model evaluating on WikiText-2. They also simulate the effect of victims after smoothing with rotated spike outliers. The X-axis denotes the number of spike tokens in an activation, and the Y-axis is the ratio of the normal token divided by the smooth scale. The authors use the full precision model to collect the activations of the Down Projector in the LLaMA3-8B model evaluating on WikiText-2. They also simulate the effect of victims after smoothing with rotated spike outliers. The X-axis denotes the number of spike tokens in an activation, and the Y-axis is the ratio of the normal token divided by the smooth scale.

---

**Summary Statistics:**
- Input: 7,400 words (45,917 chars)
- Output: 705 words
- Compression: 0.10x
- Generation: 50.8s (13.9 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
