"""Physical constants and reference conditions for density calculations.

All values are SI unless noted. Universal gas constant from CODATA 2018.
"""

from __future__ import annotations

# Universal gas constant R, J/(mol·K) — CODATA 2018
R_UNIVERSAL: float = 8.314462618

# Standard pressure (IUPAC standard atmosphere), Pa
STANDARD_PRESSURE_PA: float = 101_325.0

# Standard temperature (ITS-90), K
T_STP_K: float = 273.15

# Dry air — approximate mean molar mass, kg/mol (78% N2, 21% O2, trace gases)
DRY_AIR_MOLAR_MASS_KG_MOL: float = 0.028965

# Molar masses for common gases, kg/mol (reference tables)
MOLAR_MASS_N2_KG_MOL: float = 0.028014
MOLAR_MASS_O2_KG_MOL: float = 0.031998
MOLAR_MASS_CO2_KG_MOL: float = 0.044009
