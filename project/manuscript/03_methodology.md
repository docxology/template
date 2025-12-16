# Methodology {#sec:methodology}

## Biological Mechanisms

### Cambium Alignment and Contact

The success of graft union formation fundamentally depends on precise alignment of the cambium layers, the thin meristematic tissue responsible for secondary growth in plants \cite{melnyk2018, goldschmidt2014}. The cambium, located between the xylem and phloem, contains actively dividing cells that generate new vascular tissue. For successful grafting, the cambium layers of rootstock and scion must be brought into direct contact, enabling cell-to-cell communication and tissue integration.

The cambium contact area can be quantified as:

\begin{equation}\label{eq:cambium_contact}
C(t) = C_0 + \int_0^t r_c(\tau) \cdot A(\tau) \, d\tau
\end{equation}

where $C(t)$ is the cambium contact area at time $t$, $C_0$ is the initial contact area (determined by technique quality), $r_c(\tau)$ is the cambium growth rate, and $A(\tau)$ is the available contact area.

### Callus Formation

Following cambium contact, callus tissue forms at the graft interface. Callus consists of undifferentiated parenchyma cells that proliferate to bridge the gap between rootstock and scion \cite{melnyk2018}. The callus formation process follows an exponential growth pattern:

\begin{equation}\label{eq:callus_formation}
F(t) = F_{\max} \left(1 - e^{-\lambda_c t}\right)
\end{equation}

where $F(t)$ is the callus formation fraction (0-1), $F_{\max}$ is the maximum possible formation (typically 0.9-1.0), and $\lambda_c$ is the formation rate constant, which depends on species compatibility, temperature, and humidity.

### Vascular Connection

The final stage of graft union involves differentiation of callus cells into functional vascular tissue (xylem and phloem), establishing nutrient and water transport between rootstock and scion \cite{melnyk2018}. Vascular connection strength can be modeled as:

\begin{equation}\label{eq:vascular_connection}
V(t) = V_{\max} \cdot \min\left(1, \frac{F(t) - F_{threshold}}{F_{max} - F_{threshold}}\right)
\end{equation}

where $V(t)$ is the vascular connection strength, $F_{threshold}$ is the minimum callus formation required for vascular differentiation (typically 0.5), and $V_{\max}$ is the maximum connection strength.

## Grafting Techniques

### Whip and Tongue Grafting

Whip and tongue grafting (also called splice grafting) is among the most precise methods, suitable for rootstock and scion of similar diameter (5-25 mm) \cite{garner2013, hartmann2014}. The technique involves:

1. Making matching 30-45° angle cuts on both rootstock and scion
2. Creating interlocking tongues (notches) on both pieces
3. Aligning cambium layers precisely
4. Securing with grafting tape or wax
5. Protecting from desiccation

Success rates typically range from 75-90%, depending on species compatibility and execution quality.

### Cleft Grafting

Cleft grafting is suitable for larger diameter rootstock (10-50 mm) and is particularly useful for top-working established trees \cite{webster2002}. The procedure involves:

1. Making a vertical split in the rootstock
2. Preparing wedge-shaped scion with 2-3 buds
3. Inserting scion into cleft, ensuring cambium alignment
4. Sealing with grafting wax
5. Protecting from weather

Success rates are typically 70-80%, with higher success for larger diameter matches.

### Bark Grafting

Bark grafting is employed for large diameter rootstock (20-100 mm) and is useful for mature tree renovation \cite{garner2013}. The method involves:

1. Making vertical cut through bark on rootstock
2. Loosening bark flaps
3. Preparing scion with beveled cut
4. Inserting scion under bark, aligning cambium
5. Securing and sealing

Success rates range from 65-75%, with optimal timing in early spring when bark is slipping.

### Bud Grafting (T-budding)

Bud grafting (T-budding) is highly efficient for mass propagation, using a single bud rather than a complete scion \cite{hartmann2014}. The technique involves:

1. Making T-shaped cut in rootstock bark
2. Removing bud from scion with shield
3. Inserting bud under bark flaps
4. Wrapping securely with budding tape
5. Removing tape after bud takes (typically 2-4 weeks)

Success rates are typically 75-85%, making this method highly efficient for commercial propagation.

## Compatibility Theory

### Phylogenetic Distance Model

Phylogenetic distance is the strongest predictor of graft compatibility \cite{stebbins1950, goldschmidt2014}. Closely related species share similar vascular anatomy, biochemical pathways, and growth patterns, enabling successful union formation. Compatibility decreases exponentially with phylogenetic distance:

\begin{equation}\label{eq:phylogenetic_compatibility}
P_{phyl}(d) = e^{-k \cdot d / d_{max}}
\end{equation}

where $P_{phyl}(d)$ is the phylogenetic compatibility (0-1), $d$ is the phylogenetic distance, $d_{max}$ is the maximum distance for compatibility, and $k$ is a decay constant (typically $k \approx 2.0$).

### Cambium Match Model

Similar cambium thickness indicates better alignment potential and reduced stress at the union interface:

\begin{equation}\label{eq:cambium_match}
P_{camb}(r_s, r_r) = 1 - \min\left(1, \frac{|r_s - r_r|}{\tau \cdot r_r}\right)
\end{equation}

where $P_{camb}$ is the cambium match score, $r_s$ and $r_r$ are scion and rootstock cambium thicknesses, and $\tau$ is the tolerance threshold (typically 0.2).

### Growth Rate Compatibility

Similar growth rates reduce stress at the graft union, preventing overgrowth or undergrowth issues:

\begin{equation}\label{eq:growth_compatibility}
P_{growth}(g_s, g_r) = 1 - \min\left(1, \frac{|g_s - g_r|}{\tau_g \cdot g_r}\right)
\end{equation}

where $P_{growth}$ is the growth rate compatibility, $g_s$ and $g_r$ are scion and rootstock growth rates, and $\tau_g$ is the growth rate tolerance (typically 0.3).

### Combined Compatibility Score

The overall compatibility prediction combines multiple factors:

\begin{equation}\label{eq:combined_compatibility}
P_{total} = w_1 P_{phyl} + w_2 P_{camb} + w_3 P_{growth}
\end{equation}

where $w_1 = 0.5$, $w_2 = 0.3$, and $w_3 = 0.2$ are weights determined through empirical analysis.

## Success Factors

### Environmental Conditions

Optimal environmental conditions are critical for graft success:

- **Temperature**: 20-25°C optimal, 15-30°C acceptable range
- **Humidity**: 70-90% relative humidity optimal
- **Light**: Moderate indirect light, avoid direct sun exposure
- **Season**: Late winter to early spring for temperate species

The environmental suitability score can be calculated as:

\begin{equation}\label{eq:environmental_score}
E(T, H) = E_T(T) \cdot E_H(H)
\end{equation}

where $E_T(T)$ and $E_H(H)$ are temperature and humidity suitability functions, respectively.

### Technique Quality

The quality of technique execution significantly impacts success rates. Key factors include:

- Precision of cuts and alignment
- Speed of operation (minimizing desiccation)
- Proper sealing and protection
- Post-grafting care

Technique quality can be quantified on a 0-1 scale, with values above 0.8 associated with success rates 15-20% higher than values below 0.6.

## Computational Framework

### Biological Process Simulation

Our simulation framework models the temporal dynamics of graft healing using a system of differential equations:

\begin{equation}\label{eq:healing_dynamics}
\frac{dC}{dt} = r_c \cdot (1 - C) \cdot E(T, H) \cdot P_{total}
\end{equation}

\begin{equation}\label{eq:callus_dynamics}
\frac{dF}{dt} = r_f \cdot C \cdot (1 - F) \cdot E(T, H) \cdot P_{total}
\end{equation}

\begin{equation}\label{eq:vascular_dynamics}
\frac{dV}{dt} = r_v \cdot F \cdot (1 - V) \cdot E(T, H) \cdot P_{total}
\end{equation}

where $r_c$, $r_f$, and $r_v$ are growth rate constants for cambium contact, callus formation, and vascular connection, respectively.

### Success Probability Prediction

The overall graft success probability combines compatibility, technique quality, environmental conditions, and seasonal timing:

\begin{equation}\label{eq:success_probability}
P_{success} = 0.4 P_{total} + 0.3 Q_{tech} + 0.2 E(T, H) + 0.1 S_{timing}
\end{equation}

where $Q_{tech}$ is technique quality (0-1) and $S_{timing}$ is seasonal timing score (0-1).

## Implementation Details

The computational toolkit implements these models through modular Python packages:

- **`graft_basics.py`**: Core grafting calculations and compatibility checks
- **`biological_simulation.py`**: Simulation framework for healing processes
- **`compatibility_prediction.py`**: Compatibility prediction algorithms
- **`species_database.py`**: Database of species compatibility information
- **`technique_library.py`**: Encyclopedia of grafting techniques
- **`graft_statistics.py`**: Statistical analysis of grafting outcomes
- **`graft_analysis.py`**: Factor analysis and outcome evaluation

All implementations follow the thin orchestrator pattern, with business logic in `src/` modules and orchestration in `scripts/` files, ensuring maintainability and testability.

## Validation Framework

To validate our models and predictions, we use:

1. **Literature Review**: Comparison with published success rates and compatibility data
2. **Synthetic Data Generation**: Realistic trial data based on known biological parameters
3. **Statistical Validation**: Hypothesis testing and correlation analysis
4. **Cross-Validation**: Model performance on held-out data

The validation framework ensures that predictions align with established horticultural knowledge and biological principles.
