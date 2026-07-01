from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import matplotlib.image as mpimg
import numpy as np

from cover_visualization import (
    COVER_REPORT,
    cover_visualization_manifest,
    generate_cover_visualization,
    write_cover_visualization,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_cover_visualization_generates_png_and_svg(tmp_path):
    out = generate_cover_visualization(tmp_path, project_root=PROJECT_ROOT)
    svg = out.with_suffix(".svg")
    assert out.name == "cover_visualization.png"
    assert out.exists()
    assert svg.exists()
    assert out.stat().st_size > 250_000
    assert svg.stat().st_size > 50_000

    image = np.asarray(mpimg.imread(out))
    assert image.shape[0] == 3200
    assert image.shape[1] == 2400
    assert float(np.var(image[..., :3])) > 0.002


def test_cover_visualization_manifest_records_quality(tmp_path):
    out = write_cover_visualization(PROJECT_ROOT, output_dir=tmp_path / "figures", report_dir=tmp_path / "reports")
    manifest = cover_visualization_manifest(out)
    report = json.loads((tmp_path / "reports" / COVER_REPORT).read_text(encoding="utf-8"))
    assert manifest["schema"] == "template-gold-refinement-cover-v1"
    assert report == manifest
    assert report["width_px"] == 2400
    assert report["height_px"] == 3200
    assert report["nonwhite_fraction"] > 0.90
    assert report["color_variance"] > 0.002


def test_cover_visualization_script_exits_zero():
    proc = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "zz_generate_cover_visualization.py")],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(PROJECT_ROOT),
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert (PROJECT_ROOT / "output" / "figures" / "cover_visualization.png").exists()
    assert (PROJECT_ROOT / "output" / "figures" / "cover_visualization.svg").exists()
    assert (PROJECT_ROOT / "output" / "reports" / COVER_REPORT).exists()
