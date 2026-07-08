"""Integration test: analyze real codebases and assert architectural quality.

Uses a lightweight heuristic scoring system on sparse-checkout package subtrees
(``requests/src/requests``, ``fastapi/fastapi``). Both packages must meet
``MIN_ARCHITECTURE_SCORE`` (33) — lower than a full-repo scan because fixtures
omit repo-level packaging and test trees.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.resolve()
FIXTURES_DIR = ROOT / "tests" / "fixtures" / "real_codebases"
REQUESTS_DIR = FIXTURES_DIR / "requests"
FASTAPI_DIR = FIXTURES_DIR / "fastapi"

# Threshold per task (sparse-checkout fixtures omit repo-level packaging/tests)
MIN_ARCHITECTURE_SCORE = 33

REQUESTS_PACKAGE = FIXTURES_DIR / "requests" / "src" / "requests"
FASTAPI_PACKAGE = FIXTURES_DIR / "fastapi" / "fastapi"

# Skip the entire module if the fixture trees aren't checked out.
# Run ``scripts/fixtures/download_real_codebases.py`` to populate them.
pytestmark = pytest.mark.skipif(
    not REQUESTS_DIR.exists() or not FASTAPI_DIR.exists(),
    reason="real codebase fixtures missing — run scripts/fixtures/download_real_codebases.py",
)


def has_file(path: Path, name: str) -> bool:
    """Check if a file with given name exists somewhere under path."""
    return any(p.name == name for p in path.rglob(name))


def compute_architecture_score(codebase: Path) -> int:
    """Compute a 0-100 architecture quality score.

    Heuristic components (total 100):
      - Structure (25): packaging, layout, tests dir, docs
      - Documentation (20): README size, docstring coverage
      - Testing (20): test files present, ratio of test to source files
      - Modularity (20): file count range, max file size, import sanity
      - Type hints (10): presence of annotations
      - Dependencies (5): reasonable deps count
    """
    score = 0

    # 1. Structure (25)
    # Packaging: pyproject.toml or setup.py/setup.cfg presence
    if any(codebase.glob("pyproject.toml")) or any(codebase.glob("setup.py")) or any(codebase.glob("setup.cfg")):
        score += 7
    # Has a proper Python package (a directory with __init__.py not under tests)
    if any(p for p in codebase.rglob("__init__.py") if p.is_file() and "test" not in p.parts):
        score += 6
    # Tests directory exists (tests/ or <package>/tests)
    test_dirs = [d for d in codebase.rglob("tests") if d.is_dir()]
    if test_dirs:
        score += 6
    # Has README.md or similar top-level doc
    if has_file(codebase, "README.md") or has_file(codebase, "README.rst"):
        score += 6

    # Source files count (only under packages, not tests)
    src_py = [p for p in codebase.rglob("*.py") if "test" not in p.parts and not p.name.startswith("test_")]
    n_src = len(src_py)
    test_py = [p for p in codebase.rglob("*.py") if "test" in p.parts or p.name.startswith("test_")]
    n_tests = len(test_py)

    # 2. Documentation (20)
    # README length: if >200 chars add, >1000 add more.
    readme = None
    for r in ["README.md", "README.rst"]:
        readme = codebase / r
        if readme.exists():
            break
    readme_len = len(readme.read_text(errors="ignore")) if readme and readme.exists() else 0
    if readme_len > 1000:
        score += 10
    elif readme_len > 200:
        score += 5

    # Docstring coverage: sample up to 100 functions/classes from source files
    # Walk AST and count docstrings on public functions/classes
    def _count_docstrings() -> tuple[int, int]:
        total = 0
        documented = 0
        for pyfile in src_py[:50]:  # cap to avoid huge analysis
            try:
                tree = ast.parse(pyfile.read_text(errors="ignore"))
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    # Skip private/internal
                    if node.name.startswith("_"):
                        continue
                    total += 1
                    if ast.get_docstring(node):
                        documented += 1
            if total >= 200:  # cap
                break
        return documented, total

    doced, total_defs = _count_docstrings()
    if total_defs >= 10:
        ratio = doced / total_defs
        if ratio >= 0.7:
            score += 10
        elif ratio >= 0.4:
            score += 5
        else:
            score += 2

    # 3. Testing (20)
    # Existence of tests (already gave some points in structure)
    # Additional: test file count relative to source
    if n_tests > 0:
        ratio = n_tests / max(n_src, 1)
        if ratio >= 0.5:
            score += 10
        elif ratio >= 0.2:
            score += 5
        else:
            score += 2
    # Test density: tests > 3 different files
    if n_tests >= 3:
        score += 10
    else:
        score += n_tests * 3

    # 4. Modularity (20)
    # Reasonable source file count: 5-50 gives full, else scale
    if 5 <= n_src <= 50:
        score += 8
    elif 1 <= n_src < 5:
        score += 4
    else:
        score += 2
    # Maximum file size not too large
    max_lines = 0
    for pyfile in src_py:
        try:
            n_lines = len(pyfile.read_text(errors="ignore").splitlines())
            max_lines = max(max_lines, n_lines)
        except Exception:
            continue
    if max_lines <= 500:
        score += 6
    elif max_lines <= 1000:
        score += 3
    else:
        score += 1
    # Basic import sanity: no circular imports at module level (simple check)
    # We'll look for import statements and try to parse dependencies; check for cycles using graph.
    # That's heavy. Instead, check no wildcard imports: from x import *
    wildcard_imports = 0
    for pyfile in src_py[:30]:
        try:
            content = pyfile.read_text(errors="ignore")
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module is None or node.names[0].name == "*":
                        wildcard_imports += 1
        except Exception:
            continue
    if wildcard_imports == 0:
        score += 6
    else:
        score += max(0, 6 - wildcard_imports * 2)

    # 5. Type hints (10)
    # Count functions with annotations
    typed_funcs = 0
    total_funcs = 0
    for pyfile in src_py[:30]:
        try:
            content = pyfile.read_text(errors="ignore")
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith("_"):
                        continue
                    total_funcs += 1
                    # Check if has return annotation and all args have annotations
                    has_return = node.returns is not None
                    args_annotated = all(
                        arg.annotation is not None
                        for arg in node.args.args
                        if arg.arg != "self"  # skip self
                    )
                    if has_return and args_annotated:
                        typed_funcs += 1
        except Exception:
            continue
    if total_funcs > 0:
        ratio_typed = typed_funcs / total_funcs
        if ratio_typed >= 0.5:
            score += 10
        elif ratio_typed >= 0.25:
            score += 5
        else:
            score += 2

    # 6. Dependencies (5)
    # From pyproject.toml, count dependencies (excluding optional, dev)
    try:
        import tomllib  # Python 3.11+

        pyproj = codebase / "pyproject.toml"
        if pyproj.exists():
            with pyproj.open("rb") as f:
                data = tomllib.load(f)
            deps = data.get("project", {}).get("dependencies", [])
            n_deps = len(deps) if isinstance(deps, list) else 0
            if 5 <= n_deps <= 20:
                score += 5
            elif n_deps > 20:
                score += 3
            else:
                score += 2
    except Exception:
        # tomllib missing or parse error; ignore dependency score
        pass

    return min(100, score)


def _real_codebase_fixtures_ready() -> bool:
    try:
        return (
            REQUESTS_DIR.is_dir()
            and FASTAPI_DIR.is_dir()
            and any(REQUESTS_DIR.iterdir())
            and any(FASTAPI_DIR.iterdir())
        )
    except OSError:
        return False


@pytest.mark.integration
@pytest.mark.external_fixture
class TestRealCodebases:
    """Test suite for real-world codebase architecture analysis."""

    def test_requests_exists(self):
        """Verify requests fixture is present."""
        assert REQUESTS_DIR.exists(), (
            "Missing requests codebase fixture. Run scripts/fixtures/download_real_codebases.py first."
        )
        assert any(REQUESTS_DIR.iterdir()), f"Requests directory is empty: {REQUESTS_DIR}"

    def test_fastapi_exists(self):
        """Verify fastapi fixture is present."""
        assert FASTAPI_DIR.exists(), (
            "Missing fastapi codebase fixture. Run scripts/fixtures/download_real_codebases.py first."
        )
        assert any(FASTAPI_DIR.iterdir()), f"FastAPI directory is empty: {FASTAPI_DIR}"

    def test_requests_architecture_score(self):
        """Assert requests package source meets minimum architecture quality."""
        package = REQUESTS_PACKAGE if REQUESTS_PACKAGE.is_dir() else REQUESTS_DIR
        score = compute_architecture_score(package)
        print(f"\nRequests ArchitectureScore: {score}/100")
        assert score >= MIN_ARCHITECTURE_SCORE, f"Requests score {score} below threshold {MIN_ARCHITECTURE_SCORE}"

    def test_fastapi_architecture_score(self):
        """Assert fastapi package source meets minimum architecture quality."""
        package = FASTAPI_PACKAGE if FASTAPI_PACKAGE.is_dir() else FASTAPI_DIR
        score = compute_architecture_score(package)
        print(f"\nFastAPI ArchitectureScore: {score}/100")
        assert score >= MIN_ARCHITECTURE_SCORE, f"FastAPI score {score} below threshold {MIN_ARCHITECTURE_SCORE}"
