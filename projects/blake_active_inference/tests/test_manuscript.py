"""Tests for manuscript consistency and structural integrity.

These tests verify:
1. Theme count consistency across files
2. Citation resolution against bibliography
3. Figure file existence
4. Cross-reference integrity
5. Section structure consistency
"""

from pathlib import Path
import re
import pytest

# Path to manuscript directory
MANUSCRIPT_DIR = Path(__file__).parent.parent / "manuscript"
OUTPUT_DIR = Path(__file__).parent.parent / "output"


class TestThemeCountConsistency:
    """Verify theme count is consistent across all manuscript files."""
    
    EXPECTED_THEME_COUNT = 8
    THEME_NAMES = [
        "Boundary", "Vision", "States", "Imagination", 
        "Time", "Space", "Action", "Collectives"
    ]
    
    def test_synthesis_heading_says_eight_themes(self):
        """04_synthesis.md should say 'Eight Themes of Vision'."""
        synthesis = MANUSCRIPT_DIR / "04_synthesis.md"
        content = synthesis.read_text()
        assert "Eight Themes of Vision" in content, \
            "Synthesis heading should say 'Eight Themes of Vision'"
        assert "Nine Themes of Vision" not in content, \
            "Should not have 'Nine Themes' in synthesis heading"
    
    def test_introduction_says_eight_correspondences(self):
        """02_introduction.md should say 'Eight thematic correspondences'."""
        intro = MANUSCRIPT_DIR / "02_introduction.md"
        content = intro.read_text()
        assert "Eight thematic correspondences" in content, \
            "Introduction should say 'Eight thematic correspondences'"
        assert "Nine thematic correspondences" not in content, \
            "Should not have 'Nine thematic correspondences'"
    
    def test_synthesis_subfiles_count(self):
        """Should have exactly 8 synthesis subfiles (04a through 04h)."""
        subfiles = list(MANUSCRIPT_DIR.glob("04[a-z]_*.md"))
        assert len(subfiles) == self.EXPECTED_THEME_COUNT, \
            f"Expected {self.EXPECTED_THEME_COUNT} synthesis subfiles, found {len(subfiles)}"
    
    def test_no_remaining_nine_themes_references(self):
        """No files should contain 'nine themes' or 'Nine themes'."""
        for md_file in MANUSCRIPT_DIR.glob("*.md"):
            content = md_file.read_text().lower()
            if "nine theme" in content:
                # Check if it's in a context that's acceptable (e.g., quoted historical text)
                lines = [line for line in content.split('\n') 
                         if 'nine theme' in line.lower()]
                for line in lines:
                    # Allow if in blockquote or discussing the historical context
                    if not line.strip().startswith('>'):
                        pytest.fail(
                            f"Found 'nine theme' in {md_file.name}: {line.strip()[:50]}..."
                        )
    
    def test_introduction_lists_all_eight_themes(self):
        """Introduction should list all 8 themes in the Thematic Atlas table."""
        intro = MANUSCRIPT_DIR / "02_introduction.md"
        content = intro.read_text()
        
        # Verify themes are present in order
        previous_index = -1
        for theme in self.THEME_NAMES:
            # Check for table row format: | **Theme** |
            pattern = rf'\|\s+\*\*{theme}\*\*\s+\|'
            match = re.search(pattern, content)
            assert match, f"Introduction missing table row for theme '**{theme}**'"
            
            # Verify order
            current_index = match.start()
            assert current_index > previous_index, f"Theme '{theme}' appears out of order in Introduction"
            previous_index = current_index


class TestCitationIntegrity:
    """Verify all citations in manuscript resolve to bibliography."""
    
    def test_all_citations_resolve(self):
        """All [@key] citations should have matching BibTeX entries."""
        # Load bibliography keys
        bib_file = MANUSCRIPT_DIR / "references.bib"
        bib_content = bib_file.read_text()
        bib_keys = set(re.findall(r'@\w+\{(\w+),', bib_content))
        
        # Find all citations in manuscript
        unresolved = []
        for md_file in MANUSCRIPT_DIR.glob("*.md"):
            content = md_file.read_text()
            citations = re.findall(r'\[@(\w+)\]', content)
            for cite_key in citations:
                if cite_key not in bib_keys:
                    unresolved.append((md_file.name, cite_key))
        
        if unresolved:
            msg = "Unresolved citations:\n" + "\n".join(
                f"  {file}: @{key}" for file, key in unresolved
            )
            pytest.fail(msg)
    
    def test_bibliography_has_core_sources(self):
        """Bibliography should contain essential Blake and Friston sources."""
        bib_file = MANUSCRIPT_DIR / "references.bib"
        bib_content = bib_file.read_text()
        
        essential_keys = [
            "blake1790marriage",  # Marriage of Heaven and Hell
            "blake1804jerusalem",  # Jerusalem
            "blake1802butts",      # Fourfold vision letter
            "friston2010free",     # Free Energy Principle
            "parr2022active",      # Active Inference textbook
        ]
        
        for key in essential_keys:
            assert key in bib_content, f"Missing essential bibliography entry: {key}"


class TestFigureIntegrity:
    """Verify all figure references have corresponding files.
    
    Note: These tests verify pipeline output figures which are generated
    during the analysis stage. Tests will skip if figures haven't been
    generated yet (e.g., during unit test phase before analysis runs).
    """
    
    EXPECTED_FIGURES = [
        "fig0_thematic_atlas.png",
        "fig1_doors_of_perception.png", 
        "fig2_fourfold_vision.png",
        "fig3_perception_action_cycle.png",
        "fig4_newtons_sleep.png",
        "fig5_four_zoas.png",
        "fig6_temporal_horizons.png",
        "fig7_collective_jerusalem.png",
    ]
    
    @pytest.fixture(autouse=True)
    def check_figures_generated(self):
        """Skip figure tests if analysis stage hasn't run yet."""
        figures_dir = OUTPUT_DIR / "figures"
        if not figures_dir.exists() or not list(figures_dir.glob("fig*.png")):
            pytest.skip("Figures not yet generated - run analysis stage first")
    
    def test_all_expected_figures_exist(self):
        """All expected figure files should exist in output/figures."""
        figures_dir = OUTPUT_DIR / "figures"
        missing = []
        for fig_name in self.EXPECTED_FIGURES:
            fig_path = figures_dir / fig_name
            if not fig_path.exists():
                missing.append(fig_name)
        
        if missing:
            pytest.fail(f"Missing figures: {', '.join(missing)}")
    
    def test_figure_files_not_empty(self):
        """All figure files should have content (not empty)."""
        figures_dir = OUTPUT_DIR / "figures"
        for fig_name in self.EXPECTED_FIGURES:
            fig_path = figures_dir / fig_name
            if fig_path.exists():
                assert fig_path.stat().st_size > 0, f"Figure {fig_name} is empty"
    
    def test_figure_count_matches_themes(self):
        """Should have 8 figures (one atlas + 7 theme figures, excluding Zoas)."""
        figures_dir = OUTPUT_DIR / "figures"
        figure_files = list(figures_dir.glob("fig*.png"))
        assert len(figure_files) == 8, \
            f"Expected 8 figures, found {len(figure_files)}"


class TestManuscriptStructure:
    """Verify manuscript file structure and organization."""
    
    REQUIRED_FILES = [
        "00_preamble.md",
        "01_abstract.md", 
        "02_introduction.md",
        "02a_related_work.md",
        "03_theoretical_foundations.md",
        "04_synthesis.md",
        "05_implications.md",
        "06_conclusion.md",
        "config.yaml",
        "preamble.md",
        "references.bib",
        "README.md",
    ]
    

    
    SYNTHESIS_SUBFILES = [
        "04a_boundary.md",
        "04b_vision.md",
        "04c_states.md",
        "04d_imagination.md",
        "04e_time.md",
        "04f_space.md",
        "04g_action.md",
        "04h_collectives.md",
    ]
    
    def test_all_required_files_exist(self):
        """All required manuscript files should exist."""
        missing = []
        for filename in self.REQUIRED_FILES:
            if not (MANUSCRIPT_DIR / filename).exists():
                missing.append(filename)
        
        if missing:
            pytest.fail(f"Missing required files: {', '.join(missing)}")
    

    
    def test_synthesis_subfiles_exist(self):
        """All synthesis subfiles should exist."""
        missing = []
        for filename in self.SYNTHESIS_SUBFILES:
            if not (MANUSCRIPT_DIR / filename).exists():
                missing.append(filename)
        
        if missing:
            pytest.fail(f"Missing synthesis subfiles: {', '.join(missing)}")
    
    def test_files_not_empty(self):
        """All manuscript files should have content."""
        all_files = self.REQUIRED_FILES + self.SYNTHESIS_SUBFILES
        empty = []
        for filename in all_files:
            filepath = MANUSCRIPT_DIR / filename
            if filepath.exists() and filepath.stat().st_size == 0:
                empty.append(filename)
        
        if empty:
            pytest.fail(f"Empty files: {', '.join(empty)}")


class TestSectionNumbering:
    """Verify section numbering consistency in introduction."""
    
    def test_introduction_section_sequence(self):
        """Introduction should have sequential §2, §3, §4, §5, §6-7."""
        intro = MANUSCRIPT_DIR / "02_introduction.md"
        content = intro.read_text()
        
        # Check sequential section references
        assert "§2" in content, "Missing §2 (Related Work)"
        assert "§3" in content, "Missing §3 (Theoretical Foundations)"
        assert "§4" in content, "Missing §4 (Synthesis)"
        assert "§5" in content or "§5–6" in content, "Missing §5 or §5-6 (Conclusion)"
    
    def test_no_duplicate_section_numbers(self):
        """No section number should appear twice for different content."""
        intro = MANUSCRIPT_DIR / "02_introduction.md"
        content = intro.read_text()
        lines = content.split('\n')
        
        # Extract lines with section references in the method section
        method_lines = []
        in_method = False
        for line in lines:
            if "## III. Method" in line or "proceed through" in line.lower():
                in_method = True
            if in_method and line.strip().startswith('-') and '§' in line:
                method_lines.append(line)
            if in_method and line.startswith('#') and "Method" not in line:
                break
        
        # Check for duplicate section numbers
        section_nums = []
        for line in method_lines:
            matches = re.findall(r'§(\d+)', line)
            section_nums.extend(matches)
        
        # Check uniqueness (allow §6-7 as one reference)
        unique_nums = set(section_nums)
        if len(section_nums) != len(unique_nums):
            from collections import Counter
            counts = Counter(section_nums)
            duplicates = [n for n, c in counts.items() if c > 1]
            pytest.fail(f"Duplicate section numbers: {duplicates}")


class TestCrossReferences:
    """Verify cross-reference anchors are properly defined."""
    
    def test_anchor_ids_unique(self):
        """All anchor IDs should be unique across the manuscript."""
        anchor_ids = []
        for md_file in MANUSCRIPT_DIR.glob("*.md"):
            content = md_file.read_text()
            # Find {#anchor} patterns
            anchors = re.findall(r'\{#([^}]+)\}', content)
            for anchor in anchors:
                anchor_ids.append((md_file.name, anchor))
        
        # Check for duplicates
        seen = {}
        duplicates = []
        for filename, anchor in anchor_ids:
            if anchor in seen:
                duplicates.append(f"{anchor} (in {seen[anchor]} and {filename})")
            else:
                seen[anchor] = filename
        
        if duplicates:
            pytest.fail(f"Duplicate anchor IDs: {', '.join(duplicates)}")


class TestFigureQuality:
    """Verify figure quality metrics.
    
    Note: These tests verify pipeline output figures which are generated
    during the analysis stage. Tests will skip if figures haven't been
    generated yet.
    """
    
    MIN_FIGURE_SIZE_KB = 50  # Minimum expected figure size in KB
    
    @pytest.fixture(autouse=True)
    def check_figures_generated(self):
        """Skip figure quality tests if analysis stage hasn't run yet."""
        figures_dir = OUTPUT_DIR / "figures"
        if not figures_dir.exists() or not list(figures_dir.glob("fig*.png")):
            pytest.skip("Figures not yet generated - run analysis stage first")
    
    def test_figures_have_sufficient_resolution(self):
        """Figures should be large enough to indicate sufficient resolution."""
        figures_dir = OUTPUT_DIR / "figures"
        too_small = []
        for fig in figures_dir.glob("fig*.png"):
            size_kb = fig.stat().st_size / 1024
            if size_kb < self.MIN_FIGURE_SIZE_KB:
                too_small.append(f"{fig.name} ({size_kb:.1f}KB)")
        
        if too_small:
            pytest.fail(
                f"Figures below {self.MIN_FIGURE_SIZE_KB}KB minimum: {', '.join(too_small)}"
            )


class TestPDFOutput:
    """Verify PDF manuscript output.
    
    Note: These tests verify pipeline output which is generated during
    the PDF rendering stage. Tests will skip if PDF hasn't been generated.
    """
    
    @pytest.fixture(autouse=True)
    def check_pdf_generated(self):
        """Skip PDF tests if rendering stage hasn't run yet."""
        pdf_dir = OUTPUT_DIR / "pdf"
        if not pdf_dir.exists() or not list(pdf_dir.glob("*.pdf")):
            pytest.skip("PDF not yet generated - run rendering stage first")
    
    def test_combined_pdf_exists(self):
        """Combined manuscript PDF should exist."""
        pdf_dir = OUTPUT_DIR / "pdf"
        combined_pdfs = list(pdf_dir.glob("*_combined.pdf"))
        assert len(combined_pdfs) >= 1, "No combined PDF found"
    
    def test_combined_pdf_not_empty(self):
        """Combined PDF should have substantial content."""
        pdf_dir = OUTPUT_DIR / "pdf"
        for pdf in pdf_dir.glob("*_combined.pdf"):
            size_kb = pdf.stat().st_size / 1024
            assert size_kb > 100, f"Combined PDF too small: {size_kb:.1f}KB"


class TestMarkdownFormatting:
    """Verify markdown formatting consistency."""
    
    def test_no_trailing_whitespace_in_headers(self):
        """Headers should not have trailing whitespace."""
        issues = []
        for md_file in MANUSCRIPT_DIR.glob("*.md"):
            content = md_file.read_text()
            for i, line in enumerate(content.split('\n'), 1):
                if line.startswith('#') and line.rstrip() != line:
                    issues.append(f"{md_file.name}:{i}")
        
        if issues:
            pytest.fail(f"Headers with trailing whitespace: {', '.join(issues[:5])}...")
    
    def test_no_multiple_blank_lines(self):
        """Files should not have more than 2 consecutive blank lines."""
        issues = []
        for md_file in MANUSCRIPT_DIR.glob("*.md"):
            content = md_file.read_text()
            if '\n\n\n\n' in content:  # 3+ blank lines
                issues.append(md_file.name)
        
        if issues:
            pytest.fail(f"Files with excessive blank lines: {', '.join(issues)}")
    
    def test_headers_have_blank_before(self):
        """Headers (except first) should have a blank line before them."""
        issues = []
        for md_file in MANUSCRIPT_DIR.glob("*.md"):
            content = md_file.read_text()
            lines = content.split('\n')
            for i, line in enumerate(lines[1:], 2):  # Start from line 2
                if line.startswith('#') and i > 1:
                    prev_line = lines[i-2]
                    # Allow if previous line is empty or also a header
                    if prev_line.strip() and not prev_line.startswith('#'):
                        issues.append(f"{md_file.name}:{i}")
        
        if len(issues) > 5:
            pytest.fail(f"Headers without blank line before: {', '.join(issues[:5])}...")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
