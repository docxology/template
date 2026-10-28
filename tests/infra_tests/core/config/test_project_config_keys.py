"""A project owns its extra manuscript-config keys through its own pyproject."""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.config.loader import validate_config_keys
from infrastructure.core.project_pyproject import load_project_pyproject
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

REPO_ROOT = Path(__file__).resolve().parents[4]


def _project(tmp_path: Path, *, keys_line: str | None) -> Path:
    root = tmp_path / "projects" / "templates" / "template_widget"
    (root / "manuscript").mkdir(parents=True)
    (root / "manuscript" / "config.yaml").write_text("paper:\n  title: x\n", encoding="utf-8")
    template = '[tool.template]\nplatform_version = "4.3.0"\n'
    if keys_line is not None:
        template += f"{keys_line}\n"
    (root / "pyproject.toml").write_text(
        '[project]\nname = "template-widget"\nversion = "0.1.0"\n\n' + template,
        encoding="utf-8",
    )
    return root


def test_declared_keys_are_accepted_without_a_warning(tmp_path: Path) -> None:
    root = _project(tmp_path, keys_line='config_keys = ["widgets"]')
    config_path = root / "manuscript" / "config.yaml"
    assert validate_config_keys({"widgets": {}}, config_path, project_name="template_widget") == []


def test_undeclared_key_still_warns(tmp_path: Path) -> None:
    root = _project(tmp_path, keys_line=None)
    config_path = root / "manuscript" / "config.yaml"
    warnings = validate_config_keys({"widgets": {}}, config_path, project_name="template_widget")
    assert warnings and "widgets" in warnings[0]


def test_invalid_declaration_is_reported_not_guessed(tmp_path: Path) -> None:
    root = _project(tmp_path, keys_line='config_keys = ["not a key"]')
    declared = load_project_pyproject(root)
    assert declared is not None
    assert declared.declared_config_keys == ()
    assert declared.declared_config_keys_error == (
        "[tool.template].config_keys must be a TOML array of identifier strings"
    )


def test_canonical_exemplars_declare_exactly_their_owned_blocks() -> None:
    declared_keys = {}
    for name in PUBLIC_PROJECT_NAMES:
        declared = load_project_pyproject(REPO_ROOT / "projects" / name)
        assert declared is not None, name
        assert declared.declared_config_keys_error is None, name
        if declared.declared_config_keys:
            declared_keys[Path(name).name] = declared.declared_config_keys
    assert declared_keys == {
        "template_gold_refinement": ("gold_refinement",),
        "template_madlib": ("madlib",),
    }
