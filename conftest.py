"""Root-level pytest configuration - MUST run before any test imports.

This configuration enables:
1. Infrastructure module imports (infrastructure/)
2. Project source imports (projects/{name}/src/)
3. Project test imports (projects/{name}/tests/)
4. Headless matplotlib rendering

Path configuration is CRITICAL and must happen before any test imports.

Pytest and coverage settings are defined in pyproject.toml:
- [tool.pytest.ini_options] - Test discovery and execution
- [tool.coverage.run] - Coverage collection settings
- [tool.coverage.report] - Coverage report configuration
"""
import os
import sys

# CRITICAL: Add paths BEFORE any imports can occur
ROOT = os.path.dirname(os.path.abspath(__file__))

# Add root to sys.path so infrastructure/ and project/ are importable as packages
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Add projects/*/src for project-specific imports (active projects only)
# Note: Only active projects in projects/ directory are added here.
# Archived projects in projects_archive/ are not included.
# Discovery is dynamic - all directories in projects/ with a src/ subdirectory are included.
# Supports both top-level projects (projects/code_project/src/) and nested/program-grouped
# projects (projects/cognitive_integrity/cogsec_multiagent_1_theory/src/).
projects_dir = os.path.join(ROOT, "projects")
if os.path.isdir(projects_dir):
    for project_name in os.listdir(projects_dir):
        if project_name.startswith((".", "_")):
            continue
        project_path = os.path.join(projects_dir, project_name)
        if not os.path.isdir(project_path):
            continue
        # Check for direct src/ directory (top-level project)
        project_src = os.path.join(project_path, "src")
        if os.path.isdir(project_src) and project_src not in sys.path:
            sys.path.insert(1, project_src)
        else:
            # Check for nested projects (program-grouped: projects/<program>/<subproject>/src/)
            for sub_name in os.listdir(project_path):
                if sub_name.startswith((".", "_")):
                    continue
                sub_src = os.path.join(project_path, sub_name, "src")
                if os.path.isdir(sub_src) and sub_src not in sys.path:
                    sys.path.insert(1, sub_src)

# Force headless backend for all matplotlib usage
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# Set project root for scripts
os.environ.setdefault("PROJECT_ROOT", ROOT)
