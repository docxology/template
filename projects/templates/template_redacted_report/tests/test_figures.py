"""Real-behavior tests for the deterministic exemplar figures and registry."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

from redacted_report import FIGURE_SPECS, build_figures
from redacted_report.figures import _height_px

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = PROJECT_ROOT / "output" / "figures"


@pytest.mark.slow
def test_build_figures_writes_expected_files(tmp_path: Path) -> None:
    build_figures(tmp_path)

    for spec in FIGURE_SPECS:
        name = spec["name"]
        assert (tmp_path / f"{name}.png").is_file()
        assert (tmp_path / f"{name}.svg").is_file()
    assert (tmp_path / "figure_registry.json").is_file()


def test_registry_matches_specs_and_disk(tmp_path: Path) -> None:
    registry = build_figures(tmp_path)

    assert set(registry) == {spec["label"] for spec in FIGURE_SPECS}
    for spec in FIGURE_SPECS:
        entry = registry[spec["label"]]
        assert entry["filename"] == f"{spec['name']}.png"
        assert entry["generated_by"] == spec["generated_by"]
        assert entry["caption"] == spec["caption"]
        assert entry["metadata"]["alt_text"] == spec["alt_text"]
        assert (tmp_path / entry["filename"]).is_file()


def test_figures_are_byte_deterministic(tmp_path: Path) -> None:
    first = build_figures(tmp_path / "first")
    second = build_figures(tmp_path / "second")

    for spec in FIGURE_SPECS:
        name = spec["name"]
        assert (tmp_path / "first" / f"{name}.png").read_bytes() == (tmp_path / "second" / f"{name}.png").read_bytes()
        assert (tmp_path / "first" / f"{name}.svg").read_bytes() == (tmp_path / "second" / f"{name}.svg").read_bytes()
    assert (tmp_path / "first" / "figure_registry.json").read_bytes() == (
        tmp_path / "second" / "figure_registry.json"
    ).read_bytes()
    assert first == second


def test_png_height_stays_below_canvas_cap(tmp_path: Path) -> None:
    build_figures(tmp_path)

    for spec in FIGURE_SPECS:
        assert _height_px(tmp_path / f"{spec['name']}.png") <= 1600


def test_svg_companions_carry_accessibility_markup(tmp_path: Path) -> None:
    build_figures(tmp_path)

    for spec in FIGURE_SPECS:
        svg = (tmp_path / f"{spec['name']}.svg").read_text(encoding="utf-8")
        assert 'role="img"' in svg
        assert 'aria-labelledby="fig-title fig-desc"' in svg
        assert "<title" in svg and "<desc" in svg
        assert spec["alt_text"] in svg


def test_registry_json_is_loadable_and_well_formed(tmp_path: Path) -> None:
    build_figures(tmp_path)
    registry = json.loads((tmp_path / "figure_registry.json").read_text(encoding="utf-8"))

    for label, entry in registry.items():
        assert label.startswith("fig:")
        assert entry["label"] == label
        assert entry["figure_id"].startswith("figure_")
        assert entry["width"].endswith("textwidth")
        assert isinstance(entry["metadata"]["alt_text"], str)


def test_figure_types_match_domain_profile() -> None:
    profile = yaml.safe_load((PROJECT_ROOT / "domain_profile.yaml").read_text(encoding="utf-8"))
    declared_types = set(profile.get("figure_types", []))
    built_names = {spec["name"] for spec in FIGURE_SPECS}

    assert built_names == declared_types, f"figures {built_names} != domain_profile {declared_types}"


@pytest.mark.slow
def test_committed_figures_match_regenerated_geometry() -> None:
    """Tracked evidence must match the fresh pipeline's registry and geometry.

    The figure builder runs with this gate's explicitly selected interpreter.
    Real isolated readbacks bind its runtime, optional installed SDK and dependencies
    before and after execution. PNG raster bytes can legitimately vary with the host's
    FreeType/font backend even when the locked matplotlib version is identical;
    same-environment byte determinism is covered separately above. This gate
    therefore compares the source-bound registry, rendered canvas geometry and alpha.
    Lossless PNG encodings may have different modes for identical decoded pixels.
    """
    import subprocess
    import tempfile

    from PIL import Image

    provider_program = """
import hashlib
import importlib.metadata as metadata
import json
import sys
from pathlib import Path

try:
    import infrastructure
except ModuleNotFoundError as exc:
    if exc.name != "infrastructure":
        raise
    sdk = None
else:
    origin = Path(infrastructure.__file__).resolve()
    sdk = {
        "origin": str(origin),
        "sha256": hashlib.sha256(origin.read_bytes()).hexdigest(),
        "version": metadata.version("research-project-template"),
    }
print(json.dumps({
    "python": sys.version,
    "executable": str(Path(sys.executable).resolve()),
    "prefix": sys.prefix,
    "sdk": sdk,
    "packages": {name: metadata.version(name) for name in ("reportlab", "pytest", "coverage")},
}))
"""

    def assert_decoded_geometry(generated: Image.Image, tracked: Image.Image, name: str) -> None:
        assert generated.size == tracked.size, f"tracked {name}.png has different canvas geometry"
        with generated.convert("RGBA") as generated_rgba, tracked.convert("RGBA") as tracked_rgba:
            assert generated_rgba.getchannel("A").tobytes() == tracked_rgba.getchannel("A").tobytes(), (
                f"tracked {name}.png has different decoded alpha pixels"
            )
            with generated_rgba.convert("RGB") as generated_rgb, tracked_rgba.convert("RGB") as tracked_rgb:
                assert generated_rgb.getbbox() == tracked_rgb.getbbox(), (
                    f"tracked {name}.png has different content bounds"
                )

    # Exercise actual decoded representations, including alpha and geometry failures.
    with Image.new("RGBA", (3, 2), (80, 80, 80, 255)) as control:
        for mode in ("RGB", "L"):
            with control.convert(mode) as encoded:
                assert control.tobytes() == encoded.convert("RGBA").tobytes()
                assert_decoded_geometry(control, encoded, "lossless-control")
        with control.crop((0, 0, 2, 2)) as cropped:
            with pytest.raises(AssertionError, match="different canvas geometry"):
                assert_decoded_geometry(control, cropped, "cropped-control")
        with control.copy() as changed_alpha:
            changed_alpha.putpixel((1, 1), (80, 80, 80, 254))
            with pytest.raises(AssertionError, match="different decoded alpha pixels"):
                assert_decoded_geometry(control, changed_alpha, "alpha-control")
    with Image.new("RGBA", (3, 2), (0, 0, 0, 255)) as bounds:
        bounds.putpixel((0, 0), (80, 80, 80, 255))
        with bounds.copy() as moved:
            moved.putpixel((0, 0), (0, 0, 0, 255))
            moved.putpixel((1, 1), (80, 80, 80, 255))
            with pytest.raises(AssertionError, match="different content bounds"):
                assert_decoded_geometry(bounds, moved, "moved-control")

    def read_runtime_provider() -> dict[str, object]:
        observed = subprocess.run(
            [sys.executable, "-I", "-B", "-c", provider_program],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        assert observed.returncode == 0, observed.stderr
        return json.loads(observed.stdout)

    runtime_before = read_runtime_provider()
    with tempfile.TemporaryDirectory(prefix="redacted-fig-check-") as tmp:
        out_dir = Path(tmp) / "figures"
        completed = subprocess.run(
            [sys.executable, "-B", "scripts/02_build_figures.py", "--output-dir", str(out_dir)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
        assert completed.returncode == 0, completed.stderr
        assert read_runtime_provider() == runtime_before, "figure producer changed the selected runtime/provider"
        registry = json.loads((out_dir / "figure_registry.json").read_text(encoding="utf-8"))
        on_disk_registry = json.loads((FIGURES_DIR / "figure_registry.json").read_text(encoding="utf-8"))
        assert registry == on_disk_registry, "tracked figure_registry.json drifted from source"
        for spec in FIGURE_SPECS:
            name = spec["name"]
            with Image.open(out_dir / f"{name}.png") as generated, Image.open(FIGURES_DIR / f"{name}.png") as tracked:
                assert_decoded_geometry(generated, tracked, name)
