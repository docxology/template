#!/usr/bin/env python3
"""Publication preparation script for prose project.

This script prepares academic publication materials including:
1. Metadata extraction from manuscript
2. Citation generation in multiple formats (BibTeX, APA, MLA)
3. Publication package creation
4. DOI validation and badge generation
5. Submission checklist creation
"""

import sys
from pathlib import Path
import json

# Add project src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Add infrastructure imports (with graceful fallback)
try:
    # Ensure repo root is on path for infrastructure imports
    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root))

    from infrastructure.publishing import (
        extract_publication_metadata,
        generate_citation_bibtex,
        generate_citation_apa,
        generate_citation_mla,
        generate_citations_markdown,
        create_publication_package,
        create_submission_checklist,
        validate_doi,
        generate_doi_badge,
        generate_publication_summary,
        create_publication_announcement,
        validate_publication_readiness,
        calculate_file_hash,
    )
    INFRASTRUCTURE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Infrastructure modules not available: {e}")
    INFRASTRUCTURE_AVAILABLE = False


def extract_manuscript_metadata():
    """Extract publication metadata from manuscript files."""
    if not INFRASTRUCTURE_AVAILABLE:
        print("⚠️  Skipping metadata extraction - infrastructure not available")
        return None

    print("Extracting publication metadata from manuscript...")

    # Find manuscript files
    manuscript_dir = project_root / "manuscript"
    markdown_files = list(manuscript_dir.glob("*.md"))

    if not markdown_files:
        print("⚠️  No markdown files found in manuscript directory")
        return None

    print(f"Found {len(markdown_files)} manuscript file(s)")

    # Extract metadata
    metadata = extract_publication_metadata(markdown_files)

    if metadata:
        print(f"✅ Extracted metadata for: {getattr(metadata, 'title', 'Unknown Title')}")
        print(f"   Authors: {len(getattr(metadata, 'authors', []))}")
        print(f"   DOI: {getattr(metadata, 'doi', 'Not specified')}")
    else:
        print("⚠️  No metadata extracted from manuscript files")
        return None

    return metadata


def generate_citations(metadata):
    """Generate citations in multiple formats."""
    if not metadata or not INFRASTRUCTURE_AVAILABLE:
        return None

    print("\nGenerating citations in multiple formats...")

    citations = {}

    try:
        # BibTeX format (for LaTeX)
        citations['bibtex'] = generate_citation_bibtex(metadata)
        print("✅ Generated BibTeX citation")

    except Exception as e:
        print(f"⚠️  Failed to generate BibTeX: {e}")

    try:
        # APA format (for manuscripts)
        citations['apa'] = generate_citation_apa(metadata)
        print("✅ Generated APA citation")

    except Exception as e:
        print(f"⚠️  Failed to generate APA: {e}")

    try:
        # MLA format (for humanities)
        citations['mla'] = generate_citation_mla(metadata)
        print("✅ Generated MLA citation")

    except Exception as e:
        print(f"⚠️  Failed to generate MLA: {e}")

    try:
        # Markdown format (for README files)
        citations['markdown'] = generate_citations_markdown(metadata)
        print("✅ Generated Markdown citations")

    except Exception as e:
        print(f"⚠️  Failed to generate Markdown citations: {e}")

    return citations


def validate_doi_info(metadata):
    """Validate DOI information and generate badge."""
    if not metadata or not INFRASTRUCTURE_AVAILABLE:
        return None

    doi = getattr(metadata, 'doi', None)
    if not doi:
        print("\n⚠️  No DOI specified in metadata")
        return None

    print(f"\nValidating DOI: {doi}")

    if validate_doi(doi):
        print("✅ DOI is valid")

        # Generate DOI badge
        try:
            badge_markdown = generate_doi_badge(doi)
            print("✅ Generated DOI badge")
            return badge_markdown
        except Exception as e:
            print(f"⚠️  Failed to generate DOI badge: {e}")
            return None
    else:
        print("❌ DOI validation failed")
        return None


def create_publication_materials(metadata, citations, doi_badge):
    """Create publication materials and save to output."""
    if not INFRASTRUCTURE_AVAILABLE:
        return None

    print("\nCreating publication materials...")

    output_dir = project_root / "output"
    citations_dir = output_dir / "citations"
    citations_dir.mkdir(parents=True, exist_ok=True)

    materials = {}

    # Save individual citation files
    if citations:
        for format_name, citation_text in citations.items():
            if citation_text:
                citation_file = citations_dir / f"citation_{format_name}.txt"
                with open(citation_file, 'w', encoding='utf-8') as f:
                    f.write(citation_text)
                materials[f"citation_{format_name}"] = citation_file
                print(f"✅ Saved {format_name.upper()} citation to: {citation_file.name}")

    # Save DOI badge if available
    if doi_badge:
        badge_file = citations_dir / "doi_badge.md"
        with open(badge_file, 'w', encoding='utf-8') as f:
            f.write(doi_badge)
        materials["doi_badge"] = badge_file
        print(f"✅ Saved DOI badge to: {badge_file.name}")

    # Create publication summary
    try:
        if metadata:
            summary = generate_publication_summary(metadata)
            if summary:
                summary_file = citations_dir / "publication_summary.md"
                with open(summary_file, 'w', encoding='utf-8') as f:
                    f.write(summary)
                materials["publication_summary"] = summary_file
                print(f"✅ Saved publication summary to: {summary_file.name}")
    except Exception as e:
        print(f"⚠️  Failed to generate publication summary: {e}")

    # Create publication announcement
    try:
        if metadata:
            announcement = create_publication_announcement(metadata)
            if announcement:
                announcement_file = citations_dir / "publication_announcement.md"
                with open(announcement_file, 'w', encoding='utf-8') as f:
                    f.write(announcement)
                materials["publication_announcement"] = announcement_file
                print(f"✅ Saved publication announcement to: {announcement_file.name}")
    except Exception as e:
        print(f"⚠️  Failed to generate publication announcement: {e}")

    # Save metadata as JSON
    if metadata:
        metadata_file = citations_dir / "publication_metadata.json"
        # Convert dataclass to dictionary for JSON serialization
        metadata_dict = {
            "title": getattr(metadata, 'title', None),
            "authors": getattr(metadata, 'authors', []),
            "abstract": getattr(metadata, 'abstract', None),
            "keywords": getattr(metadata, 'keywords', []),
            "doi": getattr(metadata, 'doi', None),
            "journal": getattr(metadata, 'journal', None),
            "conference": getattr(metadata, 'conference', None),
            "publication_date": getattr(metadata, 'publication_date', None),
            "publisher": getattr(metadata, 'publisher', None),
            "license": getattr(metadata, 'license', None),
            "repository_url": getattr(metadata, 'repository_url', None),
            "citation_count": getattr(metadata, 'citation_count', 0),
            "download_count": getattr(metadata, 'download_count', 0),
        }
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata_dict, f, indent=2, ensure_ascii=False)
        materials["metadata_json"] = metadata_file
        print(f"✅ Saved metadata JSON to: {metadata_file.name}")

    return materials


def create_submission_checklist(metadata):
    """Create submission checklist for academic venues."""
    if not metadata or not INFRASTRUCTURE_AVAILABLE:
        return None

    print("\nCreating submission checklist...")

    try:
        from infrastructure.publishing import create_submission_checklist as create_checklist
        checklist = create_checklist(metadata)
        if checklist:
            output_dir = project_root / "output" / "citations"
            checklist_file = output_dir / "submission_checklist.md"

            with open(checklist_file, 'w', encoding='utf-8') as f:
                f.write(checklist)

            print(f"✅ Saved submission checklist to: {checklist_file.name}")
            return checklist_file
    except Exception as e:
        print(f"⚠️  Failed to create submission checklist: {e}")

    return None


def validate_readiness(metadata):
    """Validate publication readiness."""
    if not metadata or not INFRASTRUCTURE_AVAILABLE:
        return None

    print("\nValidating publication readiness...")

    try:
        # Collect manuscript and PDF files for validation
        manuscript_dir = project_root / "manuscript"
        markdown_files = list(manuscript_dir.glob("*.md"))

        pdf_dir = project_root / "output" / "pdf"
        pdf_files = list(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []

        from infrastructure.publishing import validate_publication_readiness as validate_readiness_func
        validation_report = validate_readiness_func(markdown_files, pdf_files)
        if validation_report:
            output_dir = project_root / "output" / "reports"
            output_dir.mkdir(parents=True, exist_ok=True)

            report_file = output_dir / "publication_readiness.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("# Publication Readiness Report\n\n")

                # Format the validation report as markdown
                report_md = f"## Publication Readiness: {'✅ Ready' if validation_report.get('ready_for_publication', False) else '❌ Not Ready'}\n\n"
                report_md += f"**Completeness Score:** {validation_report.get('completeness_score', 0)}/100\n\n"

                if validation_report.get('missing_elements'):
                    report_md += "### Missing Elements\n\n"
                    for element in validation_report['missing_elements']:
                        report_md += f"- {element}\n"
                    report_md += "\n"

                if validation_report.get('recommendations'):
                    report_md += "### Recommendations\n\n"
                    for rec in validation_report['recommendations']:
                        report_md += f"- {rec}\n"
                    report_md += "\n"

                f.write(report_md)

            print(f"✅ Saved readiness report to: {report_file.name}")
            return report_file
    except Exception as e:
        print(f"⚠️  Failed to validate publication readiness: {e}")

    return None


def main():
    """Main publication preparation function."""
    print("Starting publication preparation...")
    print(f"Project root: {project_root}")

    if not INFRASTRUCTURE_AVAILABLE:
        print("❌ Infrastructure modules not available - cannot prepare publication materials")
        return

    # Extract metadata
    metadata = extract_manuscript_metadata()

    if not metadata:
        print("❌ Could not extract publication metadata - exiting")
        return

    # Generate citations
    citations = generate_citations(metadata)

    # Validate DOI
    doi_badge = validate_doi_info(metadata)

    # Create publication materials
    materials = create_publication_materials(metadata, citations, doi_badge)

    # Create submission checklist
    checklist = create_submission_checklist(metadata)

    # Validate readiness
    readiness_report = validate_readiness(metadata)

    print("\nPublication preparation complete!")
    print(f"Title: {getattr(metadata, 'title', 'Unknown')}")
    print(f"Authors: {len(getattr(metadata, 'authors', []))}")

    if materials:
        print(f"Generated materials: {len(materials)}")

    if checklist:
        print("Submission checklist created")

    if readiness_report:
        print("Readiness validation completed")

    print("\nOutput directory: output/citations/")


if __name__ == "__main__":
    main()