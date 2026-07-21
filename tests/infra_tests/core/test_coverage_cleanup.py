"""Tests for infrastructure/core/coverage_cleanup.py.

Tests coverage file cleanup utilities using real files.
Follows No Mocks Policy - all tests use real data and real execution.
"""

from infrastructure.core.files.coverage_cleanup import clean_coverage_files


class TestCleanCoverageFiles:
    """Test clean_coverage_files function."""

    def test_returns_true_on_empty_dir(self, tmp_path):
        """Test that clean_coverage_files returns True when no files to clean."""
        result = clean_coverage_files(tmp_path)
        assert result is True

    def test_removes_coverage_file(self, tmp_path):
        """Test that .coverage file is removed."""
        coverage_file = tmp_path / ".coverage"
        coverage_file.write_text("coverage data")

        result = clean_coverage_files(tmp_path)

        assert result is True
        assert not coverage_file.exists()

    def test_removes_coverage_json_file(self, tmp_path):
        """Test that coverage_*.json files are removed."""
        json_file = tmp_path / "coverage_results.json"
        json_file.write_text("{}")

        result = clean_coverage_files(tmp_path)

        assert result is True
        assert not json_file.exists()

    def test_custom_patterns(self, tmp_path):
        """Test that custom patterns are respected."""
        keep_file = tmp_path / ".coverage"
        keep_file.write_text("coverage data")
        remove_file = tmp_path / "remove_me.txt"
        remove_file.write_text("to remove")

        result = clean_coverage_files(tmp_path, patterns=["remove_me.txt"])

        assert result is True
        assert keep_file.exists()  # Not in custom patterns
        assert not remove_file.exists()

    def test_returns_bool(self, tmp_path):
        """Test that the function always returns a boolean."""
        result = clean_coverage_files(tmp_path)
        assert isinstance(result, bool)

    def test_scope_dir_leaves_sibling_projects_untouched(self, tmp_path):
        """A scope_dir restricts cleanup to one project, sparing sibling projects.

        Regression test: clean_coverage_files(repo_root) used to glob
        recursively from repo_root regardless of which project was under
        test, deleting OTHER concurrently-running projects' live coverage
        databases. scope_dir must confine the search to the given directory.
        """
        project_a = tmp_path / "projects" / "project_a"
        project_b = tmp_path / "projects" / "project_b"
        project_a.mkdir(parents=True)
        project_b.mkdir(parents=True)
        own_coverage = project_a / ".coverage.project"
        own_coverage.write_text("own data")
        sibling_coverage = project_b / ".coverage.project"
        sibling_coverage.write_text("sibling data")

        result = clean_coverage_files(tmp_path, scope_dir=project_a)

        assert result is True
        assert not own_coverage.exists()
        assert sibling_coverage.exists()

    def test_scope_dir_outside_repo_root_does_not_raise(self, tmp_path):
        """A scope_dir resolved outside repo_root (e.g. a private-sidecar
        symlink target on a separate filesystem path) must not crash the
        relative-path label computation.

        Regression test: private lifecycle projects (``projects/active/*``,
        ``projects/working/*``, etc.) are symlinks that can resolve to a
        directory with no ancestor relationship to ``repo_root`` at all —
        ``Path.relative_to`` raises ``ValueError`` in that case, which used
        to propagate out of ``clean_coverage_files`` and fail Stage 2
        (Environment Setup) for any project reached this way.
        """
        repo_root = tmp_path / "repo"
        external_project = tmp_path / "elsewhere" / "external_project"
        repo_root.mkdir()
        external_project.mkdir(parents=True)
        stray_coverage = external_project / ".coverage"
        stray_coverage.write_text("stray data")

        result = clean_coverage_files(repo_root, scope_dir=external_project)

        assert result is True
        assert not stray_coverage.exists()

    def test_preserves_active_absolute_coverage_family(self, tmp_path, monkeypatch):
        """Outer pytest-cov data and xdist shards survive nested cleanup."""
        active = tmp_path / ".coverage.infra"
        shard = tmp_path / ".coverage.infra.worker.123"
        stale = tmp_path / ".coverage.project"
        for path in (active, shard, stale):
            path.write_text("coverage data", encoding="utf-8")
        monkeypatch.setenv("COVERAGE_FILE", str(active))

        assert clean_coverage_files(tmp_path) is True
        assert active.exists()
        assert shard.exists()
        assert not stale.exists()

    def test_preserves_active_relative_coverage_family(self, tmp_path, monkeypatch):
        """Relative COVERAGE_FILE follows coverage.py's current-directory rule."""
        active = tmp_path / ".coverage.infra"
        active.write_text("coverage data", encoding="utf-8")
        stale = tmp_path / ".coverage.project"
        stale.write_text("stale data", encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("COVERAGE_FILE", ".coverage.infra")

        assert clean_coverage_files(tmp_path) is True
        assert active.exists()
        assert not stale.exists()
