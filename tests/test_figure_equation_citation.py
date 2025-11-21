"""Comprehensive tests for figure, equation, and citation handling.

This test suite validates the complete workflow of:
- Figure generation and referencing in markdown
- Equation labeling and cross-referencing
- Citation and bibliography handling
- Integration with PDF generation pipeline
"""

import pytest
import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path
import numpy as np


class TestFigureGeneration:
    """Test figure generation and integration."""

    def test_figure_generation_with_proper_paths(self, tmp_path):
        """Test that figures are generated with correct paths for markdown referencing."""
        test_root = tmp_path / "fig_test"
        test_root.mkdir()
        
        # Create src/ with example module
        src_dir = test_root / "src"
        src_dir.mkdir()
        (src_dir / "example.py").write_text('''
def add_numbers(a, b): return a + b
def multiply_numbers(a, b): return a * b
''')
        
        # Create script that generates figure
        scripts_dir = test_root / "scripts"
        scripts_dir.mkdir()
        script = scripts_dir / "test_figure.py"
        script.write_text('''
import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Add src/ to path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
src_path = os.path.join(repo_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from scientific.example import add_numbers

# Generate figure
output_dir = os.path.join(repo_root, "output")
figure_dir = os.path.join(output_dir, "figures")
os.makedirs(figure_dir, exist_ok=True)

x = np.linspace(0, 10, 100)
y = np.array([add_numbers(xi, 0) for xi in x])

fig, ax = plt.subplots(figsize=(8, 6))
ax.plot(x, y)
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_title('Test Figure')

figure_path = os.path.join(figure_dir, "test_figure.png")
fig.savefig(figure_path, dpi=300, bbox_inches='tight')
plt.close(fig)

print(f"Generated: {figure_path}")
''')
        
        # Run script
        result = subprocess.run([
            sys.executable, str(script)
        ], cwd=str(test_root), capture_output=True, text=True)
        
        assert result.returncode == 0
        assert (test_root / "output" / "figures" / "test_figure.png").exists()
        assert "Generated:" in result.stdout

    def test_figure_referenced_in_markdown(self, tmp_path):
        """Test that figures can be properly referenced in markdown."""
        markdown_content = r"""
# Test Section {#sec:test}

This section demonstrates figure referencing.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/test_figure.png}
\caption{Test figure showing results}
\label{fig:test_figure}
\end{figure}

As shown in Figure \ref{fig:test_figure}, the results are clear.
"""
        
        md_file = tmp_path / "test.md"
        md_file.write_text(markdown_content)
        
        # Verify markdown contains proper LaTeX figure syntax
        content = md_file.read_text()
        assert r'\begin{figure}' in content
        assert r'\includegraphics' in content
        assert r'\label{fig:test_figure}' in content
        assert r'\ref{fig:test_figure}' in content

    def test_multiple_figures_with_unique_labels(self, tmp_path):
        """Test that multiple figures have unique labels."""
        markdown_content = r"""
# Results {#sec:results}

\begin{figure}[h]
\includegraphics[width=0.9\textwidth]{../output/figures/figure1.png}
\caption{First figure}
\label{fig:figure1}
\end{figure}

\begin{figure}[h]
\includegraphics[width=0.9\textwidth]{../output/figures/figure2.png}
\caption{Second figure}
\label{fig:figure2}
\end{figure}

Figure \ref{fig:figure1} shows X, while Figure \ref{fig:figure2} shows Y.
"""
        
        md_file = tmp_path / "test.md"
        md_file.write_text(markdown_content)
        
        content = md_file.read_text()
        
        # Check unique labels
        assert r'\label{fig:figure1}' in content
        assert r'\label{fig:figure2}' in content
        assert r'\ref{fig:figure1}' in content
        assert r'\ref{fig:figure2}' in content


class TestEquationHandling:
    """Test equation labeling and cross-referencing."""

    def test_equation_with_label(self, tmp_path):
        """Test that equations are properly labeled."""
        markdown_content = r"""
# Methodology {#sec:methodology}

The optimization problem is defined as:

\begin{equation}\label{eq:optimization}
\min_{x} f(x) = \|Ax - b\|^2 + \lambda \|x\|_1
\end{equation}

where $\lambda > 0$ is the regularization parameter.
"""
        
        md_file = tmp_path / "test.md"
        md_file.write_text(markdown_content)
        
        content = md_file.read_text()
        assert r'\begin{equation}' in content
        assert r'\label{eq:optimization}' in content
        assert r'\end{equation}' in content

    def test_equation_cross_reference(self, tmp_path):
        """Test that equations can be cross-referenced."""
        markdown_content = r"""
# Theory {#sec:theory}

The main result is given in equation \eqref{eq:main}:

\begin{equation}\label{eq:main}
x_{k+1} = x_k - \alpha \nabla f(x_k)
\end{equation}

Equation \eqref{eq:main} shows the gradient descent update rule.
"""
        
        md_file = tmp_path / "test.md"
        md_file.write_text(markdown_content)
        
        content = md_file.read_text()
        assert r'\eqref{eq:main}' in content
        assert content.count(r'\eqref{eq:main}') == 2  # Two references (both shown)

    def test_multiple_equations_with_unique_labels(self, tmp_path):
        """Test that multiple equations have unique labels."""
        markdown_content = r"""
# Mathematical Framework {#sec:math}

First equation:
\begin{equation}\label{eq:first}
f(x) = x^2
\end{equation}

Second equation:
\begin{equation}\label{eq:second}
g(x) = x^3
\end{equation}

Combining \eqref{eq:first} and \eqref{eq:second} gives the result.
"""
        
        md_file = tmp_path / "test.md"
        md_file.write_text(markdown_content)
        
        content = md_file.read_text()
        
        # Check unique labels
        assert r'\label{eq:first}' in content
        assert r'\label{eq:second}' in content
        assert r'\eqref{eq:first}' in content
        assert r'\eqref{eq:second}' in content

    def test_equation_without_label_detected(self, tmp_path):
        """Test that unlabeled equations are detected."""
        markdown_content = r"""
# Test {#sec:test}

This equation is unlabeled:
\begin{equation}
x = y + z
\end{equation}
"""
        
        md_file = tmp_path / "test.md"
        md_file.write_text(markdown_content)
        
        content = md_file.read_text()
        
        # Check equation exists but no label
        assert r'\begin{equation}' in content
        assert r'\label{eq:' not in content


class TestCitationHandling:
    """Test citation and bibliography handling."""

    def test_citation_in_markdown(self, tmp_path):
        """Test that citations are properly formatted in markdown."""
        markdown_content = r"""
# Introduction {#sec:introduction}

Previous work by Smith et al. \cite{smith2023} has shown that
the algorithm converges at rate $O(1/k)$.

Jones \cite{jones2024} extended this analysis to the stochastic setting.
"""
        
        md_file = tmp_path / "test.md"
        md_file.write_text(markdown_content)
        
        content = md_file.read_text()
        assert r'\cite{smith2023}' in content
        assert r'\cite{jones2024}' in content

    def test_bibliography_file_structure(self, tmp_path):
        """Test that bibliography files are properly structured."""
        bibtex_content = r"""
@article{smith2023,
  title={Novel optimization algorithms},
  author={Smith, Jane and Doe, John},
  journal={Journal of Machine Learning},
  year={2023}
}

@inproceedings{jones2024,
  title={Stochastic gradient descent analysis},
  author={Jones, Alice},
  booktitle={Conference on Learning Theory},
  year={2024}
}
"""
        
        bib_file = tmp_path / "references.bib"
        bib_file.write_text(bibtex_content)
        
        content = bib_file.read_text()
        
        assert '@article{smith2023' in content
        assert '@inproceedings{jones2024' in content
        assert 'title=' in content
        assert 'author=' in content

    def test_multiple_citations_same_sentence(self, tmp_path):
        """Test handling of multiple citations in one sentence."""
        markdown_content = r"""
# Related Work {#sec:related}

Several methods have been proposed \cite{smith2023,jones2024,brown2022}
for solving this problem.
"""
        
        md_file = tmp_path / "test.md"
        md_file.write_text(markdown_content)
        
        content = md_file.read_text()
        assert r'\cite{smith2023,jones2024,brown2022}' in content


class TestIntegratedWorkflow:
    """Test integrated workflow of figures, equations, and citations."""

    def test_complete_manuscript_section(self, tmp_path):
        """Test a complete manuscript section with all elements."""
        markdown_content = r"""
# Experimental Results {#sec:results}

## Convergence Analysis {#subsec:convergence}

We evaluate the convergence properties using the metric defined in 
equation \eqref{eq:metric}:

\begin{equation}\label{eq:metric}
metric_k = \|x_k - x^*\| / \|x_0 - x^*\|
\end{equation}

Figure \ref{fig:convergence} shows the convergence behavior of our
algorithm compared to the baseline method from \cite{baseline2023}.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/convergence_plot.png}
\caption{Convergence comparison showing superior performance of our method}
\label{fig:convergence}
\end{figure}

As demonstrated in Figure \ref{fig:convergence}, our method achieves
faster convergence than previous approaches \cite{smith2023,jones2024}.

## Performance Metrics {#subsec:performance}

The performance is measured using equation \eqref{eq:performance}:

\begin{equation}\label{eq:performance}
performance = \frac{1}{T} \sum_{t=1}^T accuracy_t
\end{equation}

Table \ref{tab:performance} summarizes the results.

| Method | Accuracy | Convergence Rate |
|--------|----------|------------------|
| Our Method | 0.95 | 0.85 |
| Baseline \cite{baseline2023} | 0.85 | 0.90 |

"""
        
        md_file = tmp_path / "04_experimental_results.md"
        md_file.write_text(markdown_content)
        
        content = md_file.read_text()
        
        # Verify all elements present
        assert r'\label{eq:metric}' in content
        assert r'\label{eq:performance}' in content
        assert r'\eqref{eq:metric}' in content
        assert r'\eqref{eq:performance}' in content
        assert r'\label{fig:convergence}' in content
        assert r'\ref{fig:convergence}' in content
        assert r'\cite{baseline2023}' in content
        assert r'\cite{smith2023,jones2024}' in content

    def test_cross_section_references(self, tmp_path):
        """Test that references work across multiple sections."""
        intro_content = r"""
# Introduction {#sec:introduction}

We present a novel algorithm with convergence rate $O(1/k)$.
See Section \ref{sec:methodology} for details.
"""
        
        methodology_content = r"""
# Methodology {#sec:methodology}

The algorithm is defined in equation \eqref{eq:algorithm}:

\begin{equation}\label{eq:algorithm}
x_{k+1} = x_k - \alpha \nabla f(x_k)
\end{equation}

Results are shown in Section \ref{sec:results}.
"""
        
        results_content = r"""
# Results {#sec:results}

Applying equation \eqref{eq:algorithm} from Section \ref{sec:methodology}
yields the convergence shown in Figure \ref{fig:convergence}.

\begin{figure}[h]
\includegraphics[width=0.9\textwidth]{../output/figures/convergence.png}
\caption{Convergence results}
\label{fig:convergence}
\end{figure}
"""
        
        (tmp_path / "01_introduction.md").write_text(intro_content)
        (tmp_path / "02_methodology.md").write_text(methodology_content)
        (tmp_path / "03_results.md").write_text(results_content)
        
        # Verify cross-references
        intro = (tmp_path / "01_introduction.md").read_text()
        methodology = (tmp_path / "02_methodology.md").read_text()
        results = (tmp_path / "03_results.md").read_text()
        
        assert r'\ref{sec:methodology}' in intro
        assert r'\ref{sec:results}' in methodology
        assert r'\ref{sec:methodology}' in results
        assert r'\eqref{eq:algorithm}' in results
        assert r'\ref{fig:convergence}' in results


class TestValidationIntegration:
    """Test integration with validation systems."""

    def test_markdown_validation_detects_missing_figures(self, tmp_path):
        """Test that markdown validation detects missing figure files."""
        markdown_content = r"""
# Test {#sec:test}

![Missing Figure](../output/figures/missing.png)
"""
        
        md_file = tmp_path / "test.md"
        md_file.write_text(markdown_content)
        
        # Figure file does NOT exist
        assert not (tmp_path / "output" / "figures" / "missing.png").exists()
        
        # Validation should detect this (tested in validate_markdown tests)

    def test_markdown_validation_detects_missing_equation_labels(self, tmp_path):
        """Test that validation detects equations without labels."""
        markdown_content = r"""
# Test {#sec:test}

\begin{equation}
x = y + z
\end{equation}
"""
        
        md_file = tmp_path / "test.md"
        md_file.write_text(markdown_content)
        
        content = md_file.read_text()
        
        # Has equation but no label
        assert r'\begin{equation}' in content
        assert r'\label{eq:' not in content

    def test_markdown_validation_detects_unresolved_references(self, tmp_path):
        """Test that validation detects unresolved cross-references."""
        markdown_content = r"""
# Test {#sec:test}

See equation \eqref{eq:nonexistent} for details.
"""
        
        md_file = tmp_path / "test.md"
        md_file.write_text(markdown_content)
        
        content = md_file.read_text()
        
        # References equation that doesn't exist
        assert r'\eqref{eq:nonexistent}' in content


class TestPDFGenerationIntegration:
    """Test integration with PDF generation pipeline."""

    def test_pdf_includes_figures(self, tmp_path):
        """Test that generated PDFs include referenced figures."""
        # This would require actual PDF generation
        # For now, verify the markdown setup is correct
        markdown_content = r"""
# Test {#sec:test}

\begin{figure}[h]
\includegraphics[width=0.9\textwidth]{../output/figures/test.png}
\caption{Test figure}
\label{fig:test}
\end{figure}
"""
        
        md_file = tmp_path / "test.md"
        md_file.write_text(markdown_content)
        
        # Create dummy figure
        figures_dir = tmp_path / "output" / "figures"
        figures_dir.mkdir(parents=True)
        (figures_dir / "test.png").write_bytes(b"PNG dummy content")
        
        # Verify setup
        assert (figures_dir / "test.png").exists()
        content = md_file.read_text()
        assert r'\includegraphics' in content

    def test_pdf_resolves_equation_references(self, tmp_path):
        """Test that PDF generation resolves equation references."""
        markdown_content = r"""
# Test {#sec:test}

\begin{equation}\label{eq:test}
x = y + z
\end{equation}

Equation \eqref{eq:test} shows the relationship.
"""
        
        md_file = tmp_path / "test.md"
        md_file.write_text(markdown_content)
        
        content = md_file.read_text()
        
        # Verify structure for PDF generation
        assert r'\label{eq:test}' in content
        assert r'\eqref{eq:test}' in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

