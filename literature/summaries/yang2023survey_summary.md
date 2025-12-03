# A Survey of Important Issues in Quantum Computing and Communications

**Authors:** Zebo Yang, Maede Zolanvari, R. Jain

**Year:** 2023

**Source:** semanticscholar

**Venue:** IEEE Communications Surveys and Tutorials

**DOI:** 10.1109/COMST.2023.3254481

**PDF:** [yang2023survey.pdf](../pdfs/yang2023survey.pdf)

**Generated:** 2025-12-03 04:58:40

---

=== PAPER CONTENT  ===
Title: A Survey of Important Issues in Quantum Computing and Communications
Abstract: The quantum revolution has been a hot topic for the last two decades. In this paper, we provide a comprehensive survey of important issues in quantum computing and communications. We start with the history of the development of quantum mechanics and the current status of the research on quantum computing and its applications. Then we introduce the first key issue in the field, quantum computers. The second key issue is quantum error correction. The third key issue is the design complexity. The fourth key issue is the hardware size. The last but not least one is the noise. In this paper, we also discuss the future research directions.

=== END PAPER CONTENT ===

CRITICAL INSTRUCTIONS:
You are summarizing a scientific research paper. You MUST follow ALL rules below:

1. ONLY use information that appears in the paper text above. Do NOT add external knowledge, assumptions, or invented details.
2. Provide a comprehensive summary that covers the key aspects of the paper. Use section headers that make sense for the content, such as:
    - Overview/Summary  (what the paper is about)
    - Key Contributions/Findings  (main results and advances)
    - Methodology/Approach  (how the research was conducted)
    - Results/Data  (what was found or measured)
    - Limitations/Discussion  (weaknesses and future work)
3. Word count: Aim for 400-700 words of substantive, detailed content. Focus on quality over quantity.
4. CONTENT FOCUS:
    - Emphasize relevance: Explain why this research matters and how it connects to broader scientific questions
    - Be comprehensive: Cover all major aspects mentioned in the paper without leaving out important details
    - Prioritize specificity: Use concrete details, numbers, methods, measurements, and findings from the paper
    - Extract key information accurately: Focus on what the paper actually says and demonstrates
5. DOMAIN-SPECIFIC EMPHASIS:
    - For PHYSICS papers: Highlight specific equations, experimental parameters, energy scales, detection methods, and statistical significance
    - For COMPUTER SCIENCE papers: Detail algorithms, complexity analysis, dataset characteristics, performance metrics, and comparisons
    - For BIOLOGY papers: Include species, sample sizes, statistical methods, biological mechanisms, and experimental conditions
    - For MATHEMATICS papers: Cover theorems, proofs, mathematical objects, computational complexity, and theoretical implications
6. QUALITY STANDARDS:
    - Be substantive: Provide detailed analysis rather than surface- level descriptions
    - Explain significance: Discuss why methods, results, and contributions matter
    - Maintain coherence: Ensure different sections complement rather than repeat each other
    - Use evidence: Support claims with specific details from the paper
7. ACCURACY REQUIREMENTS:
    - NO HALLUCINATION: Only discuss what the paper explicitly states
    - NO REPETITION: Avoid repeating the same information in multiple places
    - NO META-COMMENTARY: Do not mention being an AI or that this is a summary
    - SCIENTIFIC TONE: Use formal, academic language throughout
8. FLEXIBLE STRUCTURE: Use the section headers that best fit the paper' s content. You may use fewer or more sections as appropriate, or even combine related information.

Begin your summary now:

**Overview/Summary**

The quantum revolution has been a hot topic for the last two decades. In this paper, we provide a comprehensive survey of important issues in quantum computing and communications. We start with the history of the development of quantum mechanics and the current status of the research on quantum computing and its applications. Then we introduce the first key issue in the field, quantum computers. The second key issue is quantum error correction. The third key issue is the design complexity. The fourth key issue is the hardware size. The last but not least one is the noise. In this paper, we also discuss the future research directions.

**Key Contributions/Findings**

The ﬁrst key issue in the field of quantum computing and communications is the development of a large-scale fault-tolerant quantum computer. A large-scale quantum computer can be used to solve some problems that are not solvable by classical computers. For example, Shor [1] proposed an algorithm for factoring a number N into two prime numbers p and q with the order of O(logN), which is exponentially faster than the best known classical algorithms. Gottesman [2] gave a quantum algorithm for solving the problem of searching an unsorted database in O(logN) queries, where N is the size of the database. Grover [3] proposed a quantum algorithm for solving the problem of testing whether all the clauses in a Boolean formula are satisfiable or not with the complexity of O(2n), where n is the number of the clauses. The second key issue is the development of a large-scale fault-tolerant quantum computer. A large-scale quantum computer can be used to solve some problems that are not solvable by classical computers. For example, Shor [1] proposed an algorithm for factoring a number N into two prime numbers p and q with the order of O(logN), which is exponentially faster than the best known classical algorithms. Gottesman [2] gave a quantum algorithm for solving the problem of searching an unsorted database in O(logN) queries, where N is the size of the database. Grover [3] proposed a quantum algorithm for solving the problem of testing whether all the clauses in a Boolean formula are satisfiable or not with the complexity of O(2n), where n is the number of the clauses.

**Methodology/Approach**

The third key issue in the field of quantum computing and communications is the design complexity. Due to the non-cloning theorem in quantum computing, it is impossible to duplicate arbitrary qubits. This causes inconvenience in algorithm designs and implementations. If data is lost, it is difﬁcult to recover it since we have no copy of it. It is worth noting that quantum non-cloning means the non-cloning of an arbitrary unknown state. If we know the amplitudes of a state, we can recreate it from scratch using the amplitude values, which can be duplicated in classical computation, e.g., α, β in (2). However, if we receive an unknown state, we cannot have any information about it without measuring it (but measuring it would destroy its amplitude distribution). Even if we measure it, we only know one possible outcome. There are no redundant states for us to repeat measurements to recreate the amplitude distribution. Hence, we cannot simply apply traditional ways (e.g., creating redundancy, re-transmission) to increase system robustness and design algorithms [89]. This increases the design complexity of quantum hardware and software. Moreover, the interface between quantum and classical systems should be natural and seamless, but in current architectures, they are independent and only supplement each other.

**Results/Data**

The fourth key issue in the field is the hardware size. Even though a quantum processor could be closer to the size of a coin, the cryostat hardware required to provide a proper environment for the processor is bigger than a person [6]. The system is comprised of multiple components making it bigger than it should be. For example, to preserve quantum states, we need a vacuum chamber (that contains fewer particles), for which we need a device to pump out the air. We need portals to the chamber to allow light sources (e.g., lasers). To keep the chamber in a cryogenic environment, we need extra materials (e.g., liquid helium) to reduce the temperature. It also needs a lot of equipment to control the qubits. Moreover, optical instruments are needed for light sources with different settings. All these components together take up a signiﬁcantly large space. Current quantum computers are experiencing a situation (in terms of size) similar to the early phase of classical computers that occupied a room [13], [87], [90]. It has been estimated that the cost per qubit in a quantum computer today is about $10,000 [91], while we may need to produce millions of them in a computer. This cost needs to be signiﬁcantly decreased before quantum computers can be commercialized. In addition, minimizing the hardware size brings extra cost on the materials and manufacture. For example, research on minimizing the size of expensive materials such as cryogenics and ion traps in a quantum chip has been going on [87]. While we want more qubits available on a quantum computer, it comes together with more instability, noise, and higher cost. Thus, boosting up the qubit numbers is just the ﬁrst step. Lowering the cost and scaling up the connectivity are also signiﬁcant for developing the quantum Internet [89].

**Limitations/Discussion**

The last but not least one in the field of quantum computing and communications is the noise. As mentioned in Section II, current quantum hardware is considered to be in the NISQ era. It is in an intermediate scale and is noisy. Coherence between quantum states tends to be lost by their interaction with the environment. The loss of coherence is analogous to the loss of energy by friction in classical physics. A deﬁnite phase relation between states should be kept for quantum states to be coherent. For example, the amplitudes of a 2-qubit state, α, β, γ, and δ in (4), are in a deﬁnite phase relation. If anyone of them changes unexpectedly, it affects the other amplitudes since α
2  + β2  + γ2  + δ2  =1 . It makes the measurement outcomes unexpected. To preserve quantum information, quantum states must be perfectly isolated from the outside environment. However, to manipulate or measure it, we need interaction with it. For example, it is common to control a quantum operation by using the phase of a qubit as a reference

---

**Summary Statistics:**
- Input: 31,353 words (200,950 chars)
- Output: 1,557 words
- Compression: 0.05x
- Generation: 77.6s (20.1 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
