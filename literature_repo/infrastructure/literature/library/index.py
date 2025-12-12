"""Library index management for tracking papers and metadata.

Provides a JSON-based index for comprehensive tracking of all papers
in the library, including download status and metadata.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from infrastructure.core.exceptions import FileOperationError
from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.core.config import LiteratureConfig

logger = get_logger(__name__)


@dataclass
class LibraryEntry:
    """Represents a paper in the library index.
    
    Attributes:
        citation_key: Unique key for citing this paper (matches BibTeX and PDF filename).
        title: Paper title.
        authors: List of author names.
        year: Publication year.
        doi: Digital Object Identifier if available.
        source: Source database (arxiv, semanticscholar, etc.).
        url: URL to the paper.
        pdf_path: Relative path to downloaded PDF, None if not downloaded.
        added_date: ISO format date when entry was added.
        abstract: Paper abstract.
        venue: Publication venue/journal.
        citation_count: Number of citations if available.
        metadata: Additional metadata from source.
    """
    citation_key: str
    title: str
    authors: List[str]
    year: Optional[int] = None
    doi: Optional[str] = None
    source: str = "unknown"
    url: str = ""
    pdf_path: Optional[str] = None
    added_date: str = ""
    abstract: str = ""
    venue: Optional[str] = None
    citation_count: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LibraryEntry:
        """Create entry from dictionary.
        
        Handles missing fields gracefully by providing defaults for required fields.
        """
        # Provide defaults for required fields if missing
        defaults = {
            "title": data.get("title", "No title"),
            "citation_key": data.get("citation_key", "unknown"),
            "authors": data.get("authors", [])
        }
        # Merge defaults with provided data (data takes precedence)
        merged_data = {**defaults, **data}
        return cls(**merged_data)


class LibraryIndex:
    """Manages the library index file for tracking papers.
    
    The index is stored as a JSON file containing all papers added to the
    library, with metadata for each entry including download status.
    """

    def __init__(self, config: LiteratureConfig):
        """Initialize library index.
        
        Args:
            config: Literature configuration containing index file path.
        """
        self.config = config
        self.index_path = Path(config.library_index_file)
        self._entries: Dict[str, LibraryEntry] = {}
        self._load_index()

    def _load_index(self) -> None:
        """Load index from disk if it exists."""
        if self.index_path.exists():
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, entry_data in data.get("entries", {}).items():
                        self._entries[key] = LibraryEntry.from_dict(entry_data)
                logger.info(f"Loaded {len(self._entries)} entries from library index")
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load library index: {e}")
                self._entries = {}

    def _save_index(self) -> None:
        """Save index to disk."""
        try:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "version": "1.0",
                "updated": datetime.now().isoformat(),
                "count": len(self._entries),
                "entries": {key: entry.to_dict() for key, entry in self._entries.items()}
            }
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved library index with {len(self._entries)} entries")
        except OSError as e:
            raise FileOperationError(
                f"Failed to save library index: {e}",
                context={"path": str(self.index_path)}
            )

    def generate_citation_key(self, title: str, authors: List[str], year: Optional[int]) -> str:
        """Generate a consistent citation key.
        
        Format: authorYYYYword (e.g., smith2024machine)
        
        Args:
            title: Paper title.
            authors: List of author names.
            year: Publication year.
            
        Returns:
            Citation key string.
        """
        # Get first author's last name
        if authors:
            first_author = authors[0]
            # Handle "First Last" or "Last, First" formats
            parts = first_author.replace(",", " ").split()
            author_part = parts[-1].lower() if parts else "anonymous"
        else:
            author_part = "anonymous"
        
        # Sanitize author part
        author_part = "".join(c for c in author_part if c.isalnum())
        
        # Year part
        year_part = str(year) if year else "nodate"
        
        # First significant word from title
        title_words = title.lower().split()
        # Skip common words
        skip_words = {"a", "an", "the", "on", "in", "of", "for", "to", "and", "with"}
        title_word = "paper"
        for word in title_words:
            clean_word = "".join(c for c in word if c.isalnum())
            if clean_word and clean_word not in skip_words:
                title_word = clean_word
                break
        
        base_key = f"{author_part}{year_part}{title_word}"
        
        # Handle duplicates by adding suffix
        key = base_key
        suffix = 1
        while key in self._entries:
            existing = self._entries[key]
            # Check if it's the same paper (same DOI or exact title match)
            if existing.title.lower().strip() == title.lower().strip():
                return key  # Same paper, return existing key
            suffix += 1
            key = f"{base_key}{suffix}"
        
        return key

    def add_entry(
        self,
        title: str,
        authors: List[str],
        year: Optional[int] = None,
        doi: Optional[str] = None,
        source: str = "unknown",
        url: str = "",
        abstract: str = "",
        venue: Optional[str] = None,
        citation_count: Optional[int] = None,
        pdf_url: Optional[str] = None,
        **metadata: Any
    ) -> str:
        """Add or update an entry in the library index.
        
        Args:
            title: Paper title.
            authors: List of author names.
            year: Publication year.
            doi: Digital Object Identifier.
            source: Source database.
            url: URL to paper.
            abstract: Paper abstract.
            venue: Publication venue.
            citation_count: Citation count.
            pdf_url: URL to PDF (stored in metadata).
            **metadata: Additional metadata.
            
        Returns:
            Citation key for the entry.
        """
        # Check for existing entry by DOI
        if doi:
            for key, entry in self._entries.items():
                if entry.doi == doi:
                    logger.debug(f"Entry already exists (DOI match): {key}")
                    return key
        
        # Check for existing entry by exact title
        norm_title = title.lower().strip()
        for key, entry in self._entries.items():
            if entry.title.lower().strip() == norm_title:
                logger.debug(f"Entry already exists (title match): {key}")
                return key
        
        # Generate citation key
        citation_key = self.generate_citation_key(title, authors, year)
        
        # Check if already exists (same key means same paper)
        if citation_key in self._entries:
            logger.debug(f"Entry already exists: {citation_key} (skipping)")
            return citation_key
        
        # Store pdf_url in metadata
        if pdf_url:
            metadata["pdf_url"] = pdf_url
        
        # Create entry
        entry = LibraryEntry(
            citation_key=citation_key,
            title=title,
            authors=authors,
            year=year,
            doi=doi,
            source=source,
            url=url,
            pdf_path=None,
            added_date=datetime.now().isoformat(),
            abstract=abstract,
            venue=venue,
            citation_count=citation_count,
            metadata=metadata
        )
        
        self._entries[citation_key] = entry
        self._save_index()
        logger.info(f"Added entry to library: {citation_key}")
        
        return citation_key

    def update_pdf_path(self, citation_key: str, pdf_path: str) -> None:
        """Update the PDF path for an entry.
        
        Args:
            citation_key: Citation key of the entry.
            pdf_path: Relative path to the downloaded PDF.
        """
        if citation_key not in self._entries:
            logger.warning(f"Entry not found: {citation_key}")
            return
        
        self._entries[citation_key].pdf_path = pdf_path
        self._save_index()
        logger.debug(f"Updated PDF path for {citation_key}: {pdf_path}")

    def get_entry(self, citation_key: str) -> Optional[LibraryEntry]:
        """Get an entry by citation key.
        
        Args:
            citation_key: Citation key to look up.
            
        Returns:
            LibraryEntry if found, None otherwise.
        """
        return self._entries.get(citation_key)

    def list_entries(self) -> List[LibraryEntry]:
        """Get all entries in the library.
        
        Returns:
            List of all library entries.
        """
        return list(self._entries.values())

    def has_paper(self, doi: Optional[str] = None, title: Optional[str] = None) -> bool:
        """Check if a paper exists in the library.
        
        Args:
            doi: DOI to check.
            title: Title to check (case-insensitive).
            
        Returns:
            True if paper exists in library.
        """
        if doi:
            for entry in self._entries.values():
                if entry.doi == doi:
                    return True
        
        if title:
            norm_title = title.lower().strip()
            for entry in self._entries.values():
                if entry.title.lower().strip() == norm_title:
                    return True
        
        return False

    def export_json(self, path: Optional[Path] = None) -> Path:
        """Export the library to a JSON file.
        
        Args:
            path: Output path. Defaults to library index path.
            
        Returns:
            Path to exported file.
        """
        export_path = path or self.index_path
        
        try:
            export_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "version": "1.0",
                "exported": datetime.now().isoformat(),
                "count": len(self._entries),
                "entries": [entry.to_dict() for entry in self._entries.values()]
            }
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Exported library to {export_path}")
            return export_path
        except OSError as e:
            raise FileOperationError(
                f"Failed to export library: {e}",
                context={"path": str(export_path)}
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive library statistics.
        
        Returns:
            Dictionary with comprehensive library statistics including:
            - Total entries, PDFs, summaries
            - Source distribution
            - Year distribution
            - Completion percentages
            - Disk usage estimates
        """
        entries = list(self._entries.values())
        
        sources = {}
        years = {}
        downloaded = 0
        with_summaries = 0
        
        # Check for summaries
        summaries_dir = Path("data/summaries")
        if summaries_dir.exists():
            summary_files = set(f.stem.replace("_summary", "") for f in summaries_dir.glob("*_summary.md"))
        else:
            summary_files = set()
        
        # Check PDF directory size
        pdf_dir = Path("data/pdfs")
        pdf_size = 0
        pdf_count_filesystem = 0
        if pdf_dir.exists():
            for pdf_file in pdf_dir.glob("*.pdf"):
                if pdf_file.is_file():
                    pdf_size += pdf_file.stat().st_size
                    pdf_count_filesystem += 1
        
        for entry in entries:
            # Count by source
            sources[entry.source] = sources.get(entry.source, 0) + 1
            
            # Count by year
            if entry.year:
                years[entry.year] = years.get(entry.year, 0) + 1
            
            # Count downloads
            if entry.pdf_path:
                pdf_path = Path(entry.pdf_path)
                if not pdf_path.is_absolute():
                    pdf_path = Path("literature") / pdf_path
                if pdf_path.exists():
                    downloaded += 1
            
            # Count summaries
            if entry.citation_key in summary_files:
                with_summaries += 1
        
        total = len(entries)
        pdf_percentage = (downloaded / total * 100) if total > 0 else 0.0
        summary_percentage = (with_summaries / total * 100) if total > 0 else 0.0
        
        return {
            "total_entries": total,
            "downloaded_pdfs": downloaded,
            "pdf_percentage": pdf_percentage,
            "summaries_generated": with_summaries,
            "summary_percentage": summary_percentage,
            "pdf_count_filesystem": pdf_count_filesystem,
            "pdf_size_bytes": pdf_size,
            "pdf_size_mb": round(pdf_size / (1024 * 1024), 2),
            "sources": sources,
            "years": dict(sorted(years.items(), reverse=True)),
            "oldest_year": min(years.keys()) if years else None,
            "newest_year": max(years.keys()) if years else None,
            "recent_additions": self._get_recent_additions(5),
        }
    
    def _get_recent_additions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most recently added papers.
        
        Args:
            limit: Maximum number of recent additions to return.
            
        Returns:
            List of recent entry dictionaries with citation_key, title, and added_date.
        """
        entries = list(self._entries.values())
        sorted_entries = sorted(entries, key=lambda e: e.added_date, reverse=True)
        
        return [
            {
                "citation_key": entry.citation_key,
                "title": entry.title[:60] + "..." if len(entry.title) > 60 else entry.title,
                "added_date": entry.added_date,
                "has_pdf": entry.pdf_path is not None
            }
            for entry in sorted_entries[:limit]
        ]

    def remove_entry(self, citation_key: str) -> bool:
        """Remove an entry from the library index.

        Args:
            citation_key: Citation key of the entry to remove.

        Returns:
            True if entry was removed, False if not found.
        """
        if citation_key in self._entries:
            del self._entries[citation_key]
            self._save_index()
            logger.info(f"Removed entry from library: {citation_key}")
            return True
        else:
            logger.warning(f"Entry not found for removal: {citation_key}")
            return False

    def get_entries_without_pdf(self) -> List[LibraryEntry]:
        """Get all entries that do not have a PDF file.

        Returns:
            List of LibraryEntry objects that are missing PDF files.
        """
        entries_without_pdf = []
        for entry in self._entries.values():
            if not entry.pdf_path:
                entries_without_pdf.append(entry)
            else:
                # PDF paths in library are stored relative to project root
                # Always resolve relative to project root
                pdf_path = Path(entry.pdf_path)
                if not pdf_path.exists():
                    entries_without_pdf.append(entry)

        return entries_without_pdf

    def remove_entries_without_pdf(self) -> int:
        """Remove all entries that do not have PDF files.

        Returns:
            Number of entries removed.
        """
        entries_to_remove = self.get_entries_without_pdf()
        removed_count = 0

        for entry in entries_to_remove:
            if self.remove_entry(entry.citation_key):
                removed_count += 1

        logger.info(f"Removed {removed_count} entries without PDFs from library")
        return removed_count

