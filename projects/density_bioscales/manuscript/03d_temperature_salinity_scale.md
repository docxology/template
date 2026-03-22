# Temperature, salinity, and scale

## Temperature

Liquid densities in `fluid_reference` are tied to explicit Celsius anchors. Between 15 °C and 25 °C, fresh water moves only from about **999.1** to **997.0 kg m⁻³**—a relative change under 0.3%. For buoyancy **classification** against fresh water, that shift is often secondary compared to uncertainty in body composition or in the effective gas compartment. When a study’s narrative hinges on “just above” or “just below” neutral buoyancy, both the water temperature and the body model should be stated.

`water_density_linear_celsius` is available for quick sensitivity checks without expanding the manuscript’s equation set.

## Salinity

The bundled seawater anchor (1025 kg m⁻³ at 15 °C) is **illustrative** for coastal order-of-magnitude reasoning. Real seawater \(\rho\) depends on salinity, pressure, and temperature. In Figure \ref{fig:density_overview}, seawater appears alongside fresh water so readers can see that marine surface waters are **denser** than the 25 °C fresh-water reference line used in `scenario_water_contrast_at_25c`. A model insect with \(\rho \approx 1000\) kg m⁻³ might sink in fresh water but approach neutrality in colder or saltier water—again, a statement about the **toy scalars**, not a taxon-specific prediction.

## Length scale and model scope

The repository does **not** resolve micro-scale ventilation, surface tension, menisci at spiracles, or dynamic swimming. Effective density is a **bulk** scalar. Connecting it to locomotion, dispersal, or morphometric scaling would require additional physics (Reynolds number, wetting, appendage drag) and empirical geometry outside this package’s scope.
