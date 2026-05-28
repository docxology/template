from pathlib import Path
import subprocess
import sys

import pytest

from sheaf_fixtures import write_cli_fixture_project
from manuscript.sheaf import (
    ComposeOptions,
    MissingTrackPolicy,
    SheafSection,
    compose_all_sections,
    compose_section,
    load_manifest,
    load_track_registry,
    parse_missing,
)
from manuscript.sheaf.cli import build_parser, run_compose_cli

_parse_missing = parse_missing


def test_compose_writes_markdown_sections(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    out = tmp_path / "manuscript"
    result = compose_all_sections(root, manuscript_dir=out)
    assert len(result.paths) == 12
    text = (out / "06_methods_pymdp.md").read_text(encoding="utf-8")
    assert "pymdp simulation harness" in text
    assert "sheaf-track:pymdp" in text


def test_discussion_ontology_renders_labels_not_raw_yaml() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(root / "manuscript" / "sheaf" / "manifest.yaml")
    registry = load_track_registry(root / "manuscript" / "sheaf" / "tracks.yaml")
    section = next(s for s in manifest.sections if s.id == "discussion_outlook")
    text = compose_section(section, root, registry=registry)
    assert "**Pedagogical scope**" in text
    assert "label:" not in text


def test_compose_filters_enabled_tracks() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(root / "manuscript" / "sheaf" / "manifest.yaml")
    registry = load_track_registry(root / "manuscript" / "sheaf" / "tracks.yaml")
    section = next(s for s in manifest.sections if s.id == "intro_contributions")
    text = compose_section(
        section,
        root,
        registry=registry,
        options=ComposeOptions(enabled_tracks=frozenset({"prose"})),
    )
    assert "sheaf-track:prose" in text
    assert "sheaf-track:ontology" not in text


def test_strict_compose_raises_on_validation_error(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    bad_manifest = tmp_path / "manifest.yaml"
    bad_manifest.write_text(
        """
defaults:
  missing_track: skip
sections:
  - id: broken
    order: 99
    title: Broken
    output_name: 99_broken.md
    tracks:
      prose: manuscript/sections/does_not_exist.md
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="validation failed"):
        compose_all_sections(
            root,
            manuscript_dir=tmp_path / "out",
            manifest_path=bad_manifest,
            options=ComposeOptions(strict=True),
        )


def test_missing_track_error_policy() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(root / "manuscript" / "sheaf" / "manifest.yaml")
    registry = load_track_registry(root / "manuscript" / "sheaf" / "tracks.yaml")
    section = next(s for s in manifest.sections if s.id == "intro_motivation")
    broken = SheafSection(
        id=section.id,
        title=section.title,
        short=section.short,
        order=section.order,
        tracks={"prose": "manuscript/sections/missing_prose.md"},
        output_name=section.output_name,
        kind=section.kind,
        imrad=section.imrad,
        depth=section.depth,
        compose=section.compose,
    )
    with pytest.raises(FileNotFoundError):
        compose_section(
            broken,
            root,
            registry=registry,
            options=ComposeOptions(missing_track=MissingTrackPolicy.ERROR),
        )


def test_compose_warn_policy_records_issue() -> None:
    root = Path(__file__).resolve().parents[1]
    registry = load_track_registry(root / "manuscript" / "sheaf" / "tracks.yaml")
    section = SheafSection(
        id="warn",
        title="Warn",
        short="w",
        order=1,
        tracks={"prose": "manuscript/sections/missing.md"},
        output_name="01_warn.md",
    )
    issues: list = []
    text = compose_section(
        section,
        root,
        registry=registry,
        options=ComposeOptions(missing_track=MissingTrackPolicy.WARN),
        issues=issues,
    )
    assert text.startswith("# Warn {#sec:warn}")
    assert any(i.code == "missing_track_at_compose" for i in issues)


def test_compose_single_section_filter(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    result = compose_all_sections(
        root,
        manuscript_dir=tmp_path / "manuscript",
        options=ComposeOptions(section_ids=frozenset({"intro_motivation"})),
    )
    assert len(result.paths) == 1
    assert result.paths[0].name == "02_intro_motivation.md"


def test_parse_missing_invalid_falls_back() -> None:
    assert _parse_missing("not-a-policy", MissingTrackPolicy.SKIP) == MissingTrackPolicy.SKIP
    assert _parse_missing(None, MissingTrackPolicy.ERROR) == MissingTrackPolicy.ERROR


def test_compose_cli_validate_only_strict() -> None:
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(root / "scripts" / "compose_manuscript.py"), "--validate-only", "--strict"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_compose_cli_build_parser_accepts_missing_policy() -> None:
    args = build_parser().parse_args(["--missing", "warn", "--tracks", "prose"])
    assert args.missing == "warn"
    assert args.tracks == "prose"


def test_compose_cli_lists_tracks(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = write_cli_fixture_project(tmp_path)
    assert run_compose_cli(["--list-tracks"], project_root=root) == 0
    captured = capsys.readouterr()
    assert "prose\torder=1\trenderer=markdown" in captured.out
    assert "optional\torder=2\trenderer=markdown (optional)" in captured.out


def test_compose_cli_validate_only_exports_coverage(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = write_cli_fixture_project(tmp_path)
    json_path = root / "output" / "data" / "sheaf_coverage_matrix.json"
    heatmap_path = tmp_path / "heatmap.png"

    result = run_compose_cli(
        [
            "--validate-only",
            "--strict",
            "--coverage-json",
            str(json_path.relative_to(root)),
            "--coverage-heatmap",
            str(heatmap_path),
        ],
        project_root=root,
    )

    captured = capsys.readouterr()
    assert result == 0, captured.err
    assert str(json_path.resolve()) in captured.out
    assert str(heatmap_path.resolve()) in captured.out
    assert json_path.exists()
    assert heatmap_path.exists()
    assert (root / "manuscript" / "00_00_sheaf_coverage.md").exists()


def test_compose_cli_composes_selected_tracks(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = write_cli_fixture_project(tmp_path)

    result = run_compose_cli(
        ["--section", "demo", "--tracks", "prose", "--missing", "warn"],
        project_root=root,
    )

    captured = capsys.readouterr()
    out = root / "manuscript" / "01_demo.md"
    assert result == 0, captured.err
    assert str(out) in captured.out
    text = out.read_text(encoding="utf-8")
    assert "Demo body" in text
    assert "sheaf-track:prose" in text


def test_compose_cli_reports_validation_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = write_cli_fixture_project(tmp_path)
    (root / "manuscript" / "sheaf" / "manifest.yaml").write_text(
        """
sections:
  - id: broken
    order: 1
    title: Broken
    tracks:
      prose: manuscript/sections/missing.md
""",
        encoding="utf-8",
    )

    assert run_compose_cli(["--validate-only", "--strict"], project_root=root) == 1
    captured = capsys.readouterr()
    assert "missing" in captured.err


def test_full_section_compose_contains_all_markers() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(root / "manuscript" / "sheaf" / "manifest.yaml")
    registry = load_track_registry(root / "manuscript" / "sheaf" / "tracks.yaml")
    section = next(s for s in manifest.sections if s.id == "appendix_full_sheaf")
    text = compose_section(section, root, registry=registry)
    for track_id in section.tracks:
        assert f"sheaf-track:{track_id}" in text


def test_compose_emits_imrad_dividers_and_section_labels(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    out = tmp_path / "manuscript"
    compose_all_sections(root, manuscript_dir=out)
    methods_text = (out / "05_methods_analytical.md").read_text(encoding="utf-8")
    assert "\\section*{Methods}" in methods_text
    assert "# Bernoulli–Ising analytical model {#sec:methods_analytical}" in methods_text
    intro_text = (out / "02_intro_motivation.md").read_text(encoding="utf-8")
    assert "\\section*{Introduction}" in intro_text
    assert "{#sec:intro_motivation}" in intro_text


def test_composed_methods_sheaf_contains_figure_and_tables(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    out = tmp_path / "manuscript"
    compose_all_sections(root, manuscript_dir=out)
    text = (out / "08_methods_sheaf.md").read_text(encoding="utf-8")
    assert "sheaf_layers_overview.png" in text
    assert "<!-- sheaf-layers:registry -->" in text
    assert "<!-- sheaf-layers:binding-matrix -->" in text
    assert "sheaf-track:visualization" in text
    assert "sheaf-track:layers" in text
    viz_pos = text.index("sheaf-track:visualization")
    layers_pos = text.index("<!-- sheaf-layers:registry -->")
    assert viz_pos < layers_pos


def test_resolve_track_body_layers_report(project_root: Path) -> None:
    from manuscript.sheaf.renderers import resolve_track_body

    manifest = load_manifest(project_root / "manuscript" / "sheaf" / "manifest.yaml", project_root=project_root)
    registry = load_track_registry(project_root / manifest.registry_path)
    section = next(s for s in manifest.sections if s.id == "methods_sheaf")
    rel = section.tracks["layers"]
    body = resolve_track_body(section, "layers", project_root / rel, project_root, registry)
    assert "<!-- sheaf-layers:registry -->" in body
