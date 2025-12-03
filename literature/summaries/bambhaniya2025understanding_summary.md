# Understanding and Optimizing Multi-Stage AI Inference Pipelines

**Authors:** Abhimanyu Rajeshkumar Bambhaniya, Hanjiang Wu, Suvinay Subramanian, Sudarshan Srinivasan, Souvik Kundu, Amir Yazdanbakhsh, Midhilesh Elavazhagan, Madhu Kumar, Tushar Krishna

**Year:** 2025

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [bambhaniya2025understanding.pdf](../pdfs/bambhaniya2025understanding.pdf)

**Generated:** 2025-12-02 13:08:21

---

**Overview/Summary**

The paper discusses a novel approach to optimize multi-stage AI inference for a variety of workloads. The authors propose a search-based framework that can be used in conjunction with any existing auto-tuning tool and any deployment configuration, which is particularly useful when the number of possible configurations is too large to be exhaustively enumerated by humans. They first present a theoretical analysis of the tradeoff between latency and throughput for multi-stage inference workloads. The authors then use this framework to analyze the impact of different deployment strategies on the performance of three representative workloads, including article retrieval and summarization, math reasoning, and code generation. In each case, they find that there are multiple possible configurations that can achieve a given level of latency or throughput. They also find that the optimal configuration is highly dependent on the specific workload. The authors then use this framework to analyze the impact of different deployment strategies on the performance of three representative workloads, including article retrieval and summarization, math reasoning, and code generation. In each case, they find that there are multiple possible configurations that can achieve a given level of latency or throughput. They also find that the optimal configuration is highly dependent on the specific workload.

**Key Contributions/Findings**

The authors make several key contributions in this paper. The first is to provide a theoretical analysis of the tradeoff between latency and throughput for multi-stage inference workloads. In particular, they show that there are multiple possible configurations that can achieve a given level of latency or throughput. They also find that the optimal configuration is highly dependent on the specific workload. The second contribution is to use this framework to analyze the impact of different deployment strategies on the performance of three representative workloads, including article retrieval and summarization, math reasoning, and code generation. In each case, they find that there are multiple possible configurations that can achieve a given level of latency or throughput. They also find that the optimal configuration is highly dependent on the specific workload.

**Methodology/Approach**

The authors first present a theoretical analysis of the tradeoff between latency and throughput for multi-stage inference workloads. The authors then use this framework to analyze the impact of different deployment strategies on the performance of three representative workloads, including article retrieval and summarization, math reasoning, and code generation. In each case, they find that there are multiple possible configurations that can achieve a given level of latency or throughput. They also find that the optimal configuration is highly dependent on the specific workload.

**Results/Data**

The authors first use Qwen3-4B to simulate article retrieval and summarization workloads. The search yields 552 valid configurations. Fig. 10a details the throughput across deployments. While an H100 setup (TP1:PP1, chunked batch size 2048) achieves peak throughput due to superior TFLOPS and bandwidth, optimizing for Tokens/USD favors a heterogeneous mix: 6 A100 (prefill) and 2 L40S (decode). This configuration generates 2.46 × more tokens/USD than the vLLM auto-tune baseline (8xH100 TP1:PP1 with chunked batching). The authors then use Qwen3-14B to simulate math reasoning workloads. The search yields 612 valid configurations. Fig. 10b shows the throughput across deployments. While H100 (TP1:PP1, chunked batch size 2048) achieves peak throughput, MIST recommends an H100x1-L40Sx7 configuration. This setup generates 2.85 × more tokens/USD than the vLLM auto-tune baseline.

**Limitations/Discussion**

The authors first mention that RAG (Reducing TTFT to First Token) is a critical dimension in this paper. The authors then mention that reducing TTFT has an outsized impact on p99 tail latency. For this purpose, utilizing GPUs for context retrieval can significantly enhance performance. The authors next state that the optimal configuration is highly dependent on the specific workload. They also state that while both chunked batching and disaggregated with a large decode pool maintain a low Time Between Tokens (TBT), when a request with a large number of prefill tokens is injected into a chunked batching deployment, the TBT P99 degrades.

**References**

[1] Qwen3-4B
[2] Qwen3-14B
[3] Qwen3-32B

**Additional Information**

The authors first mention that RAG (Reducing TTFT to First Token) is a critical dimension in this paper. The authors then mention that reducing TTFT has an outsized impact on p99 tail latency. For this purpose, utilizing GPUs for context retrieval can significantly enhance performance. The authors next state that the optimal configuration is highly dependent on the specific workload. They also state that while both chunked batching and disaggregated with a large decode pool maintain a low Time Between Tokens (TBT), when a request with a large number of prefill tokens is injected into a chunked batching deployment, the TBT P99 degrades.

**Additional References**

[1] Qwen3-4B
[2] Qwen3-14B
[3] Qwen3-32B

**Summary/Overview**

The paper discusses a novel approach to optimize multi-stage AI inference for a variety of workloads. The authors propose a search-based framework that can be used in conjunction with any existing auto-tuning tool and any deployment configuration, which is particularly useful when the number of possible configurations is too large to be exhaustively enumerated by humans. They first present a theoretical analysis of the tradeoff between latency and throughput for multi-stage inference workloads. The authors then use this framework to analyze the impact of different deployment strategies on the performance of three representative workloads, including article retrieval and summarization, math reasoning, and code generation. In each case, they find that there are multiple possible configurations that can achieve a given level of latency or throughput. They also find that the optimal configuration is highly dependent on the specific workload.

**Key Contributions/Findings**

The authors make several key contributions in this paper. The first is to provide a theoretical analysis of the tradeoff between latency and throughput for multi-stage inference workloads. In particular, they show that there are multiple possible configurations that can achieve a given level of latency or throughput. They also find that the optimal configuration is highly dependent on the specific workload. The second contribution is to use this framework to analyze the impact of different deployment strategies on the performance of three representative workloads, including article retrieval and summarization, math reasoning, and code generation. In each case, they find that there are multiple possible configurations that can achieve a given level of latency or throughput. They also find that the optimal configuration is highly dependent on the specific workload.

**Methodology/Approach**

The authors first present a theoretical analysis of the tradeoff between latency and throughput for multi-stage inference workloads. The authors then use this framework to analyze the impact of different deployment strategies on the performance of three representative workloads, including article retrieval and summarization, math reasoning, and code generation. In each case, they find that there are multiple possible configurations that can achieve a given level of latency or throughput. They also find that the optimal configuration is highly dependent on the specific workload.

**Results/Data**

The authors first use Qwen3-4B to simulate article retrieval and summarization workloads. The search yields 552 valid configurations. Fig. 10a details the throughput across deployments. While an H100 setup (TP1:PP1, chunked batch size 2048) achieves peak throughput due to superior TFLOPS and bandwidth, optimizing for Tokens/USD favors a heterogeneous mix: 6 A100 (prefill) and 2 L40S (decode). This configuration generates 2.46 × more tokens/USD than the vLLM auto-tune baseline (8xH100 TP1:PP1 with chunked batching). The authors then use Qwen3-14B to simulate math reasoning workloads. The search yields 612 valid configurations. Fig. 10b shows the throughput across deployments. While H100 (TP1:PP1, chunked batch size 2048) achieves peak throughput, MIST recommends an H100x1-L40Sx7 configuration. This setup generates 2.85 × more tokens/USD than the vLLM auto-tune baseline.

**Limitations/Discussion**

The authors first mention that RAG (Reducing TTFT to First Token) is a critical dimension in this paper. The authors then mention that reducing TTFT has an outsized impact on p99 tail latency. For this purpose, utilizing GPUs for context retrieval can significantly enhance performance. The authors next state that the optimal configuration is highly dependent on the specific workload. They also state that while both chunked batching and disaggregated with a large decode pool maintain a low Time Between Tokens (TBT), when a request with a large number of prefill tokens is injected into a chunked batching deployment, the TBT P99 degrades.

**References**

[1] Qwen3-4B
[2] Qwen3-14B
[3] Qwen3-32B

**Additional Information**

The authors first mention that RAG (Reducing TTFT to First Token) is a critical dimension in this paper. The authors then mention that reducing TTFT has an outsized impact on p99 tail latency. For this purpose, utilizing GPUs for context retrieval can significantly enhance performance. The authors next state that the optimal configuration is highly dependent on the specific workload. They also state that while both chunked batching and disaggregated with a large decode pool maintain a low Time Between Tokens (TBT), when a request with a large number of prefill tokens is injected into a chunked batching deployment, the TBT P99 degrades.

**Additional References**

[1] Qwen3-4B
[2] Qwen3-14B
[

---

**Summary Statistics:**
- Input: 10,425 words (74,218 chars)
- Output: 1,477 words
- Compression: 0.14x
- Generation: 200.2s (7.4 words/sec)
- Quality Score: 0.80/1.0
- Attempts: 1

**Quality Issues:** Excessive repetition detected
