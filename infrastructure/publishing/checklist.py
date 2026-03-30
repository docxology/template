"""Submission checklist generation for academic conferences and journals."""

from __future__ import annotations

from infrastructure.publishing.models import PublicationMetadata


def create_submission_checklist(metadata: PublicationMetadata) -> str:
    """Create a submission checklist for academic conferences/journals.

    Args:
        metadata: Publication metadata

    Returns:
        Markdown formatted submission checklist
    """
    checklist = f"""# Submission Checklist for "{metadata.title}"

## Required Items

- [ ] **Title**: {metadata.title}
- [ ] **Authors**: {", ".join(metadata.authors)}
- [ ] **Abstract**: {len(metadata.abstract)} characters
- [ ] **Keywords**: {", ".join(metadata.keywords)}

## Document Requirements

- [ ] **PDF Format**: Generated using LaTeX/Pandoc
- [ ] **Page Limit**: Check conference/journal guidelines
- [ ] **Font Size**: 10-12pt as required
- [ ] **Margins**: 1-inch margins as standard
- [ ] **Line Spacing**: 1.5 or double as required

## Content Requirements

- [ ] **Abstract**: Clearly states contribution and results
- [ ] **Introduction**: Motivates the problem and approach
- [ ] **Related Work**: Properly cites relevant literature
- [ ] **Methodology**: Detailed enough for reproducibility
- [ ] **Experiments**: Comprehensive evaluation
- [ ] **Results**: Clear presentation of findings
- [ ] **Discussion**: Interprets results and limitations
- [ ] **Conclusion**: Summarizes contributions

## References and Citations

- [ ] **Complete Bibliography**: All references properly formatted
- [ ] **Citation Style**: Follows journal/conference requirements
- [ ] **DOI Links**: Working links for all citations
- [ ] **Self-Citations**: Appropriate and relevant

## Figures and Tables

- [ ] **High Quality**: All figures are clear and readable
- [ ] **Proper Captions**: Descriptive captions for all figures
- [ ] **Numbering**: Sequential numbering throughout
- [ ] **Accessibility**: Alt text and descriptions

## Reproducibility

- [ ] **Code Available**: Source code included or linked
- [ ] **Data Available**: Datasets provided or accessible
- [ ] **Instructions**: Clear setup and execution instructions
- [ ] **Dependencies**: All requirements specified

## Formatting and Style

- [ ] **Consistent Formatting**: Uniform style throughout
- [ ] **Proper Headings**: Hierarchical section structure
- [ ] **Equation Numbering**: Sequential and referenced
- [ ] **Table Formatting**: Professional appearance

## Final Checks

- [ ] **Proofreading**: No grammatical or spelling errors
- [ ] **Technical Accuracy**: All claims are correct
- [ ] **Completeness**: All sections are included
- [ ] **File Size**: Within submission limits

## Submission Timeline

- [ ] **Deadline**: [Insert submission deadline]
- [ ] **Review Period**: [Insert expected review time]
- [ ] **Camera Ready**: [Insert camera-ready deadline]

---

*This checklist was auto-generated from your project metadata. Update as needed for specific conference/journal requirements.*
"""  # noqa: E501

    return checklist
