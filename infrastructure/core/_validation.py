"""Security input validation: file paths, filenames, and content size checks.

Extracted from security.py for single-responsibility. Import via security.py
for backwards compatibility.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from infrastructure.core.exceptions import SecurityViolation


class SecurityValidator:
    """Comprehensive input validation and security checks."""

    # Dangerous patterns to block — class-level constant, built once at class definition.
    # \b anchors prevent substring false-positives (e.g. "hexec" won't match "exec").
    # \s* between identifier and ( catches evasion via whitespace (e.g. "exec (").
    _DANGEROUS_PATTERNS: tuple[str, ...] = (
        # System prompt injection — exact injected phrases
        r"(?i)system\s*prompt\s*[:=]",
        r"(?i)\bignore\s+previous\s+instructions\b",
        r"(?i)\boverride\s+system\s+prompt\b",
        r"(?i)change\s+your\s+persona",
        # Python code execution — built-ins and subprocess (\b anchors to identifier boundary)
        r"(?i)\bexec\s*\(|\beval\s*\(|\bsubprocess\.\w|\bos\.system\s*\(",
        r"(?i)\bimport\s+os\b|\bimport\s+subprocess\b",
        r"(?i)shell\s*[:=]|bash\s*[:=]|cmd\s*[:=]",
        # File system access — open/file builtins and path libraries
        r"(?i)\bopen\s*\(|\bfile\s*\(|\bpathlib\.\w|\bos\.path\.\w",
        r"(?i)\bread\s+file\b|\bwrite\s+file\b|\bdelete\s+file\b",
        # Network access — library prefixes (\b prevents partial matches like "urllib2")
        r"(?i)\brequests\.\w|\burllib\.\w|\bsocket\.\w|\bhttps?://",
        r"(?i)connect\s+to|download\s+from|upload\s+to",
        # SQL injection — DML/DDL keywords (\b on both sides reduces false positives)
        r"(?i)\b(select|insert|update|delete|drop|create)\b\s+.*\bfrom\b",
        r"(?i)union\s+select|information_schema",
        # XSS — HTML injection tags ([\s>/] prevents matching "<scripted" etc.)
        r"(?i)<script[\s>/]|<iframe[\s>/]|<object[\s>/]|<embed[\s>/]",
        r"(?i)\bon\w+\s*=|javascript:|vbscript:",
        # LaTeX injection — commands that read/write files or include external content
        r"\\input\s*\{|\\include\s*\{|\\usepackage\s*[\[{]|\\newcommand\s*\{",
        r"\\write\s*\d|\\read\s*\d|\\openout\s*\d|\\openin\s*\d",
    )

    def __init__(self) -> None:
        # Maximum sizes for different input types
        self.limits = {
            "prompt_length": 100000,  # Max LLM prompt length
            "filename_length": 255,  # Max filename length
            "path_length": 4096,  # Max path length
            "content_size": 50 * 1024 * 1024,  # 50MB max content size
        }
        self.dangerous_patterns = self._DANGEROUS_PATTERNS

    def validate_file_path(self, path: str | Path) -> Path:
        """Validate file path for security.

        Raises:
            SecurityViolation: If path is unsafe
        """
        path_obj = Path(path)

        if ".." in str(path):
            raise SecurityViolation("Directory traversal detected")

        try:
            resolved = path_obj.resolve()
        except (OSError, RuntimeError) as e:
            raise SecurityViolation("Invalid path") from e

        if len(str(path)) > self.limits["path_length"]:
            raise SecurityViolation("Path too long")

        return resolved

    def validate_filename(self, filename: str) -> str:
        """Validate and sanitize filename.

        Args:
            filename: Filename to validate

        Returns:
            Sanitized filename

        Raises:
            SecurityViolation: If filename is unsafe
        """
        if not filename or not isinstance(filename, str):
            raise SecurityViolation("Invalid filename")

        if len(filename) > self.limits["filename_length"]:
            raise SecurityViolation("Filename too long")

        sanitized = re.sub(r'[<>:"|?*\x00-\x1f\x7f-\x9f]', "_", filename)
        sanitized = re.sub(r"[\/\\]", "_", sanitized)

        if not sanitized.strip():
            sanitized = "unnamed_file"

        return sanitized

    def validate_content_size(self, content: bytes) -> bytes:
        """Validate content size.

        Args:
            content: Content to validate

        Returns:
            Content if size is acceptable

        Raises:
            SecurityViolation: If content is too large
        """
        if len(content) > self.limits["content_size"]:
            raise SecurityViolation(
                f"Content too large: {len(content)} > {self.limits['content_size']}"
            )
        return content

    def _sanitize_html(self, text: str) -> str:
        return html.escape(text, quote=True)

    def _normalize_whitespace(self, text: str) -> str:
        text = re.sub(r" +", " ", text)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        return text.strip()
