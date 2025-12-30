"""Tests for executive report generation script (Stage 10).

Integration tests for the 07_generate_executive_report.py orchestrator.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def mock_project_structure(tmp_path):
    """Create mock project structure for testing."""
    # Create projects directory
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    
    # Create two test projects
    for project_name in ["project1", "project2"]:
        project_root = projects_dir / project_name
        project_root.mkdir()
        
        # Create manuscript
        manuscript_dir = project_root / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "01_intro.md").write_text("# Test\n\nTest manuscript with 10 words for testing purposes here.\n")
        
        # Create src
        src_dir = project_root / "src"
        src_dir.mkdir()
        (src_dir / "test.py").write_text("def test():\n    pass\n")
        
        # Create reports
        reports_dir = project_root / "output" / "reports"
        reports_dir.mkdir(parents=True)
        
        test_report = {
            "project_tests": {
                "total": 50,
                "passed": 50,
                "failed": 0,
                "skipped": 0,
                "coverage_percent": 95.0
            },
            "summary": {"total_execution_time": 5.0}
        }
        (reports_dir / "test_results.json").write_text(json.dumps(test_report))
        
        pipeline_report = {
            "total_duration": 60.0,
            "stages": [
                {"name": "setup", "status": "passed", "duration": 5.0},
                {"name": "tests", "status": "passed", "duration": 10.0}
            ]
        }
        (reports_dir / "pipeline_report.json").write_text(json.dumps(pipeline_report))
        
        # Create output directory
        output_dir = tmp_path / "output" / project_name
        output_dir.mkdir(parents=True)
        
        pdf_dir = output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "test.pdf").write_text("PDF content")
    
    return tmp_path


class TestExecutiveReportScript:
    """Test executive report generation script."""
    
    def test_script_exists(self):
        """Test that the script file exists."""
        # Resolve path relative to repository root
        repo_root = Path(__file__).parent.parent.parent
        script_path = repo_root / "scripts" / "07_generate_executive_report.py"
        assert script_path.exists()
    
    def test_script_imports(self):
        """Test that the script can be imported."""
        # Add scripts to path
        repo_root = Path(__file__).parent.parent.parent
        scripts_path = repo_root / "scripts"
        sys.path.insert(0, str(scripts_path))
        
        try:
            # Import the module (will execute module-level code but not main())
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "exec_report",
                scripts_path / "07_generate_executive_report.py"
            )
            module = importlib.util.module_from_spec(spec)
            
            # Should not raise import errors
            spec.loader.exec_module(module)
            
            # Check that main function exists
            assert hasattr(module, 'main')
            assert callable(module.main)
            
        finally:
            sys.path.remove(str(scripts_path))
    
    def test_verify_project_completion(self, mock_project_structure):
        """Test project completion verification."""
        # Import verify function
        repo_root = Path(__file__).parent.parent.parent
        scripts_path = repo_root / "scripts"
        sys.path.insert(0, str(scripts_path))
        
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "exec_report",
                scripts_path / "07_generate_executive_report.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Test with valid project
            is_complete = module.verify_project_completion(mock_project_structure, "project1")
            assert is_complete is True
            
            # Test with invalid project
            is_complete = module.verify_project_completion(mock_project_structure, "nonexistent")
            assert is_complete is False
            
        finally:
            sys.path.remove(str(scripts_path))


class TestScriptIntegration:
    """Integration tests for the complete script."""
    
    def test_script_execution_help(self):
        """Test script execution with --help flag."""
        repo_root = Path(__file__).parent.parent.parent
        script_path = repo_root / "scripts" / "07_generate_executive_report.py"
        
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True
        )
        
        # Should show help and exit successfully
        assert result.returncode == 0
        assert "executive report" in result.stdout.lower() or "usage" in result.stdout.lower()


class TestErrorHandling:
    """Test error handling in the script."""
    
    def test_no_projects_handling(self, tmp_path):
        """Test handling when no projects are found."""
        # Create empty projects directory
        (tmp_path / "projects").mkdir()
        
        repo_root = Path(__file__).parent.parent.parent
        scripts_path = repo_root / "scripts"
        sys.path.insert(0, str(scripts_path))
        
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "exec_report",
                scripts_path / "07_generate_executive_report.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # The verify function should handle missing projects gracefully
            is_complete = module.verify_project_completion(tmp_path, "nonexistent")
            assert is_complete is False
            
        finally:
            sys.path.remove(str(scripts_path))
