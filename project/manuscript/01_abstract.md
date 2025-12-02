# Abstract

Containment Theory presents an alternative foundation to classical Set Theory, replacing the primitive notion of membership ($\in$) with spatial containment through boundary distinctions. Building on G. Spencer-Brown's *Laws of Form* (1969), we develop a complete computational framework for boundary logic that demonstrates its equivalence to Boolean algebra while offering distinct advantages in parsimony, geometric intuition, and handling of self-reference.

The calculus of indications operates from just two axioms: **Calling** ($\langle\langle a \rangle\rangle = a$, double crossing returns) and **Crossing** ($\langle\ \rangle\langle\ \rangle = \langle\ \rangle$, marks condense). From these primitives, we derive the complete Boolean algebra, establishing that the marked state $\langle\ \rangle$ corresponds to TRUE and the unmarked void to FALSE, with enclosure $\langle a \rangle$ representing negation and juxtaposition $ab$ representing conjunction.

We present a reduction engine that transforms arbitrary boundary forms to canonical representations, prove termination in polynomial time for ground forms, and verify all derived theorems computationally. Our implementation achieves formal verification of Spencer-Brown's consequences (C1-C9), De Morgan's laws, and the fundamental Boolean axioms through reduction to canonical forms.

The comparison with Set Theory reveals that boundary logic achieves logical completeness with minimal axiomatic commitment (2 vs 9+ axioms in ZFC), provides native geometric interpretation through nested boundaries, and naturally handles self-referential structures through Spencer-Brown's "imaginary" Boolean values—constructs that create paradoxes in classical set theory. These properties suggest applications in circuit design, cognitive modeling, and foundations of computation.

This work establishes Containment Theory as a viable alternative foundation for discrete mathematics, with complete computational verification of its theoretical claims and open-source implementation for further investigation.

**Keywords:** containment theory, boundary logic, Laws of Form, iconic mathematics, Boolean algebra, foundational mathematics, calculus of indications
