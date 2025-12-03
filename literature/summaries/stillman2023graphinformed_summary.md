# Graph-informed simulation-based inference for models of active matter

**Authors:** Namid R. Stillman, Silke Henkes, Roberto Mayor, Gilles Louppe

**Year:** 2023

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [stillman2023graphinformed.pdf](../pdfs/stillman2023graphinformed.pdf)

**Generated:** 2025-12-03 05:54:22

---

**Overview/Summary**
The paper presents a novel approach to inferring the posterior distribution of parameters in an over-damped active matter model using graph-informed simulation-based inference (GSBI). The authors use this method to estimate the posterior for the three physical parameters that control the dynamics of the system, namely the persistence time $\tau$, the active force $v_0$ and the interaction stiffness $k$. The paper is motivated by the study of collective cell migration in 2D. In this context, the authors assume that the motion is over-damped. The model is a simple one-dimensional (1D) system, where each particle moves along its normal with an active force $v_0$ and also performs a random walk with a diffusion constant $D$. The position of the $i$th particle at time $t$ is denoted by $r_i$, and the angular variable $\theta_r$ is described by the following stochastic differential equation (SDE)
\begin{align*}
\dot{r}_i &= v_0 \hat{n}_i + \frac{\zeta}{\tau} \\
\dot{\theta}_r&= \eta_i,  \qquad \langle \eta_i\rangle = 0,  \qquad \langle \eta_i(t)\eta_j(t')\rangle = \delta_{ij}\delta(t-t')
\end{align*}
where $\zeta$ is the friction in the system. The authors also update an angular variable for each particle based on the distance-based interactions between other particles. The interaction forces are described by a linear piecewise force law which decreases linearly as a function of the distance $r$. The authors refer to the slope of decrease as the stiffness of the interactions and denote this by $k$. This is also one of the parameters that they investigate, along with the persistence time $\tau$ and the active propulsion force of the particle $v_0$. For two particles $i$ and $j$, separated by a distance $r=|r_j-r_i|$ and with radii $R_i$ and $R_j$, where we denote the sum of radii with $b_{ij}$, they calculate the forces using the following interaction force law
\begin{align*}
F_{ij}(r) &= \frac{k}{r-b_{ij}}  \qquad \text{if} \qquad r < R_i+R_j \\
&= -k(r-b_{ij}-2b_{ij})  \qquad \text{if} \qquad 1+\epsilon < r < R_i+R_j \\
&= 0  \qquad \text{otherwise}
\end{align*}
where $\epsilon$ is a dimensionless parameter that reﬂects the attraction strength of interactions or the adhesion. This interaction force is calculated for particles within a contact radius given by their radius and a cutoff region equal to $1+2\epsilon$. The authors construct the system such that the number of particles remains unchanged and that the system domain is open. In this work, the cell radius is 10 microns and the velocity of cells is in units microns/hour. To generate simulation output, the authors sample from a uniform prior distribution where both $v_0$ and $k$ are between 0 and 150 and $\tau$ is between 0 and 10. The authors construct the system such that particles have polydispersity of 0.3. Finally, they assume that the number of particles remains unchanged and that the system domain is open.

**Key Contributions/Findings**
The main contribution of this paper is a novel method for inferring the posterior distribution of the physical parameters in an over-damped active matter model using GSBI. The authors use this method to estimate the posterior for the three physical parameters that control the dynamics of the system, namely $\tau$, $v_0$ and $k$. The authors also compare their approach with a previously proposed approximate Bayesian computation (ABC) method. The paper is motivated by the study of collective cell migration in 2D. In this context, the authors assume that the motion is over-damped. For each particle, the position at time $t$ is denoted by $r_i$, and the angular variable $\theta_r$ is described by the following stochastic differential equation (SDE)
\begin{align*}
\dot{r}_i &= v_0 \hat{n}_i + \frac{\zeta}{\tau} \\
\dot{\theta}_r&= \eta_i,  \qquad \langle \eta_i\rangle = 0,  \qquad \langle \eta_i(t)\eta_j(t')\rangle = \delta_{ij}\delta(t-t')
\end{align*}
where $\zeta$ is the friction in the system. The authors also update an angular variable for each particle based on the distance-based interactions between other particles. The interaction forces are described by a linear piecewise force law which decreases linearly as a function of the distance $r$. The authors refer to the slope of decrease as the stiffness of the interactions and denote this by $k$. This is also one of the parameters that they investigate, along with the persistence time $\tau$ and the active propulsion force of the particle $v_0$. For two particles $i$ and $j$, separated by a distance $r=|r_j-r_i|$ and with radii $R_i$ and $R_j$, where we denote the sum of radii with $b_{ij}$, they calculate the forces using the following interaction force law
\begin{align*}
F_{ij}(r) &= \frac{k}{r-b_{ij}}  \qquad \text{if} \qquad r < R_i+R_j \\
&= -k(r-b_{ij}-2b_{ij})  \qquad \text{if} \qquad 1+\epsilon < r < R_i+R_j \\
&= 0  \qquad \text{otherwise}
\end{align*}
where $\epsilon$ is a dimensionless parameter that reﬂects the attraction strength of interactions or the adhesion. This interaction force is calculated for particles within a contact radius given by their radius and a cutoff region equal to $1+2\epsilon$. The authors construct the system such that the number of particles remains unchanged and that the system domain is open. In this work, the cell radius is 10 microns and the velocity of cells is in units microns/hour. To generate simulation output, the authors sample from a uniform prior distribution where both $v_0$ and $k$ are between 0 and 150 and $\tau$ is between 0 and 10. The authors construct the system such that particles have polydispersity of 0.3. Finally, they assume that the number of particles remains unchanged and that the system domain is open.

**Methodology/Approach**
The authors consider three different inference approaches to estimate the posterior distribution of $\theta$. For all three, they use neural posterior estimation (NPE) with a masked autoregressive flow (MAF)  (Papamakarios et al., 2017; Greenberg et al., 2019). For all three, they use NPE with a MAF. For all architectures, they pass the NPE network observational features of size 100. Where they use only summary statistics, this is the average velocity and mean square displacement and for graph-informed statistics, they embed the interaction networks into graph-embeddings of size 100. The authors ﬁrst consider the inﬂuence of architecture size for the inference of the posterior using only summary statistics. They ﬁnd that we get best performance, as measured by the negative log-likelihood for MAFs with four layers of size 256, where we also consider fewer (3) and smaller (64,128) layers. Having found the best performance for summary statistics, they ﬁx the inference network shape to allow for fair comparison against embedding architectures. For the embedding network, they use a graph-convolutional network (Kipf & Welling, 2016) with 3 steps of message passing and with batch normalisation before each step. They also compute the uniﬁed graph embeddings as a ﬁnal step using global (mean) pooling. As we discuss in section 4, further work will explore different architectures. Here, they alter only the relative size for each message passing layer (between 64,128 and 256). They ﬁnd that large networks (256) give the best performance. Finally, they pass the graph embedding networks the position and velocity for all particles. In this work, temporal interaction data is encoded in the adjacency matrix. They construct block diagonal matrices, where each block reﬂects the spatial interaction network between particles $i$ and $j$ at a single timestep. The off-diagonals are also block matrices but connect individual particles between timesteps tand t+ 1. An annotated spatio-temporal adjacency matrix is shown in Figure 4.

**Results/Data**
The authors consider three different inference approaches to estimate the posterior distribution of $\theta$. For all three, they use NPE with a MAF. For all three, they use NPE with a MAF. For all architectures, they pass the NPE network observational features of size 100. Where they use only summary statistics, this is the average velocity and mean square displacement and for graph-informed statistics, they embed the interaction networks into graph-embeddings of size 100. The authors consider three different inference approaches to estimate the posterior distribution of $\theta$. For all three, they use NPE with a MAF. For all three, they use NPE with a MAF. For all architectures, they pass the N

---

**Summary Statistics:**
- Input: 3,472 words (22,706 chars)
- Output: 1,307 words
- Compression: 0.38x
- Generation: 68.5s (19.1 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
