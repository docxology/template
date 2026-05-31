from pathlib import Path

import re

from manuscript.hydrate import format_variables, substitute_snake_case_tokens, write_resolved_manuscript
from manuscript.variables import generate_variables

_TOKEN_RE = re.compile(r"\{\{[a-z][a-z0-9_]*(?::\.[0-9]+f)?\}\}")


def test_generate_variables_includes_structural_counts() -> None:
    root = Path(__file__).resolve().parents[1]
    vars_ = generate_variables(root, require_analysis_outputs=False)
    assert vars_["pipeline_track_count"] == 10
    assert vars_["sheaf_track_count"] == 13
    assert vars_["appendix_sheaf_track_count"] == 12
    assert vars_["imrad_manifest_rows"] == 17
    assert vars_["composed_section_count"] == 12
    assert vars_["imrad_group_count"] == 5
    assert vars_["coverage_bound"] >= vars_["coverage_present"]


def test_format_variables_adds_entropy_formatted() -> None:
    formatted = format_variables({"si_tmaze_mean_belief_entropy": 1.234567})
    assert formatted["si_tmaze_mean_belief_entropy_formatted"] == "1.2346"


def test_substitute_snake_case_tokens_supports_precision() -> None:
    text = "entropy {{si_tmaze_mean_belief_entropy:.4f}}"
    resolved, unresolved = substitute_snake_case_tokens(
        text,
        {"si_tmaze_mean_belief_entropy": "1.234567"},
    )
    assert unresolved == []
    assert resolved == "entropy 1.2346"


def test_validate_manuscript_tokens_flags_unknown() -> None:
    root = Path(__file__).resolve().parents[1]
    from manuscript.hydrate import validate_manuscript_tokens

    keys = set(generate_variables(root, require_analysis_outputs=False))
    unknown = validate_manuscript_tokens(root / "manuscript", keys)
    assert unknown == []


def test_collect_malformed_token_names_flags_single_brace() -> None:
    from manuscript.hydrate import collect_malformed_token_names

    text = "Appendix binds {appendix_sheaf_track_count} but {{sheaf_track_count}} is fine."
    assert collect_malformed_token_names(text) == ["appendix_sheaf_track_count"]


def test_collect_malformed_token_names_ignores_latex_fenced_blocks() -> None:
    from manuscript.hydrate import collect_malformed_token_names

    text = (
        "```{=latex}\n"
        "\\addcontentsline{toc}{section}{Introduction}\n"
        "```\n"
        "Valid {{pipeline_track_count}}.\n"
    )
    assert collect_malformed_token_names(text) == []


def test_write_resolved_manuscript_raises_on_single_brace_token(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "00_abstract.md").write_text(
        "Bad {appendix_sheaf_track_count} token.\n",
        encoding="utf-8",
    )
    import pytest

    with pytest.raises(ValueError, match="malformed single-brace"):
        write_resolved_manuscript(tmp_path, {"pipeline_track_count": 10})


def test_write_resolved_manuscript_raises_on_unknown_token(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "00_abstract.md").write_text("Value {{not_a_real_token}}.\n", encoding="utf-8")
    import pytest

    with pytest.raises(ValueError, match="not_a_real_token"):
        write_resolved_manuscript(tmp_path, {"pipeline_track_count": 10})


def test_write_resolved_manuscript_removes_tokens(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "00_abstract.md").write_text(
        "Tracks: {{pipeline_track_count}}; entropy {{si_tmaze_mean_belief_entropy_formatted}}.\n",
        encoding="utf-8",
    )
    variables = generate_variables(root, require_analysis_outputs=False)
    out_dir = write_resolved_manuscript(tmp_path, variables)
    resolved = (out_dir / "00_abstract.md").read_text(encoding="utf-8")
    assert _TOKEN_RE.search(resolved) is None
    assert "Tracks: 10" in resolved
