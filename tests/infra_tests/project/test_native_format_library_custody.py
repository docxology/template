"""Real filesystem controls for bounded decoder provider observations."""

import base64
import hashlib
from pathlib import Path

import pytest

from infrastructure.project.native_format_library_custody import (
    _assert_recorded_provider_file,
    _installer_console_script,
    _read,
    _relative,
    _selected,
)


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


def test_installer_shim_exemption_stays_narrow_to_real_bin_scripts() -> None:
    assert _installer_console_script("bin/decoder", b"#!/usr/bin/env python\nimport sys\n")
    # A library file, a non-script file under bin, and a shebang-less bin entry
    # all keep the exact RECORD comparison.
    assert not _installer_console_script("lib/python3.14/site-packages/decoder.so", b"#!/usr/bin/env python\n")
    assert not _installer_console_script("bin/decoder.so", b"\x7fELF native library bytes")
    assert not _installer_console_script("bin/decoder", b"no shebang at all")
    assert not _installer_console_script("bin/decoder", b"#!")
    assert not _installer_console_script("share/man/man1/decoder.1", b"#!/usr/bin/env python\n.TH DECODER 1\n")


def test_recorded_library_file_mismatch_is_still_detected_and_names_the_file(tmp_path: Path) -> None:
    """Negative control: the shim exemption must not weaken library-file custody."""
    library = tmp_path / "package" / "decoder.so"
    library.parent.mkdir()
    library.write_bytes(b"genuine native library bytes")
    content, _ = _read(tmp_path, "package/decoder.so")
    good_hash = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).decode().rstrip("=")
    relative = "package/decoder.so"

    # Exact agreement passes, so the control below is a real difference.
    _assert_recorded_provider_file(relative, content, f"sha256={good_hash}", str(len(content)))

    # A same-length byte change passes the size check and must still be caught by
    # the hash check, naming the offending file.
    mutated = b"X" + content[1:]
    assert len(mutated) == len(content) and mutated != content
    with pytest.raises(ValueError, match=r"package/decoder\.so differs from RECORD hash"):
        _assert_recorded_provider_file(relative, mutated, f"sha256={good_hash}", str(len(content)))

    # A genuine size change is caught and names the file.
    with pytest.raises(ValueError, match=r"package/decoder\.so differs from RECORD size"):
        _assert_recorded_provider_file(relative, content + b"!", f"sha256={good_hash}", str(len(content)))


def test_installed_console_scripts_are_retained_without_false_size_failure() -> None:
    """A real installed shim is exempt, and its RECORD row really disagrees."""
    import csv
    import io
    import sys
    from importlib import metadata

    prefix = Path(sys.prefix).resolve()
    inspected = 0
    for requested in _selected(["pdf"]):
        distribution = metadata.distribution(requested)
        site = Path(str(distribution.locate_file(""))).absolute()
        record = next(str(item) for item in distribution.files or () if str(item).endswith(".dist-info/RECORD"))
        rows = list(csv.reader(io.StringIO((site / record).read_text())))
        for label, declared_hash, declared_size in rows:
            if not label.startswith("../../../bin/"):
                continue
            relative = _relative(prefix, site, label)
            content, _ = _read(prefix, relative)
            if not _installer_console_script(relative, content):
                continue
            inspected += 1
            # The exemption is only justified because the recorded bytes cannot
            # describe the installer's shim.
            assert int(declared_size) != len(content) or not declared_hash
            with pytest.raises(ValueError, match="differs from RECORD"):
                _assert_recorded_provider_file(relative, content, declared_hash, declared_size)
    assert inspected, "no installer console-script shim was available to inspect"


@pytest.mark.timeout(600)
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
    for corruption in ("missing", "foreign", "hash", "shim-exemption"):
        changed = copy.deepcopy(after)
        if corruption == "missing":
            changed["distributions"].pop()
        elif corruption == "foreign":
            changed["distributions"][0]["name"] = "foreign-decoder"
        elif corruption == "shim-exemption":
            # The shim exemption cannot be forged onto a provider library file.
            target = next(row for row in changed["distributions"][0]["files"] if not row["relative"].startswith("bin/"))
            target["installer_console_script"] = True
        else:
            # Target a real provider library file: the first RECORD rows are the
            # installer's own bin/ shims, which are deliberately exempt.
            library = next(
                row for row in changed["distributions"][0]["files"] if not row["relative"].startswith("bin/")
            )
            library["sha256"] = "0" * 64
        with pytest.raises(ValueError):
            validate_native_library_custody(changed, changed, formats=formats, reader=SnapshotReader(root))
