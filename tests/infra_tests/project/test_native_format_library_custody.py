"""Real filesystem controls for bounded decoder provider observations."""

from pathlib import Path

import pytest

from infrastructure.project.native_format_library_custody import _read, _relative, _selected


def test_held_provider_reads_detect_actual_byte_and_metadata_change(tmp_path: Path) -> None:
    library = tmp_path / "library.so"
    library.write_bytes(b"original native file control")
    before = _read(tmp_path, "library.so")
    library.write_bytes(b"changed native file control")
    after = _read(tmp_path, "library.so")
    assert before[0] != after[0]
    assert before[1] != after[1]


def test_actual_escaping_file_and_parent_symlinks_refused(tmp_path: Path) -> None:
    provider = tmp_path / "provider"
    provider.mkdir()
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / "library.so").write_bytes(b"foreign library")
    (provider / "library.so").symlink_to(foreign / "library.so")
    (provider / "escape").symlink_to(foreign, target_is_directory=True)
    for label in ("library.so", "escape/library.so"):
        with pytest.raises(OSError):
            _read(provider, label)


def test_record_bin_normalization_stays_inside_original_provider(tmp_path: Path) -> None:
    site = tmp_path / "lib/python3.14/site-packages"
    assert _relative(tmp_path, site, "../../../bin/decoder") == "bin/decoder"
    with pytest.raises(ValueError, match="escapes"):
        _relative(tmp_path, site, "../../../../foreign")
    with pytest.raises(ValueError, match="escapes"):
        _read(tmp_path, "../foreign")


def test_unknown_format_cannot_select_generic_provider_success() -> None:
    with pytest.raises(ValueError, match="unknown"):
        _selected(["invented"])
    assert "python-pptx" in _selected(["slides"])


def test_actual_installed_decoder_census_and_corrupt_retained_record() -> None:
    import copy

    from infrastructure.project.native_format_library_custody import (
        observe_native_library_custody,
        validate_native_library_custody,
    )
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

    root = Path(__file__).resolve().parents[3]
    formats = ["pdf", "slides"]
    before = observe_native_library_custody(formats, repo_root=root)
    import lxml.etree
    import matplotlib
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    import numpy
    import PIL.Image
    import pypdfium2

    assert PIL.Image.new("RGB", (4, 4), "white").getpixel((0, 0)) == (255, 255, 255)
    assert numpy.linalg.norm(numpy.array([3.0, 4.0])) == 5.0
    assert lxml.etree.fromstring(b"<native/>").tag == "native"
    assert pypdfium2.__file__
    figure = Figure(figsize=(1, 1), dpi=12)
    canvas = FigureCanvasAgg(figure)
    figure.add_subplot().plot([0, 1], [0, 1])
    canvas.draw()
    assert canvas.get_width_height() == (12, 12)
    assert matplotlib.__file__
    after = observe_native_library_custody(formats, repo_root=root)
    validate_native_library_custody(before, after, formats=formats, reader=SnapshotReader(root))
    assert any(row["name"] == "matplotlib" for row in after["distributions"])
    assert any(row["module"] == "matplotlib.backends._backend_agg" for row in after["loaded_modules"])
    for corruption in ("missing", "foreign", "hash"):
        changed = copy.deepcopy(after)
        if corruption == "missing":
            changed["distributions"].pop()
        elif corruption == "foreign":
            changed["distributions"][0]["name"] = "foreign-decoder"
        else:
            changed["distributions"][0]["files"][0]["sha256"] = "0" * 64
        with pytest.raises(ValueError):
            validate_native_library_custody(changed, changed, formats=formats, reader=SnapshotReader(root))
