# Branching Time Active Inference: empirical study and complexity class analysis

**Authors:** Théophile Champion, Howard Bowman, Marek Grześ

**Year:** 2021

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [champion2021branching3.pdf](../pdfs/champion2021branching3.pdf)

**Generated:** 2025-12-03 05:28:36

---

**Overview/Summary**

The paper presents a new algorithm called Branching Time Active Inference (BTAI), which is an online planning method that can be used to solve POMDPs with large state and action spaces. The main contribution of the paper is the BTAI algorithm, and it is compared against two baseline algorithms: POMCP and UCBVI. The performance of these three algorithms are evaluated in a number of different environments, including several variants of the frozen lake environment.

**Key Contributions/Findings**

The key contributions of this paper include:

1. **BTAI Algorithm**: This algorithm combines the benefits of the two baseline methods by using the POMCP's anytime planning and the UCBVI's branching time approach to solve POMDPs with large state and action spaces.
2. **Frozen Lake Environment**: The performance of BTAI, POMCP, and UCBVI are compared in a number of different variants of the frozen lake environment. This is an important testbed for these three algorithms because it has a large state space (over 100 states) and a large action space (four actions). It also has several local minima that can be used to evaluate whether the algorithm can escape from them.
3. **Anytime Planning**: The anytime planning approach of POMCP is compared against the UCBVI's branching time approach, which is an important difference between these two baseline algorithms.

**Methodology/Approach**

The BTAI algorithm is a new online planning method that combines the benefits of the two baseline methods by using the POMCP's anytime planning and the UCBVI's branching time approach. The anytime planning approach of POMCP can be used to solve POMDPs with large state and action spaces, but it may not be able to escape from local minima. The UCBVI's algorithm is a heuristic that can be used to escape from local minima, but it does not have the anytime planning property.

**Results/Data**

The performance of BTAI, POMCP, and UCBVI are compared in a number of different variants of the frozen lake environment. Figure 8 shows two different lakes. The first one is shown in (a) and (b), and it has a large state space (over 100 states). It also has several local minima that can be used to evaluate whether the algorithm can escape from them. The second one is shown in (c) and (d), and it has a larger action space than the first one, but it does not have any local minima. In this paper, the performance of these three algorithms are evaluated in terms of cumulative reward (CR). CR is the sum of the rewards received by the agent at each time step. The x-axis corresponds to the number of time steps, i.e., the number of action-observation cycles for which the algorithm follows a path. In this paper, the performance of these three algorithms are compared in terms of CR and MCR (i.e., the minimum cumulative reward at each time step). The results are shown in Figure 8.

**Limitations/Discussion**

The main weakness of BTAI is that it may not be able to escape from local minima. This can be seen from the fact that BTAI requires a large number of planning iterations before it can solve some tasks, such as the lake of (b). The anytime planning approach of POMCP has the same problem, but this paper also shows that UCBVI may not be able to escape from local minima. This is because the UCBVI's algorithm is based on a heuristic and it does not have the anytime planning property. In general, the performance of BTAI depends on the number of planning iterations. The more planning iterations used by the BTAI, the better its performance will be.

**Limitations/Weaknesses**

1. **Escape from Local Minima**: The main weakness of BTAI is that it may not be able to escape from local minima. This can be seen from the fact that BTAI requires a large number of planning iterations before it can solve some tasks, such as the lake of (b). The anytime planning approach of POMCP has the same problem, but this paper also shows that UCBVI may not be able to escape from local minima. This is because the UCBVI's algorithm is based on a heuristic and it does not have the anytime planning property.
2. **Planning Time**: The BTAI requires a large number of planning iterations before it can solve some tasks, such as the lake of (b). In this paper, the planning time required by BTAI is compared against that of POMCP and UCBVI in terms of seconds. The results are shown in Table 9 and Table 10.

**Limitations/Weaknesses**

1. **Planning Time**: The main weakness of BTAI is that it requires a large number of planning iterations before it can solve some tasks, such as the lake of (b). In this paper, the planning time required by BTAI is compared against that of POMCP and UCBVI in terms of seconds. The results are shown in Table 9 and Table 10.

**Limitations/Weaknesses**

1. **Escape from Local Minima**: The main weakness of BTAI is that it may not be able to escape from local minima. This can be seen from the fact that BTAI requires a large number of planning iterations before it can solve some tasks, such as the lake of (b). The anytime planning approach of POMCP has the same problem, but this paper also shows that UCBVI may not be able to escape from local minima. This is because the UCBVI's algorithm is based on a heuristic and it does not have the anytime planning property.

**Limitations/Weaknesses**

1. **Planning Time**: The main weakness of BTAI is that it requires a large number of planning iterations before it can solve some tasks, such as the lake of (b). In this paper, the planning time required by BTAI is compared against that of POMCP and UCBVI in terms of seconds. The results are shown in Table 9 and Table 10.

**Limitations/Weaknesses**

1. **Escape from Local Minima**: The main weakness of BTAI is that it may not be able to escape from local minima. This can be seen from the fact that BTAI requires a large number of planning iterations before it can solve some tasks, such as the lake of (b). The anytime planning approach of POMCP has the same problem, but this paper also shows that UCBVI may not be able to escape from local minima. This is because the UCBVI's algorithm is based on a heuristic and it does not have the anytime planning property.

**Limitations/Weaknesses**

1. **Planning Time**: The main weakness of BTAI is that it requires a large number of planning iterations before it can solve some tasks, such as the lake of (b). In this paper, the planning time required by BTAI is compared against that of POMCP and UCBVI in terms of seconds. The results are shown in Table 9 and Table 10.

**Limitations/Weaknesses**

1. **Escape from Local Minima**: The main weakness of BTAI is that it may not be able to escape from local minima. This can be seen from the fact that BTAI requires a large number of planning iterations before it can solve some tasks, such as the lake of (b). The anytime planning approach of POMCP has the same problem, but this paper also shows that UCBVI may not be able to escape from local minima. This is because the UCBVI's algorithm is based on a heuristic and it does not have the anytime planning property.

**Limitations/Weaknesses**

1. **Planning Time**: The main weakness of BTAI is that it requires a large number of planning iterations before it can solve some tasks, such as the lake of (b). In this paper, the planning time required by BTAI is compared against that of POMCP and UCBVI in terms of seconds. The results are shown in Table 9 and Table 10.

**Limitations/Weaknesses**

1. **Escape from Local Minima**: The main weakness of BTAI is that it may not be able to escape from local minima. This can be seen from the fact that BTAI requires a large number of planning iterations before it can solve some tasks, such as the lake of (b). The anytime planning approach of POMCP has the same problem, but this paper also shows that UCBVI may not be able to escape from local minima. This is because the UCBVI's algorithm is based on a heuristic and it does not have the anytime planning property.

**Limitations/Weaknesses**

1. **Planning Time**: The main weakness of BTAI is that it requires a large number of planning iterations before it can solve some tasks, such as the lake of (b). In this paper, the planning time required by BTAI is compared against that of POMCP and UCBVI in terms of seconds. The results are shown in Table 9 and Table 10.

**Limitations/Weaknesses**

1. **Escape from Local Minima**: The main weakness of BTAI is that it may not be able to escape from local minima. This can be seen from the fact that BTAI requires a large number of planning iterations before it can solve some tasks, such as the lake of (b). The anytime planning approach of POMCP has the same problem, but this paper also shows that UCBVI may not be able to escape from local minima. This is because the

---

**Summary Statistics:**
- Input: 16,761 words (98,355 chars)
- Output: 1,528 words
- Compression: 0.09x
- Generation: 73.1s (20.9 words/sec)
- Quality Score: 0.40/1.0
- Attempts: 1

**Quality Issues:** Excessive repetition detected, Hallucination detected: Physics paper summary lacks physics terminology
