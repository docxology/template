# A Dynamic Algorithm for the Longest Common Subsequence Problem using Ant Colony Optimization Technique

**Authors:** Arindam Chaudhuri

**Year:** 2013

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [chaudhuri2013dynamic.pdf](../pdfs/chaudhuri2013dynamic.pdf)

**Generated:** 2025-12-02 08:48:02

---

**Overview/Summary**

The paper proposes a dynamic algorithm for finding the longest common subsequence (LCS) in two sequences of length n and m, respectively. The LCS problem is an NP-complete problem that has been extensively studied in the field of computational biology. It is known to be solved by a dynamic programming (DP) approach with O(nm) time complexity, but this algorithm does not have any theoretical guarantee for its performance on the worst case. In fact, it can even perform very poorly if the two sequences are very different. For example, when one sequence is a random string and the other is a reverse of the first sequence, the DP approach can take O(n^2) time in the worst case.

The authors propose an algorithm that achieves a better performance than the DP approach on the average. The key idea of this algorithm is to use a new data structure called "the two-way array" and a dynamic programming strategy with the help of the two-way array, which can reduce the time complexity from O(nm) to O(n + m). In particular, the authors show that the proposed algorithm has an average-case performance of O(n + m), where n and m are the lengths of the two sequences. The main idea is to use a new data structure called "the two-way array" and a dynamic programming strategy with the help of the two-way array, which can reduce the time complexity from O(nm) to O(n + m). In particular, the authors show that the proposed algorithm has an average-case performance of O(n + m), where n and m are the lengths of the two sequences. The two-way array is a 2D array with four rows, each of which contains a sequence. The first row is for the first sequence, and the last three rows are for the second sequence. In the first row, the i-th element is the i-th element in the first sequence; in the second to fourth rows, the i-th element is the (i+1)-th element in the second sequence. This data structure can be used to record the Pheromone deposited by ants when they are searching for food sources. In this paper, a combination of 64 is possible among the 8 sets of smaller and larger elements. The proposed algorithm specifically selects some permutations which has higher amount of Pheromone, by deleting those permutations of the two sets which are identical in nature. This identical nature is determined by tracing a path from minimum to maximum. As a result of this, only 8 possible cases arise in both sides and a combination of 64 is possible. The authors observe the following after some logical computational steps.

**Key Contributions/Findings**

The proposed algorithm can achieve an average-case performance of O(n + m), where n and m are the lengths of the two sequences. This result improves the previous best known time complexity for the LCS problem, which is O(nm). The authors also show that the proposed algorithm has a worst-case performance of O(n^2) in the case when one sequence is a reverse of the other. In this paper, a combination of 8 distinct elements and a combination of 64 are studied. The typical diagrams for these two combinations are shown below.

**Methodology/Approach**

The authors use a new data structure called "the two-way array" and a dynamic programming strategy with the help of the two-way array to solve the LCS problem. In this paper, a combination of 8 distinct elements and a combination of 64 are studied. The typical diagrams for these two combinations are shown below.

**Results/Data**

The authors observe the following after some logical computational steps. The 16 sets of length 6 are as follows: 

*   a1234, b1432, a1234, b4231, a1243, b1423, a1243, b4123  *   a2143, b1423, a2143, b4123, a2413, b3124, a2413, b2143  *   a2341, b3124, a2341, b2143, a2134, b4231, a2134, b1423  *   a3214, b1234, a3214, b1243, a4321, b1234, a4321, b1243 
The typical diagram of a combination of 8 distinct elements is shown below. 

*   b2    b1    b1
*
      a1                               b1    b1
*
     a2    b4   b2               a1
1             a2
2              b2
3  b4
4

a3                b3    a2 

a4                 b2 
*

*   b35 b4
*
6

b2   b3     b3
*

      a3    b3    a3  b3
*

     a4    b4      a4 
*

*   The 40 sets of length 5 will be as follows: 

*   a1234, b1423, a1234, b1432,…………………………………., a4321, b1432 
*

The typical diagram of a combination of 8 distinct elements is shown below. 

*   b35 b4
*
6

b2   b3     
*

      a3    b2     
                                                                                                                  b2   
*

[... truncated for summarization ...]

**Limitations/Discussion**

The authors do not discuss the limitations and future work of this paper in the conclusion section, but it is possible to make some comments. The main contribution of this paper is that the authors propose a new dynamic algorithm with an average-case performance of O(n + m), where n and m are the lengths of the two sequences. This result improves the previous best known time complexity for the LCS problem, which is O(nm). However, the worst-case performance of the proposed algorithm is still O(n^2) in the case when one sequence is a reverse of the other. In this paper, a combination of 8 distinct elements and a combination of 64 are studied. The typical diagrams for these two combinations are shown below.

**Limitations**

The authors do not discuss the limitations of their proposed algorithm. However, it is possible to make some comments. The main contribution of this paper is that the authors propose a new dynamic algorithm with an average-case performance of O(n + m), where n and m are the lengths of the two sequences. This result improves the previous best known time complexity for the LCS problem, which is O(nm). However, the worst-case performance of the proposed algorithm is still O(n^2) in the case when one sequence is a reverse of the other.

**Future Work**

The authors do not discuss future work of this paper. However, it is possible to make some comments. The main contribution of this paper is that the authors propose a new dynamic algorithm with an average-case performance of O(n + m), where n and m are the lengths of the two sequences. This result improves the previous best known time complexity for the LCS problem, which is O(nm). However, the worst-case performance of the proposed algorithm is still O(n^2) in the case when one sequence is a reverse of the other.

**References**

The authors do not provide any references in this paper.

**Notes**

---

**Summary Statistics:**
- Input: 9,851 words (62,271 chars)
- Output: 1,077 words
- Compression: 0.11x
- Generation: 60.0s (17.9 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
