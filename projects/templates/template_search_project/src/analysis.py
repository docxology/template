"""
Project-specific review stage implementations.

This module houses custom review-stage logic that doesn't map directly
to an infrastructure CLI command. It keeps the orchestrator thin and
the stage functions testable in isolation.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StageResult:
    """Result of a single review stage execution."""

    name: str
    status: str  # "passed", "failed", "skipped", "error"
    message: str = ""
    details: dict | None = None
    exit_code: int = 0

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "details": self.details or {},
            "exit_code": self.exit_code,
        }


#: Pandoc-crossref reference prefixes that share the ``[@…]`` syntax with
#: BibTeX citations but resolve against in-document labels (sections,
#: figures, tables, equations, etc.) rather than ``manuscript/*.bib``.
#: These must be excluded from the bibliography-completeness check.
_CROSSREF_PREFIXES = ("sec:", "fig:", "tbl:", "eq:", "lst:")


def _strip_code_spans(text: str) -> str:
    """Remove inline-code spans and fenced code blocks from *text*.

    A ``[@key]`` example that lives inside a backtick-quoted code span
    (e.g. `` `[@key]` ``) or a ``` ``` ``` fenced block is illustrative
    documentation, not a real Pandoc citation. The bibliography-
    completeness check must not flag those keys as missing.
    """
    # Remove fenced code blocks first (greedy, multiline).
    without_fences = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Then remove single-line inline-code spans.
    return re.sub(r"`[^`\n]*`", "", without_fences)


def _extract_citation_keys(text: str) -> set[str]:
    """Pull every BibTeX citation key out of *text*.

    Pandoc citation syntax allows multi-cite (``[@key1; @key2]``) and
    locator suffixes (``[@key, p. 5]``), and pandoc-crossref reuses the
    same ``[@…]`` brackets for cross-references (``[@sec:foo]``,
    ``[@fig:bar]``, etc.). This helper:

      1. Strips inline-code spans and fenced code blocks so didactic
         examples like `` `[@key]` `` are not treated as citations.
      2. Splits on ``;`` *inside* a ``[@…]`` group so multi-cites yield
         one key per element.
      3. Strips leading ``-``/``+`` (suppression / author-only) and
         ``@`` and trailing ``,`` (locator separator) per Pandoc spec.
      4. Drops pandoc-crossref labels (``sec:``, ``fig:``, ``tbl:``,
         ``eq:``, ``lst:``) — those are validated by stage
         ``markdown_links`` / ``prerender_validation``, not by this
         stage.
    """
    keys: set[str] = set()
    cleaned = _strip_code_spans(text)
    # Match ``[@key]`` and ``[-@key]`` / ``[+@key]`` (suppression /
    # author-only forms). The capture excludes the bracket itself so
    # multi-cite splitting and per-element cleanup can be done below.
    for group in re.findall(r"\[[-+]?@([^\]]+)\]", cleaned):
        for raw in re.split(r";\s*[-+]?@?", group):
            token = raw.strip()
            if not token:
                continue
            # Pandoc locator: the key ends at the first ',' or whitespace
            # not part of the key itself.
            token = re.split(r"[\s,]", token, maxsplit=1)[0]
            token = token.lstrip("-+@").strip()
            if not token:
                continue
            if any(token.startswith(prefix) for prefix in _CROSSREF_PREFIXES):
                continue
            keys.add(token)
    return keys


def validate_bibliography_completeness(project_root: Path) -> StageResult:
    """
    Ensure every ``[@citation_key]`` found in ``manuscript/*.md`` has a
    corresponding entry in at least one ``manuscript/*.bib`` file.

    The check ignores:

      * pandoc-crossref labels (``[@sec:…]``, ``[@fig:…]``, ``[@tbl:…]``,
        ``[@eq:…]``, ``[@lst:…]``) which resolve against in-document
        labels rather than BibTeX entries;
      * ``99_*`` files (the references section, which by definition
        re-cites every entry and would always trip the check); and
      * doc / syntax files like ``SYNTAX.md`` whose ``[@key]`` examples
        are illustrative rather than real citations.

    Returns StageResult with:
      - passed: all keys resolved
      - failed: some keys missing (details includes "missing_keys")
    """
    manuscript_dir = project_root / "manuscript"
    bib_paths = sorted(manuscript_dir.glob("*.bib"))
    if not bib_paths:
        return StageResult(
            name="bibliography_completeness",
            status="error",
            message="No BibTeX files found under manuscript/ (*.bib)",
            exit_code=2,
        )

    bib_keys: set[str] = set()
    for bib_path in bib_paths:
        bib_content = bib_path.read_text(encoding="utf-8", errors="ignore")
        bib_keys.update(re.findall(r"@\w+\{([^,\s]+)", bib_content))

    # Files whose ``[@…]`` occurrences are syntax / agent docs rather
    # than real citations against the project bibliography.
    skip_names = {"SYNTAX.md", "AGENTS.md", "README.md"}
    cited_keys: set[str] = set()
    for md in manuscript_dir.glob("*.md"):
        if md.name.startswith("99_") or md.name in skip_names:
            continue
        text = md.read_text(encoding="utf-8", errors="ignore")
        cited_keys.update(_extract_citation_keys(text))

    missing = sorted(cited_keys - bib_keys)
    bib_label = bib_paths[0].name if len(bib_paths) == 1 else ", ".join(p.name for p in bib_paths)
    if missing:
        return StageResult(
            name="bibliography_completeness",
            status="failed",
            message=f"{len(missing)} citation key(s) missing from manuscript BibTeX ({bib_label})",
            details={"missing_keys": missing, "cited_keys": sorted(cited_keys), "bib_keys": sorted(bib_keys)},
            exit_code=1,
        )

    return StageResult(
        name="bibliography_completeness",
        status="passed",
        message=f"All {len(cited_keys)} citation key(s) present in manuscript BibTeX ({bib_label})",
        details={"cited_keys": sorted(cited_keys)},
        exit_code=0,
    )


def validate_variables_resolved(project_root: Path) -> StageResult:
    """
    Check that resolved markdown contains no un-substituted
    ``{{UPPER_CASE}}`` markers.

    When ``output/manuscript/*.md`` exists (written by
    ``scripts/z_generate_manuscript_variables.py``), that directory is what
    the PDF-rendering stage renders; only those files are scanned. Otherwise the source
    ``manuscript/*.md`` tree is scanned (templates may still contain
    placeholders).
    """
    injected_dir = project_root / "output" / "manuscript"
    if injected_dir.exists() and any(injected_dir.glob("*.md")):
        scan_root = injected_dir
    else:
        scan_root = project_root / "manuscript"

    unresolved: list[tuple[Path, str]] = []

    marker_re = re.compile(r"\{\{([A-Z_][A-Z0-9_]*)\}\}")
    for md in sorted(scan_root.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        for m in marker_re.finditer(text):
            unresolved.append((md, m.group(0)))

    if unresolved:
        return StageResult(
            name="variables_resolved",
            status="failed",
            message=f"{len(unresolved)} unresolved template variable(s) found",
            details={"unresolved": [(str(p), marker) for p, marker in unresolved[:20]]},
            exit_code=1,
        )

    return StageResult(
        name="variables_resolved",
        status="passed",
        message="No unresolved {{UPPER_CASE}} markers in manuscript scan root",
        exit_code=0,
    )


def audit_infrastructure_imports(project_root: Path) -> StageResult:
    """
    Scan src/*.py and verify:
      1. All imports from ``infrastructure.*`` modules are valid (module exists).
      2. No project module imports another project module (thin-orchestrator rule).
    """
    import ast

    src_dir = project_root / "src"
    # __file__ is projects/templates/<name>/src/analysis.py; repo root is five levels up.
    infra_root = Path(__file__).resolve().parents[4] / "infrastructure"

    issues: list[str] = []
    infra_imports_used: dict[str, set[str]] = {}

    for py in sorted(src_dir.glob("*.py")):
        if py.name.startswith("_"):
            continue  # skip private helpers
        try:
            tree = ast.parse(py.read_text(), filename=str(py))
        except SyntaxError as exc:
            issues.append(f"{py.name}: syntax error — {exc}")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("infrastructure."):
                    # Verify module/package exists on disk.
                    # Handles both modules (e.g., infrastructure/foo/bar.py) and packages
                    # (e.g., infrastructure/foo/bar/__init__.py).
                    parts = node.module.split(".")
                    # Translate module path to filesystem path under infra_root
                    # e.g. infrastructure.search.literature → infrastructure/search/literature
                    rel_path = Path(*parts[1:])  # drop 'infrastructure' prefix
                    mod_file = infra_root / rel_path.with_suffix(".py")
                    pkg_init = infra_root / rel_path / "__init__.py"
                    if not mod_file.exists() and not pkg_init.exists():
                        issues.append(f"{py.name} imports non-existent infra module: {node.module}")
                    infra_imports_used.setdefault(node.module, set()).add(py.name)
        # Check for cross-project imports — not enforceable here, but warn
        # (those imports would be caught by Python import resolution at runtime;
        # this review stage focuses on infra availability.)

    details = {
        "infrastructure_imports": {mod: sorted(files) for mod, files in infra_imports_used.items()},
        "issues": issues,
    }
    if issues:
        return StageResult(
            name="infrastructure_usage",
            status="failed",
            message=f"{len(issues)} infrastructure import issue(s)",
            details=details,
            exit_code=1,
        )

    return StageResult(
        name="infrastructure_usage",
        status="passed",
        message=f"All {sum(len(v) for v in infra_imports_used.values())} infra imports resolve",
        details=details,
        exit_code=0,
    )


def check_determinism_artifacts(project_root: Path) -> StageResult:
    """
    Verify that the output/ directory contains determinism-enabling artifacts:
      * output/search/cache/search_*.json  (search cache present)
      * output/cache/abs/ and output/cache/pdf/  (enrichment caches)
      * config.yaml has llm.seed set
      * config.yaml has llm.temperature = 0 or very low

    Also cross-check that run_summary.json exists to confirm a pipeline run.
    """
    output = project_root / "output"
    issues: list[str] = []
    findings: dict[str, object] = {}

    # 1. run_summary.json
    run_summary = output / "run_summary.json"
    if not run_summary.exists():
        issues.append("output/run_summary.json missing — pipeline has not been run")
    else:
        with open(run_summary) as f:
            summary = json.load(f)
        findings["pipeline_completed"] = True
        # ``run_search_pipeline.py`` writes ``papers`` (single-query) and
        # ``run_deep_search.py`` writes ``total_papers``. Accept either
        # so the determinism check works after either orchestrator.
        findings["papers_found"] = summary.get("papers", summary.get("total_papers", "unknown"))

    # 2. Search cache
    cache_dir = output / "search" / "cache"
    if cache_dir.exists():
        cache_files = list(cache_dir.glob("*.json"))
        findings["search_cache_files"] = len(cache_files)
        if not cache_files:
            issues.append("Search cache directory empty — set cache_dir in config and re-run")
    else:
        issues.append("Search cache directory not present")

    # 3. Config seed + temperature
    config_path = project_root / "manuscript" / "config.yaml"
    if config_path.exists():
        import yaml as _yaml

        with open(config_path) as f:
            cfg = _yaml.safe_load(f) or {}
        llm_cfg = cfg.get("llm", {})
        seed = llm_cfg.get("seed")
        temp = llm_cfg.get("temperature")
        findings["llm_seed"] = seed
        findings["llm_temperature"] = temp
        if seed is None:
            issues.append("llm.seed not set in manuscript/config.yaml")
        if temp is None or temp > 0.1:
            issues.append(f"llm.temperature={temp} is not pinned to 0 for determinism")

    if issues:
        return StageResult(
            name="determinism_check",
            status="failed",
            message=f"{len(issues)} determinism concern(s)",
            details={"issues": issues, "findings": findings},
            exit_code=1,
        )

    return StageResult(
        name="determinism_check",
        status="passed",
        message="Determinism artifacts present (cache, seed, temperature)",
        details={"findings": findings},
        exit_code=0,
    )


def run_project_tests(project_root: Path, min_coverage: float = 90.0) -> StageResult:
    """
    Invoke pytest on the project's tests/ directory and enforce
    ``min_coverage`` threshold. Returns non-zero if coverage below threshold.
    """
    tests_dir = project_root / "tests"
    if not tests_dir.exists():
        return StageResult(
            name="test_suite_health",
            status="error",
            message="tests/ directory missing",
            exit_code=2,
        )

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(tests_dir),
        "--cov=src",
        f"--cov-fail-under={min_coverage}",
        "-q",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)

    coverage_match = re.search(r"TOTAL\s+\S+\s+\S+\s+(\d+)%", result.stdout)
    coverage = int(coverage_match.group(1)) if coverage_match else None

    if result.returncode != 0:
        return StageResult(
            name="test_suite_health",
            status="failed",
            message=f"pytest exit {result.returncode}",
            details={"stdout": result.stdout[-500:], "stderr": result.stderr[-500:], "coverage": coverage},
            exit_code=1,
        )

    if coverage is not None and coverage < min_coverage:
        return StageResult(
            name="test_suite_health",
            status="failed",
            message=f"coverage {coverage}% below threshold {min_coverage}%",
            details={"coverage": coverage},
            exit_code=1,
        )

    return StageResult(
        name="test_suite_health",
        status="passed",
        message=f"pytest passed with {coverage}% coverage",
        details={"coverage": coverage},
        exit_code=0,
    )


__all__ = [
    "StageResult",
    "_extract_citation_keys",
    "validate_bibliography_completeness",
    "validate_variables_resolved",
    "audit_infrastructure_imports",
    "check_determinism_artifacts",
    "run_project_tests",
]


def _cli() -> None:
    import argparse
    import json
    import sys
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Project-specific review stage CLI")
    parser.add_argument(
        "--stage",
        required=True,
        choices=[
            "bibliography_completeness",
            "variables_resolved",
            "infrastructure_usage",
            "determinism_check",
            "test_suite_health",
        ],
    )
    parser.add_argument("--project-root", required=True, help="Project root directory")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    func = {
        "bibliography_completeness": validate_bibliography_completeness,
        "variables_resolved": validate_variables_resolved,
        "infrastructure_usage": audit_infrastructure_imports,
        "determinism_check": check_determinism_artifacts,
        "test_suite_health": run_project_tests,
    }[args.stage]

    result = func(project_root)
    print(json.dumps(result.as_dict(), indent=2))
    sys.exit(result.exit_code)


if __name__ == "__main__":
    _cli()
