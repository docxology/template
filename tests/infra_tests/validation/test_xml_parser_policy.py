"""Tests for infrastructure/validation/xml_parser_policy.py (DEP-DEFUSEDXML-1).

Enforces the single XML-parsing policy: all parsing goes through ``defusedxml``;
the stdlib ``xml.*`` parsers and ``lxml`` are forbidden, while type-only /
construction-only imports from ``xml.etree.ElementTree`` (e.g. ``Element``)
remain allowed.

Follows the No Mocks Policy — every test writes and scans real ``.py`` files on
disk (``tmp_path``) or scans the live ``infrastructure/`` tree.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.validation.xml_parser_policy import validate_xml_parser_policy

REPO_ROOT = Path(__file__).resolve().parents[3]


def _write(tmp_path: Path, name: str, body: str) -> Path:
    pkg = tmp_path / "pkg"
    pkg.mkdir(exist_ok=True)
    target = pkg / name
    target.write_text(body, encoding="utf-8")
    return target


class TestValidateXmlParserPolicy:
    def test_defusedxml_usage_is_clean(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "good.py",
            "import defusedxml.ElementTree as ET\n\ndef parse(data):\n    return ET.fromstring(data)\n",
        )
        assert validate_xml_parser_policy(tmp_path, tmp_path) == []

    def test_type_only_element_import_is_allowed(self, tmp_path: Path) -> None:
        # Importing Element purely as a type/construction target is safe — it
        # does not parse input — and must NOT be flagged.
        _write(
            tmp_path,
            "typeonly.py",
            "import defusedxml.ElementTree as ET\n"
            "from xml.etree.ElementTree import Element\n\n"
            "def first(root: Element) -> Element:\n    return root[0]\n",
        )
        assert validate_xml_parser_policy(tmp_path, tmp_path) == []

    def test_bare_etree_module_import_is_flagged(self, tmp_path: Path) -> None:
        _write(tmp_path, "bad.py", "import xml.etree.ElementTree as ET\n")
        violations = validate_xml_parser_policy(tmp_path, tmp_path)
        assert len(violations) == 1
        assert "xml.etree.ElementTree" in violations[0]
        assert "defusedxml" in violations[0]

    def test_etree_parse_name_import_is_flagged(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "bad.py",
            "from xml.etree.ElementTree import Element, fromstring\n",
        )
        violations = validate_xml_parser_policy(tmp_path, tmp_path)
        assert len(violations) == 1
        # Flags the parse name, not the allowed Element.
        assert "fromstring" in violations[0]

    def test_minidom_import_is_flagged(self, tmp_path: Path) -> None:
        _write(tmp_path, "bad.py", "from xml.dom.minidom import parseString\n")
        violations = validate_xml_parser_policy(tmp_path, tmp_path)
        assert len(violations) == 1
        assert "xml.dom" in violations[0]

    def test_lxml_import_is_flagged(self, tmp_path: Path) -> None:
        _write(tmp_path, "bad.py", "import lxml.etree\n")
        violations = validate_xml_parser_policy(tmp_path, tmp_path)
        assert len(violations) == 1
        assert "lxml" in violations[0]

    def test_syntax_error_file_is_skipped(self, tmp_path: Path) -> None:
        _write(tmp_path, "broken.py", "def (:\n")
        assert validate_xml_parser_policy(tmp_path, tmp_path) == []

    def test_missing_dir_returns_empty(self, tmp_path: Path) -> None:
        assert validate_xml_parser_policy(tmp_path / "nope", tmp_path) == []


class TestLiveInfrastructureTreeComplies:
    """The shipped infrastructure/ tree must satisfy the policy at all times."""

    def test_infrastructure_is_policy_clean(self) -> None:
        violations = validate_xml_parser_policy(REPO_ROOT / "infrastructure", REPO_ROOT)
        assert violations == [], "Unsafe stdlib/lxml XML parsing found:\n" + "\n".join(violations)
