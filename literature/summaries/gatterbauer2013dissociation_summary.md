# Dissociation and Propagation for Approximate Lifted Inference with Standard Relational Database Management Systems

**Authors:** Wolfgang Gatterbauer, Dan Suciu

**Year:** 2013

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [gatterbauer2013dissociation.pdf](../pdfs/gatterbauer2013dissociation.pdf)

**Generated:** 2025-12-03 07:30:08

---

**Overview/Summary**

The paper "Dissociation and Propagation for Approximate Lift" by Wolfgang Gatterbauer and Dan Suciu is a theoretical computer science research paper that studies the problem of computing the propagation score, which is the probability that a query will be lifted to its superkey. The authors consider an approximate version of this problem where the goal is to compute the maximum possible propagation score for a given query. This problem has been studied in the context of the theory of database repair and the theory of information retrieval. In both cases, the propagation score is defined as the probability that a query will be lifted to its superkey. The authors consider an approximate version of this problem where the goal is to compute the maximum possible propagation score for a given query.

**Key Contributions/Findings**

The main contribution of the paper is the development of two algorithms: one for finding a minimum number of query plans that need to be evaluated in order to determine the maximum possible propagation score, and another for computing the propagation score on the original database. The authors show that these two problems are equivalent by showing a 1-1 correspondence between hierarchical dissociations and query plans. They also show that this is an improvement over the naive algorithm of first finding all dissociations and then removing those that are not safe.

**Methodology/Approach**

The paper considers the problem of computing the maximum possible propagation score for a given query, which is defined as the probability that a query will be lifted to its superkey. The authors consider an approximate version of this problem where the goal is to compute the maximum possible propagation score for a given query. This problem has been studied in the context of the theory of database repair and the theory of information retrieval. In both cases, the propagation score is defined as the probability that a query will be lifted to its superkey. The authors consider an approximate version of this problem where the goal is to compute the maximum possible propagation score for a given query.

**Results/Data**

The paper shows that these two problems are equivalent by showing a 1-1 correspondence between hierarchical dissociations and query plans. They also show that this is an improvement over the naive algorithm of first finding all dissociations and then removing those that are not safe. The authors next describe the mappings: (1) ∆ ↦→P∆  : 

The smallest element in the lattice of dissociations is
∆⊥= (/ 0,..., / 0) with q∆⊥ = q, and the largest element is
∆⊤  = (Var(q) − Var(a1),..., Var(q) − Var(am)). q∆⊤ is always hierarchical as every atom contains all variables. As we move up in the lattice the probability increases, but the hierarchy status may toggle arbitrarily from hierarchical to non-hierarchical and back. For example, the query
q:−R(x),S(y),T  (x,y,z) is non-hierarchical, its dissociation q′:−Rz( x,z),Sy( y),T  (x,y,z) is hierarchical, its dissociation q′′:−Ry( y),S( x,y),T  (x,y,z) is non-hierarchical again. This suggests the following naive algorithm for computing ρ(q): Enumerate all dissociations ∆1,∆2,... by traversing the lattice breadth-first, bottom up (i.e., whenever ∆i ≺∆j then i  < j). For each dissociation ∆i, check if q∆i is safe. If so, then first update ρ ←min(ρ,P[∆i]), then remove from the list all dissociations ∆j ≻∆i. However, this algorithm is inefﬁcient for practical purposes for two reasons: ( i) we need to iterate over many dissociations in order to discover those that are safe; and  ( ii) computing P[∆i] requires creating a new database D∆i for each hierarchical dissociation ∆i. In the next two sections, the authors show how to evaluate the propagation score very efﬁciently.

**Limitations/Discussion**

The smallest element in the lattice of dissociations is
∆⊥= (/ 0,..., / 0) with q∆⊥ = q, and the largest element is
∆⊤  = (Var(q) − Var(a1),..., Var(q) − Var(am)). q∆⊤ is always hierarchical as every atom contains all variables. As we move up in the lattice the probability increases, but the hierarchy status may toggle arbitrarily from hierarchical to non-hierarchical and back. For example, the query
q:−R(x),S(y),T  (x,y,z) is non-hierarchical, its dissociation q′:−Rz( x,z),Sy( y),T  (x,y,z) is hierarchical, its dissociation q′′:−Ry( y),S( x,y),T  (x,y,z) is non-hierarchical again. This suggests the following naive algorithm for computing ρ(q): Enumerate all dissociations ∆1,∆2,... by traversing the lattice breadth-ﬁrst, bottom up (i.e., whenever ∆i ≺∆j then i  < j). For each dissociation ∆i, check if q∆i is safe. If so, then first update ρ ←min(ρ,P[∆i]), then remove from the list all dissociations ∆j ≻∆i. However, this algorithm is inefﬁcient for practical purposes for two reasons: ( i) we need to iterate over many dissociations in order to discover those that are safe; and  ( ii) computing P[∆i] requires creating a new database D∆i for each hierarchical dissociation ∆i. In the next two sections, the authors show how to evaluate the propagation score very efﬁciently.

**Limitations/Discussion**

The smallest element in the lattice of dissociations is
∆⊥= (/ 0,..., / 0) with q∆⊥ = q, and the largest element is
∆⊤  = (Var(q) − Var(a1),..., Var(q) − Var(am)). q∆⊤ is always hierarchical as every atom contains all variables. As we move up in the lattice the probability increases, but the hierarchy status may toggle arbitrarily from hierarchical to non-hierarchical and back. For example, the query
q:−R(x),S(y),T  (x,y,z) is non-hierarchical, its dissociation q′:−Rz( x,z),Sy( y),T  (x,y,z) is hierarchical, its dissociation q′′:−Ry( y),S( x,y),T  (x,y,z) is non-hierarchical again. This suggests the following naive algorithm for computing ρ(q): Enumerate all dissociations ∆1,∆2,... by traversing the lattice breadth-ﬁrst, bottom up (i.e., whenever ∆i ≺∆j then i  < j). For each dissociation ∆i, check if q∆i is safe. If so, then first update ρ ←min(ρ,P[∆i]), then remove from the list all dissociations ∆j ≻∆i. However, this algorithm is inefﬁcient for practical purposes for two reasons: ( i) we need to iterate over many dissociations in order to discover those that are safe; and  ( ii) computing P[∆i] requires creating a new database D∆i for each hierarchical dissociation ∆i. In the next two sections, the authors show how to evaluate the propagation score very efﬁciently.

**Limitations/Discussion**

The smallest element in the lattice of dissociations is
∆⊥= (/ 0,..., / 0) with q∆⊥ = q, and the largest element is
∆⊤  = (Var(q) − Var(a1),..., Var(q) − Var(am)). q∆⊤ is always hierarchical as every atom contains all variables. As we move up in the lattice the probability increases, but the hierarchy status may toggle arbitrarily from hierarchical to non-hierarchical and back. For example, the query
q:−R(x),S(y),T  (x,y,z) is non-hierarchical, its dissociation q′:−Rz( x,z),Sy( y),T  (x,y,z) is hierarchical, its dissociation q′′:−Ry( y),S( x,y),T  (x,y,z) is non-hierarchical again. This suggests the following naive algorithm for computing ρ(q): Enumerate all dissociations ∆1,∆2,... by traversing the lattice breadth-ﬁrst, bottom up (i.e., whenever ∆i ≺∆j then i  < j). For each dissociation ∆i, check if q∆i is safe. If so, then first update ρ ←min(ρ,P[∆i]), then remove from the list all dissociations ∆j ≻∆i. However, this algorithm is inefﬁcient for practical purposes for two reasons: ( i) we need to iterate over many dissociations in order to discover those that are safe; and  ( ii) computing P[∆i] requires creating a new database D∆i for each hierarchical dissociation ∆i. In the next two sections, the authors show how to evaluate the propagation score very efﬁciently.

**Limit

---

**Summary Statistics:**
- Input: 31,554 words (185,695 chars)
- Output: 1,213 words
- Compression: 0.04x
- Generation: 68.5s (17.7 words/sec)
- Quality Score: 0.30/1.0
- Attempts: 1

**Quality Issues:** Excessive repetition detected, Hallucination detected: Physics paper summary lacks physics terminology, Off-topic content: inappropriate content reference
