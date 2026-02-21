"""Literature mining utilities for Ento-Linguistic research.

This module provides functionality for collecting, processing, and analyzing
scientific literature related to entomology and ant biology.
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

try:
    from ..analysis.text_analysis import TextProcessor
except (ImportError, ValueError):
    from analysis.text_analysis import TextProcessor

# Infrastructure integration
try:
    repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    sys.path.insert(0, str(repo_root))
    from infrastructure.core import get_logger
    INFRASTRUCTURE_AVAILABLE = True
    logger = get_logger("ento_linguistics.literature_mining")
except ImportError:
    INFRASTRUCTURE_AVAILABLE = False
    logger = logging.getLogger("ento_linguistics.literature_mining")

__all__ = [
    "Publication",
    "LiteratureCorpus",
    "PubMedMiner",
    "ArXivMiner",
    "create_entomology_query",
    "mine_entomology_literature",
]


@dataclass
class Publication:
    """Represents a scientific publication.

    Attributes:
        title: Publication title
        authors: List of author names
        abstract: Publication abstract
        doi: Digital Object Identifier
        pmid: PubMed ID
        year: Publication year
        journal: Journal name
        keywords: List of keywords
        full_text: Full text if available
    """

    title: str
    authors: List[str]
    abstract: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    year: Optional[int] = None
    journal: Optional[str] = None
    keywords: List[str] = None
    full_text: Optional[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Publication":
        """Create from dictionary."""
        return cls(**data)


class LiteratureCorpus:
    """Collection of scientific publications for analysis.

    This class manages a corpus of publications, providing methods for
    loading, saving, and querying the literature database.
    """

    def __init__(self, publications: Optional[List[Publication]] = None):
        """Initialize corpus.

        Args:
            publications: Initial list of publications
        """
        self.publications = publications or []
        self.text_processor = TextProcessor()

    def add_publication(self, publication: Publication) -> None:
        """Add a publication to the corpus.

        Args:
            publication: Publication to add
        """
        self.publications.append(publication)

    def save_to_file(self, filepath: Path) -> None:
        """Save corpus to JSON file.

        Args:
            filepath: Path to save file
        """
        data = {
            "publications": [pub.to_dict() for pub in self.publications],
            "metadata": {
                "total_publications": len(self.publications),
                "creation_date": time.time(),
            },
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, filepath: Path) -> "LiteratureCorpus":
        """Load corpus from JSON file.

        Args:
            filepath: Path to load file

        Returns:
            Loaded corpus
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        publications = [
            Publication.from_dict(pub_data) for pub_data in data["publications"]
        ]
        return cls(publications)

    def get_text_corpus(self) -> List[str]:
        """Get all available text content from publications.

        Returns:
            List of text strings (titles, abstracts, full text)
        """
        texts = []
        for pub in self.publications:
            # Combine available text fields
            text_parts = []
            if pub.title:
                text_parts.append(pub.title)
            if pub.authors:
                text_parts.extend(pub.authors)
            if pub.abstract:
                text_parts.append(pub.abstract)
            if pub.full_text:
                text_parts.append(pub.full_text)

            if text_parts:
                texts.append(" ".join(text_parts))

        return texts

    def search_publications(self, query: str, field: str = "all") -> List[Publication]:
        """Search publications by text query.

        Args:
            query: Search query
            field: Field to search ('title', 'abstract', 'all')

        Returns:
            Matching publications
        """
        query_lower = query.lower()
        matches = []

        for pub in self.publications:
            if field == "title" or field == "all":
                if pub.title and query_lower in pub.title.lower():
                    matches.append(pub)
                    continue

            if field == "abstract" or field == "all":
                if pub.abstract and query_lower in pub.abstract.lower():
                    matches.append(pub)
                    continue

            if field == "authors" or field == "all":
                if pub.authors and any(
                    query_lower in author.lower() for author in pub.authors
                ):
                    matches.append(pub)
                    continue

        return matches

    def get_statistics(self) -> Dict[str, Any]:
        """Get corpus statistics.

        Returns:
            Dictionary with corpus statistics
        """
        years = [pub.year for pub in self.publications if pub.year]
        journals = [pub.journal for pub in self.publications if pub.journal]
        has_abstract = sum(1 for pub in self.publications if pub.abstract)
        has_full_text = sum(1 for pub in self.publications if pub.full_text)

        total_pubs = len(self.publications)
        return {
            "total_publications": total_pubs,
            "date_range": (min(years), max(years)) if years else None,
            "unique_journals": len(set(journals)),
            "publications_with_abstract": has_abstract,
            "publications_with_full_text": has_full_text,
            "avg_title_length": (
                sum(len(pub.title or "") for pub in self.publications) / total_pubs
                if total_pubs > 0
                else 0
            ),
            "total_keywords": sum(len(pub.keywords) for pub in self.publications),
        }


class PubMedMiner:
    """Interface to PubMed literature database.

    This class provides methods for searching and retrieving publications
    from PubMed, with focus on entomological literature. Includes caching
    to avoid redundant API calls for repeated searches.
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    EMAIL = "entolinguistic.research@example.com"  # Should be configured

    def __init__(self, email: Optional[str] = None, enable_cache: bool = True):
        """Initialize PubMed miner.

        Args:
            email: Email for NCBI API (required for heavy usage)
            enable_cache: Whether to cache search results to avoid redundant API calls
        """
        self.email = email or self.EMAIL
        self.enable_cache = enable_cache
        self._search_cache: Dict[str, List[str]] = {}  # Cache for search results

    def search(self, query: str, max_results: int = 100) -> List[str]:
        """Search PubMed and return PMIDs.

        Args:
            query: PubMed search query (must be non-empty)
            max_results: Maximum number of results to return (1-10000)

        Returns:
            List of PubMed IDs

        Raises:
            ValueError: If query is empty or max_results is invalid
        """
        # Input validation
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if not isinstance(max_results, int) or max_results < 1 or max_results > 10000:
            raise ValueError("max_results must be an integer between 1 and 10000")

        query = query.strip()

        # Check cache first
        cache_key = f"{query}:{max_results}"
        if self.enable_cache and cache_key in self._search_cache:
            return self._search_cache[cache_key][:max_results]

        # Construct search URL with proper URL encoding
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": min(max_results, 10000),  # API limit
            "retmode": "json",
        }
        search_url = f"{self.BASE_URL}esearch.fcgi?{urlencode(params)}"

        try:
            with urlopen(
                Request(search_url, headers={"User-Agent": "Python-EntoLinguistic"})
            ) as response:
                if response.status != 200:
                    logger.warning(f"PubMed API returned status {response.status}")
                    return []

                data = json.loads(response.read().decode("utf-8"))

            pmids = data.get("esearchresult", {}).get("idlist", [])
            if not isinstance(pmids, list):
                logger.warning(f"Unexpected PubMed response format: {type(pmids)}")
                return []

            result_pmids = pmids[:max_results]  # Ensure we don't exceed requested limit

            # Cache the result
            if self.enable_cache:
                self._search_cache[cache_key] = pmids  # Cache full results

            return result_pmids

        except (URLError, HTTPError) as e:
            logger.error(f"Network error searching PubMed: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from PubMed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching PubMed: {e}")
            return []

    def clear_cache(self) -> None:
        """Clear the search result cache."""
        self._search_cache.clear()

    def get_cache_size(self) -> int:
        """Get the number of cached search results."""
        return len(self._search_cache)

    def fetch_publications(self, pmids: List[str]) -> List[Publication]:
        """Fetch publication details for given PMIDs.

        Uses eSummary for metadata (title, authors, journal, year) and
        eFetch for abstract text, then merges the results.

        Args:
            pmids: List of PubMed IDs

        Returns:
            List of Publication objects
        """
        publications = []

        # Process in batches to avoid API limits
        batch_size = 20
        for i in range(0, len(pmids), batch_size):
            batch_pmids = pmids[i : i + batch_size]

            # Fetch metadata via eSummary
            batch_pubs = self._fetch_batch_summaries(batch_pmids)

            # Fetch abstracts via eFetch and merge
            abstracts = self._fetch_batch_abstracts(batch_pmids)
            for pub in batch_pubs:
                if pub.pmid and pub.pmid in abstracts and not pub.abstract:
                    pub.abstract = abstracts[pub.pmid]

            publications.extend(batch_pubs)

            # Respect API rate limits
            time.sleep(0.5)

        abstract_count = sum(1 for p in publications if p.abstract)
        logger.info(
            f"Fetched {len(publications)} publications, "
            f"{abstract_count} with abstracts"
        )
        return publications

    def _fetch_batch_summaries(self, pmids: List[str]) -> List[Publication]:
        """Fetch summaries for a batch of PMIDs.

        Args:
            pmids: Batch of PubMed IDs

        Returns:
            List of Publication objects
        """
        if not pmids:
            return []

        id_str = ",".join(pmids)
        summary_url = (
            f"{self.BASE_URL}esummary.fcgi?" f"db=pubmed&id={id_str}&retmode=json"
        )

        try:
            with urlopen(
                Request(summary_url, headers={"User-Agent": "Python-EntoLinguistic"})
            ) as response:
                data = json.loads(response.read().decode("utf-8"))

            publications = []
            for pmid in pmids:
                if pmid in data.get("result", {}):
                    pub_data = data["result"][pmid]
                    publication = self._parse_pubmed_summary(pub_data)
                    if publication:
                        publications.append(publication)

            return publications

        except (URLError, HTTPError, json.JSONDecodeError) as e:
            logger.error(f"Error fetching PubMed summaries: {e}")
            return []

    def _fetch_batch_abstracts(self, pmids: List[str]) -> Dict[str, str]:
        """Fetch abstracts for a batch of PMIDs using eFetch API.

        The eSummary API does not return abstract text. This method uses
        eFetch with XML output to retrieve actual abstract content.

        Args:
            pmids: Batch of PubMed IDs

        Returns:
            Dictionary mapping PMID to abstract text
        """
        if not pmids:
            return {}

        id_str = ",".join(pmids)
        fetch_url = (
            f"{self.BASE_URL}efetch.fcgi?"
            f"db=pubmed&id={id_str}&rettype=abstract&retmode=xml"
        )

        try:
            with urlopen(
                Request(fetch_url, headers={"User-Agent": "Python-EntoLinguistic"})
            ) as response:
                content = response.read().decode("utf-8")

            root = ET.fromstring(content)
            abstracts = {}

            for article in root.findall(".//PubmedArticle"):
                # Extract PMID
                pmid_elem = article.find(".//PMID")
                if pmid_elem is None:
                    continue
                pmid = pmid_elem.text

                # Extract abstract text (may have multiple AbstractText elements)
                abstract_parts = []
                for abs_text in article.findall(".//AbstractText"):
                    label = abs_text.get("Label", "")
                    text = abs_text.text or ""
                    # Handle mixed content (text + child elements)
                    if abs_text.itertext():
                        text = "".join(abs_text.itertext()).strip()
                    if label and text:
                        abstract_parts.append(f"{label}: {text}")
                    elif text:
                        abstract_parts.append(text)

                if abstract_parts:
                    abstracts[pmid] = " ".join(abstract_parts)

            logger.info(
                f"eFetch retrieved {len(abstracts)} abstracts "
                f"from {len(pmids)} PMIDs"
            )
            return abstracts

        except (URLError, HTTPError, ET.ParseError) as e:
            logger.error(f"Error fetching PubMed abstracts via eFetch: {e}")
            return {}

    def _parse_pubmed_summary(self, data: Dict[str, Any]) -> Optional[Publication]:
        """Parse PubMed summary data into Publication object.

        Args:
            data: PubMed summary data

        Returns:
            Publication object or None if parsing fails
        """
        try:
            # Extract basic information
            title = data.get("title", "")
            if not title:
                return None

            # Parse authors
            authors = []
            author_list = data.get("authors", [])
            if author_list:
                for author in author_list:
                    name = author.get("name", "")
                    if name:
                        authors.append(name)

            # Extract other fields
            abstract = data.get("abstract", "")
            doi = (
                data.get("elocationid", "")
                if "DOI:" in str(data.get("elocationid", ""))
                else None
            )
            if doi and doi.startswith("DOI: "):
                doi = doi[5:]

            year = None
            pubdate = data.get("pubdate", "")
            if pubdate:
                year_match = re.search(r"\b(19|20)\d{2}\b", pubdate)
                if year_match:
                    year = int(year_match.group())

            journal = data.get("fulljournalname", data.get("source", ""))

            return Publication(
                title=title,
                authors=authors,
                abstract=abstract if abstract else None,
                doi=doi,
                pmid=data.get("uid"),
                year=year,
                journal=journal,
            )

        except Exception as e:
            logger.error(f"Error parsing PubMed data: {e}")
            return None


class ArXivMiner:
    """Interface to arXiv preprint server.

    This class provides methods for searching and retrieving preprints
    from arXiv, focusing on biology and entomology papers.
    """

    BASE_URL = "http://export.arxiv.org/api/query?"

    def __init__(self):
        """Initialize arXiv miner."""
        pass

    def search(self, query: str, max_results: int = 100) -> List[Publication]:
        """Search arXiv and return publications.

        Args:
            query: arXiv search query
            max_results: Maximum number of results

        Returns:
            List of Publication objects
        """
        search_url = (
            f"{self.BASE_URL}search_query={quote(query)}&"
            f"start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
        )

        try:
            with urlopen(
                Request(search_url, headers={"User-Agent": "Python-EntoLinguistic"})
            ) as response:
                content = response.read().decode("utf-8")

            # Parse XML response
            root = ET.fromstring(content)
            publications = []

            # Namespace for arXiv XML
            ns = {"arxiv": "http://www.w3.org/2005/Atom"}

            for entry in root.findall("arxiv:entry", ns):
                publication = self._parse_arxiv_entry(entry, ns)
                if publication:
                    publications.append(publication)

            return publications

        except (URLError, HTTPError, ET.ParseError) as e:
            logger.error(f"Error searching arXiv: {e}")
            return []

    def _parse_arxiv_entry(
        self, entry: ET.Element, ns: Dict[str, str]
    ) -> Optional[Publication]:
        """Parse arXiv entry into Publication object.

        Args:
            entry: XML entry element
            ns: XML namespace dictionary

        Returns:
            Publication object or None
        """
        try:
            # Extract title
            title_elem = entry.find("arxiv:title", ns)
            title = title_elem.text.strip() if title_elem is not None else ""
            if not title:
                return None

            # Extract authors
            authors = []
            author_elements = entry.findall("arxiv:author", ns)
            for author_elem in author_elements:
                name_elem = author_elem.find("arxiv:name", ns)
                if name_elem is not None:
                    authors.append(name_elem.text.strip())

            # Extract abstract
            summary_elem = entry.find("arxiv:summary", ns)
            abstract = summary_elem.text.strip() if summary_elem is not None else None

            # Extract DOI if available
            doi = None
            doi_elem = entry.find("arxiv:doi", ns)
            if doi_elem is not None:
                doi = doi_elem.text.strip()

            # Extract publication date
            year = None
            published_elem = entry.find("arxiv:published", ns)
            if published_elem is not None:
                date_str = published_elem.text.strip()
                year_match = re.search(r"\b(19|20)\d{2}\b", date_str)
                if year_match:
                    year = int(year_match.group())

            return Publication(
                title=title,
                authors=authors,
                abstract=abstract,
                doi=doi,
                year=year,
                journal="arXiv",
            )

        except Exception as e:
            logger.error(f"Error parsing arXiv entry: {e}")
            return None


def create_entomology_query() -> str:
    """Create a PubMed query for entomological literature.

    Returns:
        PubMed search query string
    """
    # Focus on ants and social insects
    terms = [
        "ants",
        "Formicidae",
        "Hymenoptera",
        "eusocial",
        "eusociality",
        "social insects",
        "colony",
        "nest",
        "foraging",
        "division of labor",
    ]

    return " OR ".join(f'"{term}"' for term in terms) + " AND (English[Language])"


def mine_entomology_literature(max_results: int = 1000) -> LiteratureCorpus:
    """Mine entomological literature from multiple sources.

    Args:
        max_results: Maximum publications to retrieve

    Returns:
        LiteratureCorpus with collected publications
    """
    corpus = LiteratureCorpus()

    # PubMed search
    pubmed_miner = PubMedMiner()
    query = create_entomology_query()

    logger.info(f"Searching PubMed with query: {query}")
    pmids = pubmed_miner.search(query, max_results=max_results)
    logger.info(f"Found {len(pmids)} PubMed results")

    if pmids:
        # Fetch up to max_results publications
        publications = pubmed_miner.fetch_publications(pmids[:max_results])
        for pub in publications:
            corpus.add_publication(pub)

    # arXiv search
    arxiv_miner = ArXivMiner()
    arxiv_query = "cat:q-bio.PE OR cat:q-bio.QM"  # Quantitative biology categories

    logger.info("Searching arXiv...")
    # Use full max_results for arXiv as well
    arxiv_pubs = arxiv_miner.search(arxiv_query, max_results=max_results)
    logger.info(f"Found {len(arxiv_pubs)} arXiv results")

    # Filter for entomology-related papers
    entomology_keywords = {
        "ant",
        "ants",
        "formicidae",
        "eusocial",
        "colony",
        "social insect",
    }
    filtered_arxiv = []
    for pub in arxiv_pubs:
        text = f"{pub.title} {pub.abstract or ''}".lower()
        if any(keyword in text for keyword in entomology_keywords):
            filtered_arxiv.append(pub)

    logger.info(f"Filtered to {len(filtered_arxiv)} entomology-related arXiv papers")

    for pub in filtered_arxiv:
        corpus.add_publication(pub)

    return corpus
