from pathlib import Path

def test_config_exists():
    """Verify that the manuscript config exists."""
    config_path = Path(__file__).parent.parent / "manuscript" / "config.yaml"
    assert config_path.exists()

def test_viz_script_exists():
    """Verify that the visualization script exists."""
    script_path = Path(__file__).parent.parent / "scripts" / "generate_architecture_viz.py"
    assert script_path.exists()
