# Liquids and gases

## Ideal gas

Ideal mass density follows

\begin{equation}
\rho = \frac{p M}{R T}
\label{eq:ideal_gas_density}
\end{equation}

with \(p\) in pascals, \(T\) in kelvin, and molar mass \(M\) in kg mol⁻¹. Implementation: `ideal_gas_density_kg_m3` and `dry_air_density_stp_ideal_kg_m3` in `ideal_gas.py`. Universal \(R\) and STP anchors (`STANDARD_PRESSURE_PA`, `T_STP_K`) live in `constants.py`.

For dry air, the code uses a single molar mass (`DRY_AIR_MOLAR_MASS_KG_MOL`) as a transparent stand-in for the nitrogen–oxygen mixture. At STP the ideal model yields about **1.29 kg m⁻³** (exact value is in `density_summary.json` after running the analysis scripts). That number is compared to a **fixed** literature band (`DRY_AIR_DENSITY_STP_LITERATURE_MIN_KG_M3`, `DRY_AIR_DENSITY_STP_LITERATURE_MAX_KG_M3`, spanning **1.18–1.32 kg m⁻³**) documented beside the function. The band is not fitted to data in this repository; it is a coarse plausibility check that the implementation and constants land in the right decade.

Non-ideal corrections (humidity, CO₂ fraction, altitude pressure) are out of scope here. Any extension should add explicit state variables and tests rather than silently changing STP defaults.

## Reference liquids

`fluid_reference.py` exposes tabulated densities used as **anchors**: fresh water at **15 °C** (999.1 kg m⁻³) and **25 °C** (997.0 kg m⁻³), ethanol at **20 °C** (789.0 kg m⁻³), and seawater at **15 °C** (1025.0 kg m⁻³, illustrative salinity). Function `reference_liquids_table` serialises the table for JSON export alongside gas results.

For quick thermal interpolation of fresh water between the two water anchors, `water_density_linear_celsius` applies a linear volumetric expansion form \(\rho(T) \approx \rho_{\mathrm{ref}} (1 - \alpha (T - T_{\mathrm{ref}}))\) with \(\alpha = 2.07\times10^{-4}\,\mathrm{K}^{-1}\) chosen so endpoints approximate the tabulated 15 °C and 25 °C values within a few tenths of a kg m⁻³. This is a convenience proxy, not a replacement for IAPWS-grade equations when high accuracy is required.

Figure \ref{fig:density_overview} places the liquid anchors on the same horizontal scale as illustrative insect presets so the eye can compare orders of magnitude against ideal gas at STP.
