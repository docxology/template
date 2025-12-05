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

import hashlib
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import from split modules
from infrastructure.publishing.citations import (
    generate_citation_bibtex,
    generate_citation_apa,
    generate_citation_mla,
    generate_citations_markdown,
    format_authors_apa,
    format_authors_mla,
    extract_citations_from_markdown,
)
from infrastructure.publishing.metadata import (
    extract_publication_metadata,
    validate_doi,
    generate_publication_summary,
    create_academic_profile_data,
    generate_publication_metrics,
    calculate_complexity_score,
    create_repository_metadata,
)
from infrastructure.publishing.platforms import (
    publish_to_zenodo,
    prepare_arxiv_submission,
    create_github_release,
)
from infrastructure.publishing.models import (
    PublicationMetadata,
    CitationStyle,
)


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
    from infrastructure.publishing.citations import generate_citation_apa
    
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
    from infrastructure.publishing.citations import extract_citations_from_markdown
    
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
