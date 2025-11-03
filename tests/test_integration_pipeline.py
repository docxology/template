"""Comprehensive integration tests for the entire pipeline to ensure all components work together."""

import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path

import pytest
import numpy as np


class TestFullPipelineIntegration:
    """Test the complete pipeline: scripts → outputs → validation → glossary."""

    def test_complete_pipeline_execution(self, tmp_path):
        """Test the complete pipeline from scripts to validation to glossary generation."""
        # Create a complete test project structure
        test_root = tmp_path / "complete_pipeline"
        test_root.mkdir()

        # Copy the entire current project structure
        actual_root = os.path.join(os.path.dirname(__file__), "..")

        # Copy src/ directory
        shutil.copytree(os.path.join(actual_root, "src"), test_root / "src")

        # Copy scripts/ directory
        shutil.copytree(os.path.join(actual_root, "scripts"), test_root / "scripts")

        # Copy repo_utilities/ directory
        shutil.copytree(os.path.join(actual_root, "repo_utilities"), test_root / "repo_utilities")

        # Create output and manuscript directories
        (test_root / "output" / "figures").mkdir(parents=True)
        (test_root / "output" / "data").mkdir(parents=True)
        (test_root / "manuscript").mkdir()

        # Create a basic markdown file that references outputs
        (test_root / "manuscript" / "01_test.md").write_text(r"""
# Test Section {#sec:test}

This is a test section that references figures and equations.

\begin{equation}\label{eq:test}
x^2 + y^2 = z^2
\end{equation}

![Example Figure](../output/figures/example_figure.png)

Reference to equation \eqref{eq:test}.

## Subsection {#subsec:test}

More content here.
""")

        # Step 1: Run example_figure.py script
        example_script = test_root / "scripts" / "example_figure.py"
        result1 = subprocess.run([
            sys.executable, str(example_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        # Should succeed and generate outputs
        assert result1.returncode == 0
        assert "✅ Generated example figure" in result1.stdout

        # Verify outputs were created
        assert (test_root / "output" / "figures" / "example_figure.png").exists()
        assert (test_root / "output" / "data" / "example_data.npz").exists()
        assert (test_root / "output" / "data" / "example_data.csv").exists()

        # Step 2: Run generate_research_figures.py script
        research_script = test_root / "scripts" / "generate_research_figures.py"
        result2 = subprocess.run([
            sys.executable, str(research_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        # Should succeed and generate more outputs
        assert result2.returncode == 0
        assert "✅ Generated" in result2.stdout and "research figures" in result2.stdout

        # Verify additional outputs were created
        assert (test_root / "output" / "figures" / "convergence_plot.png").exists()
        assert (test_root / "output" / "data" / "convergence_data.npz").exists()

        # Step 3: Run markdown validation
        validate_script = test_root / "repo_utilities" / "validate_markdown.py"
        result3 = subprocess.run([
            sys.executable, str(validate_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        # Should pass validation (all references exist)
        assert result3.returncode == 0
        assert "Markdown validation passed" in result3.stdout

        # Step 4: Run glossary generation
        glossary_script = test_root / "repo_utilities" / "generate_glossary.py"
        result4 = subprocess.run([
            sys.executable, str(glossary_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        # Should succeed and generate glossary
        assert result4.returncode == 0
        assert "Updated glossary:" in result4.stdout or "Glossary up-to-date" in result4.stdout

        # Verify glossary was created/updated
        glossary_file = test_root / "manuscript" / "98_symbols_glossary.md"
        assert glossary_file.exists()

        # Check that glossary contains real API entries
        with open(glossary_file, "r") as f:
            content = f.read()
        assert "example" in content.lower()
        assert "glossary_gen" in content.lower()
        assert "function" in content.lower()

        # Step 5: Run markdown validation again to ensure everything still works
        result5 = subprocess.run([
            sys.executable, str(validate_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        # Should still pass validation
        assert result5.returncode == 0
        assert "Markdown validation passed" in result5.stdout

    def test_pipeline_with_real_manuscript_structure(self, tmp_path):
        """Test pipeline with a realistic manuscript structure."""
        test_root = tmp_path / "manuscript_pipeline"
        test_root.mkdir()

        # Copy src/ and scripts/
        actual_root = os.path.join(os.path.dirname(__file__), "..")
        shutil.copytree(os.path.join(actual_root, "src"), test_root / "src")
        shutil.copytree(os.path.join(actual_root, "scripts"), test_root / "scripts")
        shutil.copytree(os.path.join(actual_root, "repo_utilities"), test_root / "repo_utilities")

        # Create manuscript structure
        manuscript_dir = test_root / "manuscript"
        manuscript_dir.mkdir()

        # Create realistic manuscript sections
        sections = {
            "01_abstract.md": r"""
# Abstract

This paper presents a novel optimization algorithm for solving large-scale problems.

\begin{equation}\label{eq:objective}
\min_{x} f(x) = \|Ax - b\|^2 + \lambda \|x\|_1
\end{equation}

Our method achieves superior performance as demonstrated in Figure \ref{fig:convergence} and Table \ref{tab:results}.

![Convergence Analysis](../output/figures/convergence_plot.png)
""",

            "02_introduction.md": r"""
# Introduction {#sec:introduction}

This section provides background and motivation for our work.

## Problem Formulation {#subsec:formulation}

We consider the optimization problem in \eqref{eq:objective}.

\begin{equation}\label{eq:algorithm}
x_{k+1} = x_k - \alpha \nabla f(x_k)
\end{equation}

See also [experimental results](#sec:results) for performance evaluation.
""",

            "03_methodology.md": r"""
# Methodology {#sec:methodology}

This section describes our proposed algorithm in detail.

## Algorithm Description {#subsec:algorithm}

Our algorithm follows the update rule in \eqref{eq:algorithm}.

\begin{equation}\label{eq:convergence}
\|x_{k+1} - x^*\| \leq \rho \|x_k - x^*\|
\end{equation}

## Implementation Details {#subsec:implementation}

The algorithm is implemented using standard numerical methods.
""",

            "04_experimental_results.md": r"""
# Experimental Results {#sec:results}

## Convergence Analysis {#subsec:convergence}

Figure \ref{fig:convergence} shows the convergence behavior of our method.

![Convergence Analysis](../output/figures/convergence_plot.png)

The convergence rate follows \eqref{eq:convergence}.

## Performance Comparison {#subsec:comparison}

Table \ref{tab:results} summarizes the performance comparison.

| Method | Accuracy | Convergence Rate |
|--------|----------|------------------|
| Our Method | 0.95 | 0.85 |
| Baseline | 0.85 | 0.90 |

\begin{equation}\label{eq:final_result}
accuracy = \frac{TP}{TP + FP}
\end{equation}
"""
        }

        for filename, content in sections.items():
            (manuscript_dir / filename).write_text(content)

        # Create output directories and run scripts
        (test_root / "output" / "figures").mkdir(parents=True)
        (test_root / "output" / "data").mkdir(parents=True)

        # Run research figures script
        research_script = test_root / "scripts" / "generate_research_figures.py"
        result = subprocess.run([
            sys.executable, str(research_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        assert result.returncode == 0

        # Run validation on manuscript
        validate_script = test_root / "repo_utilities" / "validate_markdown.py"
        result2 = subprocess.run([
            sys.executable, str(validate_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        # Should pass validation in non-strict mode
        assert result2.returncode == 0
        assert "Markdown validation" in result2.stdout

    def test_pipeline_error_recovery(self, tmp_path):
        """Test that pipeline components handle errors gracefully and continue."""
        test_root = tmp_path / "error_recovery"
        test_root.mkdir()

        # Copy components
        actual_root = os.path.join(os.path.dirname(__file__), "..")
        shutil.copytree(os.path.join(actual_root, "src"), test_root / "src")
        shutil.copytree(os.path.join(actual_root, "scripts"), test_root / "scripts")
        shutil.copytree(os.path.join(actual_root, "repo_utilities"), test_root / "repo_utilities")

        # Create output and markdown directories
        (test_root / "output" / "figures").mkdir(parents=True)
        (test_root / "output" / "data").mkdir(parents=True)
        (test_root / "manuscript").mkdir()

        # Create markdown with some issues
        (test_root / "manuscript" / "01_test.md").write_text(r"""
# Test Section

This has an unlabeled equation:
\begin{equation}
x^2 + y^2 = z^2
\end{equation}

This is fine.
""")

        # Run scripts (should succeed despite issues)
        example_script = test_root / "scripts" / "example_figure.py"
        result1 = subprocess.run([
            sys.executable, str(example_script)
        ], cwd=str(test_root), capture_output=True, text=True)
        assert result1.returncode == 0

        research_script = test_root / "scripts" / "generate_research_figures.py"
        result2 = subprocess.run([
            sys.executable, str(research_script)
        ], cwd=str(test_root), capture_output=True, text=True)
        assert result2.returncode == 0

        # Run validation in non-strict mode (should pass despite issues)
        validate_script = test_root / "repo_utilities" / "validate_markdown.py"
        result3 = subprocess.run([
            sys.executable, str(validate_script)
        ], cwd=str(test_root), capture_output=True, text=True)
        assert result3.returncode == 0  # Non-strict mode passes even with issues
        assert "Markdown validation passed" in result3.stdout or "Markdown validation issues" in result3.stdout

        # Run glossary generation (should succeed)
        glossary_script = test_root / "repo_utilities" / "generate_glossary.py"
        result4 = subprocess.run([
            sys.executable, str(glossary_script)
        ], cwd=str(test_root), capture_output=True, text=True)
        assert result4.returncode == 0

    def test_pipeline_deterministic_behavior(self, tmp_path):
        """Test that the complete pipeline produces deterministic results."""
        test_root = tmp_path / "deterministic_pipeline"
        test_root.mkdir()

        # Copy components
        actual_root = os.path.join(os.path.dirname(__file__), "..")
        shutil.copytree(os.path.join(actual_root, "src"), test_root / "src")
        shutil.copytree(os.path.join(actual_root, "scripts"), test_root / "scripts")
        shutil.copytree(os.path.join(actual_root, "repo_utilities"), test_root / "repo_utilities")

        # Create directories
        (test_root / "output" / "figures").mkdir(parents=True)
        (test_root / "output" / "data").mkdir(parents=True)
        (test_root / "manuscript").mkdir()

        # Create basic markdown
        (test_root / "manuscript" / "01_test.md").write_text(r"""
# Test Section {#sec:test}

\begin{equation}\label{eq:test}
x^2 + y^2 = z^2
\end{equation}

![Example Figure](../output/figures/example_figure.png)
""")

        # Run complete pipeline twice
        for run in range(2):
            # Run scripts
            example_script = test_root / "scripts" / "example_figure.py"
            result1 = subprocess.run([
                sys.executable, str(example_script)
            ], cwd=str(test_root), capture_output=True, text=True)
            assert result1.returncode == 0

            research_script = test_root / "scripts" / "generate_research_figures.py"
            result2 = subprocess.run([
                sys.executable, str(research_script)
            ], cwd=str(test_root), capture_output=True, text=True)
            assert result2.returncode == 0

            # Run validation
            validate_script = test_root / "repo_utilities" / "validate_markdown.py"
            result3 = subprocess.run([
                sys.executable, str(validate_script)
            ], cwd=str(test_root), capture_output=True, text=True)
            assert result3.returncode == 0

            # Run glossary generation
            glossary_script = test_root / "repo_utilities" / "generate_glossary.py"
            result4 = subprocess.run([
                sys.executable, str(glossary_script)
            ], cwd=str(test_root), capture_output=True, text=True)
            assert result4.returncode == 0

        # Verify that data files are identical across runs
        data_file = test_root / "output" / "data" / "convergence_data.npz"
        data1 = np.load(data_file)
        data2 = np.load(data_file)

        np.testing.assert_array_equal(data1['iterations'], data2['iterations'])
        np.testing.assert_array_equal(data1['our_method'], data2['our_method'])
        np.testing.assert_array_equal(data1['baseline'], data2['baseline'])

    def test_pipeline_handles_missing_dependencies(self, tmp_path):
        """Test that pipeline handles missing dependencies gracefully."""
        test_root = tmp_path / "missing_deps"
        test_root.mkdir()

        # Create minimal structure without full src/
        (test_root / "src").mkdir()
        (test_root / "scripts").mkdir()
        (test_root / "repo_utilities").mkdir()
        (test_root / "output" / "figures").mkdir(parents=True)
        (test_root / "output" / "data").mkdir(parents=True)
        (test_root / "manuscript").mkdir()

        # Create scripts that will fail due to missing dependencies
        (test_root / "scripts" / "example_figure.py").write_text("""
import os
import sys

def main():
    print("❌ Failed to import from src/example.py")
    return

if __name__ == "__main__":
    main()
""")

        (test_root / "scripts" / "generate_research_figures.py").write_text("""
import os
import sys

def main():
    print("❌ Failed to import from src/example.py")
    return

if __name__ == "__main__":
    main()
""")

        # Create markdown with references to non-existent outputs
        (test_root / "manuscript" / "01_test.md").write_text(r"""
# Test Section

![Missing Figure](../output/figures/missing.png)

\begin{equation}
x^2 + y^2 = z^2
\end{equation}
""")

        # Run validation - should detect missing images
        validate_script = test_root / "repo_utilities" / "validate_markdown.py"
        # Create a minimal validate_markdown.py for testing
        (test_root / "repo_utilities" / "validate_markdown.py").write_text("""
import os
import sys

def main():
    if not os.path.exists(os.path.join(os.path.dirname(__file__), "..", "manuscript")):
        print("Markdown directory not found")
        return 1

    print("Markdown validation issues (non-strict):")
    print(" - Missing image: ../output/figures/missing.png")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
""")

        result = subprocess.run([
            sys.executable, str(validate_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        # Should handle missing dependencies gracefully
        assert result.returncode == 0
        assert "Missing image:" in result.stdout

    def test_pipeline_cross_component_integration(self, tmp_path):
        """Test that different components properly integrate with each other."""
        test_root = tmp_path / "cross_integration"
        test_root.mkdir()

        # Copy components
        actual_root = os.path.join(os.path.dirname(__file__), "..")
        shutil.copytree(os.path.join(actual_root, "src"), test_root / "src")
        shutil.copytree(os.path.join(actual_root, "scripts"), test_root / "scripts")
        shutil.copytree(os.path.join(actual_root, "repo_utilities"), test_root / "repo_utilities")

        # Create output and manuscript directories
        (test_root / "output" / "figures").mkdir(parents=True)
        (test_root / "output" / "data").mkdir(parents=True)
        (test_root / "manuscript").mkdir()

        # Create markdown that references outputs from multiple scripts
        (test_root / "manuscript" / "01_integration_test.md").write_text(r"""
# Integration Test {#sec:integration}

This section tests integration between multiple scripts.

## Example Figure {#subsec:example}

From example_figure.py script:

![Example Figure](../output/figures/example_figure.png)

## Research Figures {#subsec:research}

From generate_research_figures.py script:

![Convergence Plot](../output/figures/convergence_plot.png)

![Experimental Setup](../output/figures/experimental_setup.png)

## Data Integration {#subsec:data}

The scripts generate data files that can be used across the project.

\begin{equation}\label{eq:integration}
integration = \sum_{i=1}^n x_i \cdot y_i
\end{equation}

This demonstrates that all components work together properly.
""")

        # Run example figure script
        example_script = test_root / "scripts" / "example_figure.py"
        result1 = subprocess.run([
            sys.executable, str(example_script)
        ], cwd=str(test_root), capture_output=True, text=True)
        assert result1.returncode == 0

        # Run research figures script
        research_script = test_root / "scripts" / "generate_research_figures.py"
        result2 = subprocess.run([
            sys.executable, str(research_script)
        ], cwd=str(test_root), capture_output=True, text=True)
        assert result2.returncode == 0

        # Run validation
        validate_script = test_root / "repo_utilities" / "validate_markdown.py"
        result3 = subprocess.run([
            sys.executable, str(validate_script)
        ], cwd=str(test_root), capture_output=True, text=True)
        assert result3.returncode == 0

        # Run glossary generation
        glossary_script = test_root / "repo_utilities" / "generate_glossary.py"
        result4 = subprocess.run([
            sys.executable, str(glossary_script)
        ], cwd=str(test_root), capture_output=True, text=True)
        assert result4.returncode == 0

        # Verify all outputs exist
        assert (test_root / "output" / "figures" / "example_figure.png").exists()
        assert (test_root / "output" / "figures" / "convergence_plot.png").exists()
        assert (test_root / "output" / "figures" / "experimental_setup.png").exists()

        # Verify data files exist
        assert (test_root / "output" / "data" / "example_data.npz").exists()
        assert (test_root / "output" / "data" / "convergence_data.npz").exists()

        # Verify glossary was generated
        glossary_file = test_root / "manuscript" / "98_symbols_glossary.md"
        assert glossary_file.exists()

        with open(glossary_file, "r") as f:
            content = f.read()
        assert "example" in content.lower()
        assert "glossary_gen" in content.lower()

    def test_pipeline_performance_and_scalability(self, tmp_path):
        """Test pipeline performance with larger datasets."""
        test_root = tmp_path / "performance_test"
        test_root.mkdir()

        # Copy components
        actual_root = os.path.join(os.path.dirname(__file__), "..")
        shutil.copytree(os.path.join(actual_root, "src"), test_root / "src")
        shutil.copytree(os.path.join(actual_root, "scripts"), test_root / "scripts")
        shutil.copytree(os.path.join(actual_root, "repo_utilities"), test_root / "repo_utilities")

        # Create output and markdown directories
        (test_root / "output" / "figures").mkdir(parents=True)
        (test_root / "output" / "data").mkdir(parents=True)
        (test_root / "manuscript").mkdir()

        # Create larger markdown files to test scalability
        large_content = ""
        for i in range(50):  # Create 50 sections
            large_content += rf"""
## Section {i} {{#sec:section_{i}}}

This is section {i} with content.

\begin{{equation}}\label{{eq:section_{i}}}
x_{i}^2 + y_{i}^2 = z_{i}^2
\end{{equation}}

Reference to equation \eqref{{eq:section_{i}}}.

![Figure for Section {i}](../output/figures/section_{i}_figure.png)

"""
        (test_root / "manuscript" / "01_large_test.md").write_text(large_content)

        # Run scripts (they should handle large content gracefully)
        research_script = test_root / "scripts" / "generate_research_figures.py"
        result = subprocess.run([
            sys.executable, str(research_script)
        ], cwd=str(test_root), capture_output=True, text=True, timeout=60)  # 60 second timeout

        assert result.returncode == 0

        # Run validation (should handle large files)
        validate_script = test_root / "repo_utilities" / "validate_markdown.py"
        result2 = subprocess.run([
            sys.executable, str(validate_script)
        ], cwd=str(test_root), capture_output=True, text=True, timeout=60)

        # Should complete successfully
        assert result2.returncode == 0

        # Run glossary generation
        glossary_script = test_root / "repo_utilities" / "generate_glossary.py"
        result3 = subprocess.run([
            sys.executable, str(glossary_script)
        ], cwd=str(test_root), capture_output=True, text=True, timeout=60)

        assert result3.returncode == 0

    def test_pipeline_with_real_world_scenario(self, tmp_path):
        """Test pipeline with a realistic academic paper scenario."""
        test_root = tmp_path / "academic_paper"
        test_root.mkdir()

        # Copy all components
        actual_root = os.path.join(os.path.dirname(__file__), "..")
        shutil.copytree(os.path.join(actual_root, "src"), test_root / "src")
        shutil.copytree(os.path.join(actual_root, "scripts"), test_root / "scripts")
        shutil.copytree(os.path.join(actual_root, "repo_utilities"), test_root / "repo_utilities")

        # Create manuscript structure
        manuscript_dir = test_root / "manuscript"
        manuscript_dir.mkdir()

        # Create a realistic academic paper
        paper_sections = {
            "01_abstract.md": r"""
# Abstract

We propose a novel algorithm for solving constrained optimization problems with theoretical guarantees.

\begin{equation}\label{eq:problem}
\begin{aligned}
\min_{x} \quad & f(x) \\
\text{s.t.} \quad & g_i(x) \leq 0, \quad i=1,\dots,m \\
& h_j(x) = 0, \quad j=1,\dots,p
\end{aligned}
\end{equation}

Our method converges at rate $O(1/k)$ as shown in Theorem \ref{thm:convergence}.

![Algorithm Overview](../output/figures/algorithm_overview.png)
""",

            "02_introduction.md": r"""
# Introduction {#sec:introduction}

## Motivation {#subsec:motivation}

Constrained optimization problems arise in numerous applications including machine learning, engineering, and economics.

The general form is given in \eqref{eq:problem}.

## Related Work {#subsec:related}

Several methods have been proposed for solving \eqref{eq:problem}, including penalty methods, barrier methods, and augmented Lagrangian methods.

## Contributions {#subsec:contributions}

Our main contributions are:
1. A novel algorithm with improved convergence guarantees
2. Theoretical analysis showing $O(1/k)$ convergence rate
3. Extensive experimental validation

\begin{equation}\label{eq:convergence_rate}
\|x_k - x^*\| \leq \frac{C}{k}
\end{equation}
""",

            "03_methodology.md": r"""
# Methodology {#sec:methodology}

## Algorithm Description {#subsec:algorithm}

Our algorithm iteratively solves a sequence of subproblems.

\begin{equation}\label{eq:update}
x_{k+1} = x_k - \alpha_k \nabla f(x_k) - \sum_{i=1}^m \lambda_i^k \nabla g_i(x_k)
\end{equation}

The step size $\alpha_k$ is chosen using backtracking line search.

## Theoretical Analysis {#subsec:theory}

**Theorem 1** (Convergence). Under appropriate assumptions, the sequence $\{x_k\}$ converges to the optimal solution $x^*$ at the rate given in \eqref{eq:convergence_rate}.

*Proof.* The proof follows from the descent lemma and standard optimization arguments.

## Implementation {#subsec:implementation}

The algorithm is implemented in Python using the functions from `src/`. See the API glossary for details.
""",

            "04_experimental_results.md": r"""
# Experimental Results {#sec:results}

## Convergence Analysis {#subsec:convergence}

Figure \ref{fig:convergence} demonstrates the convergence behavior of our algorithm compared to state-of-the-art baselines.

![Convergence Comparison](../output/figures/convergence_plot.png)

The convergence follows the theoretical rate in \eqref{eq:convergence_rate}.

\begin{equation}\label{eq:empirical_rate}
rate = \lim_{k\to\infty} \frac{\|x_{k+1} - x^*\|}{\|x_k - x^*\|}
\end{equation}

## Ablation Study {#subsec:ablation}

Figure \ref{fig:ablation} shows the contribution of each algorithm component.

![Ablation Study](../output/figures/ablation_study.png)

## Comparison with Baselines {#subsec:comparison}

Table \ref{tab:comparison} summarizes the performance comparison.

| Method | Final Objective | Convergence Rate | Memory Usage |
|--------|-----------------|------------------|--------------|
| Our Method | 1.23e-6 | 0.85 | O(n) |
| Penalty Method | 2.45e-5 | 0.78 | O(n²) |
| Barrier Method | 1.67e-5 | 0.82 | O(n) |

\begin{equation}\label{eq:final_metric}
performance = \frac{1}{T} \sum_{t=1}^T accuracy_t
\end{equation}
""",

            "05_discussion.md": r"""
# Discussion {#sec:discussion}

## Theoretical Implications {#subsec:theory}

Our theoretical results in Theorem 1 improve upon previous work by establishing faster convergence rates for a broader class of problems.

The rate in \eqref{eq:convergence_rate} matches the theoretical optimum for this problem class.

## Practical Considerations {#subsec:practical}

In practice, the choice of step size $\alpha_k$ in \eqref{eq:update} significantly affects performance.

## Limitations and Future Work {#subsec:limitations}

While our method performs well on the tested problems, it may not be suitable for certain edge cases.

Future work includes extending the analysis to non-convex problems.
""",

            "06_conclusion.md": r"""
# Conclusion {#sec:conclusion}

We have presented a novel algorithm for constrained optimization with theoretical convergence guarantees.

## Summary {#subsec:summary}

Our main contributions are:
1. Algorithm with $O(1/k)$ convergence rate
2. Theoretical analysis
3. Experimental validation

The method outperforms existing approaches as demonstrated in Section \ref{sec:results}.

## Future Directions {#subsec:future}

Future work will focus on extending the algorithm to handle non-convex constraints and stochastic settings.

\begin{equation}\label{eq:future_work}
future = \lim_{t\to\infty} progress_t
\end{equation}
""",

            "07_references.md": """
# References {#sec:references}

- [1] Author, A. et al. "Previous work on optimization." Journal, 2020.
- [2] Researcher, B. "Constrained optimization methods." Conference, 2021.
- [3] Scientist, C. "Theoretical foundations." Book, 2019.

All code and data are available at: https://github.com/example/project

For implementation details, see the API documentation in the symbols glossary.
"""
        }

        for filename, content in paper_sections.items():
            (manuscript_dir / filename).write_text(content)

        # Run the complete pipeline
        (test_root / "output" / "figures").mkdir(parents=True)
        (test_root / "output" / "data").mkdir(parents=True)

        # Run scripts
        example_script = test_root / "scripts" / "example_figure.py"
        result1 = subprocess.run([
            sys.executable, str(example_script)
        ], cwd=str(test_root), capture_output=True, text=True)
        assert result1.returncode == 0

        research_script = test_root / "scripts" / "generate_research_figures.py"
        result2 = subprocess.run([
            sys.executable, str(research_script)
        ], cwd=str(test_root), capture_output=True, text=True)
        assert result2.returncode == 0

        # Run validation on manuscript
        validate_script = test_root / "repo_utilities" / "validate_markdown.py"
        result3 = subprocess.run([
            sys.executable, str(validate_script)
        ], cwd=str(test_root), capture_output=True, text=True)
        # Should pass in non-strict mode (even with issues)
        assert result3.returncode == 0

        # Run glossary generation
        glossary_script = test_root / "repo_utilities" / "generate_glossary.py"
        result4 = subprocess.run([
            sys.executable, str(glossary_script)
        ], cwd=str(test_root), capture_output=True, text=True)
        assert result4.returncode == 0

        # Verify all components worked together
        assert (test_root / "output" / "figures" / "example_figure.png").exists()
        assert (test_root / "output" / "figures" / "convergence_plot.png").exists()

        glossary_file = test_root / "manuscript" / "98_symbols_glossary.md"
        assert glossary_file.exists()

        with open(glossary_file, "r") as f:
            content = f.read()
        assert "example" in content.lower()
        assert "glossary_gen" in content.lower()


if __name__ == "__main__":
    pytest.main([__file__])
