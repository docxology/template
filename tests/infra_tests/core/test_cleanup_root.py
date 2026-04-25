"""Tests for infrastructure.core.files.cleanup_root."""


from infrastructure.core.files.cleanup_root import clean_root_output_directory


class TestCleanRootOutputDirectory:
    def test_no_output_dir(self, tmp_path):
        result = clean_root_output_directory(tmp_path, ["proj1"])
        assert result is True

    def test_empty_output_dir(self, tmp_path):
        (tmp_path / "output").mkdir()
        result = clean_root_output_directory(tmp_path, ["proj1"])
        assert result is True

    def test_keeps_project_dirs(self, tmp_path):
        output = tmp_path / "output"
        proj_dir = output / "myproj"
        proj_dir.mkdir(parents=True)
        (proj_dir / "file.txt").write_text("data")

        result = clean_root_output_directory(tmp_path, ["myproj"])
        assert result is True
        assert proj_dir.exists()

    def test_keeps_program_dir_for_qualified_projects(self, tmp_path):
        output = tmp_path / "output"
        program_dir = output / "my_program"
        nested_output = program_dir / "nested_project"
        nested_output.mkdir(parents=True)
        (nested_output / "file.txt").write_text("data")

        result = clean_root_output_directory(tmp_path, ["my_program/nested_project"])

        assert result is True
        assert program_dir.exists()
        assert nested_output.exists()

    def test_removes_obsolete_leaf_dir_for_qualified_projects(self, tmp_path):
        output = tmp_path / "output"
        obsolete_leaf = output / "nested_project"
        obsolete_leaf.mkdir(parents=True)
        (obsolete_leaf / "old.pdf").write_text("old")
        current_nested = output / "my_program" / "nested_project"
        current_nested.mkdir(parents=True)

        result = clean_root_output_directory(tmp_path, ["my_program/nested_project"])

        assert result is True
        assert not obsolete_leaf.exists()
        assert current_nested.exists()

    def test_removes_root_level_dirs(self, tmp_path):
        output = tmp_path / "output"
        for d in ["data", "figures", "pdf", "web", "slides", "reports", "logs", "tex"]:
            (output / d).mkdir(parents=True)
            (output / d / "file.txt").write_text("data")

        result = clean_root_output_directory(tmp_path, ["proj1"])
        assert result is True
        for d in ["data", "figures", "pdf", "web", "slides", "reports", "logs", "tex"]:
            assert not (output / d).exists()

    def test_keeps_special_dirs(self, tmp_path):
        output = tmp_path / "output"
        for d in ["executive_summary", "multi_project_summary"]:
            (output / d).mkdir(parents=True)

        result = clean_root_output_directory(tmp_path, [])
        assert result is True
        assert (output / "executive_summary").exists()
        assert (output / "multi_project_summary").exists()

    def test_keeps_unknown_dirs(self, tmp_path):
        output = tmp_path / "output"
        unknown = output / "mysterious_dir"
        unknown.mkdir(parents=True)

        result = clean_root_output_directory(tmp_path, [])
        assert result is True
        assert unknown.exists()

    def test_keeps_root_level_files(self, tmp_path):
        output = tmp_path / "output"
        output.mkdir()
        (output / "readme.txt").write_text("info")

        result = clean_root_output_directory(tmp_path, [])
        assert result is True
        assert (output / "readme.txt").exists()

    def test_mixed_scenario(self, tmp_path):
        output = tmp_path / "output"
        # Project dir - keep
        (output / "proj1").mkdir(parents=True)
        # Root-level dir - remove
        (output / "pdf").mkdir(parents=True)
        (output / "pdf" / "old.pdf").write_text("old")
        # File - keep
        (output / "notes.txt").write_text("notes")

        result = clean_root_output_directory(tmp_path, ["proj1"])
        assert result is True
        assert (output / "proj1").exists()
        assert not (output / "pdf").exists()
        assert (output / "notes.txt").exists()
