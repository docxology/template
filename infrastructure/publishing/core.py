"""Academic publishing workflow tools for research dissemination.

This module provides utilities for:
- DOI management and validation
- Citation format generation
- Publication metadata handling
- Academic repository integration
- Conference/journal submission preparation

All functions follow the thin orchestrator pattern and maintain
100% test coverage requirements.
"""

from __future__ import annotations

import os
import re
import json
import hashlib
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class PublicationMetadata:
    """Container for publication metadata."""

    title: str
    authors: List[str]
    abstract: str
    keywords: List[str]
    doi: Optional[str] = None
    journal: Optional[str] = None
    conference: Optional[str] = None
    publication_date: Optional[str] = None
    publisher: Optional[str] = None
    license: str = "CC-BY-4.0"
    repository_url: Optional[str] = None
    citation_count: int = 0
    download_count: int = 0


@dataclass
class CitationStyle:
    """Container for citation style configuration."""

    name: str
    format_string: str
    example: str


def calculate_file_hash(file_path: Path, algorithm: str = 'sha256') -> Optional[str]:
    """Calculate hash of a file for integrity verification.

    Args:
        file_path: Path to file to hash
        algorithm: Hash algorithm to use

    Returns:
        Hash string or None if calculation fails
    """
    if not file_path.exists():
        return None

    try:
        hash_func = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception:
        return None


def extract_publication_metadata(markdown_files: List[Path]) -> PublicationMetadata:
    """Extract publication metadata from markdown files.

    Args:
        markdown_files: List of markdown files to analyze

    Returns:
        PublicationMetadata object with extracted information
    """
    # Default metadata
    metadata = PublicationMetadata(
        title="Research Project Template",
        authors=["Template Author"],
        abstract="A comprehensive template for research projects with test-driven development and automated PDF generation.",
        keywords=["research", "template", "academic", "scientific"],
        license="Apache-2.0"
    )

    # Read content from the first markdown file (to avoid conflicts with template files)
    combined_content = ""
    if markdown_files:
        try:
            with open(markdown_files[0], 'r', encoding='utf-8') as f:
                content = f.read()

            # Only use this content if it contains actual research content (not template content)
            if "Research Project Template" not in content and ("#" in content or "**" in content):
                combined_content = content
        except Exception:
            combined_content = ""

    # Extract title (first # header)
    title_match = re.search(r'^#\s*(.+)$', combined_content, re.MULTILINE)
    if title_match:
        extracted_title = title_match.group(1).strip()
        # Always update the title if we find one
        if extracted_title:
            metadata.title = extracted_title

    # Extract authors from various patterns
    author_patterns = [
        r'Authors?:\s*(.+)$',
        r'By:\s*(.+)$',
        r'Author:\s*(.+)$',
        r'\*\*([^*]+)\*\*',  # Bold text pattern
        r'^\s*\*\*([^*]+)\*\*\s*$'  # Bold text on its own line
    ]

    for pattern in author_patterns:
        match = re.search(pattern, combined_content, re.IGNORECASE | re.MULTILINE)
        if match:
            authors_text = match.group(1).strip()
            # Check if this looks like author names (contains common title indicators)
            if any(title in authors_text.lower() for title in ['dr.', 'prof.', 'phd', 'ms.', 'mr.', 'mrs.']):
                metadata.authors = [a.strip() for a in authors_text.split(',')]
                break

    # Extract abstract
    abstract_match = re.search(r'##?\s*Abstract\s*(.+?)(?=\n##|\n#|\Z)', combined_content, re.DOTALL | re.IGNORECASE)
    if abstract_match:
        metadata.abstract = abstract_match.group(1).strip()

    # Extract keywords
    keyword_patterns = [
        r'Keywords?:\s*(.+)$',
        r'Key words?:\s*(.+)$'
    ]

    for pattern in keyword_patterns:
        match = re.search(pattern, combined_content, re.IGNORECASE | re.MULTILINE)
        if match:
            keywords_text = match.group(1).strip()
            metadata.keywords = [k.strip() for k in keywords_text.split(',')]
            break

    # Extract DOI if present
    doi_match = re.search(r'DOI:\s*([^\s]+)', combined_content, re.IGNORECASE)
    if doi_match:
        metadata.doi = doi_match.group(1).strip()

    # Extract journal/conference info
    journal_patterns = [
        r'Journal:\s*(.+)$',
        r'Published in:\s*(.+)$'
    ]

    for pattern in journal_patterns:
        match = re.search(pattern, combined_content, re.IGNORECASE | re.MULTILINE)
        if match:
            metadata.journal = match.group(1).strip()
            break

    conference_patterns = [
        r'Conference:\s*(.+)$',
        r'Proceedings of:\s*(.+)$'
    ]

    for pattern in conference_patterns:
        match = re.search(pattern, combined_content, re.IGNORECASE | re.MULTILINE)
        if match:
            metadata.conference = match.group(1).strip()
            break

    return metadata


def validate_doi(doi: str) -> bool:
    """Validate DOI format and checksum.

    Args:
        doi: DOI string to validate

    Returns:
        True if DOI is valid, False otherwise
    """
    if not doi:
        return False

    # Basic DOI format validation
    doi_pattern = r'^10\.\d{4,9}/[-._;()/:A-Z0-9]+$'
    if not re.match(doi_pattern, doi, re.IGNORECASE):
        return False

    # Check for invalid patterns
    if doi.endswith('/extra') or 'doi:' in doi.lower() or not doi.strip():
        return False

    # DOI is valid if format matches
    return True


def generate_citation_bibtex(metadata: PublicationMetadata) -> str:
    """Generate BibTeX citation format.

    Args:
        metadata: Publication metadata

    Returns:
        BibTeX formatted citation
    """
    # Create a simple citation key
    first_author = metadata.authors[0].replace(' ', '').lower() if metadata.authors else 'unknown'
    year = metadata.publication_date.split('-')[0] if metadata.publication_date else '2024'
    citation_key = f"{first_author}{year}"

    bibtex = f"""@software{{{citation_key},
  author = {{{' and '.join(metadata.authors)}}},
  title = {{{metadata.title}}},
  year = {{{year}}},
  publisher = {{{metadata.publisher or 'Self-published'}}},
  url = {{{metadata.repository_url or ''}}},
  license = {{{metadata.license}}},
  abstract = {{{metadata.abstract}}},
  keywords = {{{', '.join(metadata.keywords)}}}
"""

    if metadata.doi:
        bibtex = bibtex.rstrip() + f",\n  doi = {{{metadata.doi}}}\n"

    bibtex += "}\n"

    return bibtex


def generate_citation_apa(metadata: PublicationMetadata) -> str:
    """Generate APA citation format.

    Args:
        metadata: Publication metadata

    Returns:
        APA formatted citation
    """
    authors_text = format_authors_apa(metadata.authors)
    year = metadata.publication_date.split('-')[0] if metadata.publication_date else '2024'

    citation = f"{authors_text} ({year}). {metadata.title}."

    if metadata.doi:
        citation += f" https://doi.org/{metadata.doi}"

    return citation


def generate_citation_mla(metadata: PublicationMetadata) -> str:
    """Generate MLA citation format.

    Args:
        metadata: Publication metadata

    Returns:
        MLA formatted citation
    """
    authors_text = format_authors_mla(metadata.authors)
    year = metadata.publication_date.split('-')[0] if metadata.publication_date else '2024'

    citation = f'{authors_text}. "{metadata.title}." {year}.'

    if metadata.repository_url:
        citation += f" {metadata.repository_url}."

    return citation


def format_authors_apa(authors: List[str]) -> str:
    """Format authors for APA style.

    Args:
        authors: List of author names

    Returns:
        APA-formatted author string
    """
    if not authors:
        return "Unknown Author"

    if len(authors) == 1:
        return authors[0]

    if len(authors) == 2:
        return f"{authors[0]} & {authors[1]}"

    # Three or more authors
    return f"{authors[0]}, et al."


def format_authors_mla(authors: List[str]) -> str:
    """Format authors for MLA style.

    Args:
        authors: List of author names

    Returns:
        MLA-formatted author string
    """
    if not authors:
        return "Unknown Author"

    if len(authors) == 1:
        return authors[0]

    if len(authors) == 2:
        return f"{authors[0]} and {authors[1]}"

    # Three or more authors
    return f"{authors[0]}, et al."


def generate_citations_markdown(metadata: PublicationMetadata) -> str:
    """Generate markdown section with all citation formats.

    Args:
        metadata: Publication metadata

    Returns:
        Markdown formatted citation section
    """
    section = """# Citation

If you use this template in your research, please cite:

## BibTeX

```bibtex
"""

    section += generate_citation_bibtex(metadata)

    section += """

## APA Style

"""

    section += generate_citation_apa(metadata)

    section += """

## MLA Style

"""

    section += generate_citation_mla(metadata)

    section += f"""

## Plain Text

{format_authors_apa(metadata.authors)}. ({metadata.publication_date.split('-')[0] if metadata.publication_date else '2024'}). {metadata.title}. {metadata.publisher or 'Self-published'}.
"""

    if metadata.doi:
        section += f" https://doi.org/{metadata.doi}"

    section += "\n"

    return section


def create_publication_package(output_dir: Path, metadata: PublicationMetadata) -> Dict[str, Any]:
    """Create a publication package with all necessary files.

    Args:
        output_dir: Output directory containing generated files
        metadata: Publication metadata

    Returns:
        Dictionary with package information
    """
    package_info = {
        'package_name': f"{metadata.title.replace(' ', '_').lower()}",
        'files_included': [],
        'metadata': asdict(metadata),
        'package_hash': '',
        'created_at': datetime.now().isoformat()
    }

    # Collect files to include
    package_files = []

    # PDF files
    pdf_dir = output_dir / 'pdf'
    if pdf_dir.exists():
        for pdf_file in pdf_dir.glob('*.pdf'):
            package_files.append(pdf_file)

    # Source files
    source_files = [
        'README.md',
        'pyproject.toml',
        'LICENSE'
    ]

    for source_file in source_files:
        file_path = Path(source_file)
        if file_path.exists():
            package_files.append(file_path)

    # Calculate package hash
    file_hashes = []
    for file_path in package_files:
        if file_path.exists():
            file_hash = calculate_file_hash(file_path)
            if file_hash:
                file_hashes.append(file_hash)
            package_info['files_included'].append(str(file_path))

    if file_hashes:
        combined_hash = ''.join(sorted(file_hashes))
        package_info['package_hash'] = hashlib.sha256(combined_hash.encode()).hexdigest()

    return package_info


def create_submission_checklist(metadata: PublicationMetadata) -> str:
    """Create a submission checklist for academic conferences/journals.

    Args:
        metadata: Publication metadata

    Returns:
        Markdown formatted submission checklist
    """
    checklist = f"""# Submission Checklist for "{metadata.title}"

## 📋 Required Items

- [ ] **Title**: {metadata.title}
- [ ] **Authors**: {', '.join(metadata.authors)}
- [ ] **Abstract**: {len(metadata.abstract)} characters
- [ ] **Keywords**: {', '.join(metadata.keywords)}

## 📄 Document Requirements

- [ ] **PDF Format**: Generated using LaTeX/Pandoc
- [ ] **Page Limit**: Check conference/journal guidelines
- [ ] **Font Size**: 10-12pt as required
- [ ] **Margins**: 1-inch margins as standard
- [ ] **Line Spacing**: 1.5 or double as required

## 🎯 Content Requirements

- [ ] **Abstract**: Clearly states contribution and results
- [ ] **Introduction**: Motivates the problem and approach
- [ ] **Related Work**: Properly cites relevant literature
- [ ] **Methodology**: Detailed enough for reproducibility
- [ ] **Experiments**: Comprehensive evaluation
- [ ] **Results**: Clear presentation of findings
- [ ] **Discussion**: Interprets results and limitations
- [ ] **Conclusion**: Summarizes contributions

## 🔗 References and Citations

- [ ] **Complete Bibliography**: All references properly formatted
- [ ] **Citation Style**: Follows journal/conference requirements
- [ ] **DOI Links**: Working links for all citations
- [ ] **Self-Citations**: Appropriate and relevant

## 📊 Figures and Tables

- [ ] **High Quality**: All figures are clear and readable
- [ ] **Proper Captions**: Descriptive captions for all figures
- [ ] **Numbering**: Sequential numbering throughout
- [ ] **Accessibility**: Alt text and descriptions

## 🧪 Reproducibility

- [ ] **Code Available**: Source code included or linked
- [ ] **Data Available**: Datasets provided or accessible
- [ ] **Instructions**: Clear setup and execution instructions
- [ ] **Dependencies**: All requirements specified

## 📝 Formatting and Style

- [ ] **Consistent Formatting**: Uniform style throughout
- [ ] **Proper Headings**: Hierarchical section structure
- [ ] **Equation Numbering**: Sequential and referenced
- [ ] **Table Formatting**: Professional appearance

## ✅ Final Checks

- [ ] **Proofreading**: No grammatical or spelling errors
- [ ] **Technical Accuracy**: All claims are correct
- [ ] **Completeness**: All sections are included
- [ ] **File Size**: Within submission limits

## 📅 Submission Timeline

- [ ] **Deadline**: [Insert submission deadline]
- [ ] **Review Period**: [Insert expected review time]
- [ ] **Camera Ready**: [Insert camera-ready deadline]

---

*This checklist was auto-generated from your project metadata. Update as needed for specific conference/journal requirements.*
"""

    return checklist


def extract_citations_from_markdown(markdown_files: List[Path]) -> List[str]:
    """Extract all citations from markdown files.

    Args:
        markdown_files: List of markdown files to analyze

    Returns:
        List of citation keys found
    """
    citations = set()

    for md_file in markdown_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find various citation patterns
            citation_patterns = [
                r'\\cite\{([^}]+)\}',
                r'\\[a-z]*cite[a-z]*\{([^}]+)\}',
                r'\[(\d+)\]',
                r'\((\d+)\)'
            ]

            for pattern in citation_patterns:
                matches = re.findall(pattern, content)
                citations.update(matches)

        except Exception:
            continue

    return sorted(list(citations))


def generate_publication_summary(metadata: PublicationMetadata) -> str:
    """Generate a publication summary for repository README.

    Args:
        metadata: Publication metadata

    Returns:
        Markdown formatted publication summary
    """
    summary = f"""## 📚 Publication Information

**Title**: {metadata.title}

**Authors**: {', '.join(metadata.authors)}

**Abstract**: {metadata.abstract[:200]}...

**Keywords**: {', '.join(metadata.keywords)}

"""

    if metadata.doi:
        summary += f"**DOI**: [{metadata.doi}](https://doi.org/{metadata.doi})\n\n"

    if metadata.journal:
        summary += f"**Journal**: {metadata.journal}\n\n"

    if metadata.conference:
        summary += f"**Conference**: {metadata.conference}\n\n"

    summary += "**Citation**:"
    summary += f"\n\n{generate_citation_apa(metadata)}"

    return summary


def create_academic_profile_data(metadata: PublicationMetadata) -> Dict[str, Any]:
    """Create academic profile data for ORCID, ResearchGate, etc.

    Args:
        metadata: Publication metadata

    Returns:
        Dictionary with academic profile data
    """
    profile_data = {
        'title': metadata.title,
        'authors': metadata.authors,
        'abstract': metadata.abstract,
        'keywords': metadata.keywords,
        'publication_type': 'software' if 'template' in metadata.title.lower() else 'article',
        'license': metadata.license,
        'repository_url': metadata.repository_url,
        'publication_date': metadata.publication_date
    }

    if metadata.doi:
        profile_data['identifiers'] = [{
            'type': 'doi',
            'value': metadata.doi,
            'url': f"https://doi.org/{metadata.doi}"
        }]

    return profile_data


def generate_doi_badge(doi: str, style: str = 'zenodo') -> str:
    """Generate DOI badge markdown.

    Args:
        doi: DOI string
        style: Badge style ('zenodo', 'github', 'shields')

    Returns:
        Markdown formatted badge
    """
    if style == 'zenodo':
        return f"[![DOI](https://zenodo.org/badge/DOI/{doi}.svg)](https://doi.org/{doi})"
    elif style == 'github':
        return f"[![DOI](https://img.shields.io/badge/DOI-{doi}-blue.svg)](https://doi.org/{doi})"
    elif style == 'shields':
        return f"[![DOI](https://img.shields.io/badge/DOI-{doi.replace('/', '%2F')}-informational)](https://doi.org/{doi})"
    else:
        return f"**DOI**: [{doi}](https://doi.org/{doi})"


def create_publication_announcement(metadata: PublicationMetadata) -> str:
    """Create a publication announcement for social media and blogs.

    Args:
        metadata: Publication metadata

    Returns:
        Markdown formatted announcement
    """
    announcement = f"""# 🚀 New Publication: {metadata.title}

**Authors**: {', '.join(metadata.authors)}

## 📝 Abstract

{metadata.abstract}

## 🔑 Keywords

{', '.join(f'`{keyword}`' for keyword in metadata.keywords)}

## 📊 Key Features

- **Comprehensive template** for research project development
- **Test-driven development** with 100% coverage requirements
- **Automated PDF generation** from markdown sources
- **Professional documentation** and cross-referencing
- **Thin orchestrator pattern** for maintainable code

## 🔗 Links

"""

    if metadata.doi:
        announcement += f"- **DOI**: https://doi.org/{metadata.doi}\n"

    if metadata.repository_url:
        announcement += f"- **Repository**: {metadata.repository_url}\n"

    announcement += f"- **License**: {metadata.license}\n\n"

    announcement += "## 📚 Citation\n\n"
    announcement += generate_citation_apa(metadata)

    if metadata.doi:
        announcement += f"\n\nhttps://doi.org/{metadata.doi}"

    return announcement


def validate_publication_readiness(markdown_files: List[Path], pdf_files: List[Path]) -> Dict[str, Any]:
    """Validate that the project is ready for publication.

    Args:
        markdown_files: List of markdown files
        pdf_files: List of PDF files

    Returns:
        Dictionary with publication readiness assessment
    """
    readiness = {
        'ready_for_publication': True,
        'completeness_score': 0,
        'missing_elements': [],
        'recommendations': []
    }

    # Check document completeness by reading file content
    all_content = ""
    for md_file in markdown_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                all_content += f.read()
        except:
            continue

    has_abstract = 'abstract' in all_content.lower()
    has_introduction = 'introduction' in all_content.lower()
    has_methodology = 'methodology' in all_content.lower()
    has_results = 'results' in all_content.lower() or 'experimental' in all_content.lower()
    has_conclusion = 'conclusion' in all_content.lower()

    score = 0
    if has_abstract: score += 15
    if has_introduction: score += 15
    if has_methodology: score += 20
    if has_results: score += 20
    if has_conclusion: score += 15

    readiness['completeness_score'] = score

    if score < 80:
        readiness['ready_for_publication'] = False
        readiness['missing_elements'].append("Document structure incomplete")

    # Check PDF generation
    if not pdf_files:
        readiness['ready_for_publication'] = False
        readiness['missing_elements'].append("No PDF files generated")

    # Check for citations
    citations = extract_citations_from_markdown(markdown_files)
    if not citations:
        readiness['recommendations'].append("Consider adding citations to related work")

    # Check for figures
    figure_count = len(re.findall(r'\\includegraphics', all_content))
    if figure_count == 0:
        readiness['recommendations'].append("Consider adding figures to illustrate key concepts")

    # Final assessment
    if readiness['ready_for_publication']:
        readiness['recommendations'].append("Project appears ready for publication!")
    else:
        readiness['recommendations'].append("Address missing elements before publication")

    return readiness


def generate_publication_metrics(metadata: PublicationMetadata) -> Dict[str, Any]:
    """Generate publication metrics for reporting.

    Args:
        metadata: Publication metadata

    Returns:
        Dictionary with publication metrics
    """
    # Calculate various metrics
    title_length = len(metadata.title)
    abstract_length = len(metadata.abstract)
    author_count = len(metadata.authors)
    keyword_count = len(metadata.keywords)

    # Estimate reading time (words per minute)
    abstract_words = len(metadata.abstract.split())
    reading_time_minutes = max(1, abstract_words // 200)  # 200 words per minute

    metrics = {
        'title_length': title_length,
        'abstract_length': abstract_length,
        'abstract_word_count': abstract_words,
        'author_count': author_count,
        'keyword_count': keyword_count,
        'reading_time_minutes': reading_time_minutes,
        'license_type': metadata.license,
        'has_doi': bool(metadata.doi),
        'publication_type': 'software' if 'template' in metadata.title.lower() else 'article',
        'complexity_score': calculate_complexity_score(metadata)
    }

    return metrics


def calculate_complexity_score(metadata: PublicationMetadata) -> int:
    """Calculate a complexity score for the publication.

    Args:
        metadata: Publication metadata

    Returns:
        Complexity score (0-100)
    """
    score = 0

    # Title complexity
    if len(metadata.title) > 30:
        score += 10
    if len(metadata.title) > 50:
        score += 10
    if len(metadata.title) > 100:
        score += 10

    # Abstract complexity
    if len(metadata.abstract) > 200:
        score += 10
    if len(metadata.abstract) > 500:
        score += 15
    if len(metadata.abstract) > 1000:
        score += 15

    # Author complexity
    if len(metadata.authors) > 1:
        score += 10
    if len(metadata.authors) > 3:
        score += 15

    # Keyword complexity
    if len(metadata.keywords) > 3:
        score += 10
    if len(metadata.keywords) > 5:
        score += 10
    if len(metadata.keywords) > 10:
        score += 10

    # DOI presence
    if metadata.doi:
        score += 15

    return min(100, score)


def create_repository_metadata(metadata: PublicationMetadata) -> str:
    """Create repository metadata for GitHub repository.

    Args:
        metadata: Publication metadata

    Returns:
        JSON-LD formatted repository metadata
    """
    repo_metadata = {
        "@context": "https://schema.org",
        "@type": "SoftwareSourceCode",
        "name": metadata.title,
        "description": metadata.abstract,
        "author": [
            {
                "@type": "Person",
                "name": author
            } for author in metadata.authors
        ],
        "keywords": metadata.keywords,
        "license": f"https://spdx.org/licenses/{metadata.license}",
        "programmingLanguage": "Python",
        "operatingSystem": "Cross-platform"
    }

    if metadata.repository_url:
        repo_metadata["codeRepository"] = metadata.repository_url

    if metadata.doi:
        repo_metadata["identifier"] = f"https://doi.org/{metadata.doi}"

    return json.dumps(repo_metadata, indent=2)


# =============================================================================
# DISSEMINATION EXTENSIONS
# =============================================================================

def publish_to_zenodo(
    metadata: PublicationMetadata,
    file_paths: List[Path],
    access_token: str,
    sandbox: bool = True
) -> str:
    """Publish to Zenodo.
    
    Args:
        metadata: Publication metadata
        file_paths: List of files to upload
        access_token: Zenodo API token
        sandbox: Use sandbox environment
        
    Returns:
        DOI of published deposition
    """
    from infrastructure.publishing.api import ZenodoClient, ZenodoConfig
    
    config = ZenodoConfig(access_token=access_token, sandbox=sandbox)
    client = ZenodoClient(config)
    
    # Create deposition
    dep_metadata = {
        "title": metadata.title,
        "upload_type": "publication",
        "publication_type": "article",
        "description": metadata.abstract,
        "creators": [{"name": author} for author in metadata.authors],
        "keywords": metadata.keywords,
        "license": metadata.license.lower()
    }
    
    dep_id = client.create_deposition(dep_metadata)
    
    # Upload files
    for path in file_paths:
        if path.exists():
            client.upload_file(dep_id, str(path))
            
    # Publish
    return client.publish(dep_id)


def prepare_arxiv_submission(
    output_dir: Path,
    metadata: PublicationMetadata
) -> Path:
    """Prepare submission package for arXiv.
    
    Args:
        output_dir: Directory containing build artifacts
        metadata: Publication metadata
        
    Returns:
        Path to generated .tar.gz file
    """
    import tarfile
    import shutil
    
    submission_dir = output_dir / "arxiv_submission"
    if submission_dir.exists():
        shutil.rmtree(submission_dir)
    submission_dir.mkdir()
    
    # Copy LaTeX sources
    tex_dir = output_dir.parent / "manuscript" # Assuming typical structure
    if tex_dir.exists():
        for item in tex_dir.glob("*"):
            if item.is_file() and item.suffix in ['.tex', '.bib', '.cls', '.bst']:
                shutil.copy2(item, submission_dir)
            elif item.is_dir() and item.name in ['figures']:
                shutil.copytree(item, submission_dir / item.name)
                
    # Create bbl file if it exists (arXiv needs it)
    bbl_file = output_dir / "pdf" / f"{metadata.title.replace(' ', '_')}.bbl"
    if bbl_file.exists():
        shutil.copy2(bbl_file, submission_dir)
        
    # Create tarball
    tar_path = output_dir / f"arxiv_submission_{datetime.now().strftime('%Y%m%d')}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(submission_dir, arcname="")
        
    return tar_path


def create_github_release(
    tag_name: str,
    release_name: str,
    description: str,
    assets: List[Path],
    token: str,
    repo: str
) -> str:
    """Create GitHub release.
    
    Args:
        tag_name: Git tag
        release_name: Release title
        description: Release notes
        assets: List of files to attach
        token: GitHub API token
        repo: Repository name (owner/repo)
        
    Returns:
        Release URL
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Create release
    url = f"https://api.github.com/repos/{repo}/releases"
    payload = {
        "tag_name": tag_name,
        "name": release_name,
        "body": description,
        "draft": False,
        "prerelease": False
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        release_data = response.json()
        upload_url = release_data["upload_url"].split("{")[0]
        html_url = release_data["html_url"]
        
        # Upload assets
        for asset in assets:
            if not asset.exists():
                continue
                
            name = asset.name
            with open(asset, "rb") as f:
                upload_headers = headers.copy()
                upload_headers["Content-Type"] = "application/octet-stream"
                requests.post(
                    f"{upload_url}?name={name}",
                    headers=upload_headers,
                    data=f
                )
                
        return html_url
        
    except requests.exceptions.RequestException as e:
        raise PublishingError(f"GitHub release failed: {e}")

