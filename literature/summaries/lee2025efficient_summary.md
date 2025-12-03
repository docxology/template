# Efficient LLM Inference with Activation Checkpointing and Hybrid Caching

**Authors:** Sanghyeon Lee, Hongbeen Kim, Soojin Hwang, Guseul Heo, Minwoo Noh, Jaehyuk Huh

**Year:** 2025

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [lee2025efficient.pdf](../pdfs/lee2025efficient.pdf)

**Generated:** 2025-12-03 06:19:31

---

**Overview/Summary**
The paper proposes a novel approach to improve the inference efficiency of large language models (LLMs) by using both activation and key-value (KV) caches in host memory. The authors argue that existing LLM inference systems, such as FlexGen and DeepSpeed- Inference, are not efficient because they only use one type of cache or offload a single type of data to the host. They also propose a new algorithm for mini-batch formation to minimize the imbalance between the number of KV transfers and the number of activation transfers in each mini-batch. The authors evaluate their system on four different LLM models with varying sizes, and compare it with the existing state-of-the-art systems.

**Key Contributions/Findings**
The key contributions of this work are (1) a new hybrid caching approach that uses both activation and KV caches in host memory; and (2) an efficient algorithm for mini-batch formation to minimize the imbalance between the number of KV transfers and the number of activation transfers. The authors show that their system can reduce the volume of data transfer between the host and GPU, which is a critical factor in determining the inference efficiency. They also demonstrate that their approach can improve the throughput by 2.19 times on average compared with FlexGen.

**Methodology/Approach**
The authors first propose a new hybrid caching approach that uses both activation and KV caches in host memory. The proposed approach is based on the observation that the existing LLM inference systems, such as FlexGen and DeepSpeed- Inference, are not efficient because they only use one type of cache or offload a single type of data to the host. They also propose an algorithm for mini-batch formation to minimize the imbalance between the number of KV transfers and the number of activation transfers in each mini-batch. The authors evaluate their system on four different LLM models with varying sizes, and compare it with the existing state-of-the-art systems.

**Results/Data**
The performance evaluation of HybridServe (Hybrid- Serve-Hybrid-Cache) in comparison with prior work and Hybrid-Serve-Act-Cache is shown in Figure 12. The x-axis of each represents the input prompt length, while the y-axis indicates the token generation throughput. Throughput was obtained by dividing the total number of tokens by the end-to-end latency (i.e., prefill latency + generation latency). The batch size is set to 128, and each request in the batch generates 128 output tokens.

**Limitations/Discussion**
The authors compare their system with an Activation-cache only system, denoted as Hybrid-Serve-Act-Cache. They also compare their system with two modern LLM inference frameworks that support host memory offloading: DeepSpeed-Inference and FlexGen. The authors use the configuration that shows the best performance across various setups for FlexGen. Frameworks employing lossy sparsification techniques, such as ALISA and InfiniGen, are not included in their experiments. However, these sparsification methods could still be applied alongside their hybrid cache approach to help reduce data transfer in a complementary way.

**Evaluation**
The authors perform evaluation in a single GPU system featuring an NVIDIA RTX 4090 GPU with 24GB of GDDR6X memory and PCIe 4.0 x16 interface. The host system is powered by a dual-socket 16-core Intel Xeon Gold 6326 processor, with 882GB of DDR4 memory.

**Throughput Improvement**
Figure 12 shows the throughput of HybridServe (Hybrid-Serve-Hybrid-Cache) in comparison with prior work and Hybrid-Serve-Act-Cache. The x-axis of each represents the input prompt length, while the y-axis indicates the token generation throughput. Throughput was obtained by dividing the total number of tokens by the end-to-end latency (i.e., prefill latency + generation latency). The batch size is set to 128, and each request in the batch generates 128 output tokens.

**Limitations/Discussion**
The authors compare their system with an Activation-cache only system, denoted as Hybrid-Serve-Act-Cache. They also compare their system with two modern LLM inference frameworks that support host memory offloading: DeepSpeed-Inference and FlexGen. The authors use the configuration that shows the best performance across various setups for FlexGen. Frameworks employing lossy sparsification techniques, such as ALISA and InfiniGen, are not included in their experiments. However, these sparsification methods could still be applied alongside their hybrid cache approach to help reduce data transfer in a complementary way.

**Evaluation**
The authors perform evaluation in a single GPU system featuring an NVIDIA RTX 4090 GPU with 24GB of GDDR6X memory and PCIe 4.0 x16 interface. The host system is powered by a dual-socket 16-core Intel Xeon Gold 6326 processor, with 882GB of DDR4 memory.

**Throughput Improvement**
Figure 12 shows the throughput of HybridServe (Hybrid-Serve-Hybrid-Cache) in comparison with prior work and Hybrid-Serve-Act-Cache. The x-axis of each represents the input prompt length, while the y-axis indicates the token generation throughput. Throughput was obtained by dividing the total number of tokens by the end-to-end latency (i.e., prefill latency + generation latency). The batch size is set to 128, and each request in the batch generates 128 output tokens.

**Limitations/Discussion**
The authors compare their system with an Activation-cache only system, denoted as Hybrid-Serve-Act-Cache. They also compare their system with two modern LLM inference frameworks that support host memory offloading: DeepSpeed-Inference and FlexGen. The authors use the configuration that shows the best performance across various setups for FlexGen. Frameworks employing lossy sparsification techniques, such as ALISA and InfiniGen, are not included in their experiments. However, these sparsification methods could still be applied alongside their hybrid cache approach to help reduce data transfer in a complementary way.

**Evaluation**
The authors perform evaluation in a single GPU system featuring an NVIDIA RTX 4090 GPU with 24GB of GDDR6X memory and PCIe 4.0 x16 interface. The host system is powered by a dual-socket 16-core Intel Xeon Gold 6326 processor, with 882GB of DDR4 memory.

**Throughput Improvement**
Figure 12 shows the throughput of HybridServe (Hybrid-Serve-Hybrid-Cache) in comparison with prior work and Hybrid-Serve-Act-Cache. The x-axis of each represents the input prompt length, while the y-axis indicates the token generation throughput. Throughput was obtained by dividing the total number of tokens by the end-to-end latency (i.e., prefill latency + generation latency). The batch size is set to 128, and each request in the batch generates 128 output tokens.

**Limitations/Discussion**
The authors compare their system with an Activation-cache only system, denoted as Hybrid-Serve-Act-Cache. They also compare their system with two modern LLM inference frameworks that support host memory offloading: DeepSpeed-Inference and FlexGen. The authors use the configuration that shows the best performance across various setups for FlexGen. Frameworks employing lossy sparsification techniques, such as ALISA and InfiniGen, are not included in their experiments. However, these sparsification methods could still be applied alongside their hybrid cache approach to help reduce data transfer in a complementary way.

**Evaluation**
The authors perform evaluation in a single GPU system featuring an NVIDIA RTX 4090 GPU with 24GB of GDDR6X memory and PCIe 4.0 x16 interface. The host system is powered by a dual-socket 16-core Intel Xeon Gold 6326 processor, with 882GB of DDR4 memory.

**Throughput Improvement**
Figure 12 shows the throughput of HybridServe (Hybrid-Serve-Hybrid-Cache) in comparison with prior work and Hybrid-Serve-Act-Cache. The x-axis of each represents the input prompt length, while the y-axis indicates the token generation throughput. Throughput was obtained by dividing the total number of tokens by the end-to-end latency (i.e., prefill latency + generation latency). The batch size is set to 128, and each request in the batch generates 128 output tokens.

**Limitations/Discussion**
The authors compare their system with an Activation-cache only system, denoted as Hybrid-Serve-Act-Cache. They also compare their system with two modern LLM inference frameworks that support host memory offloading: DeepSpeed-Inference and FlexGen. The authors use the configuration that shows the best performance across various setups for FlexGen. Frameworks employing lossy sparsification techniques, such as ALISA and InfiniGen, are not included in their experiments. However, these sparsification methods could still be applied alongside their hybrid cache approach to help reduce data transfer in a complementary way.

**Evaluation**
The authors perform evaluation in a single GPU system featuring an NVIDIA RTX 4090 GPU with 24GB of GDDR6X memory and PCIe 4.0 x16 interface. The host system is powered by a dual-socket 16-core Intel Xeon Gold 6326 processor, with 882GB of DDR4 memory.

**Throughput Improvement**
Figure 12 shows the throughput of HybridServe (Hybrid-Serve-Hybrid-Cache) in comparison with prior work and Hybrid-Serve-Act-Cache. The x-axis of each represents the input prompt length, while the y-axis indicates the token generation throughput. Throughput was obtained by dividing the total number of tokens by the end-to-end latency (i.e., prefill latency + generation latency). The batch size is set to 128, and each request in the batch generates 128 output tokens.

**Limitations/Discussion**
The authors

---

**Summary Statistics:**
- Input: 10,896 words (71,851 chars)
- Output: 1,403 words
- Compression: 0.13x
- Generation: 68.0s (20.6 words/sec)
- Quality Score: 0.80/1.0
- Attempts: 1

**Quality Issues:** Excessive repetition detected
