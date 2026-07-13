"""PDF proof renderer extracted from the public visual-variant façade."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from redacted_report.publication_meta import publication_author_and_date
from redacted_report.profiles import (
    PDF_BACKGROUND_MODES,
    REDACTION_VISUAL_STYLES,
    ColorRGB,
    PDFBackgroundProfile,
    RedactionVisualProfile,
    _BACKGROUND_BY_NAME,
    _STYLE_BY_NAME,
)
from redacted_report.redaction import (
    RedactionDecision,
    RedactionSegment,
    build_redaction_ledger,
    redact_text,
)


# --- Section metadata for the comprehensive proof document ---

_SECTION_MAP: dict[str, tuple[str, str]] = {
    "s1": (
        "Abstract",
        "This exemplar demonstrates a complete disclosure-control pipeline for sanitized public release reports.",
    ),
    "s2": (
        "1. Introduction",
        "The pipeline operates in two layers: text-level disclosure control and visual proof with steganography.",
    ),
    "s3": (
        "2. Fixture: SECRET Segment",
        "Invented high-side content demonstrating source-identity and operational-detail redaction.",
    ),
    "s4": (
        "2.1 SIGINT Collection Platform",
        "Invented SIGINT content demonstrating operational-detail and time-place-selector redaction.",
    ),
    "s5": (
        "2.2 TOP_SECRET//SCI Compartment",
        "Invented compartmented content demonstrating mosaic risk from multi-source combination.",
    ),
    "s6": (
        "3. Sanitized Public Narrative",
        "The public export after redaction, with source-safe ledger and hash manifest.",
    ),
    "s7": ("4. Visual Proof Matrix", "Four redaction styles across four PDF backgrounds yield sixteen variant PDFs."),
    "s8": ("5. Steganography Layer", "Nine security methods post-process each base PDF for provenance and integrity."),
    "s9": ("6. Kmyth TPM Sealing", "TPM2-TSS storage hierarchy sealing with mssim-to-swtpm protocol proxy on macOS."),
    "s10": (
        "6.1 FlushContext Patch",
        "Kmyth-seal patched to flush transient TPM objects between consecutive seal invocations.",
    ),
    "s11": ("7. Release Gate", "Three-role approval gate: originator, classification reviewer, release authority."),
    "s12": ("8. Residual Risk Detection", "Pattern-based detection of common public-release leaks in sanitized text."),
    "s13": ("9. CUI Classification Example", "Controlled Unclassified Information segment above the public ceiling."),
    "s14": (
        "10. Comprehensive Release Packet",
        "Combined export with audit, ledger, hashes, review gate, and paragraph audit table.",
    ),
}


class _ProofPDFRenderer:
    """Multi-page proof PDF renderer with figures, tables, and redaction treatments."""

    def __init__(
        self,
        *,
        output_pdf: Path,
        style: RedactionVisualProfile,
        background: PDFBackgroundProfile,
        title: str,
        color_cls: Any,
        pagesize: tuple[float, float],
        string_width_fn: Any,
        canvas_cls: Any,
    ) -> None:
        self.output_pdf = output_pdf
        self.style = style
        self.background = background
        self.title = title
        self.Color = color_cls
        self.pagesize = pagesize
        self.string_width = string_width_fn
        self.Canvas = canvas_cls
        self.page_width, self.page_height = pagesize
        self.left_margin = 36
        self.right_margin = 36
        self.top_margin = 54
        self.bottom_margin = 54
        self.usable_width = self.page_width - self.left_margin - self.right_margin
        self.doc: Any = None
        self.y = 0.0
        self.page_num = 0

    def _color(self, rgb: ColorRGB) -> Any:
        return self.Color(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255)

    def _new_page(self) -> None:
        if self.page_num > 0:
            self._draw_footer()
            self.doc.showPage()
        self.page_num += 1
        self.doc.setFillColor(self._color(self.background.fill_rgb))
        self.doc.rect(0, 0, self.page_width, self.page_height, stroke=0, fill=1)
        self.y = self.page_height - self.top_margin
        self._draw_header()

    def _draw_header(self) -> None:
        self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
        self.doc.setFont("Helvetica", 7)
        self.doc.drawString(self.left_margin, self.page_height - 28, self.title)
        self.doc.drawRightString(
            self.page_width - self.right_margin,
            self.page_height - 28,
            f"{self.style.label} / {self.background.label}  |  Page {self.page_num}",
        )
        self.doc.setStrokeColor(self._color(self.background.subdued_text_rgb))
        self.doc.setLineWidth(0.3)
        self.doc.line(
            self.left_margin,
            self.page_height - 32,
            self.page_width - self.right_margin,
            self.page_height - 32,
        )

    def _draw_footer(self) -> None:
        self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
        self.doc.setFont("Helvetica", 6)
        self.doc.drawString(
            self.left_margin,
            18,
            "Dev proof only: invented fixture text, source-safe masks, no operational content.",
        )
        self.doc.drawRightString(
            self.page_width - self.right_margin,
            18,
            f"Style: {self.style.name}  |  BG: {self.background.name}",
        )

    def _ensure_space(self, needed: float) -> None:
        if self.y - needed < self.bottom_margin + 30:
            self._new_page()

    def _draw_title_page(self) -> None:
        self.page_num = 1
        self.doc.setFillColor(self._color(self.background.fill_rgb))
        self.doc.rect(0, 0, self.page_width, self.page_height, stroke=0, fill=1)

        # Title
        self.doc.setFillColor(self._color(self.background.text_rgb))
        self.doc.setFont("Helvetica-Bold", 20)
        self.doc.drawCentredString(self.page_width / 2, self.page_height - 120, self.title)

        # Subtitle
        self.doc.setFont("Helvetica", 11)
        self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
        self.doc.drawCentredString(
            self.page_width / 2,
            self.page_height - 145,
            "Disclosure Control and Release Audit with TPM-Backed Sealed Sidecars",
        )

        # Author / date — from manuscript/config.yaml (single source of truth)
        author, paper_date = publication_author_and_date()
        self.doc.setFont("Helvetica", 9)
        self.doc.drawCentredString(self.page_width / 2, self.page_height - 175, author)
        self.doc.drawCentredString(self.page_width / 2, self.page_height - 190, paper_date or "")

        # Visual treatment badge
        badge_y = self.page_height - 230
        self.doc.setFillColor(self._color(self.style.fill_rgb))
        self.doc.rect(self.page_width / 2 - 120, badge_y - 12, 240, 24, stroke=1, fill=1)
        self.doc.setFillColor(self._color(self.style.text_rgb))
        self.doc.setFont("Helvetica-Bold", 9)
        self.doc.drawCentredString(self.page_width / 2, badge_y - 3, f"{self.style.label} on {self.background.label}")

        # Abstract preview
        self.y = badge_y - 50
        self._draw_section_header("Abstract")
        abstract_text = (
            "This exemplar demonstrates a complete disclosure-control pipeline for sanitized public release "
            "reports. The methodology combines classification-ceiling enforcement, source-protection validation, "
            "mosaic-risk scoring, and TPM-backed sealed sidecars across a sixteen-variant visual proof matrix. "
            "Four redaction styles are rendered across four PDF backgrounds, yielding sixteen base proof PDFs. "
            "Each receives nine steganographic security methods and optional Kmyth TPM .ski sidecar sealing."
        )
        self._draw_body_text(abstract_text)

        # Architecture overview figure
        self._ensure_space(180)
        self._draw_architecture_diagram()

        self._draw_footer()

    def _draw_section_header(self, text: str) -> None:
        self._ensure_space(30)
        self.y -= 10
        self.doc.setFillColor(self._color(self.background.text_rgb))
        self.doc.setFont("Helvetica-Bold", 12)
        self.doc.drawString(self.left_margin, self.y, text)
        self.doc.setStrokeColor(self._color(self.background.subdued_text_rgb))
        self.doc.setLineWidth(0.5)
        self.doc.line(self.left_margin, self.y - 4, self.page_width - self.right_margin, self.y - 4)
        self.y -= 18

    def _draw_body_text(self, text: str, font_size: float = 9, indent: float = 0) -> None:
        self.doc.setFont("Helvetica", font_size)
        self.doc.setFillColor(self._color(self.background.text_rgb))
        max_w = self.usable_width - indent
        words = text.split()
        line = ""
        for word in words:
            test = f"{line} {word}".strip()
            if self.string_width(test, "Helvetica", font_size) > max_w:
                if self.y - font_size - 4 < self.bottom_margin + 30:
                    self._new_page()
                    self.doc.setFont("Helvetica", font_size)
                    self.doc.setFillColor(self._color(self.background.text_rgb))
                self.doc.drawString(self.left_margin + indent, self.y, line)
                self.y -= font_size + 4
                line = word
            else:
                line = test
        if line:
            if self.y - font_size - 4 < self.bottom_margin + 30:
                self._new_page()
                self.doc.setFont("Helvetica", font_size)
                self.doc.setFillColor(self._color(self.background.text_rgb))
            self.doc.drawString(self.left_margin + indent, self.y, line)
            self.y -= font_size + 4
        self.y -= 4

    def _draw_segment_content(
        self,
        segment: RedactionSegment,
        decisions: Sequence[RedactionDecision],
    ) -> None:
        self._ensure_space(60)
        # Segment label
        self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
        self.doc.setFont("Helvetica-Bold", 7)
        label = f"{segment.id} | {segment.classification}"
        if segment.source_controls:
            label += f" | Controls: {', '.join(segment.source_controls)}"
        self.doc.drawString(self.left_margin, self.y, label)
        self.y -= 12

        # Segment text with redaction boxes
        self.y = _draw_segment(
            self.doc,
            segment,
            decisions,
            x=self.left_margin,
            y=self.y,
            max_width=self.usable_width,
            style=self.style,
            background=self.background,
            color_factory=self._color,
            string_width=self.string_width,
        )
        self.y -= 14

    def _draw_architecture_diagram(self) -> None:
        self._ensure_space(160)
        self._draw_section_header("Pipeline Architecture")
        cx = self.page_width / 2
        box_w = 160
        box_h = 28

        # Layer 1
        y1 = self.y - 10
        self.doc.setFillColor(self._color((30, 80, 120)))
        self.doc.rect(cx - box_w / 2, y1 - box_h, box_w, box_h, stroke=0, fill=1)
        self.doc.setFillColor(self._color((255, 255, 255)))
        self.doc.setFont("Helvetica-Bold", 8)
        self.doc.drawCentredString(cx, y1 - 18, "Layer 1: Disclosure Control")

        # Arrow
        self.doc.setStrokeColor(self._color(self.background.subdued_text_rgb))
        self.doc.setLineWidth(1)
        self.doc.line(cx, y1 - box_h - 2, cx, y1 - box_h - 14)
        self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
        self.doc.setFont("Helvetica", 6)
        self.doc.drawCentredString(cx + 20, y1 - box_h - 10, "sanitized text")

        # Layer 2
        y2 = y1 - box_h - 18
        self.doc.setFillColor(self._color((60, 100, 50)))
        self.doc.rect(cx - box_w / 2, y2 - box_h, box_w, box_h, stroke=0, fill=1)
        self.doc.setFillColor(self._color((255, 255, 255)))
        self.doc.setFont("Helvetica-Bold", 8)
        self.doc.drawCentredString(cx, y2 - 18, "Layer 2: Visual + Steganography")

        # Arrow
        self.doc.line(cx, y2 - box_h - 2, cx, y2 - box_h - 14)
        self.doc.drawCentredString(cx + 20, y2 - box_h - 10, "proof PDFs")

        # Layer 3
        y3 = y2 - box_h - 18
        self.doc.setFillColor(self._color((120, 60, 30)))
        self.doc.rect(cx - box_w / 2, y3 - box_h, box_w, box_h, stroke=0, fill=1)
        self.doc.setFillColor(self._color((255, 255, 255)))
        self.doc.setFont("Helvetica-Bold", 8)
        self.doc.drawCentredString(cx, y3 - 18, "Layer 3: Kmyth TPM Sealing")

        # Side outputs
        self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
        self.doc.setFont("Helvetica", 6)
        outputs = [
            ("Redaction Ledger", cx - box_w / 2 - 90, y1 - 14),
            ("Hash Manifest", cx + box_w / 2 + 10, y2 - 14),
            (".ski Sidecars", cx + box_w / 2 + 10, y3 - 14),
        ]
        for label, lx, ly in outputs:
            self.doc.drawString(lx, ly, label)
            self.doc.line(lx + 60, ly + 3, lx + 70 if lx < cx else lx - 10, ly + 3)

        self.y = y3 - box_h - 20

    def _draw_security_methods_table(self) -> None:
        self._ensure_space(180)
        self._draw_section_header("Steganographic Security Methods")

        methods = [
            ("SHA-256/SHA-512 Hash Manifest", "Cryptographic integrity verification"),
            ("Diagonal Watermark Overlay", "Visible provenance stamp"),
            ("Footer Provenance Overlay", "Page-level release metadata"),
            ("First-Page Invisible Text", "Hidden identification marker"),
            ("QR Payload Barcode", "Machine-readable provenance"),
            ("Code128 Page Barcode", "Per-page tracking barcode"),
            ("PDF Info Metadata", "Document-level metadata injection"),
            ("XMP Metadata", "Standards-compliant metadata embedding"),
            ("Embedded Stego Manifest", "Self-contained provenance archive"),
            ("Kmyth TPM .ski Sidecar", "Hardware-backed sealed object"),
            ("PDF Password Encryption", "AES-256 protection (optional)"),
        ]

        col_w = self.usable_width
        row_h = 16
        for i, (name, desc) in enumerate(methods):
            self._ensure_space(row_h + 4)
            if i % 2 == 0:
                self.doc.setFillColor(self._color(self.background.fill_rgb))
                self.doc.rect(self.left_margin, self.y - row_h + 2, col_w, row_h, stroke=0, fill=1)
            self.doc.setFillColor(self._color(self.background.text_rgb))
            self.doc.setFont("Helvetica-Bold", 7)
            self.doc.drawString(self.left_margin + 4, self.y - 6, name)
            self.doc.setFont("Helvetica", 7)
            self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
            self.doc.drawString(self.left_margin + 200, self.y - 6, desc)
            self.y -= row_h

        self.y -= 10

    def _draw_kmyth_flow_diagram(self) -> None:
        self._ensure_space(140)
        self._draw_section_header("Kmyth TPM Sealing Flow (macOS)")

        boxes = [
            ("kmyth-seal", 60, self._color((40, 80, 120))),
            ("mssim TCTI", 170, self._color((60, 100, 50))),
            ("Proxy", 280, self._color((120, 80, 30))),
            ("swtpm", 390, self._color((120, 60, 30))),
        ]
        box_w = 90
        box_h = 24
        flow_y = self.y - 20

        for label, bx, bc in boxes:
            self.doc.setFillColor(bc)
            self.doc.rect(bx, flow_y - box_h, box_w, box_h, stroke=0, fill=1)
            self.doc.setFillColor(self._color((255, 255, 255)))
            self.doc.setFont("Helvetica-Bold", 7)
            self.doc.drawCentredString(bx + box_w / 2, flow_y - 15, label)
            if bx < 390:
                self.doc.setStrokeColor(self._color(self.background.subdued_text_rgb))
                self.doc.setLineWidth(1)
                self.doc.line(bx + box_w, flow_y - box_h / 2, bx + box_w + 10, flow_y - box_h / 2)

        # Protocol annotations
        self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
        self.doc.setFont("Helvetica", 5.5)
        annotations = [
            (155, "TSS2 API calls"),
            (265, "mssim wire protocol"),
            (375, "swtpm CMD_* protocol"),
        ]
        for ax, text in annotations:
            self.doc.drawCentredString(ax, flow_y - box_h - 8, text)

        # TPM details
        self.y = flow_y - box_h - 20
        details = [
            "Control channel: POWER_ON(1) -> success, NV_ON(11) -> success, TPM_SESSION_END(20) -> close",
            "Data channel: 4B cmd_type(8) + 1B locality + 4B tpm_size | raw TPM command -> swtpm",
            "FlushContext patch: Tss2_Sys_FlushContext(storageKey) before free_tpm2_resources",
            "Result: 32 .ski sidecars sealed across 16 variants without slot exhaustion",
        ]
        for detail in details:
            self._draw_body_text(detail, font_size=7, indent=10)

    def _draw_matrix_grid(self) -> None:
        self._ensure_space(160)
        self._draw_section_header("Visual Proof Matrix (4x4)")

        styles = [p.name for p in REDACTION_VISUAL_STYLES]
        backgrounds = [p.name for p in PDF_BACKGROUND_MODES]
        cell_w = 80
        cell_h = 40
        grid_x = self.left_margin + 30
        grid_y = self.y - 30

        # Column headers
        self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
        self.doc.setFont("Helvetica-Bold", 6)
        for j, bg in enumerate(backgrounds):
            self.doc.drawCentredString(grid_x + j * cell_w + cell_w / 2, grid_y + 6, bg)

        # Row headers and cells
        for i, st in enumerate(styles):
            ry = grid_y - (i + 1) * cell_h
            self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
            self.doc.setFont("Helvetica-Bold", 6)
            self.doc.drawRightString(grid_x - 4, ry + cell_h / 2 - 2, st)

            for j, bg in enumerate(backgrounds):
                cx = grid_x + j * cell_w
                # Draw cell with style color
                profile = _STYLE_BY_NAME[st]
                bg_profile = _BACKGROUND_BY_NAME[bg]
                self.doc.setFillColor(self._color(bg_profile.fill_rgb))
                self.doc.rect(cx, ry, cell_w, cell_h, stroke=1, fill=1)
                # Draw redaction token sample
                self.doc.setFillColor(self._color(profile.fill_rgb))
                self.doc.rect(cx + 8, ry + 8, 30, 10, stroke=1, fill=1)
                self.doc.setFillColor(self._color(profile.text_rgb))
                self.doc.setFont("Helvetica-Bold", 4)
                self.doc.drawCentredString(cx + 23, ry + 10, profile.token)
                # Label
                self.doc.setFillColor(self._color(bg_profile.subdued_text_rgb))
                self.doc.setFont("Helvetica", 5)
                self.doc.drawCentredString(cx + cell_w / 2, ry + 4, f"{st}_{bg}")

        self.y = grid_y - len(styles) * cell_h - 20

    def _draw_classification_chart(self) -> None:
        self._ensure_space(120)
        self._draw_section_header("Classification Taxonomy")

        levels = [
            ("UNCLASSIFIED", 0, (100, 160, 100)),
            ("CUI", 1, (140, 180, 80)),
            ("CONFIDENTIAL", 2, (200, 180, 60)),
            ("SECRET", 3, (220, 140, 40)),
            ("TOP_SECRET", 4, (200, 80, 40)),
            ("TOP_SECRET_SCI", 5, (160, 40, 40)),
        ]
        bar_w = 70
        bar_h_base = 12
        chart_x = self.left_margin + 100
        chart_y = self.y - 10

        for i, (name, rank, rgb) in enumerate(levels):
            by = chart_y - i * (bar_h_base + 6)
            h = bar_h_base + rank * 4
            self.doc.setFillColor(self._color(rgb))
            self.doc.rect(chart_x, by - h, bar_w, h, stroke=0, fill=1)
            self.doc.setFillColor(self._color(self.background.text_rgb))
            self.doc.setFont("Helvetica-Bold", 7)
            self.doc.drawRightString(chart_x - 4, by - h / 2 - 2, name.replace("_", " "))
            self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
            self.doc.setFont("Helvetica", 5)
            self.doc.drawString(chart_x + bar_w + 4, by - h / 2 - 2, f"rank={rank}")

        # Public ceiling line
        ceiling_y = chart_y - 0 * (bar_h_base + 6) + bar_h_base
        self.doc.setStrokeColor(self._color((200, 0, 0)))
        self.doc.setLineWidth(1.5)
        self.doc.setDash(2, 2)
        self.doc.line(chart_x - 80, ceiling_y, chart_x + bar_w + 40, ceiling_y)
        self.doc.setDash()
        self.doc.setFillColor(self._color((200, 0, 0)))
        self.doc.setFont("Helvetica-Bold", 6)
        self.doc.drawString(chart_x + bar_w + 44, ceiling_y - 2, "Public Ceiling")

        self.y = chart_y - len(levels) * (bar_h_base + 6) - 20

    def _draw_ledger_table(self, segments: Sequence[RedactionSegment], decisions: Sequence[RedactionDecision]) -> None:
        self._ensure_space(120)
        self._draw_section_header("Redaction Ledger Summary (Source-Safe)")

        ledger = build_redaction_ledger(list(segments), list(decisions))
        col_names = ["Decision ID", "Segment", "Span", "Reason", "Valid"]
        col_widths = [80, 50, 60, 90, 40]
        row_h = 14
        table_x = self.left_margin

        # Header row
        self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
        self.doc.setFont("Helvetica-Bold", 6)
        cx = table_x
        for i, col in enumerate(col_names):
            self.doc.drawString(cx + 2, self.y - 8, col)
            cx += col_widths[i]
        self.y -= row_h

        for row in ledger[:12]:
            self._ensure_space(row_h + 4)
            cx = table_x
            values = [
                str(row.get("decision_id", ""))[:14],
                str(row.get("segment_id", "")),
                f"{row.get('start', '')}-{row.get('end', '')}",
                str(row.get("reason", "")),
                "Y" if row.get("valid_span") else "N",
            ]
            self.doc.setFillColor(self._color(self.background.text_rgb))
            self.doc.setFont("Helvetica", 6)
            for i, val in enumerate(values):
                self.doc.drawString(cx + 2, self.y - 8, val)
                cx += col_widths[i]
            self.y -= row_h

        self.y -= 10

    def _draw_review_gate(self, decisions: Sequence[RedactionDecision]) -> None:
        self._ensure_space(80)
        self._draw_section_header("Release Gate Status")

        gate_info = [
            ("Policy", "intelligence_release_review"),
            ("Required Roles", "originator, classification_reviewer, release_authority"),
            ("Minimum Approvals", "3"),
            ("Mosaic Threshold", "0.30"),
            ("Block Warnings", "True"),
            ("Reviewers", "originator-a (approve), classification-reviewer (approve), release-board (approve)"),
            ("Gate Status", "APPROVED"),
        ]
        for label, value in gate_info:
            self._ensure_space(16)
            self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
            self.doc.setFont("Helvetica-Bold", 7)
            self.doc.drawString(self.left_margin, self.y - 8, label)
            self.doc.setFillColor(self._color(self.background.text_rgb))
            self.doc.setFont("Helvetica", 7)
            self.doc.drawString(self.left_margin + 120, self.y - 8, value)
            self.y -= 14

        self.y -= 10

    def render(self, segments: Sequence[RedactionSegment], decisions: Sequence[RedactionDecision]) -> None:
        # invariant=1 pins CreationDate + /ID: the matrix's sha256 bindings need byte-reproducible runs.
        self.doc = self.Canvas(str(self.output_pdf), pagesize=self.pagesize, pageCompression=1, invariant=1)

        # Title page
        self._draw_title_page()

        # Content pages
        self._new_page()
        decision_map = _decisions_by_segment(decisions)

        for segment in segments:
            section_info = _SECTION_MAP.get(segment.id)
            if section_info:
                header, intro = section_info
                self._draw_section_header(header)
                if intro:
                    self._draw_body_text(intro, font_size=8)
                self._draw_segment_content(segment, decision_map.get(segment.id, ()))

            # Insert figures at key points
            if segment.id == "s5":
                self._draw_classification_chart()
            elif segment.id == "s7":
                self._draw_matrix_grid()
            elif segment.id == "s8":
                self._draw_security_methods_table()
            elif segment.id == "s9":
                self._draw_kmyth_flow_diagram()
            elif segment.id == "s11":
                self._draw_review_gate(decisions)
            elif segment.id == "s14":
                self._draw_ledger_table(segments, decisions)

        # Closing
        self._ensure_space(40)
        self._draw_section_header("Conclusion")
        self._draw_body_text(
            "This exemplar confirms that disclosure control can be decomposed into orthogonal concerns: "
            "text-level audit, visual presentation, steganographic provenance, and hardware-backed sealing. "
            "Each concern is independently configurable and verifiable. The sixteen-variant visual proof "
            "matrix, nine steganographic security methods, and thirty-two Kmyth TPM .ski sidecars demonstrate "
            "a reproducible, source-safe, and auditable release pipeline.",
            font_size=9,
        )

        self._draw_footer()
        self.doc.save()


def _draw_segment(
    doc: Any,
    segment: RedactionSegment,
    decisions: Sequence[RedactionDecision],
    *,
    x: float,
    y: float,
    max_width: float,
    style: RedactionVisualProfile,
    background: PDFBackgroundProfile,
    color_factory: Any,
    string_width: Any,
) -> float:
    redact_text(segment.text, list(decisions))
    cursor_x = x
    cursor_y = y
    font_name = "Helvetica"
    font_size = 10
    line_height = 14
    doc.setFont(font_name, font_size)
    for kind, value in _redaction_parts(segment.text, decisions):
        if kind == "text":
            for token in _split_keep_spaces(value):
                token_width = string_width(token, font_name, font_size)
                if cursor_x + token_width > x + max_width:
                    cursor_x = x
                    cursor_y -= line_height
                if background.blur_context and token.strip():
                    _draw_blurred_text(doc, token, cursor_x, cursor_y, background, color_factory)
                else:
                    doc.setFillColor(color_factory(background.text_rgb))
                    doc.drawString(cursor_x, cursor_y, token)
                cursor_x += token_width
        else:
            box_width = max(58, min(150, len(value) * 5.2))
            if cursor_x + box_width > x + max_width:
                cursor_x = x
                cursor_y -= line_height
            _draw_redaction_box(doc, cursor_x, cursor_y - 2, box_width, style, color_factory)
            cursor_x += box_width + 5
    return cursor_y - line_height


def _draw_redaction_box(
    doc: Any,
    x: float,
    y: float,
    width: float,
    style: RedactionVisualProfile,
    color_factory: Any,
) -> None:
    doc.setStrokeColor(color_factory(style.border_rgb))
    doc.setFillColor(color_factory(style.fill_rgb))
    doc.rect(x, y - 2, width, 11, stroke=1, fill=1)
    doc.setFillColor(color_factory(style.text_rgb))
    doc.setFont("Helvetica-Bold", 5.5)
    if style.name == "blur":
        for offset in (0, 0.8, -0.8):
            doc.drawCentredString(x + width / 2 + offset, y + 1, style.token)
    elif style.name != "whiteout":
        doc.drawCentredString(x + width / 2, y + 1, style.token)


def _draw_blurred_text(
    doc: Any,
    text: str,
    x: float,
    y: float,
    background: PDFBackgroundProfile,
    color_factory: Any,
) -> None:
    doc.setFillColor(color_factory(background.subdued_text_rgb))
    doc.setFont("Helvetica", 10)
    for dx, dy in ((-0.6, 0), (0.6, 0), (0, 0.6), (0, -0.6)):
        doc.drawString(x + dx, y + dy, text)


def _redaction_parts(
    text: str,
    decisions: Sequence[RedactionDecision],
) -> tuple[tuple[str, str], ...]:
    parts: list[tuple[str, str]] = []
    cursor = 0
    for decision in sorted(decisions, key=lambda item: item.start):
        if cursor < decision.start:
            parts.append(("text", text[cursor : decision.start]))
        parts.append(("redaction", text[decision.start : decision.end]))
        cursor = decision.end
    if cursor < len(text):
        parts.append(("text", text[cursor:]))
    return tuple(parts)


def _split_keep_spaces(text: str) -> tuple[str, ...]:
    tokens: list[str] = []
    for word in text.split(" "):
        if not tokens:
            tokens.append(word)
        else:
            tokens.append(" " + word)
    return tuple(token for token in tokens if token)


def _decisions_by_segment(decisions: Sequence[RedactionDecision]) -> dict[str, list[RedactionDecision]]:
    grouped: dict[str, list[RedactionDecision]] = {}
    for decision in decisions:
        grouped.setdefault(decision.segment_id, []).append(decision)
    return grouped
