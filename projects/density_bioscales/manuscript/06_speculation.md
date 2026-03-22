# Speculation and uncertainty

The **speculative** content in this repository is intentionally narrow and tied to code objects.

## Parameter boxes versus distributions

`sweep_internal_gas_mass_fraction_interval` (and the alias `sweep_air_fraction_interval`) returns an `Interval` of mixture densities when only the `internal_gas` mass fraction moves within a stated band while other compartments rescale proportionally. That construction answers: “If I am wrong about gas mass share within this window, where can \(\rho\) go?” It does **not** answer: “What is the Bayesian posterior for \(\rho\) given data?” No likelihood, no prior, and no imaging or gravimetry appear in the pipeline.

## Effective gas density

`DENSITY_INTERNAL_GAS_SPACE_KG_M3` (**240 kg m⁻³**) is the largest single modeling choice after the preset fractions. It exists solely to prevent the mass-fraction harmonic mean from collapsing when a small **mass** of gas is associated with a large **volume** effect. Treating it as a knob for sensitivity study (override `component_density_kg_m3` in API calls) is appropriate; treating it as a measured tracheal density is not.

## Epistemic humility

Interpreting any \(\rho\) here as biomechanical or ecological fact would require specimen-scale measurements (displacement, CT-based volume fractions, gravimetry under controlled saturation) and explicit treatment of surface chemistry and dynamics. The code’s role is to keep assumptions **visible** and outputs **reproducible** so that when better data arrive, the same scaffolding can ingest new component densities or bounds without rewriting the narrative layer from scratch.
