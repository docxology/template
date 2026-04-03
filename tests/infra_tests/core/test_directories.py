"""Tests for infrastructure.core.runtime._directories."""


from infrastructure.core.runtime._directories import (
    _project_output_dirs,
    setup_directories,
    validate_directory_structure,
    verify_source_structure,
)


class TestProjectOutputDirs:
    def test_returns_list(self):
        dirs = _project_output_dirs("myproj")
        assert isinstance(dirs, list)
        assert len(dirs) > 0

    def test_contains_output_dirs(self):
        dirs = _project_output_dirs("myproj")
        assert "output/myproj" in dirs
        assert "output/myproj/pdf" in dirs
        assert "output/myproj/figures" in dirs

    def test_contains_project_dirs(self):
        dirs = _project_output_dirs("myproj")
        assert "projects/myproj/output" in dirs
        assert "projects/myproj/output/figures" in dirs


class TestSetupDirectories:
    def test_creates_default_directories(self, tmp_path):
        result = setup_directories(tmp_path, "testproj")
        assert result is True
        # Check some directories exist
        assert (tmp_path / "output" / "testproj").is_dir()
        assert (tmp_path / "output" / "testproj" / "pdf").is_dir()
        assert (tmp_path / "projects" / "testproj" / "output").is_dir()

    def test_creates_custom_directories(self, tmp_path):
        custom = ["custom/dir1", "custom/dir2"]
        result = setup_directories(tmp_path, "proj", directories=custom)
        assert result is True
        assert (tmp_path / "custom" / "dir1").is_dir()
        assert (tmp_path / "custom" / "dir2").is_dir()

    def test_idempotent(self, tmp_path):
        result1 = setup_directories(tmp_path, "proj")
        result2 = setup_directories(tmp_path, "proj")
        assert result1 is True
        assert result2 is True


class TestVerifySourceStructure:
    def test_all_present(self, tmp_path):
        # Create required directories
        (tmp_path / "infrastructure").mkdir()
        (tmp_path / "projects" / "myproj" / "src").mkdir(parents=True)
        (tmp_path / "projects" / "myproj" / "tests").mkdir(parents=True)

        result = verify_source_structure(tmp_path, "myproj")
        assert result is True

    def test_missing_required(self, tmp_path):
        # Only create infrastructure, not projects
        (tmp_path / "infrastructure").mkdir()

        result = verify_source_structure(tmp_path, "myproj")
        assert result is False

    def test_with_optional_dirs(self, tmp_path):
        # Create required
        (tmp_path / "infrastructure").mkdir()
        (tmp_path / "projects" / "myproj" / "src").mkdir(parents=True)
        (tmp_path / "projects" / "myproj" / "tests").mkdir(parents=True)
        # Create optional
        (tmp_path / "scripts").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "projects" / "myproj" / "manuscript").mkdir(parents=True)

        result = verify_source_structure(tmp_path, "myproj")
        assert result is True


class TestValidateDirectoryStructure:
    def test_all_missing(self, tmp_path):
        missing = validate_directory_structure(tmp_path, "proj")
        assert len(missing) > 0

    def test_all_present(self, tmp_path):
        # Create all required dirs
        dirs = _project_output_dirs("proj")
        for d in dirs:
            (tmp_path / d).mkdir(parents=True, exist_ok=True)

        missing = validate_directory_structure(tmp_path, "proj")
        assert missing == []

    def test_partial_missing(self, tmp_path):
        # Create some but not all
        dirs = _project_output_dirs("proj")
        for d in dirs[:5]:
            (tmp_path / d).mkdir(parents=True, exist_ok=True)

        missing = validate_directory_structure(tmp_path, "proj")
        assert len(missing) > 0
        assert len(missing) == len(dirs) - 5
