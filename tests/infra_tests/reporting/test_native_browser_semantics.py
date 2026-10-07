"""Actual native math/link/image controls from independently parsed sources."""

from __future__ import annotations

import shutil
import time
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess
from infrastructure.reporting.native_format_browser_oracles import audit_browser_html
from infrastructure.reporting.native_format_content_contracts import semantic_content_contract_from_ast
from infrastructure.reporting.native_format_observer_validation import replay_browser_observation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.rendering._web_assets import harden_mathjax_script


@pytest.mark.timeout(240)
@pytest.mark.parametrize(
    "mutation,expected",
    [
        ("baseline", None),
        ("changed-math", "html.math.source"),
        ("changed-citation", "html.link.source"),
        ("distorted-figure", "html.figure.distortion"),
        ("hidden-math", "html.math.invisible"),
        ("opaque-figure", "html.figure.visual"),
    ],
)
def test_actual_native_semantics(mutation: str, expected: str | None) -> None:
    root = Path(__file__).resolve().parents[3]
    archives = root / "output/readiness/native-dependencies"
    if not shutil.which("pandoc") or not archives.is_dir():
        pytest.skip("actual Pandoc and source-lock authenticated npm archives required")
    chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if not chrome.is_file():
        pytest.skip("actual native browser required")
    import tempfile

    with tempfile.TemporaryDirectory(prefix="browser-semantic-control-", dir=root / "output/readiness") as private:
        directory = Path(private)
        source = directory / "source.md"
        source.write_text(
            "# Invented measurement\n\nMeasured value -3.25 mV.\n\n$x^2 + \\frac{1}{2}$\n\n[Reference](https://example.org/reference)\n\n![Invented pixels](figure.png)\n"
        )
        image = Image.new("RGB", (160, 80), "#204090")
        ImageDraw.Draw(image).rectangle((10, 10, 80, 60), fill="#f0b030")
        image.save(directory / "figure.png")
        html = directory / "original.html"
        env = build_bounded_env()
        common = ["pandoc", str(source), "--from=markdown+tex_math_dollars+raw_tex+header_attributes"]
        parsed = run_bounded_subprocess([*common, "--to=json"], cwd=root, env=env, timeout=30)
        assert parsed.returncode == parsed.original_returncode == 0
        contract = semantic_content_contract_from_ast(
            "invented:html", ((source.relative_to(root).as_posix(), source.read_bytes()),), parsed.stdout.encode()
        )
        rendered = run_bounded_subprocess(
            [
                *common,
                "--standalone",
                "--mathjax=https://cdn.jsdelivr.net/npm/mathjax@4.0.0/tex-chtml.js",
                "-o",
                str(html),
            ],
            cwd=root,
            env=env,
            timeout=30,
        )
        assert rendered.returncode == rendered.original_returncode == 0
        harden_mathjax_script(html)
        content = html.read_text()
        if mutation == "changed-math":
            content = content.replace("x^2", "x^3")
        elif mutation == "changed-citation":
            content = content.replace('href="https://example.org/reference"', 'href="https://example.org/wrong"')
        elif mutation == "distorted-figure":
            content = content.replace("</head>", "<style>img{width:160px;height:20px}</style></head>")
        elif mutation == "hidden-math":
            content = content.replace("</head>", "<style>.math{opacity:0}</style></head>")
        elif mutation == "opaque-figure":
            content = content.replace(
                "</head>",
                "<style>figure{position:relative}figure:after{content:'';position:absolute;inset:0;background:white;z-index:99}</style></head>",
            )
        html.write_text(content)
        reader = SnapshotReader(root)
        original = reader.read(html.relative_to(root).as_posix())
        evidence = directory / "observation"
        evidence.mkdir(mode=0o700)
        observed = audit_browser_html(
            root,
            evidence,
            original.content,
            contract,
            chrome=str(chrome),
            env=env,
            deadline=time.monotonic() + 150,
            run_id="b" * 32,
            artifact=original,
        )
        assert not observed["blockers"]
        for viewport in observed["viewports"]:
            assert not viewport["blockers"]
            codes = {item["code"] for item in viewport["findings"]}
            assert (not codes) if expected is None else expected in codes, {
                "codes": codes,
                "math": viewport["dom"]["math"],
                "math_regions": viewport["pixels"]["math_regions"],
            }
        import sys

        replay_browser_observation(
            root,
            evidence,
            original,
            contract,
            observed,
            SnapshotReader(root),
            run_id="b" * 32,
            custody={"root": str(root), "implementation_root": str(root / "infrastructure")},
            runtime={"executable": sys.executable},
        )
        assert html.read_bytes() == original.content
