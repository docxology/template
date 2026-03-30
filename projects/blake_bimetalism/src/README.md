# `src/` Block: Analytical Engine

This module provides the business logic, mathematical modeling, and visualization orchestration for the **Blake Bimetallism** manuscript project.

## Structure

- **`analysis.py`**: Quantifies the structural divergence between historical mint ratios (e.g., Hamilton's 15:1; Newton's 15.21:1) and fluctuating European market ratios. It computes the "Gresham Entropy Gap"—a thermodynamic framing of how bi-metal equilibrium violently breaks down into monometallic flight.
- **`figures.py`**: A facade module that imports the 6 mathematical visualizations from the dedicated `src.viz` engine and exposes them seamlessly to the pipeline orchestrators.
- **`manuscript.py`**: Serializer and data-injector object ensuring the quantitative outputs derived from `analysis.py` can be explicitly mapped into the 18 markdown chapters.
- **`viz/`**: Dedicated subpackage constructing 3D topological surfaces and bipartite graphs (using `matplotlib` and `networkx`) to represent systemic monetary collapse and sound money resistance.

## Academic Parity

The models within `src` implement the structural theories provided by:
- Milton Friedman & Anna Schwartz (19th century deflation)
- Marc Flandreau (Bimetallism as political theology)
- Angela Redish (Mechanics of silver/gold specie flows)
