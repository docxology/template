"""Tests for infrastructure.validation.repo._repo_documented_commands — coverage."""


from infrastructure.validation.repo._repo_documented_commands import (
    _candidate_script_paths,
    check_documented_commands,
)


class TestCandidateScriptPaths:
    def test_basic_path(self, tmp_path):
        paths = _candidate_script_paths(tmp_path, "scripts/run.py")
        assert tmp_path / "scripts" / "run.py" in paths

    def test_run_sh_special(self, tmp_path):
        paths = _candidate_script_paths(tmp_path, "run.sh")
        # run.sh gets checked at repo root too
        assert tmp_path / "run.sh" in paths

    def test_with_projects(self, tmp_path):
        (tmp_path / "projects" / "proj1" / "scripts").mkdir(parents=True)
        paths = _candidate_script_paths(tmp_path, "analysis.py")
        assert any("proj1" in str(p) for p in paths)

    def test_no_duplicates(self, tmp_path):
        paths = _candidate_script_paths(tmp_path, "test.py")
        assert len(paths) == len(set(paths))


class TestCheckDocumentedCommands:
    def test_no_readme(self, tmp_path):
        issues = check_documented_commands(tmp_path, set())
        assert issues == []

    def test_no_scripts_referenced(self, tmp_path):
        (tmp_path / "README.md").write_text("# Project\n\nNo scripts here.\n")
        issues = check_documented_commands(tmp_path, set())
        assert issues == []

    def test_existing_script(self, tmp_path):
        (tmp_path / "scripts").mkdir()
        (tmp_path / "scripts" / "run.py").write_text("print('hi')")
        (tmp_path / "README.md").write_text("Run `scripts/run.py` to start.\n")
        issues = check_documented_commands(tmp_path, set())
        assert issues == []

    def test_missing_script_sh(self, tmp_path):
        (tmp_path / "README.md").write_text("Run `scripts/missing.sh` to start.\n")
        issues = check_documented_commands(tmp_path, set())
        assert len(issues) == 1
        assert "missing.sh" in issues[0].message

    def test_src_module_skipped(self, tmp_path):
        (tmp_path / "README.md").write_text("Use `src/main.py` module.\n")
        issues = check_documented_commands(tmp_path, set())
        assert issues == []

    def test_known_module_skipped(self, tmp_path):
        (tmp_path / "README.md").write_text("Run `analysis.py` for results.\n")
        issues = check_documented_commands(tmp_path, {"analysis.py"})
        assert issues == []

    def test_inside_code_block_skipped(self, tmp_path):
        content = "```\n`scripts/fake.sh`\n```\n"
        (tmp_path / "README.md").write_text(content)
        issues = check_documented_commands(tmp_path, set())
        assert issues == []

    def test_docs_directory(self, tmp_path):
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "guide.md").write_text("Use `scripts/missing.sh` here.\n")
        issues = check_documented_commands(tmp_path, set())
        assert len(issues) >= 1

    def test_found_via_candidate(self, tmp_path):
        """Script not at literal path but found via candidate search."""
        (tmp_path / "scripts").mkdir()
        (tmp_path / "scripts" / "helper.sh").write_text("#!/bin/bash\n")
        (tmp_path / "README.md").write_text("Run `helper.sh` for help.\n")
        issues = check_documented_commands(tmp_path, set())
        assert issues == []
