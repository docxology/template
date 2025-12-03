# Variational approach to enhanced sampling and free energy calculations.

**Authors:** O. Valsson, M. Parrinello

**Year:** 2014

**Source:** semanticscholar

**Venue:** Physical Review Letters

**DOI:** 10.1103/PhysRevLett.113.090601

**PDF:** [valsson2014variational.pdf](../pdfs/valsson2014variational.pdf)

**Generated:** 2025-12-02 08:13:44

---

**Overview/Summary**
The authors of this paper present a new method for enhanced sampling and free energy calculations in molecular simulations. The main idea is to optimize the potential function $V$ by minimizing the difference between the target probability distribution $p$ and the current one, $q$, which is the Boltzmann weight $e^{-\beta V}$, through an iterative procedure. This new approach is called Variational Approach (VA). In this paper, the authors apply the VA to a number of different problems in molecular simulations. The first part of the paper reviews the main results from previous work on free energy calculations and the second part describes the details of the VA. The third part presents the numerical results for the three test cases: the Lennard-Jones cluster, the SPC water model, and a simple model of the protein folding problem. 

**Key Contributions/Findings**
The main result of this paper is that the VA provides a new way to obtain free energy estimates with high accuracy. The authors show that the VA can be used for both enhanced sampling (ES) and free energy calculations (FEC). In the first part, the authors review the previous work on FFC. They also provide a number of references which are not included in this paper. The second part describes the details of the VA. The third part presents the numerical results for the three test cases: the Lennard-Jones cluster, the SPC water model, and a simple model of the protein folding problem. 

**Methodology/Approach**
The authors use the variational principle to obtain an approximate free energy function $F$. They first introduce the concept of the target distribution $p$ and the current one $q$, which is the Boltzmann weight $e^{-\beta V}$. The VA can be used for both enhanced sampling (ES) and FFC. In the first part, the authors review the previous work on FFC. They also provide a number of references which are not included in this paper. The second part describes the details of the VA. 

**Results/Data**
The authors use the variational principle to obtain an approximate free energy function $F$. They first introduce the concept of the target distribution $p$ and the current one $q$, which is the Boltzmann weight $e^{-\beta V}$. The VA can be used for both enhanced sampling (ES) and FFC. In the first part, the authors review the previous work on FFC. They also provide a number of references which are not included in this paper. The second part describes the details of the VA. 

**Limitations/Discussion**
The authors point out that there is ample room for improvement. The optimization procedure presented here is not necessarily optimal and different systems and CVs might require different optimization strategies and different basis set. They plan to explore a number of alternative procedures. For instance one could think of setting up an iterative procedure in which an approximate calculation is made for $F_0(s)$ using Eq. 3 at the early stages of the calculation. One can then insert into Eq. 2 a new $p_0(s) = e^{-\beta F_0(s)}$ and the resulting functional is then optimized and the procedure iterated until after k steps $p_k(s) = e^{-\beta F_k(s)$ and $V_k(s)\approx 0$. The authors also point out that the systems considered here are by necessity simple, as conventionally done when introducing a completely new method. The strengths and limitations of their approach will become clearer as it is further developed. They would like to point out the potential of their method in the development of a more rigorous coarse graining procedure. Finally they note that the authors have implemented the optimization procedure presented here in a development version of the PLUMED 2 [19] plug-in and will make this publicly available in the coming future.

**References**
[1] G. Torrie and J. Valleau, J. Comput. Phys. 23, 187 (1977).
[2] T. Huber, A. E. Torda, and W. F. Gunsteren, J Computer-aided Mol Des 8, 695 (1994).
[3] E. Darve and A. Pohorille, J. Chem. Phys. 115, 9169 (2001).
[4] F. Wang and D. Landau, Phys. Rev. Lett. 86, 2050 (2001).
[5] A. Laio and M. Parrinello, Proc. Natl. Acad. Sci. U.S.A. 99, 12562 (2002).
[6] U. Hansmann and L. Wille, Phys. Rev. Lett. 88 (2002).
[7] L. Maragliano and E. Vanden-Eijnden, Chem. Phys. Lett. 426, 168 (2006).
[8] C. F. Abrams and E. Vanden-Eijnden, Proc. Natl. Acad. Sci. U.S.A. 107, 4961 (2010).
[9] P. Maragakis, A. van der Vaart, and M. Karplus, J. Phys. Chem. B 113, 4664 (2009).
[10] A. Barducci, M. Bonomi, and M. Parrinello, WIREs: Comp. Mol. Sci. 1, 826 (2011).
[11] A. Barducci, G. Bussi, and M. Parrinello, Phys. Rev. Lett. 100, 020603 (2008).
[12] J. F. Dama, M. Parrinello, and G. A. V oth, Phys. Rev. Lett.112 (2014).
[13] H. J. Kushner and G. G. Yin, Stochastic Approximation and Recursive Algorithms and Applications  (Springer-Verlag, 2003).
[14] F. Bach and E. Moulines, in Advances in Neural Information Processing Systems 26 , edited by C. Burges, L. Bottou, M. Welling, Z. Ghahramani, and K. Weinberger  (Curran Associates, Inc., 2013) pp. 773–781.
[15] G. Bussi, F. L. Gervasio, A. Laio, and M. Parrinello, J. Am. Chem. Soc. 128, 13435 (2006).
[16] P. Raiteri, A. Laio, F. L. Gervasio, C. Micheletti, and M. Par-ri-nello, J. Phys. Chem. B 110, 3533 (2006).
[17] S. Piana and A. Laio, J. Phys. Chem. B 111, 4553 (2007).
[18] P. Tiwary and M. Parrinello, J. Phys. Chem. B DOI: 10.1021/JP504920s (2014).
[19] G. A. Tribello, M. Bonomi, D. Branduardi, C. Camilloni, and G. Bussi, Comput. Phys. Commun. 185, 604 (2014).

---

**Summary Statistics:**
- Input: 3,388 words (19,738 chars)
- Output: 912 words
- Compression: 0.27x
- Generation: 55.2s (16.5 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
