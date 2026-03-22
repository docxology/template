# Insect composite model

For immiscible components with mass fractions \(w_i\) and component densities \(\rho_i\), the project uses the parallel (harmonic) mixing rule for mass-specific averaging:

\begin{equation}
\frac{1}{\rho} = \sum_i \frac{w_i}{\rho_i}.
\label{eq:mixture_rule}
\end{equation}

Code entry point: `mixture_density_mass_fractions` in `composite_density.py`. Mass fractions must be non-negative and sum to one (`normalize_fractions` can convert raw mass-like weights).

## Component densities

Default component densities (kg m⁻³) are order-of-magnitude materials-style anchors in `insect_composition.py`: cuticle **1300**, soft tissue **1050**, hemolymph **1035**. They are not tuned per taxon.

## Internal gas compartment

Tracheal and gut gas carry negligible **mass** relative to aqueous tissue but can occupy non-negligible **volume**. In a **mass-fraction** formulation, inserting literal atmospheric air at \(\rho \approx 1.2\) kg m⁻³ with percent-level \(w_{\mathrm{gas}}\) drives \(1/\rho\) toward \(w_{\mathrm{gas}}/\rho_{\mathrm{air}}\), collapsing \(\rho\) to unrealistically small values. The model therefore uses a compartment `internal_gas` with a **phenomenological effective density** `DENSITY_INTERNAL_GAS_SPACE_KG_M3` (**240 kg m⁻³** in the current table). That value encodes “gas-filled lumina” at the resolution of this toy rule—it is **not** a direct measurement of tracheal gas density and should not be read as a biological constant.

Sensitivity of \(\rho\) to uncertainty in \(w_{\mathrm{internal\_gas}}\) is reported as an interval by `sweep_internal_gas_mass_fraction_interval` (alias `sweep_air_fraction_interval`): endpoints renormalize other compartments so fractions still sum to unity, then evaluate Equation \ref{eq:mixture_rule} at each endpoint.

## Illustrative presets

Named presets are documentation devices, not fitted posteriors:

| Preset | Role in the manuscript |
|--------|-------------------------|
| `preset_adult_fly_illustrative` | Moderate `internal_gas` mass fraction (0.05); cuticle 0.12, soft tissue 0.58, hemolymph 0.25. |
| `preset_larva_illustrative` | Softer body plan with low gas mass fraction (0.01); higher hemolymph + tissue share. |
| `preset_arid_beetle_illustrative` | Heavier cuticle (0.22); illustrates how sclerotization shifts \(\rho\) at fixed mixing rule. |

Central mixture densities for these presets land between roughly **900 kg m⁻³** and **1030 kg m⁻³** under the default component table—near fresh water, so buoyancy contrast against 25 °C water is a few percent or less unless parameters move outside the illustrative box.
