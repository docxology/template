"""Tests for infrastructure.validation.output.validator module.

Comprehensive tests for output validation functionality including
copied outputs validation and output structure validation.
"""


class TestValidateRootOutputStructure:
    """Test validate_root_output_structure function."""

    def test_output_directory_not_exists(self, tmp_path):
        """Test validation when output directory doesn't exist."""
        from infrastructure.validation.output.validator import validate_root_output_structure

        result = validate_root_output_structure(tmp_path)

        assert result["valid"] is False
        assert "does not exist" in result["issues"][0]
        assert result["project_folders"] == []
        assert result["invalid_folders"] == []

    def test_valid_project_folders_only(self, tmp_path):
        """Test validation with only valid project folders."""
        from infrastructure.validation.output.validator import validate_root_output_structure

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create a projects directory with valid project (needs full structure)
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        project_dir = projects_dir / "test_project"
        project_dir.mkdir()
        (project_dir / "manuscript").mkdir()
        (project_dir / "manuscript" / "config.yaml").write_text("paper:\n  title: Test")
        (project_dir / "src").mkdir()
        (project_dir / "src" / "__init__.py").write_text("")
        (project_dir / "tests").mkdir()
        (project_dir / "tests" / "__init__.py").write_text("")
        (project_dir / "output").mkdir()

        # Create project folder in output
        (output_dir / "test_project").mkdir()

        result = validate_root_output_structure(tmp_path)

        assert result["valid"] is True
        assert "test_project" in result["project_folders"]
        assert result["invalid_folders"] == []

    def test_valid_nested_program_folder_only(self, tmp_path):
        """Nested project outputs keep their top-level program directory."""
        from infrastructure.validation.output.validator import validate_root_output_structure

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        project_dir = tmp_path / "projects" / "my_program" / "nested_project"
        (project_dir / "manuscript").mkdir(parents=True)
        (project_dir / "manuscript" / "config.yaml").write_text("paper:\n  title: Test")
        (project_dir / "src").mkdir()
        (project_dir / "src" / "__init__.py").write_text("")
        (project_dir / "tests").mkdir()
        (project_dir / "tests" / "__init__.py").write_text("")
        (project_dir / "output").mkdir()

        (output_dir / "my_program" / "nested_project").mkdir(parents=True)

        result = validate_root_output_structure(tmp_path)

        assert result["valid"] is True
        assert "my_program" in result["project_folders"]
        assert result["invalid_folders"] == []

    def test_invalid_root_level_directories(self, tmp_path):
        """Test validation with invalid root-level directories."""
        from infrastructure.validation.output.validator import validate_root_output_structure

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create a projects directory with valid project (needs full structure)
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        project_dir = projects_dir / "test_project"
        project_dir.mkdir()
        (project_dir / "manuscript").mkdir()
        (project_dir / "manuscript" / "config.yaml").write_text("paper:\n  title: Test")
        (project_dir / "src").mkdir()
        (project_dir / "src" / "__init__.py").write_text("")
        (project_dir / "tests").mkdir()
        (project_dir / "tests" / "__init__.py").write_text("")
        (project_dir / "output").mkdir()

        # Create project folder
        (output_dir / "test_project").mkdir()

        # Create invalid root-level directories
        (output_dir / "data").mkdir()
        (output_dir / "figures").mkdir()
        (output_dir / "pdf").mkdir()

        result = validate_root_output_structure(tmp_path)

        assert result["valid"] is False
        assert len(result["invalid_folders"]) == 3
        assert "data" in result["invalid_folders"]
        assert "figures" in result["invalid_folders"]
        assert "pdf" in result["invalid_folders"]

    def test_unknown_directories_flagged(self, tmp_path):
        """Test that unknown directories are flagged."""
        from infrastructure.validation.output.validator import validate_root_output_structure

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create a projects directory with valid project (needs full structure)
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        project_dir = projects_dir / "test_project"
        project_dir.mkdir()
        (project_dir / "manuscript").mkdir()
        (project_dir / "manuscript" / "config.yaml").write_text("paper:\n  title: Test")
        (project_dir / "src").mkdir()
        (project_dir / "src" / "__init__.py").write_text("")
        (project_dir / "tests").mkdir()
        (project_dir / "tests" / "__init__.py").write_text("")
        (project_dir / "output").mkdir()

        # Create unknown directory (not a project, not a standard folder)
        (output_dir / "random_folder").mkdir()

        result = validate_root_output_structure(tmp_path)

        assert result["valid"] is False
        assert any("Unknown directory" in issue for issue in result["issues"])

    def test_files_in_output_ignored(self, tmp_path):
        """Test that files in output directory are ignored."""
        from infrastructure.validation.output.validator import validate_root_output_structure

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create a projects directory with valid project (needs full structure)
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        project_dir = projects_dir / "test_project"
        project_dir.mkdir()
        (project_dir / "manuscript").mkdir()
        (project_dir / "manuscript" / "config.yaml").write_text("paper:\n  title: Test")
        (project_dir / "src").mkdir()
        (project_dir / "src" / "__init__.py").write_text("")
        (project_dir / "tests").mkdir()
        (project_dir / "tests" / "__init__.py").write_text("")
        (project_dir / "output").mkdir()

        # Create project folder
        (output_dir / "test_project").mkdir()

        # Create file (should be ignored)
        (output_dir / "readme.txt").write_text("readme content")

        result = validate_root_output_structure(tmp_path)

        assert result["valid"] is True

    def test_gitkeep_ignored(self, tmp_path):
        """Test that .gitkeep and .gitignore are ignored."""
        from infrastructure.validation.output.validator import validate_root_output_structure

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create a projects directory with valid project (needs full structure)
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        project_dir = projects_dir / "test_project"
        project_dir.mkdir()
        (project_dir / "manuscript").mkdir()
        (project_dir / "manuscript" / "config.yaml").write_text("paper:\n  title: Test")
        (project_dir / "src").mkdir()
        (project_dir / "src" / "__init__.py").write_text("")
        (project_dir / "tests").mkdir()
        (project_dir / "tests" / "__init__.py").write_text("")
        (project_dir / "output").mkdir()

        # Create project folder
        (output_dir / "test_project").mkdir()

        # Create .gitkeep directory (unusual but should be ignored)
        (output_dir / ".gitkeep").mkdir()
        (output_dir / ".gitignore").mkdir()

        result = validate_root_output_structure(tmp_path)

        assert result["valid"] is True

    def test_multi_project_report_dirs_ignored(self, tmp_path):
        """Multi-project report folders are valid root output entries."""
        from infrastructure.validation.output.validator import validate_root_output_structure

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / "multi_project_summary").mkdir()
        (output_dir / "executive_summary").mkdir()

        result = validate_root_output_structure(tmp_path)

        assert result["valid"] is True
        assert result["invalid_folders"] == []
