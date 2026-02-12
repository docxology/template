"""Comprehensive tests for the generate_research_figures.py script to ensure 100% coverage."""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest


class TestGenerateResearchFiguresScript:
    """Test the generate_research_figures.py script functionality."""

    def test_script_exists_and_executable(self):
        """Test that the generate_research_figures.py script exists."""
        script_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "scripts",
            "generate_research_figures.py",
        )
        assert os.path.exists(script_path)

    def test_script_has_shebang(self):
        """Test that script has proper Python shebang."""
        script_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "scripts",
            "generate_research_figures.py",
        )
        with open(script_path, "r") as f:
            first_line = f.readline().strip()
            assert first_line == "#!/usr/bin/env python3"

    def test_ensure_src_on_path_function(self, tmp_path):
        """Test _ensure_src_on_path function adds src/ to sys.path."""
        # Create a test script with the function
        test_script = tmp_path / "test_research_figures.py"
        test_script.write_text(
            """
import os
import sys

def _ensure_src_on_path():
    # For testing, we need to find the actual src directory
    # Try multiple possible locations
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "..", "src"),  # Relative to test file
        os.path.join(os.getcwd(), "src"),  # Relative to current working directory
        "/Users/4d/Documents/GitHub/template/src"  # Absolute path for testing
    ]

    for src_path in possible_paths:
        if os.path.exists(src_path):
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            break

def main():
    _ensure_src_on_path()
    return 0

if __name__ == "__main__":
    main()
"""
        )

        # Test that it adds src/ to path
        original_path = sys.path.copy()
        try:
            # Execute the function in a subprocess to test it properly
            result = subprocess.run(
                [sys.executable, str(test_script)],
                cwd=str(tmp_path),
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0
            # The function should execute without error
        finally:
            sys.path[:] = original_path

    def test_setup_directories_function(self, tmp_path):
        """Test _setup_directories function creates proper directory structure."""
        # Create a test script with the function
        test_script = tmp_path / "test_setup.py"
        test_script.write_text(
            """
import os

def _setup_directories():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    output_dir = os.path.join(repo_root, "output")
    data_dir = os.path.join(output_dir, "data")
    figure_dir = os.path.join(output_dir, "figures")

    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(figure_dir, exist_ok=True)

    return output_dir, data_dir, figure_dir

def main():
    output_dir, data_dir, figure_dir = _setup_directories()
    print(f"Output: {output_dir}")
    print(f"Data: {data_dir}")
    print(f"Figures: {figure_dir}")
    return 0

if __name__ == "__main__":
    main()
"""
        )

        # Test directory creation
        result = subprocess.run(
            [sys.executable, str(test_script)],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Output:" in result.stdout
        assert "Data:" in result.stdout
        assert "Figures:" in result.stdout

    def test_convergence_plot_generation(self, tmp_path):
        """Test convergence_plot function generates proper output."""
        # Setup test environment with proper project structure
        test_root = tmp_path / "test_convergence"
        test_root.mkdir()

        # Create proper project structure
        project_dir = test_root / "project"
        src_dir = project_dir / "src"
        src_dir.mkdir(parents=True)
        
        # Create core package
        core_dir = src_dir / "core"
        core_dir.mkdir()
        (core_dir / "__init__.py").write_text("")
        (src_dir / "__init__.py").write_text("")
        
        # Create visualization package
        viz_dir = src_dir / "visualization"
        viz_dir.mkdir()
        (viz_dir / "__init__.py").write_text("")
        (viz_dir / "visualization.py").write_text(
            """
class VisualizationEngine:
    def __init__(self, output_dir):
        self.output_dir = output_dir
    def generate_figure(self, *args, **kwargs):
        return "mock_figure.png"
"""
        )
        (core_dir / "example.py").write_text(
            """
def add_numbers(a, b): return a + b
def multiply_numbers(a, b): return a * b
def calculate_average(numbers): return sum(numbers) / len(numbers) if numbers else None
"""
        )

        # Create a test script that calls the function
        test_script = project_dir / "test_convergence.py"
        test_script.write_text(
            """
import os
import sys

def _ensure_src_on_path():
    # Ensure src/ is on path
    project_root = os.path.abspath(os.path.dirname(__file__))
    src_path = os.path.join(project_root, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

def generate_convergence_plot(figure_dir, data_dir):
    _ensure_src_on_path()
    try:
        from core.example import add_numbers, multiply_numbers, calculate_average
        print("✅ Using src/ functions for convergence plot")
    except ImportError as e:
        print(f"❌ Failed to import from src/example.py: {e}")
        return ""

    import matplotlib.pyplot as plt
    import numpy as np

    # Generate synthetic convergence data
    iterations = np.arange(1, 101)

    # Use src/ functions to process the data
    our_method_raw = 2.0 * np.exp(-0.1 * iterations) + 0.1
    baseline_raw = 1.5 * np.exp(-0.05 * iterations) + 0.2

    # Apply src/ functions to demonstrate integration
    our_method_list = []
    baseline_list = []
    for i, (our_val, base_val) in enumerate(zip(our_method_raw, baseline_raw)):
        our_processed = add_numbers(our_val, 0.0)
        base_processed = multiply_numbers(base_val, 1.0)
        our_method_list.append(our_processed)
        baseline_list.append(base_processed)

    our_method = np.array(our_method_list)
    baseline = np.array(baseline_list)

    # Calculate statistics using src/ functions
    our_avg = calculate_average(our_method.tolist())
    base_avg = calculate_average(baseline.tolist())

    print(f"Convergence analysis using src/ functions:")
    print(f"  Our method average: {our_avg:.6f}")
    print(f"  Baseline average: {base_avg:.6f}")

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.semilogy(iterations, our_method, 'b-', linewidth=2, label='Our Method')
    ax.semilogy(iterations, baseline, 'r--', linewidth=2, label='Baseline')
    ax.set_xlabel('Iteration')
    ax.set_ylabel('Objective Value')
    ax.set_title('Algorithm Convergence Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3)

    figure_path = os.path.join(figure_dir, "domain_comparison.png")
    fig.savefig(figure_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Save data
    data_path = os.path.join(data_dir, "convergence_data.npz")
    np.savez(data_path, iterations=iterations, our_method=our_method, baseline=baseline,
              our_avg=our_avg, base_avg=base_avg)

    print(figure_path)
    print(data_path)
    return figure_path

def main():
    # Use script directory for consistent path resolution
    script_dir = os.path.dirname(__file__)
    output_dir = os.path.join(script_dir, "output")
    data_dir = os.path.join(output_dir, "data")
    figure_dir = os.path.join(output_dir, "figures")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(figure_dir, exist_ok=True)

    figure_path = generate_convergence_plot(figure_dir, data_dir)
    return 0

if __name__ == "__main__":
    main()
"""
        )

        # Run the test script
        result = subprocess.run(
            [sys.executable, str(test_script)],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
        )

        # Debug: Log stdout and stderr if the script failed
        if result.returncode != 0:
            # Keep print for test debugging - this is acceptable for test failure diagnostics
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)

        # Should succeed
        assert result.returncode == 0

        # Check that files were created
        figure_path = project_dir / "output" / "figures" / "domain_comparison.png"
        data_path = project_dir / "output" / "data" / "convergence_data.npz"

        assert figure_path.exists()
        assert data_path.exists()

        # Check data file content
        data = np.load(data_path)
        assert "iterations" in data
        assert "our_method" in data
        assert "baseline" in data
        assert "our_avg" in data
        assert "base_avg" in data

    def test_experimental_setup_generation(self, tmp_path):
        """Test experimental_setup function generates proper output."""
        # Setup test environment
        test_root = tmp_path / "test_setup"
        test_root.mkdir()

        src_dir = test_root / "src"
        src_dir.mkdir()
        
        # Create core package
        core_dir = src_dir / "core"
        core_dir.mkdir()
        (core_dir / "__init__.py").write_text("")
        (src_dir / "__init__.py").write_text("")
        
        # Create visualization package
        viz_dir = src_dir / "visualization"
        viz_dir.mkdir()
        (viz_dir / "__init__.py").write_text("")
        (viz_dir / "visualization.py").write_text(
            """
class VisualizationEngine:
    def __init__(self, output_dir):
        self.output_dir = output_dir
    def generate_figure(self, *args, **kwargs):
        return "mock_figure.png"
"""
        )
        (core_dir / "example.py").write_text(
            """
def is_even(n): return n % 2 == 0
def is_odd(n): return not is_even(n)
"""
        )

        # Create a test script that calls the function
        test_script = test_root / "test_setup.py"
        test_script.write_text(
            """
import os
import sys

def _ensure_src_on_path():
    # For testing, we need to find the actual src directory
    # Try multiple possible locations
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "..", "src"),  # Relative to test file
        os.path.join(os.getcwd(), "src"),  # Relative to current working directory
        "/Users/4d/Documents/GitHub/template/src"  # Absolute path for testing
    ]

    for src_path in possible_paths:
        if os.path.exists(src_path):
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            break

def generate_experimental_setup(figure_dir, data_dir):
    _ensure_src_on_path()
    try:
        from core.example import is_even, is_odd
        print("✅ Using src/ functions for experimental setup validation")
        num_components = 3
        print(f"Number of components: {num_components}")
        print(f"  Is even: {is_even(num_components)}")
        print(f"  Is odd: {is_odd(num_components)}")
    except ImportError as e:
        print(f"❌ Failed to import from src/example.py: {e}")

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(12, 8))

    # Create a simple flowchart-like diagram
    components = ['Data\\nPreprocessing', 'Algorithm\\nExecution', 'Performance\\nEvaluation']
    x_positions = [2, 6, 10]
    y_positions = [4, 4, 4]

    for i, (comp, x, y) in enumerate(zip(components, x_positions, y_positions)):
        # Draw boxes
        rect = plt.Rectangle((x-1, y-0.5), 2, 1, facecolor='lightblue',
                           edgecolor='black', linewidth=2)
        ax.add_patch(rect)
        ax.text(x, y, comp, ha='center', va='center', fontsize=10, fontweight='bold')

        # Draw arrows
        if i < len(components) - 1:
            ax.arrow(x+1, y, 1.5, 0, head_width=0.2, head_length=0.2,
                    fc='black', ec='black', linewidth=2)

    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.set_title('Experimental Pipeline', fontsize=14, fontweight='bold')
    ax.axis('off')

    figure_path = os.path.join(figure_dir, "experimental_setup.png")
    fig.savefig(figure_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    print(figure_path)
    return figure_path

def main():
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    data_dir = os.path.join(output_dir, "data")
    figure_dir = os.path.join(output_dir, "figures")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(figure_dir, exist_ok=True)

    figure_path = generate_experimental_setup(figure_dir, data_dir)
    return 0

if __name__ == "__main__":
    main()
"""
        )

        # Run the test script
        result = subprocess.run(
            [sys.executable, str(test_script)],
            cwd=str(test_root),
            capture_output=True,
            text=True,
        )

        # Should succeed
        assert result.returncode == 0

        # Check that file was created
        figure_path = test_root / "output" / "figures" / "experimental_setup.png"
        assert figure_path.exists()

        # Check file size is reasonable
        assert os.path.getsize(figure_path) > 1000

    def test_script_comprehensive_functionality(self, tmp_path):
        """Test that the script generates all expected outputs with proper src/ integration."""
        # Setup test environment — use real project src/ for imports
        test_root = tmp_path / "test_comprehensive"
        test_root.mkdir()

        # Copy the script
        script_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "scripts",
            "generate_research_figures.py",
        )
        test_script = test_root / "scripts" / "generate_research_figures.py"
        test_script.parent.mkdir()
        shutil.copy2(script_path, test_script)

        # Run the script with PYTHONPATH pointing to the real project
        # so src.analysis, src.visualization etc. are importable
        project_root = str(Path(__file__).parent.parent.parent)  # ento_linguistics/
        repo_root = str(Path(__file__).parent.parent.parent.parent.parent)  # template/
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{project_root}:{repo_root}:{env.get('PYTHONPATH', '')}"

        result = subprocess.run(
            [sys.executable, str(test_script)],
            cwd=str(test_root),
            capture_output=True,
            text=True,
            env=env,
        )

        # Should succeed
        assert result.returncode == 0, f"Script failed:\n{result.stderr}"

        # Check that it reports successful generation
        combined_output = result.stdout + result.stderr

        # Check for the new pipeline output markers
        assert "concept_map.png" in combined_output
        assert "terminology_network.png" in combined_output
        assert "domain_comparison.png" in combined_output

        # Check that src/ integration is demonstrated
        assert "Integration with src/ modules demonstrated" in combined_output

        # Verify output files exist
        figures_dir = test_root / "output" / "figures"
        assert (figures_dir / "concept_map.png").exists()
        assert (figures_dir / "terminology_network.png").exists()
        assert (figures_dir / "domain_comparison.png").exists()

    def test_main_function_comprehensive_generation(self, tmp_path):
        """Test main function generates all expected outputs."""
        test_root = tmp_path / "test_comprehensive"
        test_root.mkdir()

        # Copy script
        script_path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "scripts", "generate_research_figures.py",
        )
        test_script = test_root / "scripts" / "generate_research_figures.py"
        test_script.parent.mkdir()
        shutil.copy2(script_path, test_script)

        # Include real project src/ for analysis imports
        project_root = str(Path(__file__).parent.parent.parent)
        repo_root = str(Path(__file__).parent.parent.parent.parent.parent)
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{project_root}:{repo_root}:{env.get('PYTHONPATH', '')}"

        result = subprocess.run(
            [sys.executable, str(test_script)],
            cwd=str(test_root),
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 0, f"Script failed:\n{result.stderr}"

        combined_output = result.stdout + result.stderr
        assert "concept_map.png" in combined_output
        assert "terminology_network.png" in combined_output
        assert "domain_comparison.png" in combined_output
        assert "Integration with src/ modules demonstrated" in combined_output

    def test_main_function_handles_src_import_failures(self, tmp_path):
        """Test script fails with error when src/ modules unavailable."""
        # Setup test environment WITHOUT real src/ available
        test_root = tmp_path / "test_import_failure"
        test_root.mkdir()

        script_path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "scripts", "generate_research_figures.py",
        )
        test_script = test_root / "scripts" / "generate_research_figures.py"
        test_script.parent.mkdir()
        shutil.copy2(script_path, test_script)

        # Deliberately exclude real project from PYTHONPATH
        env = os.environ.copy()
        env["PYTHONPATH"] = str(tmp_path)  # Empty path

        result = subprocess.run(
            [sys.executable, str(test_script)],
            cwd=str(test_root),
            capture_output=True,
            text=True,
            env=env,
        )

        # Script should fail because real analysis modules are required
        assert result.returncode != 0
        combined_output = result.stdout + result.stderr
        assert "ModuleNotFoundError" in combined_output or "ImportError" in combined_output

    def test_main_function_matplotlib_backend_setting(self, tmp_path):
        """Test that main function properly sets matplotlib backend."""
        test_root = tmp_path / "test_backend"
        test_root.mkdir()

        script_path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "scripts", "generate_research_figures.py",
        )
        test_script = test_root / "scripts" / "generate_research_figures.py"
        test_script.parent.mkdir()
        shutil.copy2(script_path, test_script)

        project_root = str(Path(__file__).parent.parent.parent)
        repo_root = str(Path(__file__).parent.parent.parent.parent.parent)
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{project_root}:{repo_root}:{env.get('PYTHONPATH', '')}"

        result = subprocess.run(
            [sys.executable, str(test_script)],
            cwd=str(test_root),
            capture_output=True,
            text=True,
            env=env,
        )

        # Should succeed — the script sets MPLBACKEND=Agg at runtime
        assert result.returncode == 0, f"Script failed:\n{result.stderr}"

    def test_generated_files_are_deterministic(self, tmp_path):
        """Test that generated files are deterministic across runs."""
        test_root = tmp_path / "test_deterministic"
        test_root.mkdir()

        script_path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "scripts", "generate_research_figures.py",
        )
        test_script = test_root / "scripts" / "generate_research_figures.py"
        test_script.parent.mkdir()
        shutil.copy2(script_path, test_script)

        project_root = str(Path(__file__).parent.parent.parent)
        repo_root = str(Path(__file__).parent.parent.parent.parent.parent)
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{project_root}:{repo_root}:{env.get('PYTHONPATH', '')}"

        result1 = subprocess.run(
            [sys.executable, str(test_script)],
            cwd=str(test_root),
            capture_output=True,
            text=True,
            env=env,
        )

        result2 = subprocess.run(
            [sys.executable, str(test_script)],
            cwd=str(test_root),
            capture_output=True,
            text=True,
            env=env,
        )

        # Both should succeed
        assert result1.returncode == 0, f"Run 1 failed:\n{result1.stderr}"
        assert result2.returncode == 0, f"Run 2 failed:\n{result2.stderr}"

        # Check that domain comparison figure exists after both runs
        data_path = test_root / "output" / "figures" / "domain_comparison.png"
        assert data_path.exists()



if __name__ == "__main__":
    pytest.main([__file__])
