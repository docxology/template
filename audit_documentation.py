#!/usr/bin/env python3
"""Audit script to check docstrings and type hints across the codebase."""

import ast
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass, field


@dataclass
class AuditResult:
    """Store audit results for a module."""
    module_path: str
    has_module_docstring: bool = False
    missing_function_docstrings: List[str] = field(default_factory=list)
    missing_class_docstrings: List[str] = field(default_factory=list)
    missing_type_hints: List[Tuple[str, str]] = field(default_factory=list)
    public_functions: Set[str] = field(default_factory=set)
    public_classes: Set[str] = field(default_factory=set)


class DocstringAuditor(ast.NodeVisitor):
    """AST visitor to audit docstrings and type hints."""

    def __init__(self, module_path: str):
        self.module_path = module_path
        self.result = AuditResult(module_path=module_path)
        self.module_docstring_checked = False

    def visit_Module(self, node: ast.Module) -> None:
        """Check module-level docstring."""
        docstring = ast.get_docstring(node)
        self.result.has_module_docstring = docstring is not None
        self.module_docstring_checked = True
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check function docstrings and type hints."""
        # Only check public functions (not starting with _)
        if not node.name.startswith('_'):
            self.result.public_functions.add(node.name)

            # Check docstring
            docstring = ast.get_docstring(node)
            if docstring is None:
                self.result.missing_function_docstrings.append(node.name)

            # Check return type hint
            if node.returns is None and node.name != '__init__':
                self.result.missing_type_hints.append((node.name, 'missing return type'))

            # Check argument type hints (skip self, cls, and *args, **kwargs)
            for arg in node.args.args:
                if arg.arg in ('self', 'cls'):
                    continue
                if arg.annotation is None:
                    self.result.missing_type_hints.append(
                        (node.name, f'missing type hint for argument: {arg.arg}')
                    )

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Check async function docstrings and type hints."""
        if not node.name.startswith('_'):
            self.result.public_functions.add(node.name)

            docstring = ast.get_docstring(node)
            if docstring is None:
                self.result.missing_function_docstrings.append(node.name)

            if node.returns is None:
                self.result.missing_type_hints.append((node.name, 'missing return type'))

            for arg in node.args.args:
                if arg.arg in ('self', 'cls'):
                    continue
                if arg.annotation is None:
                    self.result.missing_type_hints.append(
                        (node.name, f'missing type hint for argument: {arg.arg}')
                    )

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Check class docstrings."""
        if not node.name.startswith('_'):
            self.result.public_classes.add(node.name)

            docstring = ast.get_docstring(node)
            if docstring is None:
                self.result.missing_class_docstrings.append(node.name)

        self.generic_visit(node)


def audit_file(file_path: Path) -> AuditResult:
    """Audit a single Python file for docstrings and type hints.

    Args:
        file_path: Path to the Python file to audit

    Returns:
        AuditResult containing the audit findings
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        tree = ast.parse(source)
        auditor = DocstringAuditor(str(file_path))
        auditor.visit(tree)

        return auditor.result
    except Exception as e:
        print(f"Error auditing {file_path}: {e}", file=sys.stderr)
        return AuditResult(module_path=str(file_path))


def audit_directory(base_dir: Path, pattern: str = "**/*.py") -> List[AuditResult]:
    """Audit all Python files in a directory.

    Args:
        base_dir: Base directory to search
        pattern: Glob pattern for finding files

    Returns:
        List of audit results
    """
    results = []
    for file_path in sorted(base_dir.glob(pattern)):
        # Skip __pycache__ and test files
        if '__pycache__' in str(file_path):
            continue

        result = audit_file(file_path)
        results.append(result)

    return results


def generate_report(results: List[AuditResult]) -> None:
    """Generate the audit report."""
    print("## Code Quality Audit\n")

    # Separate results by completeness
    missing_module_docs = []
    missing_func_docs = []
    missing_class_docs = []
    missing_hints = []
    well_documented = []

    for result in results:
        if not result.has_module_docstring:
            missing_module_docs.append(result.module_path)

        for func_name in result.missing_function_docstrings:
            missing_func_docs.append(f"{result.module_path}:{func_name}")

        for class_name in result.missing_class_docstrings:
            missing_class_docs.append(f"{result.module_path}:{class_name}")

        for func_name, hint_type in result.missing_type_hints:
            missing_hints.append(f"{result.module_path}:{func_name} - {hint_type}")

        # A module is well-documented if it has all the basics
        if (result.has_module_docstring and
            not result.missing_function_docstrings and
            not result.missing_class_docstrings):
            well_documented.append(result.module_path)

    # Print sections
    if missing_module_docs:
        print("### Missing Module Docstrings")
        for path in missing_module_docs:
            print(f"- {path}")
        print()

    if missing_func_docs:
        print("### Missing Function Docstrings")
        for item in missing_func_docs:
            print(f"- {item}")
        print()

    if missing_class_docs:
        print("### Missing Class Docstrings")
        for item in missing_class_docs:
            print(f"- {item}")
        print()

    if missing_hints:
        print("### Missing Type Hints")
        for item in missing_hints:
            print(f"- {item}")
        print()

    if well_documented:
        print("### Well-Documented Modules")
        for path in well_documented:
            print(f"- {path} ✓")
        print()

    # Summary statistics
    total_modules = len(results)
    total_missing_module_docs = len(missing_module_docs)
    total_missing_func_docs = len(missing_func_docs)
    total_missing_class_docs = len(missing_class_docs)
    total_missing_hints = len(missing_hints)
    total_well_documented = len(well_documented)

    print("### Summary")
    print(f"- Modules checked: {total_modules}")
    print(f"- Missing module docstrings: {total_missing_module_docs}")
    print(f"- Missing function docstrings: {total_missing_func_docs}")
    print(f"- Missing class docstrings: {total_missing_class_docs}")
    print(f"- Missing type hints: {total_missing_hints}")
    print(f"- Well-documented modules: {total_well_documented}")
    print(f"- Documentation coverage: {(total_well_documented / total_modules * 100):.1f}%")


def main():
    """Main entry point."""
    repo_root = Path(__file__).parent

    print("Auditing infrastructure/...")
    infra_results = audit_directory(repo_root / "infrastructure")

    print("Auditing projects/code_project/src/...")
    project_results = audit_directory(repo_root / "projects" / "code_project" / "src")

    all_results = infra_results + project_results

    print("\n" + "="*80 + "\n")
    generate_report(all_results)


if __name__ == "__main__":
    main()
