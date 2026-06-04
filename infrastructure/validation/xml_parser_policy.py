"""XML parser policy enforcement (DEP-DEFUSEDXML-1).

Single, current policy for this repository: **all XML parsing of external or
untrusted input must go through ``defusedxml``** (e.g. ``defusedxml.ElementTree``).
The standard-library ``xml.*`` parsers and ``lxml`` are vulnerable to entity
expansion / external-entity attacks (billion laughs, XXE) and must not be used
to parse input.

What is *allowed*:

* ``import defusedxml.ElementTree as ET`` and any other ``defusedxml`` import —
  this is the sanctioned hardened parser.
* Type-only / construction-only imports from ``xml.etree.ElementTree`` such as
  ``from xml.etree.ElementTree import Element`` (used purely as a type-hint
  target or to *build* trees, never to parse input).

What is *forbidden* (these are the same surfaces Bandit's ``B313``–``B320`` /
``B405``–``B410`` flag — this guard makes the policy explicit and self-checking
inside the test suite, independent of the Bandit severity gate):

* Importing a stdlib XML *parser* module: ``import xml.etree.ElementTree``,
  ``xml.dom.minidom``, ``xml.sax``, ``xml.parsers.expat``.
* Importing a parsing entry point by name from ``xml.etree.ElementTree``
  (``parse``, ``fromstring``, ``iterparse``, ``XML``, ``XMLParser``, …).
* Any ``lxml`` import (``lxml.etree`` is unsafe by default).

The check is import-level and AST-based: a module that never imports a stdlib
parser cannot parse untrusted input with one, so enforcing at the import
boundary is both sufficient and free of comment/docstring false positives.

See ``docs/rules/security.md`` (section "XML Parsing") for the prose policy.
"""

from __future__ import annotations

import ast
from pathlib import Path

# Parsing entry points exported by ``xml.etree.ElementTree``. Importing any of
# these by name means the module parses XML; everything else from that module
# (Element, SubElement, tostring, ElementTree, …) only builds/serializes trees.
_ETREE_PARSE_NAMES: frozenset[str] = frozenset(
    {
        "parse",
        "fromstring",
        "fromstringlist",
        "iterparse",
        "XML",
        "XMLID",
        "XMLParser",
        "XMLPullParser",
    }
)

# Dotted module names whose plain ``import x.y.z`` grants access to an unsafe
# stdlib/lxml parser. ``xml.etree.ElementTree`` is included because the bare
# module import exposes ``.parse`` / ``.fromstring``.
_FORBIDDEN_IMPORT_MODULES: tuple[str, ...] = (
    "xml.etree.ElementTree",
    "xml.etree.cElementTree",
    "xml.dom",
    "xml.sax",
    "xml.parsers.expat",
    "lxml",
)

# ``from <module> import ...`` roots that are forbidden wholesale (no member of
# these provides a safe-by-default parser).
_FORBIDDEN_FROM_ROOTS: tuple[str, ...] = (
    "xml.dom",
    "xml.sax",
    "xml.parsers.expat",
    "lxml",
)


def _module_matches(name: str, candidates: tuple[str, ...]) -> bool:
    """True if ``name`` equals or is a submodule of any candidate."""
    return any(name == c or name.startswith(c + ".") for c in candidates)


def _scan_source(source: str) -> list[tuple[int, str]]:
    """Return ``(lineno, reason)`` for every forbidden XML import in ``source``.

    Raises ``SyntaxError`` if the source does not parse; callers decide how to
    surface that (the live-tree scan treats unparseable files as skipped).
    """
    tree = ast.parse(source)
    findings: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _module_matches(alias.name, _FORBIDDEN_IMPORT_MODULES):
                    findings.append(
                        (
                            node.lineno,
                            f"unsafe stdlib XML parser import `import {alias.name}` — use defusedxml instead",
                        )
                    )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module in ("xml.etree.ElementTree", "xml.etree.cElementTree"):
                bad = [a.name for a in node.names if a.name in _ETREE_PARSE_NAMES]
                if bad:
                    findings.append(
                        (
                            node.lineno,
                            f"unsafe XML parse import `from {module} import "
                            f"{', '.join(bad)}` — use defusedxml instead "
                            f"(type/construction names like Element are allowed)",
                        )
                    )
            elif _module_matches(module, _FORBIDDEN_FROM_ROOTS):
                names = ", ".join(a.name for a in node.names)
                findings.append(
                    (
                        node.lineno,
                        f"unsafe stdlib/lxml XML import `from {module} import {names}` — use defusedxml instead",
                    )
                )

    return findings


def validate_xml_parser_policy(scan_dir: Path, repo_root: Path) -> list[str]:
    """Scan ``scan_dir`` for XML-parser-policy violations.

    Args:
        scan_dir: Directory tree of ``.py`` files to scan (recursively).
        repo_root: Repository root, used to render violations as repo-relative
            ``path:line: reason`` strings.

    Returns:
        Sorted list of formatted violation strings. Empty list means the tree
        complies with the defusedxml-only policy.
    """
    violations: list[str] = []

    if not scan_dir.exists():
        return violations

    for py_file in sorted(scan_dir.rglob("*.py")):
        try:
            source = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # Unreadable file: out of scope for a static import policy check.
            continue
        try:
            findings = _scan_source(source)
        except SyntaxError:
            # A file that does not even parse cannot import anything at runtime;
            # syntax errors are the linter's job, not this policy guard's.
            continue
        try:
            rel = py_file.relative_to(repo_root)
        except ValueError:
            rel = py_file
        for lineno, reason in findings:
            violations.append(f"{rel}:{lineno}: {reason}")

    return violations
