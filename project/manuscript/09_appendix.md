# Appendix {#sec:appendix}

This appendix provides additional technical details, species compatibility tables, and detailed protocols that support the main results.

## A. Detailed Technique Protocols

### A.1 Whip and Tongue Grafting Protocol

**Complete Step-by-Step Procedure**:

1. **Timing**: Late winter to early spring (February-April in northern hemisphere)
2. **Rootstock Selection**: Healthy, vigorous, diameter 5-25 mm
3. **Scion Selection**: Dormant, 1-year-old wood, 2-4 buds, matching diameter
4. **Cut Preparation**: 
   - Rootstock: 30-45° angle cut, 2-3 cm long, tongue 1 cm deep
   - Scion: Matching cut and tongue
5. **Alignment**: Precise cambium alignment on both sides
6. **Securing**: Grafting tape wrap, wax seal
7. **Protection**: Shade, humidity control, monitoring

**Success Factors**:
- Diameter match within 10%
- Sharp, clean cuts
- Rapid operation (<2 minutes)
- Proper sealing

### A.2 Cleft Grafting Protocol

**Complete Procedure**:

1. **Timing**: Late winter (dormant season)
2. **Rootstock**: Diameter 10-50 mm, cut horizontally
3. **Split**: Vertical split 3-5 cm deep
4. **Scion**: Wedge-shaped, 2-3 buds, cambium exposed
5. **Insertion**: Align cambium, insert 1-2 scions
6. **Sealing**: Complete wax coverage
7. **Protection**: Weather protection, monitoring

## B. Species Compatibility Tables

### B.1 Apple (Malus domestica) Compatibility

| Rootstock | Scion | Compatibility | Notes |
|-----------|-------|---------------|-------|
| M.9 | M. domestica | 0.95 | Standard combination |
| M.26 | M. domestica | 0.93 | Dwarfing rootstock |
| Seedling | M. domestica | 0.90 | Variable vigor |
| M.9 | Pyrus communis | 0.65 | Cross-genus, moderate |

### B.2 Pear (Pyrus communis) Compatibility

| Rootstock | Scion | Compatibility | Notes |
|-----------|-------|---------------|-------|
| P. betulifolia | P. communis | 0.92 | Common rootstock |
| P. calleryana | P. communis | 0.88 | Ornamental rootstock |
| Quince | P. communis | 0.75 | Inter-generic, dwarfing |

### B.3 Stone Fruits Compatibility

| Rootstock | Scion | Compatibility | Notes |
|-----------|-------|---------------|-------|
| Prunus avium | P. avium | 0.94 | Cherry on cherry |
| P. mahaleb | P. avium | 0.85 | Standard cherry rootstock |
| P. persica | P. persica | 0.92 | Peach on peach |
| P. domestica | P. persica | 0.70 | Cross-species, moderate |

## C. Software API Documentation

### C.1 Core Functions

**`check_cambium_alignment(rootstock_diameter, scion_diameter, tolerance=0.1)`**

Checks if rootstock and scion diameters are compatible for cambium alignment.

**Parameters**:
- `rootstock_diameter`: Rootstock stem diameter (mm)
- `scion_diameter`: Scion stem diameter (mm)
- `tolerance`: Maximum relative difference allowed (default 0.1)

**Returns**: Tuple of (is_compatible: bool, diameter_ratio: float)

**Example**:
```python
is_compat, ratio = check_cambium_alignment(15.0, 14.5, tolerance=0.1)
# Returns: (True, 0.967)
```

**`predict_compatibility_combined(phylogenetic_distance, cambium_match, growth_rate_match, weights=None)`**

Predicts compatibility using multiple factors.

**Parameters**:
- `phylogenetic_distance`: Phylogenetic distance (0-1)
- `cambium_match`: Cambium thickness match score (0-1)
- `growth_rate_match`: Growth rate match score (0-1)
- `weights`: Optional weights dictionary

**Returns**: Combined compatibility score (0-1)

### C.2 Simulation Functions

**`CambiumIntegrationSimulation(parameters, seed, output_dir)`**

Simulates cambium integration and callus formation process.

**Parameters**:
- `parameters`: Dictionary with compatibility, temperature, humidity, etc.
- `seed`: Random seed for reproducibility
- `output_dir`: Directory for saving results

**Methods**:
- `run(max_days, save_checkpoints, verbose)`: Run simulation
- `save_results(filename, formats)`: Save simulation results

**Example**:
```python
params = {"compatibility": 0.8, "temperature": 22.0, "humidity": 0.8}
sim = CambiumIntegrationSimulation(parameters=params, seed=42)
state = sim.run(max_days=60)
```

## D. Statistical Methods Details

### D.1 Success Rate Analysis

Success rates are calculated using:

\begin{equation}\label{eq:success_rate_calc}
\text{Success Rate} = \frac{\text{Number of Successful Grafts}}{\text{Total Number of Grafts}}
\end{equation}

Confidence intervals are calculated using the normal approximation to the binomial distribution:

\begin{equation}\label{eq:confidence_interval}
CI = p \pm z_{\alpha/2} \sqrt{\frac{p(1-p)}{n}}
\end{equation}

where $p$ is the observed success rate, $n$ is the sample size, and $z_{\alpha/2}$ is the critical value for confidence level $\alpha$.

### D.2 Correlation Analysis

Correlation between factors and success is calculated using point-biserial correlation for binary success outcomes:

\begin{equation}\label{eq:point_biserial}
r_{pb} = \frac{M_1 - M_0}{s} \sqrt{\frac{n_1 n_0}{n^2}}
\end{equation}

where $M_1$ and $M_0$ are means for successful and failed grafts, $s$ is the standard deviation, and $n_1$, $n_0$, $n$ are sample sizes.

### D.3 ANOVA for Technique Comparison

One-way ANOVA is used to compare success rates across techniques:

\begin{equation}\label{eq:anova_f}
F = \frac{MS_{between}}{MS_{within}} = \frac{SS_{between} / df_{between}}{SS_{within} / df_{within}}
\end{equation}

Post-hoc tests (Tukey HSD) identify specific technique differences.

## E. Economic Model Parameters

### E.1 Cost Parameters

**Labor Costs**:
- Skilled grafter: \$25-40/hour
- Grafts per hour: 20-50 (depending on technique)
- Labor cost per graft: \$0.50-2.00

**Material Costs**:
- Grafting tape: \$0.10-0.20 per graft
- Grafting wax: \$0.05-0.15 per graft
- Tools (amortized): \$0.10-0.30 per graft
- Total material: \$0.25-0.65 per graft

**Overhead Costs**:
- Facility and utilities: \$0.20-0.50 per graft
- Management and administration: \$0.10-0.30 per graft

**Total Cost Range**: \$1.05-3.45 per graft (average \$3.50)

### E.2 Revenue Parameters

**Value per Successful Graft**:
- Fruit tree sapling: \$15-30
- Ornamental tree: \$20-50
- Specialty/rare species: \$50-200
- Average: \$20.00

**Time to Market**: 1-3 years depending on species and growth rate

### E.3 Economic Metrics

**Net Profit**:
\begin{equation}\label{eq:net_profit}
\text{Net Profit} = \text{Revenue} - \text{Total Cost}
\end{equation}

**Return on Investment (ROI)**:
\begin{equation}\label{eq:roi}
\text{ROI} = \frac{\text{Net Profit}}{\text{Total Cost}} \times 100\%
\end{equation}

**Break-Even Success Rate**:
\begin{equation}\label{eq:break_even}
\text{Break-Even Rate} = \frac{\text{Cost per Graft}}{\text{Value per Successful Graft}}
\end{equation}

Typical break-even rates: 15-20%, well below average success rates of 70-85%.

## F. Environmental Parameter Ranges

### F.1 Temperature Ranges by Species Type

| Species Type | Optimal Range | Acceptable Range | Suboptimal |
|--------------|---------------|------------------|------------|
| Temperate | 20-25°C | 15-30°C | <15°C or >30°C |
| Tropical | 22-28°C | 18-35°C | <18°C or >35°C |
| Subtropical | 15-25°C | 8-32°C | <8°C or >32°C |

### F.2 Humidity Ranges

| Condition | Optimal | Acceptable | Suboptimal |
|-----------|---------|------------|------------|
| Relative Humidity | 70-90% | 50-70% or 90-100% | <50% |

### F.3 Seasonal Windows

| Species Type | Northern Hemisphere | Southern Hemisphere |
|--------------|---------------------|-------------------|
| Temperate | Feb-Apr (months 2-4) | Aug-Oct (months 8-10) |
| Tropical | Jun-Sep (months 6-9) | Dec-Mar (months 12-3) |
| Subtropical | Nov-Mar (months 11-3) | May-Sep (months 5-9) |

## G. Computational Environment

All computational analyses were conducted using:

- **Python**: 3.10+
- **NumPy**: 1.24+ (numerical computations)
- **Matplotlib**: 3.7+ (visualization)
- **SciPy**: 1.10+ (statistical analysis)
- **Platform**: Cross-platform (Linux, macOS, Windows)

Simulations use seeded random number generators for reproducibility, with all random seeds documented in analysis scripts.
