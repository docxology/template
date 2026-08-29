"""Tests for the public exemplar capability inventory."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from infrastructure.project.public_capabilities import (
    CANONICAL_CI_PYTHON_VERSIONS,
    CAPABILITY_MANIFEST_SCHEMA_VERSION,
    CIMatrixEntry,
    PACKAGE_NAME_OVERRIDES,
    PublicCapabilityReport,
    audit_public_capability,
    audit_public_capabilities,
    build_ci_matrix,
    manifest_roster_digest,
    validate_ci_matrix,
    validate_manifest_roster,
    validate_unique_package_names,
)
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

_CI_CEILING = CANONICAL_CI_PYTHON_VERSIONS[-1]
_CI_MINOR = _CI_CEILING.split(".")[1]
from scripts.gates.public_capabilities import main as capability_gate_main
from tests._support.projects import make_project, write_doc


@pytest.fixture(scope="module")
def public_report() -> PublicCapabilityReport:
    """Build the real static manifest once for deterministic contract tests."""
    repo = Path(__file__).resolve().parents[3]
    return audit_public_capabilities(repo)


def _complete_project(
    root: Path,
    *,
    name: str = "template_test",
    package_name: str | None = None,
    requires_python: str = ">=3.10",
    config: str = "paper:\n  title: Synthetic Test Project\n",
    manuscript: str = "# Result\nNo generated values are required.\n",
    hydration_script: str | None = None,
    hydration_source: str | None = None,
) -> Path:
    project = make_project(root, name, with_manuscript=True, with_scripts=True)
    write_doc(project / "README.md", "# Example\n")
    write_doc(project / "AGENTS.md", "# Example agent contract\n")
    write_doc(project / ".agents" / "skills" / "SKILL.md", "# Example skill\n")
    write_doc(project / "tests" / "test_contract.py", "def test_contract():\n    assert 1 + 1 == 2\n")
    write_doc(project / "scripts" / "analysis.py", "def main():\n    return 0\n")
    write_doc(project / "manuscript" / "config.yaml", config)
    write_doc(project / "manuscript" / "00_result.md", manuscript)
    write_doc(
        project / "pyproject.toml",
        (
            f'[project]\nname = "{package_name or name.replace("_", "-")}"\n'
            f'version = "0.1.0"\nrequires-python = "{requires_python}"\n'
        ),
    )
    if hydration_script is not None:
        write_doc(
            project / "scripts" / hydration_script,
            hydration_source
            or ('def main() -> int:\n    return 0\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'),
        )
    return project


def test_public_capability_inventory_covers_all_canonical_exemplars(
    public_report: PublicCapabilityReport,
) -> None:
    report = public_report

    assert tuple(project.project for project in report.projects) == PUBLIC_PROJECT_NAMES
    assert report.schema_version == CAPABILITY_MANIFEST_SCHEMA_VERSION
    assert report.roster_digest == manifest_roster_digest(PUBLIC_PROJECT_NAMES)
    assert report.ci_python_versions == CANONICAL_CI_PYTHON_VERSIONS
    assert len(report.ci_matrix) == len(PUBLIC_PROJECT_NAMES) * len(CANONICAL_CI_PYTHON_VERSIONS)
    assert report.passed
    assert all(project.test_file_count > 0 for project in report.projects)
    assert all(project.package.name for project in report.projects)
    assert len({project.package.normalized_name for project in report.projects}) == len(report.projects)
    assert all(
        project.package.normalized_name == project.package.expected_name.replace("_", "-")
        for project in report.projects
    )
    assert all(project.package.import_targets for project in report.projects)
    assert all(project.probes for project in report.projects)
    meta = next(project for project in report.projects if project.project == "templates/template_template")
    assert meta.package.expected_name == PACKAGE_NAME_OVERRIDES["templates/template_template"]
    assert meta.package.name == "template-template-meta-project"


def test_public_capability_manifest_json_is_stable(public_report: PublicCapabilityReport) -> None:
    first = json.dumps(public_report.to_dict(), sort_keys=True, separators=(",", ":"))
    second = json.dumps(public_report.to_dict(), sort_keys=True, separators=(",", ":"))

    assert first == second
    payload = json.loads(first)
    assert payload["schema_version"] == CAPABILITY_MANIFEST_SCHEMA_VERSION
    assert len(payload["roster_digest"]) == 64
    assert len(payload["ci_matrix"]["include"]) == len(public_report.ci_matrix)


def test_public_capability_inventory_reports_missing_structure(tmp_path: Path) -> None:
    project = make_project(tmp_path, "template_test", with_manuscript=True)
    write_doc(project / "README.md", "# Example\n")
    capability = audit_public_capability(tmp_path, "template_test")

    assert capability.passed is False
    assert "scripts" in capability.missing_paths
    assert "pyproject.toml" in capability.missing_paths


def test_public_capability_inventory_classifies_skip_contracts(tmp_path: Path) -> None:
    project = _complete_project(tmp_path)
    write_doc(
        project / "tests" / "test_skip_contract.py",
        "import pytest\n\ndef test_optional():\n    pytest.skip('optional tool not installed')\n",
    )
    capability = audit_public_capability(tmp_path, "template_test")

    assert len(capability.skip_contracts) == 1
    assert capability.skip_contracts[0].category == "OPTIONAL_CAPABILITY"
    assert capability.issues == ()


def test_disabled_formats_and_no_hydrator_are_valid_without_live_tokens(tmp_path: Path) -> None:
    _complete_project(
        tmp_path,
        config=(
            "paper:\n"
            "  title: Disabled formats\n"
            "render:\n"
            "  formats:\n"
            "    pdf: false\n"
            "    html: false\n"
            "    slides: false\n"
            "    docx: false\n"
            "    epub: false\n"
        ),
        manuscript=(
            "# Static manuscript\n"
            "Inline documentation such as `{{TOKEN}}` is not a hydration requirement.\n"
            "```text\n{{FENCED_EXAMPLE}}\n```\n"
        ),
    )

    capability = audit_public_capability(tmp_path, "template_test")

    assert capability.passed
    assert capability.hydration.mode == "none"
    assert capability.hydration.token_count == 0
    assert not any(getattr(capability.render_formats, name) for name in ("pdf", "html", "slides", "docx", "epub"))


def test_live_manuscript_token_requires_a_hydration_entrypoint(tmp_path: Path) -> None:
    _complete_project(
        tmp_path,
        manuscript="# Result\nThe measured value is {{MEASURED_VALUE}}.\n",
    )

    capability = audit_public_capability(tmp_path, "template_test")

    assert capability.passed is False
    assert capability.hydration.required is True
    assert capability.hydration.entrypoint is None
    assert any("no hydration entrypoint" in issue for issue in capability.issues)


def test_live_manuscript_token_accepts_conventional_hydration_entrypoint(tmp_path: Path) -> None:
    _complete_project(
        tmp_path,
        manuscript="# Result\nThe measured value is {{MEASURED_VALUE}}.\n",
        hydration_script="z_generate_manuscript_variables.py",
    )

    capability = audit_public_capability(tmp_path, "template_test")

    assert capability.passed
    assert capability.hydration.mode == "required"
    assert capability.hydration.entrypoint == "scripts/z_generate_manuscript_variables.py"
    assert capability.hydration.smoke == "static-compile-main-guard"
    assert capability.hydration.entrypoint_sha256 is not None


def test_hydration_entrypoint_must_compile(tmp_path: Path) -> None:
    _complete_project(
        tmp_path,
        manuscript="# Result\nThe measured value is {{MEASURED_VALUE}}.\n",
        hydration_script="z_generate_manuscript_variables.py",
        hydration_source="def main(:\n    return 0\n",
    )

    capability = audit_public_capability(tmp_path, "template_test")

    assert capability.passed is False
    assert capability.hydration.smoke == "failed"
    assert any("does not compile" in issue for issue in capability.issues)


def test_hydration_entrypoint_requires_main_guard(tmp_path: Path) -> None:
    _complete_project(
        tmp_path,
        manuscript="# Result\nThe measured value is {{MEASURED_VALUE}}.\n",
        hydration_script="z_generate_manuscript_variables.py",
        hydration_source="def main() -> int:\n    return 0\n",
    )

    capability = audit_public_capability(tmp_path, "template_test")

    assert capability.passed is False
    assert any("__main__ guard" in issue for issue in capability.issues)


@pytest.mark.parametrize(
    "guard_body",
    [
        "    if False:\n        main()\n",
        "    False and main()\n",
        "    callback = lambda: main()\n",
    ],
)
def test_hydration_entrypoint_rejects_main_call_in_dead_nested_branch(
    tmp_path: Path,
    guard_body: str,
) -> None:
    _complete_project(
        tmp_path,
        manuscript="# Result\nThe measured value is {{MEASURED_VALUE}}.\n",
        hydration_script="z_generate_manuscript_variables.py",
        hydration_source=('def main() -> int:\n    return 0\n\nif __name__ == "__main__":\n' + guard_body),
    )

    capability = audit_public_capability(tmp_path, "template_test")

    assert capability.passed is False
    assert capability.hydration.smoke == "failed"
    assert any("directly invoke main()" in issue for issue in capability.issues)


def test_hydration_entrypoint_must_be_confined_without_symlinks(tmp_path: Path) -> None:
    project = _complete_project(
        tmp_path,
        manuscript="# Result\nThe measured value is {{MEASURED_VALUE}}.\n",
    )
    outside = tmp_path / "outside_hydrator.py"
    write_doc(
        outside,
        ('def main() -> int:\n    return 0\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'),
    )
    (project / "scripts" / "z_generate_manuscript_variables.py").symlink_to(outside)

    capability = audit_public_capability(tmp_path, "template_test")

    assert capability.passed is False
    assert any("escapes or is missing" in issue for issue in capability.issues)


def test_package_identity_is_bound_after_name_normalization(tmp_path: Path) -> None:
    _complete_project(tmp_path, name="template_identity", package_name="unrelated-package")

    capability = audit_public_capability(tmp_path, "template_identity")

    assert capability.passed is False
    assert capability.package.normalized_name == "unrelated-package"
    assert capability.package.expected_name == "template_identity"
    assert any("does not match project" in issue for issue in capability.issues)


def test_package_identity_rejects_invalid_and_duplicate_normalized_names(tmp_path: Path) -> None:
    _complete_project(tmp_path, package_name="-invalid")

    capability = audit_public_capability(tmp_path, "template_test")

    assert capability.passed is False
    assert any("not a valid distribution name" in issue for issue in capability.issues)
    collision = validate_unique_package_names(
        (("templates/alpha", "shared_package"), ("templates/beta", "shared-package"))
    )
    assert collision
    assert "shared-package" in collision[0]


@pytest.mark.parametrize(
    "relative_path",
    [
        Path("src/stub.py"),
        Path("tests/test_contract.py"),
        Path("tests/_support.py"),
    ],
)
def test_python_discovery_fails_closed_on_invalid_source_and_test_syntax(
    tmp_path: Path,
    relative_path: Path,
) -> None:
    project = _complete_project(tmp_path)
    write_doc(project / relative_path, "def broken(:\n    return None\n")

    capability = audit_public_capability(tmp_path, "template_test")

    assert capability.passed is False
    assert any(relative_path.as_posix() in issue and "does not compile" in issue for issue in capability.issues)
    syntax_probe = next(probe for probe in capability.probes if probe.id == "python-syntax")
    assert syntax_probe.status == "fail"


def test_ci_python_floor_must_include_every_canonical_version(tmp_path: Path) -> None:
    _complete_project(tmp_path, requires_python=">=3.13")

    capability = audit_public_capability(tmp_path, "template_test")

    assert capability.passed is False
    assert any("CI Python 3.10.x series" in issue for issue in capability.issues)
    assert any(
        f"CI Python {version}.x series" in issue
        for version in CANONICAL_CI_PYTHON_VERSIONS
        for issue in capability.issues
    )


@pytest.mark.parametrize(
    ("requires_python", "expected_fragment"),
    [
        (f">=3.10,<=3.{_CI_MINOR}.0", f"CI Python {_CI_CEILING}.x series"),
        (f">=3.10,!={_CI_CEILING}.42", f"CI Python {_CI_CEILING}.x series"),
        (">=3.10,!=3.10.*", "CI Python 3.10.x series"),
        (f">=3.10,<{_CI_CEILING}.99", f"CI Python {_CI_CEILING}.x series"),
    ],
)
def test_ci_python_contract_rejects_partial_minor_series(
    tmp_path: Path,
    requires_python: str,
    expected_fragment: str,
) -> None:
    _complete_project(tmp_path, requires_python=requires_python)

    capability = audit_public_capability(tmp_path, "template_test")

    assert capability.passed is False
    assert any(expected_fragment in issue for issue in capability.issues)


def test_ci_python_contract_accepts_complete_minor_series(tmp_path: Path) -> None:
    _complete_project(tmp_path, requires_python=f">=3.10,<3.{int(_CI_MINOR) + 1}")

    capability = audit_public_capability(tmp_path, "template_test")

    assert capability.passed


def test_analysis_allowlist_fails_closed_on_escaping_entrypoint(tmp_path: Path) -> None:
    _complete_project(
        tmp_path,
        config=("paper:\n  title: Escaping analysis\nanalysis:\n  scripts:\n    - ../outside.py\n"),
    )
    write_doc(tmp_path / "projects" / "outside.py", "raise RuntimeError('must never run')\n")

    capability = audit_public_capability(tmp_path, "template_test")

    assert capability.passed is False
    assert capability.analysis.configured is True
    assert capability.analysis.entrypoints == ()
    assert any("does not match confined runnable entrypoints" in issue for issue in capability.issues)


def test_render_format_declarations_reject_string_truthiness(tmp_path: Path) -> None:
    _complete_project(
        tmp_path,
        config=('paper:\n  title: Invalid render declaration\nrender:\n  formats:\n    pdf: "false"\n'),
    )

    capability = audit_public_capability(tmp_path, "template_test")

    assert capability.passed is False
    assert any("must be a YAML boolean" in issue for issue in capability.issues)


def test_roster_and_ci_matrix_negative_controls() -> None:
    canonical = build_ci_matrix()
    assert validate_manifest_roster(PUBLIC_PROJECT_NAMES) == ()
    assert validate_ci_matrix(canonical) == ()

    assert "missing projects" in validate_manifest_roster(PUBLIC_PROJECT_NAMES[:-1])[0]
    assert "duplicate projects" in validate_manifest_roster((*PUBLIC_PROJECT_NAMES, PUBLIC_PROJECT_NAMES[0]))[0]
    assert "unexpected projects" in validate_manifest_roster((*PUBLIC_PROJECT_NAMES, "active/private_project"))[0]
    assert "missing lanes" in validate_ci_matrix(canonical[:-1])[0]
    assert "duplicate lanes" in validate_ci_matrix((*canonical, canonical[0]))[0]
    assert "unexpected lanes" in validate_ci_matrix((*canonical, CIMatrixEntry("active/private_project", "3.10")))[0]


@pytest.mark.parametrize(
    ("marker", "expected_pass"),
    [
        ("@pytest.mark.skip", False),
        ('@pytest.mark.skip(reason="documented platform exclusion")', True),
    ],
)
def test_skip_decorator_requires_a_reason(
    tmp_path: Path,
    marker: str,
    expected_pass: bool,
) -> None:
    project = _complete_project(tmp_path)
    write_doc(
        project / "tests" / "test_decorated_skip.py",
        f"import pytest\n\n{marker}\ndef test_decorated() -> None:\n    assert True\n",
    )

    capability = audit_public_capability(tmp_path, "template_test")

    assert capability.passed is expected_pass
    decorated = [contract for contract in capability.skip_contracts if contract.kind == "skip"]
    assert len(decorated) == 1
    assert bool(decorated[0].reason) is expected_pass


@pytest.mark.parametrize(
    ("marker", "expected_pass"),
    [
        ("@pytest.mark.skipif(True)", False),
        ('@pytest.mark.skipif(True, reason="documented condition")', True),
    ],
)
def test_skipif_condition_is_not_mistaken_for_a_reason(
    tmp_path: Path,
    marker: str,
    expected_pass: bool,
) -> None:
    project = _complete_project(tmp_path)
    write_doc(
        project / "tests" / "test_skipif_contract.py",
        f"import pytest\n\n{marker}\ndef test_conditional() -> None:\n    assert True\n",
    )

    capability = audit_public_capability(tmp_path, "template_test")

    assert capability.passed is expected_pass
    skipif = [contract for contract in capability.skip_contracts if contract.kind == "skipif"]
    assert len(skipif) == 1
    assert bool(skipif[0].reason) is expected_pass


def test_imperative_skip_and_importorskip_keep_distinct_reason_contracts(tmp_path: Path) -> None:
    project = _complete_project(tmp_path)
    write_doc(
        project / "tests" / "test_imperative_skips.py",
        (
            'import pytest\n\npytest.importorskip("optional_dependency")\n\n'
            "def test_conditional() -> None:\n"
            '    pytest.skip(reason="documented runtime condition")\n'
        ),
    )

    capability = audit_public_capability(tmp_path, "template_test")

    assert capability.passed
    contracts = [
        contract for contract in capability.skip_contracts if contract.path.endswith("test_imperative_skips.py")
    ]
    assert [(contract.kind, contract.reason) for contract in contracts] == [
        ("importorskip", "optional import: optional_dependency"),
        ("skip", "documented runtime condition"),
    ]


def test_ci_matrix_cli_emits_one_line_exact_product(
    public_report: PublicCapabilityReport,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = Path(__file__).resolve().parents[3]

    exit_code = capability_gate_main(["--repo-root", str(repo), "--ci-matrix-json"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert output.count("\n") == 1
    assert json.loads(output) == {"include": [entry.to_dict() for entry in public_report.ci_matrix]}


def test_ci_workflow_consumes_only_the_capability_matrix() -> None:
    repo = Path(__file__).resolve().parents[3]
    workflow = yaml.safe_load((repo / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    detect = workflow["jobs"]["detect-projects"]
    matrix_step = next(step for step in detect["steps"] if step.get("id") == "matrix")
    strategy = workflow["jobs"]["test-project"]["strategy"]

    assert detect["outputs"] == {"matrix": "${{ steps.matrix.outputs.matrix }}"}
    assert "scripts/gates/public_capabilities.py --ci-matrix-json" in matrix_step["run"]
    assert strategy["matrix"] == "${{ fromJSON(needs.detect-projects.outputs.matrix) }}"
    assert workflow["jobs"]["test-project"]["env"]["UV_PYTHON"] == "${{ matrix.python-version }}"
    assert workflow["jobs"]["test-infra"]["env"]["UV_PYTHON"] == "${{ matrix.python-version }}"
    assert (
        sum(step.get("name") == "Verify selected Python minor" for step in workflow["jobs"]["test-project"]["steps"])
        == 1
    )


def test_project_matrix_provisions_the_pinned_pandoc_toolchain() -> None:
    repo = Path(__file__).resolve().parents[3]
    workflow = yaml.safe_load((repo / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))

    project_step = next(
        step for step in workflow["jobs"]["test-project"]["steps"] if step.get("name") == "Install pandoc"
    )
    infra_step = next(step for step in workflow["jobs"]["test-infra"]["steps"] if step.get("name") == "Install pandoc")

    assert project_step == infra_step
    assert project_step["uses"] == "pandoc/actions/setup@86321b6dd4675f5014c611e05088e10d4939e09e"
    assert "if" not in project_step


def test_textbook_matrix_provisions_the_pinned_mermaid_toolchain() -> None:
    repo = Path(__file__).resolve().parents[3]
    workflow = yaml.safe_load((repo / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))

    project_steps = workflow["jobs"]["test-project"]["steps"]
    mermaid_steps = [
        step
        for step in project_steps
        if step.get("uses") == "./.github/actions/setup-docs-lint"
    ]

    assert mermaid_steps == [
        {
            "uses": "./.github/actions/setup-docs-lint",
            "if": "matrix.project == 'templates/template_textbook'",
        }
    ]
