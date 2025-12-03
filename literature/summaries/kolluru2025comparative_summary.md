# Comparative Analysis of Large Language Model Inference Serving Systems: A Performance Study of vLLM and HuggingFace TGI

**Authors:** Saicharan Kolluru

**Year:** 2025

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [kolluru2025comparative.pdf](../pdfs/kolluru2025comparative.pdf)

**Generated:** 2025-12-03 04:08:17

---

**Overview/Summary**

The paper presents a comprehensive empirical evaluation of two leading open-source frameworks for large language model (LLM) serving: vLLM and HuggingFace TGI. The authors compare the performance profiles of these two systems across multiple model sizes, concurrency levels, and workload patterns to guide practitioners in selecting the best framework for their specific use case.

**Key Contributions/Findings**

The key findings are as follows:
1. **vLLM achieves 2-24x higher throughput than TGI depending on concurrency and model size**, with the advantage most pronounced under high load.
2. **TGI provides 1.3-2x lower Time-to-First-Token at low concurrency, making it more responsive for interactive applications**.
3. **vLLM utilizes 19-27% less GPU memory through PagedAttention, enabling larger batch sizes in memory-constrained scenarios**.
4. **vLLM achieves 85-92% GPU utilization compared to TGI's 68-74%, translating to better resource efficiency**.
5. **TGI shows better p50 Time-to-First-Token but worse p99 total latency, indicating different scheduling trade-offs**.

**Methodology/Approach**

The authors compare the performance of vLLM and HuggingFace TGI through a systematic benchmarking process across multiple model sizes (from 125M to 3.2B parameters) and concurrency levels (from 1 to 16 GPUs). The two systems are evaluated on a set of representative workloads that vary in terms of generation length, batch size, and latency requirements.

**Results/Data**

The authors' key findings are based on the following results:
- **Throughput**: vLLM achieves 2-24x higher throughput than TGI depending on concurrency and model size. The advantage is most pronounced under high load.
- **Time-to-First-Token (TTFT)**: TGI provides 1.3-2x lower TTFT at low concurrency, making it more responsive for interactive applications. However, the p99 total latency of vLLM is worse than that of TGI.
- **GPU Utilization**: vLLM utilizes 19-27% less GPU memory through PagedAttention, enabling larger batch sizes in memory-constrained scenarios. The authors also compare the two systems' utilization rates at different concurrency levels.

**Limitations/Discussion**

The limitations and future work are as follows:
1. **Model size**: This paper only compares the performance of vLLM and TGI with a set of representative model sizes, which may not cover all possible scenarios.
2. **Workload characteristics**: The authors' findings should be guided by workload characteristics: high-throughput, batch- oriented workloads favor vLLM; latency-sensitive, interactive applications may prefer TGI; memory-constrained deployments benefit from vLLM's efficiency.
3. **Organizational priorities and existing infrastructure**: The choice of framework should align with organizational priorities, existing infrastructure, and specific application requirements.

**Conclusion**

The authors' main conclusions are as follows:
1. **vLLM achieves 2-24x higher throughput than TGI depending on concurrency and model size**, with the advantage most pronounced under high load.
2. **TGI provides 1.3-2x lower Time-to-First-Token at low concurrency, making it more responsive for interactive applications**.
3. **vLLM utilizes 19-27% less GPU memory through PagedAttention, enabling larger batch sizes in memory-constrained scenarios**.
4. **vLLM achieves 85-92% GPU utilization compared to TGI's 68-74%, translating to better resource efficiency**.
5. **TGI shows better p50 TTFT but worse p99 total latency, indicating different scheduling trade-offs**.

The authors' work is based on the following limitations and future work:
1. **Practitioner guidance**: The choice of framework should be guided by workload characteristics: high-throughput, batch- oriented workloads favor vLLM; latency-sensitive, interactive applications may prefer TGI; memory-constrained deployments benefit from vLLM's efficiency.
2. **Organizational priorities and existing infrastructure**: The choice of framework should align with organizational priorities, existing infrastructure, and specific application requirements.

**Acknowledgments**

The authors thank the vLLM and HuggingFace teams for developing these valuable open-source tools.

**References**

[1] Brown, T., Mann, B., Ryder, N., Subbiah, M., Kaplan, J. D., Dhariwal, P.,  ... & Amodei, D. (2020). Language models are few-shot learners. Advances in neural information processing systems, 33, 1877-1901.
[2] Chowdhery, A., Narang, S., Devlin, J., Bosma, M., Mishra, G., Roberts, A.,  ... & Fiedel, N. (2022). PaLM: Scaling language modeling with pathways. arXiv preprint arXiv:2204.02311.
[3] Touvron, H., Lavril, T., Izacard, G., Martinet, X., Lachaux, M. A., Martinet, X.,  ... & Lample, G. (2023). LLaMA: Open and efficient foundation language models. arXiv preprint arXiv:2302.13971.
[4] Kwon, W., Li, Z., Zhuang, S., Sheng, Y., Zheng, L., Yu, C. H.,  ... & Stoica, I. (2023). Efficient memory management for large language model serving with PagedAttention. Proceedings of the 29th Symposium on Operating Systems Principles, 611-626.
[5] HuggingFace. (2023). Text Generation Inference. GitHub repository, https://github.com/huggingface/text-generation-inference.
[6] Pope, R., Douglas, S., Chowdhery, A., Devlin, J., Bradbury, J., Heek, J.,  ... & Fiedel, N. (2022). Efficiently scaling transformer inference. arXiv preprint arXiv:2211.05102.
[7] Yu, G. I., Jeong, J. S., Kim, G. W., Kim, S.,  ... & Chun, B. G. (2022). Orca: A distributed serving system for transformer-based generative models. Proceedings of the 16th USENIX Symposium on Operating Systems Design and Implementation, 521-538.
[8] Aminabadi, R. Y., Rajbhandari, S., Zhang, M., Awan, A. A., Li, C., Li, D.,  ... & He, Y. (2022). Deep-Speed inference: Enabling efficient inference of transformer models at unprecedented scale. Proceedings of the International Conference for High Performance Computing, Networking, Storage and Analysis, 1-15.
[9] Sheng, Y., Zheng, L., Yuan, B., Li, Z., Ryabinin, M., Chen, B.,  ... & Stoica, I. (2023). FlexGen: High-throughput generative inference of large language models with a single GPU. arXiv preprint arXiv:2303.06865.
[10] Zheng, L., Chiang, W. L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y.,  ... & Stoica, I. (2023). Judging LLM-As-A-Judge with MT-Bench and chatbot arena. arXiv preprint arXiv:2306.05685.

**References**

[1] Brown, T., Mann, B., Ryder, N., Subbiah, M., Kaplan, J. D., Dhariwal, P.,  ... & Amodei, D. (2020). Language models are few-shot learners. Advances in neural information processing systems, 33, 1877-1901.
[2] Chowdhery, A., Narang, S., Devlin, J., Bosma, M., Mishra, G., Roberts, A.,  ... & Fiedel, N. (2022). PaLM: Scaling language modeling with pathways. arXiv preprint arXiv:2204.02311.
[3] Touvron, H., Lavril, T., Izacard, G., Martinet, X., Lachaux, M. A., Martinet, X.,  ... & Lample, G. (2023). LLaMA: Open and efficient foundation language models. arXiv preprint arXiv:2302.13971.
[4] Kwon, W., Li, Z., Zhuang, S., Sheng, Y., Zheng, L., Yu, C. H.,  ... & Stoica, I. (2023). Efficient memory management for large language model serving with PagedAttention. Proceedings of the 29th Symposium on Operating Systems Principles, 611-626.
[5] HuggingFace. (2023). Text Generation Inference. GitHub repository, https://github.com/huggingface/text-generation-inference.
[6] Pope, R., Douglas, S., Chowdhery, A., Devlin, J., Bradbury, J., Heek, J.,  ... & Fiedel, N. (2022). Efficiently scaling transformer inference. arXiv preprint arXiv:2211.05102.
[7] Yu, G. I., Jeong, J. S., Kim, G. W., Kim, S.,  ... & Chun, B. G. (2022). Orca: A distributed serving system for transformer-based generative models. Proceedings of the

---

**Summary Statistics:**
- Input: 3,032 words (23,423 chars)
- Output: 1,058 words
- Compression: 0.35x
- Generation: 68.6s (15.4 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
