"""Link audit skip policies for markdown validation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnchorLinkPolicy:
    """Rules for when anchor links should skip heading validation."""

    manuscript_path_token: str = "manuscript"
    cross_ref_prefixes: tuple[str, ...] = ("fig:", "sec:", "eq:", "table:", "tab:")
    common_sections: tuple[str, ...] = (
        "methodology",
        "experimental_results",
        "discussion",
        "conclusion",
        "results",
    )

    def should_skip(self, file_key: str, target: str) -> bool:
        """Return True if the path should be skipped by the link policy."""
        anchor = target.lstrip("#")
        if self.manuscript_path_token in file_key:
            return True
        if any(anchor.startswith(prefix) for prefix in self.cross_ref_prefixes):
            return True
        if anchor in self.common_sections:
            return True
        return any(section in anchor.lower() for section in self.common_sections)


@dataclass(frozen=True)
class FileReferencePolicy:
    """Rules for when file references should skip existence checks."""

    generated_output_tokens: tuple[str, ...] = ("output/", "/output/")

    def should_skip(self, target: str) -> bool:
        """Return True if the path should be skipped by the link policy."""
        return any(token in target for token in self.generated_output_tokens)


DEFAULT_ANCHOR_POLICY = AnchorLinkPolicy()
DEFAULT_FILE_REF_POLICY = FileReferencePolicy()
