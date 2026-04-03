"""Tests for infrastructure.rendering.config — comprehensive coverage."""

from infrastructure.rendering.config import RenderingConfig


class TestRenderingConfig:
    def test_defaults(self):
        config = RenderingConfig()
        assert config.pandoc_path == "pandoc"
        assert config.latex_compiler == "xelatex"
        assert config.pdf_dir == "output/pdf"
        assert config.web_dir == "output/web"
        assert config.slides_dir == "output/slides"
        assert config.slide_theme == "metropolis"

    def test_custom_values(self):
        config = RenderingConfig(
            pandoc_path="/usr/local/bin/pandoc",
            latex_compiler="lualatex",
            pdf_dir="/custom/pdf",
        )
        assert config.pandoc_path == "/usr/local/bin/pandoc"
        assert config.latex_compiler == "lualatex"
        assert config.pdf_dir == "/custom/pdf"

    def test_from_env_empty(self):
        config = RenderingConfig.from_env(env={})
        assert config.pandoc_path == "pandoc"
        assert config.latex_compiler == "xelatex"

    def test_from_env_with_values(self):
        env = {
            "PANDOC_PATH": "/opt/pandoc",
            "LATEX_COMPILER": "pdflatex",
            "PDF_DIR": "/build/pdf",
            "SLIDE_THEME": "default",
        }
        config = RenderingConfig.from_env(env=env)
        assert config.pandoc_path == "/opt/pandoc"
        assert config.latex_compiler == "pdflatex"
        assert config.pdf_dir == "/build/pdf"
        assert config.slide_theme == "default"

    def test_from_env_partial(self):
        env = {"WEB_DIR": "/web/output"}
        config = RenderingConfig.from_env(env=env)
        assert config.web_dir == "/web/output"
        # Other values should remain default
        assert config.pandoc_path == "pandoc"
