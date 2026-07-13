from __future__ import annotations

import subprocess
from pathlib import Path

from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.pdf_renderer import PDFRenderer


def test_render_markdown_falls_back_to_alternate_engine(tmp_path) -> None:
    source_file = tmp_path / "manuscript.md"
    source_file.write_text("# Title\n\nBody", encoding="utf-8")

    config = RenderingConfig(
        output_dir=str(tmp_path / "output"),
        pdf_dir=str(tmp_path / "output" / "pdf"),
        manuscript_dir=str(tmp_path),
        figures_dir=str(tmp_path / "figures"),
    )
    availability = {"pandoc": "/usr/bin/pandoc", "xelatex": "/usr/bin/xelatex", "pdflatex": "/usr/bin/pdflatex"}

    def fake_which(name: str) -> str | None:
        return availability.get(name)

    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        output_file = Path(cmd[cmd.index("-o") + 1])
        if "--pdf-engine=xelatex" in cmd:
            raise subprocess.CalledProcessError(1, cmd, stderr="xelatex unavailable")
        output_file.write_bytes(b"%PDF-1.4\n%EOF")
        return subprocess.CompletedProcess(cmd, 0)

    renderer = PDFRenderer(
        config,
        executable_resolver=fake_which,
        process_runner=fake_run,
    )

    output = renderer.render_markdown(source_file)

    assert output.exists()
    assert len(calls) == 2
    assert "--pdf-engine=pdflatex" in calls[-1]
