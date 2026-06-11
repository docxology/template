"""Tests for infrastructure.orchestration.secure_run.

We dispatch into a no-op steganography processor (a real class injected
via the ``processor_factory`` parameter), confirming the wrapper
delegates correctly without exercising the cryptography code path.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.orchestration.secure_run import (
    SecureRunOptions,
    apply_steganography_to_project,
    run_secure_pipeline,
    validate_kmyth_for_secure_run,
)
from tests.infra_tests.steganography.test_kmyth_adapter import _write_fake_kmyth_tools


class _NoopProcessor:
    """Real class, no mocking. Records calls and returns the input path."""

    def __init__(self, _config):
        self.calls: list[Path] = []

    def process(self, pdf_path: Path, *, title: str = "", authors=None, keywords=None, author_emails=None):
        self.calls.append(pdf_path)
        # Return an object with a `.name` to match the production interface.
        out = pdf_path.with_name(pdf_path.stem + "_steganography.pdf")
        out.write_bytes(b"%PDF-1.4\n")
        return out


def _make_pdf(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"%PDF-1.4\n%\xff\xff\xff\xff\n")


@pytest.fixture
def fake_repo_with_pdf(fake_repo: Path) -> Path:
    """A fake repo with a PDF in template_code_project/output/pdf/."""
    pdf_dir = fake_repo / "projects" / "template_code_project" / "output" / "pdf"
    _make_pdf(pdf_dir / "manuscript.pdf")
    return fake_repo


def test_apply_steganography_dispatches_to_processor(fake_repo_with_pdf: Path) -> None:
    captured: list[_NoopProcessor] = []

    def _factory(config):
        proc = _NoopProcessor(config)
        captured.append(proc)
        return proc

    rc = apply_steganography_to_project(
        fake_repo_with_pdf,
        "template_code_project",
        processor_factory=_factory,
    )
    assert rc == 0
    assert len(captured) == 1
    assert len(captured[0].calls) == 1
    assert captured[0].calls[0].name == "manuscript.pdf"


def test_apply_steganography_skips_already_processed(fake_repo: Path) -> None:
    """Files whose stem already contains '_steganography' must not be re-processed."""
    pdf_dir = fake_repo / "projects" / "template_code_project" / "output" / "pdf"
    _make_pdf(pdf_dir / "manuscript.pdf")
    _make_pdf(pdf_dir / "manuscript_steganography.pdf")

    captured: list[_NoopProcessor] = []
    rc = apply_steganography_to_project(
        fake_repo,
        "template_code_project",
        processor_factory=lambda cfg: captured.append(_NoopProcessor(cfg)) or captured[-1],
    )
    assert rc == 0
    assert len(captured[0].calls) == 1
    assert captured[0].calls[0].name == "manuscript.pdf"


def test_apply_steganography_no_pdfs_returns_2(fake_repo: Path) -> None:
    rc = apply_steganography_to_project(
        fake_repo,
        "template_code_project",
        processor_factory=lambda cfg: _NoopProcessor(cfg),
    )
    assert rc == 2


def test_apply_steganography_unknown_project_returns_1(fake_repo: Path) -> None:
    rc = apply_steganography_to_project(
        fake_repo,
        "no_such_project_xyz",
        processor_factory=lambda cfg: _NoopProcessor(cfg),
    )
    assert rc == 1


def test_apply_steganography_merges_repo_defaults_then_project_config(fake_repo: Path) -> None:
    """Repo secure defaults are overlaid by the project's steganography section."""
    repo_cfg = fake_repo / "infrastructure" / "config"
    repo_cfg.mkdir(parents=True)
    (repo_cfg / "secure_config.yaml").write_text(
        "steganography:\n"
        "  enabled: true\n"
        "  overlay_text: REPO\n"
        "  hashing_enabled: true\n"
        "  pdf_encryption_algorithm: AES-256\n",
        encoding="utf-8",
    )
    proj = fake_repo / "projects" / "template_code_project"
    (proj / "manuscript").mkdir(parents=True, exist_ok=True)
    (proj / "manuscript" / "config.yaml").write_text(
        "paper:\n  title: Test Title\n"
        "authors:\n  - name: Alice\n"
        "    email: alice@example.test\n"
        "keywords: [k1, k2]\n"
        "steganography:\n"
        "  overlay_text: PROJECT\n"
        "  barcodes_enabled: false\n",
        encoding="utf-8",
    )
    _make_pdf(proj / "output" / "pdf" / "paper.pdf")

    received = {}

    class _ConfigCapturingProc:
        def __init__(self, cfg):
            received["config"] = cfg
            self.calls = []

        def process(self, p, *, title="", authors=None, keywords=None, author_emails=None):
            received["title"] = title
            received["authors"] = list(authors or [])
            received["keywords"] = list(keywords or [])
            received["author_emails"] = list(author_emails or [])
            self.calls.append(p)
            return p

    rc = apply_steganography_to_project(
        fake_repo,
        "template_code_project",
        processor_factory=_ConfigCapturingProc,
    )
    assert rc == 0
    assert received["title"] == "Test Title"
    assert received["authors"] == ["Alice"]
    assert received["keywords"] == ["k1", "k2"]
    assert received["author_emails"] == ["alice@example.test"]
    assert received["config"] == {
        "enabled": True,
        "overlay_text": "PROJECT",
        "hashing_enabled": True,
        "pdf_encryption_algorithm": "AES-256",
        "barcodes_enabled": False,
    }


# --- run_secure_pipeline -----------------------------------------------------


class _StubRunner:
    def __init__(self, repo_root, stream=None):
        self.repo_root = repo_root
        self.calls = []
        self.return_code = 0

    def run(self, invocation):
        self.calls.append(("run", invocation))
        return self.return_code


def test_run_secure_pipeline_steg_only_skips_pipeline(fake_repo_with_pdf: Path) -> None:
    captured = []

    rc = run_secure_pipeline(
        fake_repo_with_pdf,
        SecureRunOptions(project="template_code_project", steganography_only=True),
        runner_cls=_StubRunner,
        processor_factory=lambda cfg: captured.append(_NoopProcessor(cfg)) or captured[-1],
    )
    assert rc == 0
    # No pipeline runs in steganography-only mode
    assert len(captured) == 1


def test_run_secure_pipeline_runs_pipeline_then_steg(
    fake_repo_with_pdf: Path,
) -> None:
    captured = []
    runner_holder: list[_StubRunner] = []

    class _Capturing(_StubRunner):
        def __init__(self, repo_root, stream=None):
            super().__init__(repo_root, stream)
            runner_holder.append(self)

    rc = run_secure_pipeline(
        fake_repo_with_pdf,
        SecureRunOptions(project="template_code_project"),
        runner_cls=_Capturing,
        processor_factory=lambda cfg: captured.append(_NoopProcessor(cfg)) or captured[-1],
    )
    assert rc == 0
    assert len(runner_holder) == 1
    assert runner_holder[0].calls[0][0] == "run"
    assert runner_holder[0].calls[0][1].project == "template_code_project"
    assert len(captured) == 1


def test_run_secure_pipeline_pipeline_failure_short_circuits(
    fake_repo_with_pdf: Path,
) -> None:
    class _FailingRunner(_StubRunner):
        def __init__(self, repo_root, stream=None):
            super().__init__(repo_root, stream)
            self.return_code = 7

    rc = run_secure_pipeline(
        fake_repo_with_pdf,
        SecureRunOptions(project="template_code_project"),
        runner_cls=_FailingRunner,
        processor_factory=lambda cfg: _NoopProcessor(cfg),
    )
    assert rc == 7


def test_run_secure_pipeline_rejects_traversal(fake_repo_with_pdf: Path) -> None:
    with pytest.raises(ValueError):
        run_secure_pipeline(
            fake_repo_with_pdf,
            SecureRunOptions(project="../etc/passwd"),
            runner_cls=_StubRunner,
            processor_factory=lambda cfg: _NoopProcessor(cfg),
        )


def test_run_secure_pipeline_pipeline_phase_requires_project(fake_repo_with_pdf: Path) -> None:
    rc = run_secure_pipeline(
        fake_repo_with_pdf,
        SecureRunOptions(project=None, steganography_only=False),
        runner_cls=_StubRunner,
        processor_factory=lambda cfg: _NoopProcessor(cfg),
    )
    assert rc == 2


def test_apply_steganography_only_processed_pdfs_returns_2(fake_repo: Path) -> None:
    """When the directory only contains *_steganography.pdf, treat as empty."""
    pdf_dir = fake_repo / "projects" / "template_code_project" / "output" / "pdf"
    _make_pdf(pdf_dir / "doc_steganography.pdf")
    rc = apply_steganography_to_project(
        fake_repo,
        "template_code_project",
        processor_factory=lambda cfg: _NoopProcessor(cfg),
    )
    assert rc == 2


def test_apply_steganography_failure_in_processor(fake_repo_with_pdf: Path) -> None:
    """A processor that raises must mark the run as failed (rc=1)."""

    class _BadProc:
        def __init__(self, _cfg):
            pass

        def process(self, *args, **kwargs):
            raise RuntimeError("kaboom")

    rc = apply_steganography_to_project(
        fake_repo_with_pdf,
        "template_code_project",
        processor_factory=lambda cfg: _BadProc(cfg),
    )
    assert rc == 1


def test_apply_steganography_falls_back_to_central_pdf_dir(fake_repo: Path) -> None:
    """When projects/<n>/output/pdf is missing, the wrapper falls back to output/<n>/pdf."""
    central = fake_repo / "output" / "template_code_project" / "pdf"
    _make_pdf(central / "doc.pdf")
    captured: list[_NoopProcessor] = []
    rc = apply_steganography_to_project(
        fake_repo,
        "template_code_project",
        processor_factory=lambda cfg: captured.append(_NoopProcessor(cfg)) or captured[-1],
    )
    assert rc == 0
    assert captured[0].calls[0].name == "doc.pdf"


def test_apply_steganography_handles_corrupt_yaml(fake_repo: Path) -> None:
    """A malformed config.yaml is logged and treated as empty; no exception bubbles up."""
    proj = fake_repo / "projects" / "template_code_project"
    (proj / "manuscript").mkdir(parents=True, exist_ok=True)
    (proj / "manuscript" / "config.yaml").write_text("paper:\n  title: [unterminated", encoding="utf-8")
    _make_pdf(proj / "output" / "pdf" / "p.pdf")

    captured: list[_NoopProcessor] = []
    rc = apply_steganography_to_project(
        fake_repo,
        "template_code_project",
        processor_factory=lambda cfg: captured.append(_NoopProcessor(cfg)) or captured[-1],
    )
    assert rc == 0
    assert captured[0].calls[0].name == "p.pdf"


def test_run_secure_pipeline_no_projects_for_steg_only_returns_one(tmp_path: Path) -> None:
    """If steganography_only=True with no project and no projects discovered, rc==1."""
    (tmp_path / "projects").mkdir()
    rc = run_secure_pipeline(
        tmp_path,
        SecureRunOptions(project=None, steganography_only=True),
        runner_cls=_StubRunner,
        processor_factory=lambda cfg: _NoopProcessor(cfg),
    )
    assert rc == 1


def test_run_secure_pipeline_partial_failure_propagates(fake_repo: Path) -> None:
    """If one project's steganography fails, the overall status is 1."""
    proj_a = fake_repo / "projects" / "template_code_project" / "output" / "pdf"
    proj_b = fake_repo / "projects" / "template_prose_project" / "output" / "pdf"
    _make_pdf(proj_a / "a.pdf")
    _make_pdf(proj_b / "b.pdf")

    class _SelectiveFailProc:
        def __init__(self, _cfg):
            pass

        def process(self, pdf_path, **_):
            if pdf_path.name == "b.pdf":
                raise RuntimeError("fail")
            return pdf_path

    rc = run_secure_pipeline(
        fake_repo,
        SecureRunOptions(project=None, steganography_only=True),
        runner_cls=_StubRunner,
        processor_factory=lambda cfg: _SelectiveFailProc(cfg),
    )
    assert rc == 1


def test_run_secure_pipeline_steg_only_all_projects(fake_repo: Path) -> None:
    """With steganography_only=True and no project, all discovered projects are processed."""
    # Add PDFs to two projects
    for name in ("template_code_project", "template_prose_project"):
        _make_pdf(fake_repo / "projects" / name / "output" / "pdf" / f"{name}.pdf")

    captured: list[_NoopProcessor] = []

    def _factory(cfg):
        proc = _NoopProcessor(cfg)
        captured.append(proc)
        return proc

    rc = run_secure_pipeline(
        fake_repo,
        SecureRunOptions(project=None, steganography_only=True),
        runner_cls=_StubRunner,
        processor_factory=_factory,
    )
    assert rc == 0
    # Two projects had PDFs; the other two had none (status 2, non-fatal)
    processed_count = sum(len(p.calls) for p in captured)
    assert processed_count == 2


def test_validate_kmyth_for_secure_run_accepts_configured_binary_dir(fake_repo: Path, tmp_path: Path) -> None:
    bin_dir = _write_fake_kmyth_tools(tmp_path / "bin")
    repo_cfg = fake_repo / "infrastructure" / "config"
    repo_cfg.mkdir(parents=True)
    (repo_cfg / "secure_config.yaml").write_text(
        f"steganography:\n  kmyth_binary_dir: {bin_dir}\n  kmyth_source_dir: {tmp_path / 'source'}\n",
        encoding="utf-8",
    )

    assert validate_kmyth_for_secure_run(fake_repo) == 0


def test_validate_kmyth_for_secure_run_returns_one_when_unavailable(fake_repo: Path, tmp_path: Path) -> None:
    repo_cfg = fake_repo / "infrastructure" / "config"
    repo_cfg.mkdir(parents=True)
    (repo_cfg / "secure_config.yaml").write_text(
        "steganography:\n"
        f"  kmyth_binary_dir: {tmp_path / 'missing-bin'}\n"
        f"  kmyth_source_dir: {tmp_path / 'missing-source'}\n",
        encoding="utf-8",
    )

    assert validate_kmyth_for_secure_run(fake_repo) == 1


def test_run_secure_pipeline_validate_kmyth_short_circuits(fake_repo: Path, tmp_path: Path) -> None:
    bin_dir = _write_fake_kmyth_tools(tmp_path / "bin")
    repo_cfg = fake_repo / "infrastructure" / "config"
    repo_cfg.mkdir(parents=True)
    (repo_cfg / "secure_config.yaml").write_text(
        f"steganography:\n  kmyth_binary_dir: {bin_dir}\n  kmyth_source_dir: {tmp_path / 'source'}\n",
        encoding="utf-8",
    )

    rc = run_secure_pipeline(
        fake_repo,
        SecureRunOptions(project=None, validate_kmyth=True),
        runner_cls=_StubRunner,
        processor_factory=lambda cfg: _NoopProcessor(cfg),
    )

    assert rc == 0
