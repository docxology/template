# Blake Bimetallism: Scholarly Documentation Hub

**A Theoretical Synthesis of William Blake's Cosmology and 500 Years of Macroeconomic Architecture (1558–2026)**

This `doc/` directory serves as the technical referencing hub for the `blake_bimetalism` manuscript system. The project mathematically maps William Blake's prophetic critique of *Urizen* (abstract, centralized, geometric control) and *Orc* (decentralized, tangible, labor-driven resistance) onto the structural history of Bimetallism, the Gold Standard, and the modern Fiat Void.

## The 18-Chapter Manuscript Integration

The manuscript is constructed from 18 rigorously synchronized Markdown files that trace a seamless historical arc. The Root Run Orchestrator (`run.sh`) processes these via LaTeX natively:

### Abstract & Introduction (The Framing)
- `00_abstract.md`: Executive summary of the 500-year dual-value thesis.
- `01_introduction.md`: Establishes the Newtonian metrological regime vs. Blakean prophetic vision.

### British Financial Architecture (1558–1816)
- `02a_newtonian_standard.md`: Analyzes Isaac Newton's 1717 ratio (15.21:1) and the structural overvaluation of gold.
- `02b_gresham_entropy.md`: Introduces Gresham's Law as the primary thermodynamic driver of bimetallic collapse.
- `02c_bank_restriction_1797.md`: The 1797 suspension of specie payment and the psychological shock of unbacked paper.
- `02d_bullionist_controversy.md`: The Bullionist debates (Ricardo, Thornton) over the measurement of value.

### Blakean Mythopoetics (The Philosophical Engine)
- `03a_urizenic_materialism.md`: The geometry of the Mint; atomistic materialism and monetary ontology.
- `03b_los_and_fourfold_vision.md`: The Forge against the Mint; transmuting quantitative value into qualitative ontology.
- `03c_alchemical_forges.md`: Solving the dualistic meta-stability of silver and gold through Imagination.

### The Apogee of British Urizen
- `04a_illuminated_nonduality.md`: Overcoming the "Selfhood" through Blake's composite art forms.
- `04b_coinage_act_1816.md`: Lord Liverpool’s 1816 demonetization of silver and the consolidation of the Gold Standard.
- `04c_esoteric_finance.md`: Integrating Alexander Del Mar and Saree Makdisi on the violence of financial abstractions.

### The American Arc (1792–2026)
- `05a_atlantic_crucible.md`: Contrasts Hamilton's republican 15:1 ratio against Newton's imperial 15.21:1.
- `05b_america_prophecy.md`: The "Crime of 1873," William Jennings Bryan, and the political theology of the Free Silver crusade.
- `05c_transatlantic_gresham.md`: Jacksonian "Free Banking" and the Greenback suspension as the dialectic of centralization vs. populism.
- `05d_absolute_fiat_void.md`: 1913–1971; the Federal Reserve, the 1933 Gold Seizure, and the Nixon Shock explicitly decoupling currency from the labor theory of value.
- `05e_sound_money_rebellion.md`: 2011–2026; "Monetary Federalism" and the state-level (e.g., Texas, Utah) constitutional rebellion to reclaim tangible gold and silver tender.

### Conclusion
- `06_conclusion.md`: The 500-year synthesis. The eternal resonance of the Forge against the Mint.

## The `src/viz/` Programmatic Engine

Beyond narrative prose, this project utilizes a subpackage (`src/viz/`) to formally generate 6 distinct mathematical charts that are directly referenced in the manuscript:
1. **Bimetallic and Prophetic Timeline** (`timeline.png`)
2. **The Arbitrage Fracture** (`historic_ratio.png`)
3. **Procedural Alchemy of Bimetallic Vectors** (`alchemical_bimetallism.png`)
4. **The Flight of Credit: Bank of England Reserves** (`historic_reserves.png`)
5. **The Monetary Ascension: From Ulro to Eden** (`fourfold_mapping.png`)
6. **Topological Fracture of Gresham's Law** (`topological_fracture.png`)

These outputs are generated deterministically via `scripts/generate_figures.py` during the `02_run_analysis.py` pipeline phase.

## Documentation Style Guide & Rendering Standards

To guarantee a zero-warning rendering pipeline across HTML, PDF, and Slides, the manuscript adheres strictly to Pandoc Markdown styling conventions:

- **Isolated Figure Blocks**: Any programmatic chart or graphic must be embedded as a standalone paragraph (`![Caption Text](../output/figures/chart.png){#fig-reference}`). It must be completely surrounded by blank lines. If it touches header text or body copy, the automated figure captioning will fail.
- **Caption Generation**: Pandoc automatically generates enumerated "Figure X:" prefixes at compile-time. Consequently, alt-text must *never* contain hardcoded figure numbers inside the `![]` brackets, or the PDF will render double unformatted labels.
- **Header Spacing**: Consistent markdown style must be maintained: all headers (`#`, `##`, `###`) require a trailing blank line before any subsequent text to ensure compatibility with downstream linting and parsing engines.

## Quick Start
To build the finalized PDF manuscript containing the 18 chapters and beautifully integrated programmatic visualization:
```bash
./run.sh --pipeline --project blake_bimetalism
```
