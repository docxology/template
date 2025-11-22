# Code Placement Decision Tree

Quick reference for determining where new code belongs in the two-layer architecture.

## Simple Decision Tree

```
START: New code to write?
│
├─ Is it about building/validating/managing documents?
│  ├─ YES → LAYER 1: INFRASTRUCTURE
│  │   (Add to src/infrastructure/)
│  │
│  └─ NO → Does it implement research algorithms/analysis?
│     ├─ YES → LAYER 2: SCIENTIFIC
│     │   (Add to src/scientific/)
│     │
│     └─ NO → Reconsider scope or ask team
```

---

## Detailed Examples

### Questions to Ask

**1. Will this code be used in EVERY research project using this template?**
- YES → Infrastructure
- NO → Scientific

**2. Does this code validate or build outputs?**
- YES → Infrastructure
- NO → Scientific

**3. Is this code specific to our research domain?**
- YES → Scientific
- NO → Infrastructure

**4. Does this code depend on knowing what our research is about?**
- YES → Scientific
- NO → Infrastructure

**5. Would another research group reuse this code unchanged?**
- YES → Infrastructure
- NO → Scientific

---

## Layer 1: Infrastructure Examples

### ✅ Belongs in src/infrastructure/

**Build and Document Management:**
- PDF generation and LaTeX compilation
- Markdown file processing and validation
- Figure numbering and cross-referencing
- Image file management and insertion
- Document quality checking
- Cross-reference validation

**Example: Figure Manager**
```python
# src/infrastructure/figure_manager.py

class FigureManager:
    """Manage figure numbering and references.
    
    This is infrastructure - works for ANY research project.
    """
    def register_figure(self, path: str, label: str) -> None:
        """Register a figure with automatic numbering."""
        pass
    
    def generate_latex_ref(self, label: str) -> str:
        """Generate LaTeX reference to figure."""
        pass
```

**Publishing and Metadata:**
- DOI validation
- Citation generation (BibTeX, APA, etc.)
- Publication metadata extraction
- Academic profile integration

**Build Verification:**
- Build artifact checking
- Reproducibility verification
- Environment state capture
- File integrity validation

**Example: Build Verifier**
```python
# src/infrastructure/build_verifier.py

def verify_build_artifacts(
    output_dir: str,
    expected_files: List[str]
) -> bool:
    """Verify expected build artifacts exist.
    
    This is infrastructure - validates ANY project's outputs.
    """
    pass
```

### ❌ NOT Infrastructure

- Domain-specific algorithms
- Research-specific visualization
- Custom statistical analysis
- Project-specific data processing
- Experimental simulations

---

## Layer 2: Scientific Examples

### ✅ Belongs in src/scientific/

**Algorithms and Computation:**
- Simulation implementations
- Statistical analysis
- Data processing specific to problem
- Optimization algorithms
- Model training/inference

**Example: Simulation**
```python
# src/scientific/simulation.py

class MySimulation(SimulationBase):
    """Specific simulation for our research.
    
    This is scientific - implements OUR algorithm.
    """
    def step(self) -> None:
        """Execute one simulation step."""
        # Our specific algorithm here
        pass
```

**Data Generation and Processing:**
- Synthetic data generators for experiments
- Domain-specific preprocessing
- Feature extraction for analysis
- Dataset normalization

**Analysis and Reporting:**
- Statistical hypothesis testing
- Convergence analysis
- Performance metrics specific to problem
- Custom report generation

**Example: Analysis**
```python
# src/scientific/analysis.py

def analyze_convergence(
    results: np.ndarray,
    tolerance: float
) -> Dict[str, Any]:
    """Analyze convergence of OUR algorithm.
    
    This is scientific - domain-specific analysis.
    """
    pass
```

**Visualization:**
- Domain-specific plots
- Research-specific visualizations
- Custom chart types for analysis
- Interactive visualizations

**Example: Plotting**
```python
# src/scientific/plots.py

def plot_experimental_results(
    data: Dict[str, np.ndarray]
) -> plt.Figure:
    """Plot results specific to our experiments.
    
    This is scientific - domain-specific visualization.
    """
    pass
```

### ❌ NOT Scientific

- Generic figure numbering (→ Infrastructure)
- PDF generation (→ Infrastructure)
- Document validation (→ Infrastructure)
- Generic plotting utilities (could be infrastructure)
- Cross-project utilities (→ Infrastructure)

---

## Gray Areas

### When Code Could Go Either Way

**Data Processing:**
- Generic preprocessing → Infrastructure (e.g., `normalize_data`)
- Domain-specific preprocessing → Scientific (e.g., `preprocess_brain_scans`)

**Visualization:**
- Generic plotting → Infrastructure (e.g., `plot_scatter`)
- Domain-specific plots → Scientific (e.g., `plot_convergence_with_our_metric`)

**Metrics:**
- Generic metrics → Infrastructure (e.g., `calculate_accuracy`)
- Domain-specific metrics → Scientific (e.g., `calculate_domain_score`)

**Strategies:**
1. If unsure, ask: "Could we use this in another project?"
2. If yes → Infrastructure
3. If the generic version goes to Infrastructure, specific version stays in Scientific
4. Example:
   ```python
   # Infrastructure: Generic normalization
   from infrastructure.data_processing import normalize_data
   
   # Scientific: Use generic + add domain logic
   def preprocess_our_data(raw_data):
       normalized = normalize_data(raw_data)
       # Add our specific processing here
       return our_transform(normalized)
   ```

---

## Practical Workflow

### Starting a New Feature

**Feature:** Add convergence analysis with custom stopping criterion

```
1. Analyze the feature
   ├─ Generic part: "convergence analysis" → infrastructure/performance.py
   ├─ Specific part: "our stopping criterion" → scientific/analysis.py
   └─ Decision: Split into two files

2. Create infrastructure first
   └─ src/infrastructure/performance.py
      ├─ Generic convergence metrics
      ├─ Reusable analysis functions
      └─ 100% tested

3. Use infrastructure in scientific
   └─ src/scientific/analysis.py
      ├─ Import from infrastructure
      ├─ Add domain-specific logic
      └─ 100% tested

4. Use scientific in scripts
   └─ scripts/analyze_results.py
      ├─ Import from scientific
      ├─ Orchestrate execution
      └─ Generate outputs

5. Document everywhere
   ├─ src/infrastructure/AGENTS.md
   ├─ src/scientific/AGENTS.md
   └─ scripts/AGENTS.md
```

### Adding a New Data Processing Step

```
Question: Where does this belong?

If answer is "for our specific problem":
└─ Scientific layer (src/scientific/data_processing.py)
   def process_our_specific_data(raw_data):
       pass

If answer is "any research could use this":
└─ Infrastructure layer (src/infrastructure/data_processing.py)
   def normalize_data(raw_data):
       pass

If both generic + specific:
├─ Infrastructure: Generic version
│  def normalize_data(raw_data, method="zscore"):
│      pass
└─ Scientific: Specific usage
   def process_our_data(raw_data):
       return normalize_data(raw_data, method="our_method")
```

---

## Anti-Patterns

### ❌ Wrong: Infrastructure Imports Scientific

```python
# BAD: src/infrastructure/integrity.py
from scientific.simulation import MySimulation  # ❌ Don't do this!

def verify_scientific_output(sim: MySimulation):
    pass
```

**Problem:** Breaks abstraction, makes infrastructure project-specific

**Fix:** Move to scientific layer or refactor to use generic interfaces

### ❌ Wrong: Business Logic in Scripts

```python
# BAD: scripts/analysis.py
def custom_algorithm(data):
    # Complex algorithm here  ❌ Don't do this!
    pass

# Scripts should orchestrate, not compute
```

**Problem:** Violates thin orchestrator pattern

**Fix:** Move to src/scientific/, import in script

### ❌ Wrong: Duplicate Code Across Layers

```python
# BAD: src/infrastructure/plots.py
def plot_convergence(data):
    pass

# BAD: src/scientific/plots.py
def plot_convergence(data):  # ❌ Duplicate!
    pass
```

**Problem:** Maintenance nightmare, inconsistency

**Fix:** Keep in one layer, import from other if needed

### ❌ Wrong: Too Much in One Module

```python
# BAD: src/scientific/everything.py - 2000+ lines
# Simulation, statistics, plotting, data processing...all mixed

# Better: Separate modules
# src/scientific/simulation.py
# src/scientific/statistics.py
# src/scientific/plots.py
# src/scientific/data_processing.py
```

**Problem:** Hard to test, understand, and maintain

**Fix:** One responsibility per module

---

## Common Questions

### "Where does utility function X go?"

1. Is it used by build/document generation? → Infrastructure
2. Is it used by scientific code? → Scientific
3. Is it used by both? → Both use each other appropriately
   - Generic version in Infrastructure
   - Specific version in Scientific
   - Scientific imports Infrastructure

### "Can I put code in repo_utilities/?"

Generally no - instead:
- Business logic → src/
- Scripts → scripts/
- Orchestration → repo_utilities/ ✅

Only simple orchestrators and shell scripts in repo_utilities/.

### "Should scientific code be in src/ or scripts/?"

- **src/scientific/** - Business logic, algorithms, computations (tested)
- **scripts/** - Orchestration and I/O (thin orchestrators, calls src/)

Rule: If it can be tested independently, it goes in src/.

### "How do I use infrastructure code in scientific code?"

```python
# src/scientific/my_analysis.py
from infrastructure.figure_manager import FigureManager
from infrastructure.markdown_integration import MarkdownIntegration

def analyze_and_report(data):
    # Scientific computation
    results = run_analysis(data)
    
    # Use infrastructure for document management
    fm = FigureManager()
    fm.register_figure("results.png", label="fig:results")
    
    return results
```

✅ This is fine - scientific uses infrastructure

### "How do I use scientific code in infrastructure code?"

❌ **Don't.**

Infrastructure should be generic and not depend on specific research.

If you need to, reconsider:
- Is the code really infrastructure?
- Should it be in scientific layer instead?
- Can you extract the generic parts?

---

## Testing Location

Choose based on WHAT you're testing, not WHERE:

```python
# Infrastructure code → tests/infrastructure/
# tests/infrastructure/test_figure_manager.py
def test_figure_numbering():
    fm = FigureManager()
    fm.register_figure("a.png", "fig:a")
    assert fm.next_number == 2

# Scientific code → tests/scientific/
# tests/scientific/test_simulation.py
def test_simulation_step():
    sim = MySimulation()
    sim.step()
    assert sim.time == 1.0

# Integration tests → tests/integration/
# tests/integration/test_full_pipeline.py
def test_script_execution():
    # Test that scientific scripts use infrastructure correctly
    pass
```

---

## Summary Matrix

| Aspect | Infrastructure | Scientific |
|--------|---|---|
| **Location** | `src/infrastructure/` | `src/scientific/` |
| **Purpose** | Build & validation tools | Algorithms & analysis |
| **Reusable** | Across all projects | Project-specific |
| **Examples** | PDF generation, figure mgmt | Simulation, statistics |
| **Dependencies** | Other infrastructure | Infrastructure + other scientific |
| **Testing** | `tests/infrastructure/` | `tests/scientific/` |
| **Scripts** | `repo_utilities/*.py` | `scripts/*.py` |

---

## Quick Reference

**For Infrastructure:**
```
Add to src/infrastructure/
├─ If it helps build documents
├─ If it validates outputs
├─ If any project would use it
└─ If it doesn't know about our research
```

**For Scientific:**
```
Add to src/scientific/
├─ If it implements our algorithms
├─ If it analyzes our data
├─ If it visualizes our results
└─ If it's specific to our research
```

---

When in doubt: **Ask yourself** — "Would another research group use this unchanged?" If yes → Infrastructure. If no → Scientific.



